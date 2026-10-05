# Exporter un document Markdown en PDF

Le réglage d'orientation de l'extension VS Code **Markdown PDF** s'applique au
document entier. Pour garder le texte en portrait tout en donnant à chaque
diagramme Mermaid sa propre page A4 orientée selon ses proportions, utiliser
l'exporteur du dépôt. Il découpe le document aux blocs Mermaid, rend chaque
segment de texte et chaque diagramme séparément, puis assemble les pages dans
l'ordre original en un PDF unique.

## Prérequis

- Node.js 22.13 ou plus récent et npm ;
- une connexion Internet lors de la première installation des dépendances ;
- le navigateur Chromium installé par Puppeteer pendant cette installation.

Depuis la racine du dépôt, installer les dépendances une seule fois :

```bash
npm --prefix tools/markdown-pdf ci
```

Puis exporter le fichier voulu :

```bash
npm --prefix tools/markdown-pdf run export -- docs/strategie-publication.md
```

Par défaut, le PDF est créé à côté du Markdown avec le même nom et l'extension
`.pdf`. Pour choisir un autre chemin :

```bash
npm --prefix tools/markdown-pdf run export -- docs/strategie-publication.md --output /chemin/vers/strategie.pdf
```

Les blocs de texte occupent des pages A4 portrait, une page ou plus selon leur
contenu. Chaque bloc Mermaid est une page A4 autonome : portrait si le diagramme
est plus haut que large, paysage s'il est plus large que haut. Les
autres blocs de code restent du texte ordinaire. Les images et liens relatifs
sont résolus à partir du dossier du fichier Markdown.

Le script ne modifie pas le Markdown. Il ne traite pas les directives propres à
des extensions Markdown non standard ; utiliser la syntaxe Markdown prise en
charge par `markdown-it`. Il conserve les liens du Markdown. Le chargement des
images dépend de l'accès du navigateur aux fichiers ou aux URL concernés et
doit être vérifié sur le PDF obtenu. Si le PDF de sortie par défaut existe
déjà, le script s'arrête sans le modifier ; choisir explicitement une sortie
avec `--output` pour remplacer un fichier existant.
