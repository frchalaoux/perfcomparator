# Exporter un document Markdown en PDF

Le réglage d'orientation de l'extension VS Code **Markdown PDF** s'applique au
document entier. Cet exporteur fournit une mise en page mixte sélectionnable
par option CLI : le texte et les diagrammes portrait sont composés dans le même
flux de pagination ; les diagrammes paysage ont leurs propres pages A4.

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

La mise en page peut être choisie explicitement :

```bash
npm --prefix tools/markdown-pdf run export -- docs/strategie-publication.md --layout inline
```

Par défaut, le PDF est créé à côté du Markdown avec le même nom et l'extension
`.pdf`. Pour choisir un autre chemin :

```bash
npm --prefix tools/markdown-pdf run export -- docs/strategie-publication.md --output /chemin/vers/strategie.pdf
```

Avec `--layout inline`, les blocs de texte occupent des pages A4 portrait. Un
diagramme portrait reste entier et partage la page courante s'il y tient ; sinon
il passe à la suivante. Un diagramme plus large que haut est placé seul sur une
page A4 paysage. Les autres blocs de code restent du texte ordinaire. Les
images et liens relatifs sont résolus à partir du dossier du fichier Markdown.

Le script ne modifie pas le Markdown. Il ne traite pas les directives propres à
des extensions Markdown non standard ; utiliser la syntaxe Markdown prise en
charge par `markdown-it`. Il conserve les liens du Markdown. Le chargement des
images dépend de l'accès du navigateur aux fichiers ou aux URL concernés et
doit être vérifié sur le PDF obtenu. Si le PDF de sortie par défaut existe
déjà, le script s'arrête sans le modifier ; choisir explicitement une sortie
avec `--output` pour remplacer un fichier existant.
