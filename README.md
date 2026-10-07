# PerfComparator

PerfComparator, anciennement `benchmark-mac`, est une suite locale pour comparer
les performances de plusieurs machines avant un achat, ou celles de plusieurs
systèmes d'exploitation installés en multiboot sur une même machine. Elle
utilise les mêmes scénarios, paramètres et version exacte de CPython sur macOS,
Windows et Linux, puis produit des rapports JSON portables.

La stable actuelle est [`v0.5.0`](https://github.com/frchalaoux/perfcomparator/releases/tag/v0.5.0) ; la préversion de développement actuelle est [`v0.5.0.dev0`](https://github.com/frchalaoux/perfcomparator/releases/tag/v0.5.0.dev0).
Retrouver [tous les tags](https://github.com/frchalaoux/perfcomparator/tags).
Consulter la [stratégie de publication](docs/strategie-publication.md).
Télécharger l'application depuis la [page qui détecte votre système](https://frchalaoux.github.io/perfcomparator/).
Consulter le [guide d'installation pour macOS, Windows et Linux](docs/installation.md).
Consulter le [guide de désinstallation](docs/desinstallation.md).

Installation directe de la stable `v0.5.0` :

```sh
curl -LsSf https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.5.0/install.sh | sh
```

```powershell
irm https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.5.0/install.ps1 | iex
```

## Préversion publiée `v0.5.0.dev0`

Cette préversion ajoute un installateur graphique par système : il installe
`uv`, CPython avec Tk, PerfComparator et crée un lanceur de bureau. L'interface
ne se lance pas automatiquement à la fin de l'installation. L'installation
Windows via `install.bat` utilise PowerShell 7 s'il est présent, sinon Windows
PowerShell 5.1 ; l'installateur affiche la commande à utiliser pour ouvrir
l'interface ou configurer une contribution.
La page de téléchargement recommande l'archive macOS, Windows ou Linux en
fonction du système détecté. Les trois archives sont disponibles dans
la [release GitHub `v0.5.0.dev0`](https://github.com/frchalaoux/perfcomparator/releases/tag/v0.5.0.dev0).

`v0.4.0` conserve le protocole de mesure `0.3.0` et ajoute notamment
l'identification de l'année des Mac Apple lorsqu'elle est fiable ainsi qu'un
parcours de contribution qui explique comment compléter manuellement le nom.

```bash
curl -LsSf https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.4.0/install.sh | sh
```

```powershell
irm https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.4.0/install.ps1 | iex
```

## Préversion publiée `v0.4.0.dev7`

La préversion `0.4.0.dev7` enregistre l'année de commercialisation du Mac dans
`system.model_year` lorsqu'elle est déterminable. Lorsqu'elle ne l'est pas,
`contribute` explique que l'année peut être ajoutée au nom commercial si elle
est connue. Le format du rapport public et le protocole de mesure restent
inchangés.

Ses installateurs sont :

```bash
curl -LsSf https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.4.0.dev7/install.sh | sh
```

```powershell
irm https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.4.0.dev7/install.ps1 | iex
```

## Préversion antérieure publiée `v0.4.0.dev6`

La préversion `0.4.0.dev6` simplifie les contributions au catalogue : une pull
request ne contient plus que le rapport public. L'index est calculé depuis les
rapports lors du déploiement du site et n'est plus versionné, ce qui supprime
les échecs dus à un index périmé.

Ses installateurs sont :

```bash
curl -LsSf https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.4.0.dev6/install.sh | sh
```

```powershell
irm https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.4.0.dev6/install.ps1 | iex
```

## Préversion antérieure `v0.4.0.dev5`

La préversion `0.4.0.dev5` détecte, confirme et publie facultativement la
référence commerciale ou SKU de la machine. Windows utilise
`SystemSKUNumber`, Linux le champ DMI `product_sku`, et macOS la référence
officielle lorsqu'elle est exposée. Les UUID, numéros de série et références
Apple génériques contenant `xx` ne sont jamais collectés ou sont refusés.

Ses installateurs sont :

```bash
curl -LsSf https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.4.0.dev5/install.sh | sh
```

```powershell
irm https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.4.0.dev5/install.ps1 | iex
```

## Préversion antérieure `v0.4.0.dev4`

La préversion `0.4.0.dev4` détecte le fabricant, le nom du produit et
l'identifiant de modèle sur macOS, Windows et Linux. Avant une contribution,
l'utilisateur confirme ou corrige le nom commercial public affiché dans le
catalogue. Aucun numéro de série, UUID matériel ni nom d'hôte n'est exporté.

Ses installateurs sont :

```bash
curl -LsSf https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.4.0.dev4/install.sh | sh
```

```powershell
irm https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.4.0.dev4/install.ps1 | iex
```

## Préversion antérieure `v0.4.0.dev3`

La préversion `0.4.0.dev3` accepte l'export sûr des rapports privés de schéma
`3` ou `4` qui utilisent le protocole `0.3.0`. Elle clarifie aussi chaque état
de la contribution : pull request, validation, fusion automatique, déploiement
Pages, téléchargement puis comparaison locale.

Ses installateurs sont :

```bash
curl -LsSf https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.4.0.dev3/install.sh | sh
```

```powershell
irm https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.4.0.dev3/install.ps1 | iex
```

## Préversion antérieure `v0.4.0.dev2`

La préversion `0.4.0.dev2` ajoute `perfcomparator contribute`, un parcours guidé
qui choisit le rapport, construit et affiche l'export public, prépare GitHub CLI,
connecte le compte dans le navigateur et propose la pull request après une
confirmation distante explicite. `--dry-run` permet d'essayer tout le parcours
local sans connexion à GitHub.

Ses installateurs sont :

```bash
curl -LsSf https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.4.0.dev2/install.sh | sh
```

```powershell
irm https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.4.0.dev2/install.ps1 | iex
```

## Préversion antérieure `v0.4.0.dev1`

La préversion `0.4.0.dev1` permet d'exporter un rapport public strict, de le
valider, de le proposer au catalogue communautaire et de comparer directement
un rapport téléchargé. Le protocole de mesure reste `0.3.0`.

Ses installateurs sont :

```bash
curl -LsSf https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.4.0.dev1/install.sh | sh
```

```powershell
irm https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.4.0.dev1/install.ps1 | iex
```

## Préversion antérieure `v0.4.0.dev0`

La préversion `0.4.0.dev0` introduit le nom **PerfComparator**, le paquet
`perfcomparator` et la commande principale `perfcomparator`. La commande
`benchmark-mac` reste disponible comme alias pendant la transition. Le module
Python interne reste `benchmark_mac`, et le protocole de mesure reste `0.3.0` :
les rapports demeurent compatibles avec ceux de la famille `0.3.x` reconnue.
L'installateur remplace aussi l'ancien paquet enregistré par `uv`.

Ses installateurs sont :

```bash
curl -LsSf https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.4.0.dev0/install.sh | sh
```

```powershell
irm https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.4.0.dev0/install.ps1 | iex
```

## Versions publiées

Consulter [tous les tags disponibles](https://github.com/frchalaoux/perfcomparator/tags)
ou choisir une version ci-dessous.

| Version | Canal | À choisir pour | État |
| --- | --- | --- | --- |
| [`v0.5.0`](https://github.com/frchalaoux/perfcomparator/tree/v0.5.0) | Stable | Installer l'application graphique, afficher sa version et exporter des PDF | Version recommandée |
| [`v0.5.0.dev0`](https://github.com/frchalaoux/perfcomparator/tree/v0.5.0.dev0) | Développement publié | Tester les installateurs graphiques et les lanceurs par système | Préversion |
| [`v0.4.0`](https://github.com/frchalaoux/perfcomparator/tree/v0.4.0) | Stable antérieure | Utiliser l'année du modèle Apple et contribuer au catalogue | Remplacée par `v0.5.0` |
| [`v0.4.0.dev7`](https://github.com/frchalaoux/perfcomparator/tree/v0.4.0.dev7) | Développement publié | Identifier l'année du modèle Apple et contribuer clairement | Préversion |
| [`v0.4.0.dev6`](https://github.com/frchalaoux/perfcomparator/tree/v0.4.0.dev6) | Développement publié | Soumettre un seul rapport sans maintenir d'index | Préversion |
| [`v0.4.0.dev5`](https://github.com/frchalaoux/perfcomparator/tree/v0.4.0.dev5) | Développement publié | Identifier une configuration par sa référence commerciale facultative | Préversion |
| [`v0.4.0.dev4`](https://github.com/frchalaoux/perfcomparator/tree/v0.4.0.dev4) | Développement publié | Identifier les machines par leur nom commercial confirmé | Préversion |
| [`v0.4.0.dev3`](https://github.com/frchalaoux/perfcomparator/tree/v0.4.0.dev3) | Développement publié | Contribuer avec un ancien rapport compatible et suivre sa publication | Préversion |
| [`v0.4.0.dev2`](https://github.com/frchalaoux/perfcomparator/tree/v0.4.0.dev2) | Développement publié | Soumettre un rapport sans connaître Git | Préversion |
| [`v0.4.0.dev1`](https://github.com/frchalaoux/perfcomparator/tree/v0.4.0.dev1) | Développement publié | Publier et comparer des rapports communautaires | Préversion |
| [`v0.4.0.dev0`](https://github.com/frchalaoux/perfcomparator/tree/v0.4.0.dev0) | Développement publié | Tester le changement de nom et la migration | Préversion |
| [`v0.3.2`](https://github.com/frchalaoux/perfcomparator/tree/v0.3.2) | Stable antérieure | Conserver et comparer explicitement les protocoles | Remplacée par `v0.4.0` |
| [`v0.3.2.dev0`](https://github.com/frchalaoux/benchmark-mac/tree/v0.3.2.dev0) | Développement antérieur | Reproduire la validation du protocole mémorisé | Préversion publiée |
| [`v0.3.1`](https://github.com/frchalaoux/benchmark-mac/tree/v0.3.1) | Stable antérieure | Comparer clairement plusieurs machines | Remplacée par `v0.3.2` |
| [`v0.3.1.dev0`](https://github.com/frchalaoux/benchmark-mac/tree/v0.3.1.dev0) | Développement antérieur | Reproduire la validation de la correction CLI | Préversion publiée |
| [`v0.3.0`](https://github.com/frchalaoux/benchmark-mac/tree/v0.3.0) | Stable antérieure | Comparer CPU, mémoire, stockage, applications et GPU | Remplacée par `v0.3.1` |
| [`v0.3.0.dev2`](https://github.com/frchalaoux/benchmark-mac/tree/v0.3.0.dev2) | Développement antérieur | Reproduire les validations de la stable | Convention des tags explicitée |
| [`v0.3.0.dev1`](https://github.com/frchalaoux/benchmark-mac/tree/v0.3.0.dev1) | Développement antérieur | Tester les corrections Windows | Corrige l'installation et le PID 0 sous Windows |
| [`v0.3.0.dev0`](https://github.com/frchalaoux/benchmark-mac/tree/v0.3.0.dev0) | Développement antérieur | Reproduire une campagne existante | Problèmes d'installation et de contrôle préalable sous Windows |
| [`v0.2.1`](https://github.com/frchalaoux/benchmark-mac/tree/v0.2.1) | Stable antérieure | Reproduire une campagne sans GPU | Remplacée par `v0.3.0` |
| [`v0.2.0`](https://github.com/frchalaoux/benchmark-mac/tree/v0.2.0) | Stable antérieure | Reproduire une campagne existante | Échec SQLite possible sous Windows |
| [`v0.2.0.dev2`](https://github.com/frchalaoux/benchmark-mac/tree/v0.2.0.dev2) | Développement archivé | Reproduire une campagne de préversion | Base fonctionnelle de `v0.2.0` |
| [`v0.2.0.dev1`](https://github.com/frchalaoux/benchmark-mac/tree/v0.2.0.dev1) | Développement archivé | Reproduire une campagne existante | Comparaison multicœur trop stricte |
| [`v0.2.0.dev0`](https://github.com/frchalaoux/benchmark-mac/tree/v0.2.0.dev0) | Développement obsolète | Reproduire une ancienne campagne | Installateur incorrect par défaut |
| [`v0.1.0`](https://github.com/frchalaoux/benchmark-mac/tree/v0.1.0) | Stable antérieure | Reproduire les premiers rapports simples | Remplacée par `v0.2.1` |

La [fiche détaillée des versions](docs/versions.md) indique les différences,
les commandes d'installation pour chaque système et les précautions de mise à
jour. Les fonctionnalités décrites ci-dessous correspondent à la série `0.3` ;
les différences avec la stable sont signalées explicitement.

## Version stable antérieure `v0.3.2`

`v0.3.2` mémorise séparément `suite_version` et `protocol_version` dans les
nouveaux rapports. Elle conserve le protocole de mesure `0.3.0` et reste
compatible avec les rapports historiques reconnus de cette famille.

Sur macOS ou Linux :

```bash
curl -LsSf https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.3.2/install.sh | sh
```

Sous Windows, dans PowerShell :

```powershell
irm https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.3.2/install.ps1 | iex
```

Le contrôle `benchmark-mac --version` doit afficher `benchmark-mac 0.3.2`.

## Couverture actuelle

- **CPU** : entiers et flottants mono-cœur, SHA-256, compression zlib et calcul multicœur ;
- **mémoire** : bande passante de copie séquentielle ;
- **stockage** : lectures et écritures séquentielles et aléatoires de 4 Kio ;
- **applications** : traitement JSON et charge SQLite ;
- **GPU** : calcul FP32, bande passante, filtre d'image et rendu raster hors écran ;
- **inventaire** : modèle, OS, CPU, mémoire, GPU, disque et environnement Python.

Les mesures GPU utilisent `wgpu-py`, une petite couche WebGPU qui choisit Metal,
Direct3D 12 ou Vulkan selon le système. Elles ne nécessitent ni Blender, ni
fenêtre graphique, ni scène externe.

Une machine peut exposer plusieurs GPU. `perfcomparator info` les numérote ; par
défaut, la suite choisit d'abord un GPU dédié, puis un GPU intégré. Pour mesurer
chaque carte séparément, produire un rapport par indice :

```bash
perfcomparator run --group gpu --gpu 0 --label "Portable — GPU 0"
perfcomparator run --group gpu --gpu 1 --label "Portable — GPU 1"
```

Le GPU effectivement choisi est annoncé avant la campagne et enregistré dans
chaque résultat GPU.

Dans une machine virtuelle sans accélération graphique transmise, WebGPU peut
n'exposer que `Microsoft Basic Render Driver`, classé `CPU`. Ce moteur logiciel
est signalé et refusé pour éviter de présenter un score CPU comme une performance
GPU. Les douze autres benchmarks continuent normalement.

## Installation depuis GitHub

Python n'a pas besoin d'être installé. Le script installe `uv`, puis `uv`
télécharge et gère CPython 3.14.4 avant d'installer l'application.

### Préversion antérieure `v0.3.1.dev0`

Cette préversion affiche, pour chaque machine candidate, son propre écart et sa
propre conclusion dans le détail CLI. La première machine reste explicitement
la référence 100.

Sur macOS ou Linux :

```bash
curl -LsSf https://raw.githubusercontent.com/frchalaoux/benchmark-mac/v0.3.1.dev0/install.sh | sh
```

Sous Windows, dans PowerShell :

```powershell
irm https://raw.githubusercontent.com/frchalaoux/benchmark-mac/v0.3.1.dev0/install.ps1 | iex
```

Le contrôle `benchmark-mac --version` doit afficher
`benchmark-mac 0.3.1.dev0`.

### Version stable `v0.3.1`

Sur macOS ou Linux :

```bash
curl -LsSf https://raw.githubusercontent.com/frchalaoux/benchmark-mac/v0.3.1/install.sh | sh
```

Sous Windows, dans PowerShell :

```powershell
irm https://raw.githubusercontent.com/frchalaoux/benchmark-mac/v0.3.1/install.ps1 | iex
```

Cette version installe CPython 3.14.4, met automatiquement à niveau un ancien
`uv` si nécessaire et remplace toute version précédente de l'outil. Vérifier
l'installation avec `benchmark-mac --version`, qui doit afficher
`benchmark-mac 0.3.1`.

### Préversion antérieure `v0.3.0.dev2`

Cette préversion reste disponible pour reproduire les campagnes de validation
de la stable. Sous Windows, la mise à niveau de `uv` s'exécute dans un processus
enfant et le pseudo-processus PID 0 est ignoré.

> **Convention des préversions :** les tags suivent la forme `vX.Y.Z.devK`.
> Ce tag s'écrit donc exactement `v0.3.0.dev2`. Les points font partie
> du nom Git et doivent être conservés dans les URL et les commandes.

Sur macOS ou Linux :

```bash
curl -LsSf https://raw.githubusercontent.com/frchalaoux/benchmark-mac/v0.3.0.dev2/install.sh | sh
```

Sous Windows, dans PowerShell :

```powershell
irm https://raw.githubusercontent.com/frchalaoux/benchmark-mac/v0.3.0.dev2/install.ps1 | iex
```

L'installateur emploie `uv tool install --reinstall` : la même commande permet
donc aussi de passer d'une version antérieure à cette préversion. Vérifier le
résultat avec `benchmark-mac --version`, qui doit afficher
`benchmark-mac 0.3.0.dev2`.

`v0.2.0.dev0` reste téléchargeable pour la reproductibilité, mais son
installateur nécessite un contournement détaillé dans la
[fiche des versions](docs/versions.md#installer-lancienne-v020dev0).

Vérifier ensuite l'installation :

```bash
perfcomparator --version
uv tool list
perfcomparator list
perfcomparator compare --help
```

Avec une version `0.3.x`, employer l'ancienne commande `benchmark-mac`.

## Installation depuis le dossier de développement

```bash
./install.sh
```

ou simplement :

```bash
uv sync
uv run perfcomparator list
```

## Lancer les benchmarks

Avant de lancer une campagne comparable :

1. brancher le portable au secteur et sélectionner le mode de performances à
   utiliser sur toutes les machines ;
2. fermer navigateurs, synchronisations, mises à jour, jeux, rendus, machines
   virtuelles et autres tâches lourdes ;
3. attendre quelques minutes après le démarrage ou une charge importante, dans
   une pièce aux conditions aussi proches que possible ;
4. conserver le même profil, le même nombre de passages et, pour le stockage,
   le même type d'emplacement `--work-dir`.

Au démarrage, PerfComparator observe pendant une seconde la charge CPU, la
mémoire, l'échange et les processus actifs. Il affiche un avertissement si le
point de départ paraît éloigné du repos, puis poursuit la mesure. Ce contrôle
ponctuel aide à repérer une mauvaise campagne ; il ne peut pas prouver que la
machine a atteint son potentiel maximal.

Toute la suite, avec le profil standard :

```bash
perfcomparator run --label "MacBook Pro M4 Pro"
```

Chaque test est exécuté trois fois par défaut et le rapport conserve la médiane,
le minimum, le maximum et la dispersion. Le nombre de passages est réglable :

```bash
perfcomparator run --repeat 5 --profile thorough
```

Un groupe ou plusieurs groupes :

```bash
perfcomparator run --group cpu
perfcomparator run --group memory --group storage --profile thorough
perfcomparator run --group gpu --profile standard
```

Un ou plusieurs tests individuels :

```bash
perfcomparator run cpu.integer
perfcomparator run cpu.hash memory.copy application.sqlite --profile quick
```

Le catalogue complet est fourni par `perfcomparator list`. La commande
`perfcomparator describe cpu.hash` affiche le protocole, les limites et les
références d'un test. Les profils `quick`, `standard` et `thorough` augmentent
progressivement les durées et volumes.

## Exporter un rapport public

Cette commande est disponible à partir de la préversion `0.4.0.dev1`.

Un rapport de campagne privé contient des informations de diagnostic qui ne
doivent pas être publiées directement. La commande `export-public` reconstruit
un fichier distinct depuis une liste blanche, localement et sans envoi réseau :

```bash
perfcomparator export-public data/results/benchmark_….json \
  --output rapport-public.json \
  --machine-name "Apple MacBook Pro 15 pouces (2018)" \
  --machine-sku "MR942FN/A" \
  --accept-cc0
```

`--accept-cc0` confirme que les données exportées pourront être diffusées sous
licence CC0 1.0. `--machine-name` permet de confirmer le nom commercial affiché
dans le catalogue. `--machine-sku` ajoute facultativement la référence exacte
de la configuration, jamais son numéro de série. Sans ces options,
PerfComparator emploie les informations matérielles disponibles. L'export
retire notamment le label libre, la date précise, les
chemins, processus, PID, messages d'échec, versions détaillées du système,
informations de disque, numéro de série, UUID matériels et nom d'hôte. Il porte
un identifiant de contenu déterministe et la mention `community-unverified` :
l'anonymisation et la validation du format ne certifient jamais le nom de la
machine ni les performances déclarées.

Le [contrat complet du format public](docs/format-rapport-public.md) précise les
données conservées et les limites de confidentialité.

Le [tutoriel catalogue de A à Z](docs/tutoriel-catalogue.md) décrit tout le
parcours : mesure, export, contribution GitHub, téléchargement et comparaison.

Un fichier reçu se contrôle localement avant toute utilisation :

```bash
perfcomparator validate-public rapport-public.json
```

Cette validation borne la taille à 2 Mio, refuse les champs inconnus et vérifie
le protocole, les unités, paramètres, échantillons, dispersions et l'identifiant
de contenu. Elle ne constitue pas une certification des scores.

### Contribution guidée

À partir de `0.4.0.dev2`, aucune connaissance de Git ou du shell n'est requise :

```bash
perfcomparator contribute
```

La commande propose les rapports récents, demande le consentement CC0, puis
fait confirmer un nom commercial public et une référence commerciale
facultative proposés à partir du matériel détecté.
Elle conserve un export relisible sous `data/public/`, puis affiche précisément
les opérations distantes avant de créer ou réutiliser le fork et d'ouvrir la
pull request.
GitHub CLI est installé dans le dossier utilisateur par l'installateur
PerfComparator, depuis une archive officielle épinglée et vérifiée par SHA-256.
La création éventuelle du compte et la vérification de son adresse restent dans
le navigateur.

**Contribution envoyée** signifie que la pull request a été créée. Le catalogue
enchaîne ensuite automatiquement sa validation, sa fusion si elle ne contient
que le rapport public attendu, la génération de l'index, puis le déploiement
GitHub Pages. Le rapport devient alors visible dans le
[catalogue web](https://frchalaoux.github.io/perfcomparator-results/). Une
contribution invalide reste ouverte avec son erreur.
GitHub peut encore demander au mainteneur d'autoriser le contrôle initial de la
première contribution provenant d'un fork ; après ce contrôle, la suite est
automatique.

Un essai strictement local s'exécute ainsi :

```bash
perfcomparator contribute --dry-run
```

Depuis le catalogue web, le bouton **Télécharger le JSON** fournit un rapport
directement utilisable :

```bash
perfcomparator compare mon-rapport-local.json rapport-telecharge.json \
  --html comparaison.html
```

## Comparer plusieurs machines

Copier les rapports JSON dans un même dossier, puis utiliser le premier comme
référence :

```bash
perfcomparator compare mac-m4.json pc-ryzen.json
```

À partir de `0.4.0.dev1`, chaque fichier peut être un rapport privé, un rapport
public téléchargé depuis le catalogue, ou un mélange des deux. Les rapports
publics sont revalidés automatiquement avant le calcul.

Pour obtenir le rapport visuel autonome et adapter le résultat à ses usages :

```bash
perfcomparator compare mac-m4.json pc-ryzen.json pc-intel.json \
  --weight developpement=50 \
  --weight creation=30 \
  --weight quotidien=20 \
  --html comparaison.html
```

Le premier rapport est la référence 100. Le HTML traduit les rapports en
indices, écarts qualitatifs et temps équivalents. Il contient des barres, un
graphique d'écart pour deux machines, une carte thermique pour plusieurs
machines, des chronologies et un résumé en langage courant.

La comparaison exige des versions de protocole compatibles, le même profil et
la même version de Python. `0.3.0.dev1`, `0.3.0.dev2`, `0.3.0`, `0.3.1.dev0`,
`0.3.1`, `0.3.2.dev0`, `0.3.2`, `0.4.0.dev0`, `0.4.0.dev1`, `0.4.0.dev2` et
`0.4.0.dev3`, `0.4.0.dev4`, `0.4.0.dev5`, `0.4.0.dev6` et `0.4.0.dev7` sont compatibles entre
elles. Les
rapports sont enregistrés dans
`data/results/` par défaut. Les nouvelles campagnes conservent séparément la
version exacte de la suite (`suite_version`) et celle du protocole
de mesure (`protocol_version`). Deux versions différentes de la suite restent
donc comparables lorsqu'elles déclarent le même protocole. Pour les anciens
rapports sans ce champ, la table de compatibilité historique reste appliquée.
Une différence dont les plages min–max se chevauchent est signalée comme non
concluante. Les rapports `0.2.x` et `0.3.x` ne sont pas directement comparables,
car le catalogue, les scénarios et le schéma JSON ont évolué.

## Développement

```bash
uv sync
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv build
```

Consulter la [documentation](DOCUMENTATION.md) pour le protocole de mesure et
l'architecture du projet.
