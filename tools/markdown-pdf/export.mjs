import { spawnSync } from 'node:child_process';
import { access, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

import MarkdownIt from 'markdown-it';
import puppeteer from 'puppeteer';
import { PDFDocument } from 'pdf-lib';

const toolDir = path.dirname(fileURLToPath(import.meta.url));
const mmdc = path.join(
  toolDir,
  'node_modules',
  '.bin',
  process.platform === 'win32' ? 'mmdc.cmd' : 'mmdc',
);
const markdown = new MarkdownIt({ html: true, linkify: true, typographer: true });

function usage() {
  console.error('Usage: npm run export -- <input.md> [-o|--output <output.pdf>]');
  process.exit(2);
}

function parseArgs(args) {
  let input;
  let output;
  let outputExplicit = false;
  for (let i = 0; i < args.length; i += 1) {
    if (args[i] === '-o' || args[i] === '--output') {
      output = args[++i];
      outputExplicit = true;
      if (!output) usage();
    } else if (args[i].startsWith('-')) {
      usage();
    } else if (input) {
      usage();
    } else {
      input = args[i];
    }
  }
  if (!input) usage();
  const invocationDir = process.env.INIT_CWD || process.cwd();
  return {
    input: path.resolve(invocationDir, input),
    output: path.resolve(invocationDir, output ?? input.replace(/\.md$/i, '') + '.pdf'),
    outputExplicit,
  };
}

function splitDocument(source) {
  const lines = source.split(/(?<=\n)/);
  const sections = [];
  let textLines = [];
  let index = 0;

  const flushText = () => {
    if (textLines.some((line) => line.trim())) {
      sections.push({ type: 'text', markdown: textLines.join('') });
    }
    textLines = [];
  };

  while (index < lines.length) {
    const opening = lines[index].match(/^\s{0,3}(`{3,}|~{3,})\s*mermaid\b[^\r\n]*(?:\r?\n)?$/i);
    if (!opening) {
      textLines.push(lines[index]);
      index += 1;
      continue;
    }

    flushText();
    const fence = opening[1];
    const body = [];
    index += 1;
    let closed = false;
    while (index < lines.length) {
      if (new RegExp(`^\\s{0,3}${fence[0]}{${fence.length},}\\s*(?:\\r?\\n)?$`).test(lines[index])) {
        closed = true;
        index += 1;
        break;
      }
      body.push(lines[index]);
      index += 1;
    }
    if (!closed) throw new Error('Bloc Mermaid non terminé : clôturez-le avec les backticks ou tildes correspondants.');
    sections.push({ type: 'diagram', source: body.join('').replace(/\s+$/, '') });
  }
  flushText();
  return sections;
}

function htmlDocument(body, baseUrl) {
  return `<!doctype html><html lang="fr"><head><meta charset="utf-8">
    <base href="${baseUrl}">
    <style>
      @page { size: A4 portrait; margin: 18mm 17mm; }
      body { color: #202124; font: 11pt/1.48 Arial, sans-serif; }
      h1, h2, h3, h4 { line-height: 1.2; page-break-after: avoid; }
      pre, blockquote, table, img { page-break-inside: avoid; }
      pre { white-space: pre-wrap; overflow-wrap: anywhere; }
      table { border-collapse: collapse; width: 100%; }
      th, td { border: 1px solid #999; padding: 5px 7px; vertical-align: top; }
      th { background: #eee; }
      img { max-width: 100%; }
      a { color: #0645ad; }
    </style></head><body>${body}</body></html>`;
}

async function renderText(browser, section, baseUrl) {
  const page = await browser.newPage();
  try {
    await page.setContent(htmlDocument(markdown.render(section.markdown), baseUrl), {
      waitUntil: 'networkidle0',
    });
    return await page.pdf({ format: 'A4', printBackground: true, preferCSSPageSize: true });
  } finally {
    await page.close();
  }
}

function renderMermaidSvg(inputPath, outputPath) {
  const result = spawnSync(mmdc, ['-i', inputPath, '-o', outputPath], {
    encoding: 'utf8',
    shell: process.platform === 'win32',
  });
  if (result.status !== 0) {
    throw new Error(`Échec du rendu Mermaid :\n${result.stderr || result.stdout || 'erreur inconnue'}`);
  }
}

function svgRatio(svg) {
  const viewBox = svg.match(/\bviewBox=["']\s*([\d.+-]+)[ ,]+([\d.+-]+)[ ,]+([\d.+-]+)[ ,]+([\d.+-]+)\s*["']/i);
  if (viewBox) {
    const width = Number(viewBox[3]);
    const height = Number(viewBox[4]);
    if (width > 0 && height > 0) return width / height;
  }
  const width = svg.match(/\bwidth=["']([\d.]+)(px)?["']/i);
  const height = svg.match(/\bheight=["']([\d.]+)(px)?["']/i);
  if (width && height && Number(height[1]) > 0) return Number(width[1]) / Number(height[1]);
  throw new Error('Impossible de déterminer le ratio du diagramme Mermaid rendu.');
}

async function renderDiagram(browser, svg) {
  const landscape = svgRatio(svg) > 1;
  const page = await browser.newPage();
  try {
    await page.setContent(`<!doctype html><html><head><meta charset="utf-8"><style>
      @page { size: A4 ${landscape ? 'landscape' : 'portrait'}; margin: 10mm; }
      html, body { width: 100%; height: 100%; margin: 0; }
      body { display: flex; align-items: center; justify-content: center; }
      svg { display: block; max-width: 100%; max-height: 100%; width: auto; height: auto; }
    </style></head><body>${svg}</body></html>`, { waitUntil: 'load' });
    return await page.pdf({
      format: 'A4',
      landscape,
      printBackground: true,
      preferCSSPageSize: true,
    });
  } finally {
    await page.close();
  }
}

async function main() {
  const { input, output, outputExplicit } = parseArgs(process.argv.slice(2));
  if (!outputExplicit) {
    try {
      await access(output);
      throw new Error(`Le fichier existe déjà : ${output}\nChoisissez une autre sortie avec --output pour éviter de l'écraser.`);
    } catch (error) {
      if (error.code !== 'ENOENT') throw error;
    }
  }
  const source = await readFile(input, 'utf8');
  const sections = splitDocument(source);
  const workDir = await mkdtemp(path.join(os.tmpdir(), 'perfcomparator-markdown-pdf-'));
  let browser;
  const fragments = [];
  let diagramNumber = 0;

  try {
    browser = await puppeteer.launch({ headless: true });
    const baseUrl = pathToFileURL(`${path.dirname(input)}${path.sep}`).href;
    for (const section of sections) {
      if (section.type === 'text') {
        fragments.push(await renderText(browser, section, baseUrl));
      } else {
        diagramNumber += 1;
        const mermaidInput = path.join(workDir, `diagram-${diagramNumber}.mmd`);
        const svgPath = path.join(workDir, `diagram-${diagramNumber}.svg`);
        await writeFile(mermaidInput, section.source, 'utf8');
        renderMermaidSvg(mermaidInput, svgPath);
        const svg = await readFile(svgPath, 'utf8');
        fragments.push(await renderDiagram(browser, svg));
        console.log(`Diagramme ${diagramNumber} : page A4 ${svgRatio(svg) > 1 ? 'paysage' : 'portrait'}`);
      }
    }

    const result = await PDFDocument.create();
    for (const fragment of fragments) {
      const pdf = await PDFDocument.load(fragment);
      const pages = await result.copyPages(pdf, pdf.getPageIndices());
      pages.forEach((page) => result.addPage(page));
    }
    await writeFile(output, await result.save());
    console.log(`PDF créé : ${output}`);
  } finally {
    if (browser) await browser.close();
    await rm(workDir, { recursive: true, force: true });
  }
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
