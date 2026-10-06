# Versions disponibles et installation

## Version stable `v0.5.0`

[Consulter le code source de `v0.5.0`](https://github.com/frchalaoux/perfcomparator/tree/v0.5.0) ·
[Télécharger les installateurs](https://github.com/frchalaoux/perfcomparator/releases/tag/v0.5.0)

Cette stable réunit les installateurs graphiques pour macOS, Windows et Linux,
l'affichage de la version dans l'interface et les options d'export PDF.
Les étapes complètes sont dans le [guide d'installation par système](installation.md).

```bash
curl -LsSf https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.5.0/install.sh | sh
```

```powershell
irm https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.5.0/install.ps1 | iex
```

Après installation, `perfcomparator --version` affiche `PerfComparator 0.5.0`.
La préversion de développement actuelle est
[`v0.5.0.dev0`](https://github.com/frchalaoux/perfcomparator/releases/tag/v0.5.0.dev0) ;
la page des [tags](https://github.com/frchalaoux/perfcomparator/tags) recense
toutes les versions publiées.

## Préversion publiée `v0.5.0.dev0`

[Consulter le code source de `v0.5.0.dev0`](https://github.com/frchalaoux/perfcomparator/tree/v0.5.0.dev0)

Cette version ajoute les installateurs graphiques macOS, Windows et Linux :
ils installent `uv`, CPython avec Tk et PerfComparator, puis créent un raccourci.
L'interface ne s'ouvre pas automatiquement. La page de téléchargement détecte
le système pour recommander le bon fichier. Les trois archives sont disponibles
dans la [release GitHub `v0.5.0.dev0`](https://github.com/frchalaoux/perfcomparator/releases/tag/v0.5.0.dev0).
Les étapes complètes sont dans le [guide d'installation par système](installation.md).

```bash
curl -LsSf https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.5.0.dev0/install.sh | sh
```

```powershell
irm https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.5.0.dev0/install.ps1 | iex
```

Après installation, `perfcomparator --version` affiche
`PerfComparator 0.5.0.dev0`.

La page GitHub [Tags](https://github.com/frchalaoux/perfcomparator/tags) est la
liste de référence des versions publiées. Un tag fige le code et permet de
réinstaller exactement la même suite sur plusieurs machines.

## Choisir une version

### `v0.4.0` — stable antérieure

[Consulter le code source de `v0.4.0`](https://github.com/frchalaoux/perfcomparator/tree/v0.4.0)

Cette version rend disponible l'année de commercialisation du Mac dans le
rapport local lorsqu'elle est déterminable et précise dans `contribute` que
l'utilisateur peut compléter manuellement le nom commercial. Le protocole de
mesure reste `0.3.0` et le format de rapport public est inchangé.

```bash
curl -LsSf https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.4.0/install.sh | sh
```

```powershell
irm https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.4.0/install.ps1 | iex
```

Après installation, `perfcomparator --version` affiche `PerfComparator 0.4.0`.
La préversion de développement actuelle est
[`v0.5.0.dev0`](https://github.com/frchalaoux/perfcomparator/tree/v0.5.0.dev0) ;
la page [de tous les tags](https://github.com/frchalaoux/perfcomparator/tags)
recense les versions publiées.

### `v0.4.0.dev7` — développement publié

[Consulter le code source de `v0.4.0.dev7`](https://github.com/frchalaoux/perfcomparator/tree/v0.4.0.dev7)

Cette préversion enregistre l'année de commercialisation du Mac dans le rapport
local lorsque l'identification est fiable. Pour les modèles ambigus, la demande
du nom dans `contribute` indique que l'année connue peut être saisie dans le nom
commercial. Le format public et le protocole `0.3.0` restent inchangés.

```bash
curl -LsSf https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.4.0.dev7/install.sh | sh
```

```powershell
irm https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.4.0.dev7/install.ps1 | iex
```

Après installation, `perfcomparator --version` affiche
`PerfComparator 0.4.0.dev7`.

### `v0.4.0.dev6` — développement publié

[Consulter le code source de `v0.4.0.dev6`](https://github.com/frchalaoux/perfcomparator/tree/v0.4.0.dev6)

Cette préversion simplifie la contribution au catalogue. La pull request ne
contient plus que le rapport public ; l'index est généré depuis les rapports au
moment du déploiement GitHub Pages et n'est plus versionné. Le protocole de
mesure reste `0.3.0`.

```bash
curl -LsSf https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.4.0.dev6/install.sh | sh
```

```powershell
irm https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.4.0.dev6/install.ps1 | iex
```

Après installation, `perfcomparator --version` affiche
`PerfComparator 0.4.0.dev6`.

### `v0.4.0.dev5` — développement publié

[Consulter le code source de `v0.4.0.dev5`](https://github.com/frchalaoux/perfcomparator/tree/v0.4.0.dev5)

Cette préversion ajoute une référence commerciale ou SKU facultative. Elle est
détectée depuis `SystemSKUNumber` sous Windows, le DMI `product_sku` sous Linux
et les informations officielles disponibles sous macOS, puis confirmée avant
publication. Le format public v3 refuse les UUID et les références Apple
génériques contenant `xx`. Les formats publics v1 et v2 restent acceptés. Le
protocole de mesure reste `0.3.0`.

```bash
curl -LsSf https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.4.0.dev5/install.sh | sh
```

```powershell
irm https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.4.0.dev5/install.ps1 | iex
```

Le contrôle `perfcomparator --version` devra afficher
`PerfComparator 0.4.0.dev5`.

### `v0.4.0.dev4` — développement publié

[Consulter le code source de `v0.4.0.dev4`](https://github.com/frchalaoux/perfcomparator/tree/v0.4.0.dev4)

Cette préversion détecte le fabricant, le nom du produit et l'identifiant de
modèle sur macOS, Windows et Linux. Le parcours de contribution demande de
confirmer ou corriger le nom commercial public avant l'export. Le format public
v2 expose cette identité non unique, mais jamais le numéro de série, les UUID
matériels ni le nom d'hôte. Les rapports publics v1 restent acceptés. Le
protocole de mesure reste `0.3.0` et la stable recommandée reste `v0.3.2`.

Commandes d'installation :

```bash
curl -LsSf https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.4.0.dev4/install.sh | sh
```

```powershell
irm https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.4.0.dev4/install.ps1 | iex
```

Le contrôle `perfcomparator --version` devra afficher
`PerfComparator 0.4.0.dev4`.

### `v0.4.0.dev3` — développement publié

[Consulter le code source de `v0.4.0.dev3`](https://github.com/frchalaoux/perfcomparator/tree/v0.4.0.dev3)

Cette préversion accepte les rapports privés de schéma `3` ou `4` lorsque leur
protocole est `0.3.0`. Elle décrit aussi sans ambiguïté la création de la pull
request, sa validation et sa fusion automatiques, le déploiement du catalogue,
le téléchargement et la comparaison locale. Le protocole de mesure reste
`0.3.0` et la stable recommandée reste `v0.3.2`.

Commandes d'installation :

```bash
curl -LsSf https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.4.0.dev3/install.sh | sh
```

```powershell
irm https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.4.0.dev3/install.ps1 | iex
```

Le contrôle `perfcomparator --version` devra afficher
`PerfComparator 0.4.0.dev3`.

### `v0.4.0.dev2` — développement publié

[Consulter le code source de `v0.4.0.dev2`](https://github.com/frchalaoux/perfcomparator/tree/v0.4.0.dev2)

Cette préversion ajoute `perfcomparator contribute`. Le parcours interactif
choisit un rapport, construit et affiche son export public, prépare une version
officielle épinglée de GitHub CLI, puis crée le fork, la branche et la pull
request par l'API GitHub après une confirmation distante explicite. Git n'est
pas requis. `--dry-run` réalise tout le contrôle local sans connexion GitHub.
Le protocole de mesure reste `0.3.0` et la stable recommandée reste `v0.3.2`.

Commandes d'installation :

```bash
curl -LsSf https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.4.0.dev2/install.sh | sh
```

```powershell
irm https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.4.0.dev2/install.ps1 | iex
```

Le contrôle `perfcomparator --version` devra afficher
`PerfComparator 0.4.0.dev2`.

### `v0.4.0.dev1` — développement publié

[Consulter le code source de `v0.4.0.dev1`](https://github.com/frchalaoux/perfcomparator/tree/v0.4.0.dev1)

Cette préversion ajoute l'export public par liste blanche, la validation locale
du format communautaire et la comparaison directe des rapports publics
téléchargés. Le tutoriel accompagne la mesure, la contribution au catalogue et
la comparaison de bout en bout. Le protocole de mesure reste `0.3.0` et la
stable recommandée reste `v0.3.2`.

Commandes d'installation :

```bash
curl -LsSf https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.4.0.dev1/install.sh | sh
```

```powershell
irm https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.4.0.dev1/install.ps1 | iex
```

Le contrôle `perfcomparator --version` devra afficher
`PerfComparator 0.4.0.dev1`.

### `v0.4.0.dev0` — développement publié

[Consulter le code source de `v0.4.0.dev0`](https://github.com/frchalaoux/perfcomparator/tree/v0.4.0.dev0)

Cette préversion réalise le changement de nom vers **PerfComparator** sans
modifier le protocole de mesure `0.3.0`. Le paquet devient `perfcomparator` et
la commande principale devient `perfcomparator`; `benchmark-mac` reste un alias
de compatibilité. La stable recommandée reste `v0.3.2`. Lors d'une mise à
niveau, l'installateur retire l'ancien
enregistrement `uv`, puis installe PerfComparator avec l'alias historique.

Commandes d'installation :

```bash
curl -LsSf https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.4.0.dev0/install.sh | sh
```

```powershell
irm https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.4.0.dev0/install.ps1 | iex
```

Le contrôle `perfcomparator --version` devra afficher
`PerfComparator 0.4.0.dev0`.

### `v0.3.2` — stable antérieure

[Consulter le code source de `v0.3.2`](https://github.com/frchalaoux/perfcomparator/tree/v0.3.2)

Cette stable reprend `protocol_version` sans modifier le protocole de mesure
`0.3.0`. Elle reste compatible avec les rapports historiques reconnus de cette
famille.

### `v0.3.2.dev0` — développement publié

[Consulter le code source de `v0.3.2.dev0`](https://github.com/frchalaoux/benchmark-mac/tree/v0.3.2.dev0)

Cette préversion ajoute `protocol_version` aux nouveaux rapports sans
modifier le protocole de mesure `0.3.0`. Elle conserve la version exacte du
logiciel dans `suite_version` et compare automatiquement des versions de suite
différentes lorsqu'elles déclarent le même protocole. Les anciens rapports sans
ce champ restent pris en charge par la table historique.

Sur macOS ou Linux :

```bash
curl -LsSf https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.3.2.dev0/install.sh | sh
```

```powershell
irm https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.3.2.dev0/install.ps1 | iex
```

Le contrôle `benchmark-mac --version` doit afficher `benchmark-mac 0.3.2.dev0`.

### `v0.3.1` — stable antérieure

[Consulter le code source de `v0.3.1`](https://github.com/frchalaoux/benchmark-mac/tree/v0.3.1)

Cette version stabilise la correction des comparaisons CLI de plus de deux
machines : chaque candidate affiche son propre écart et sa propre conclusion.
Le protocole de mesure reste identique à celui de `v0.3.0`.

### `v0.3.1.dev0` — développement antérieur

[Consulter le code source de `v0.3.1.dev0`](https://github.com/frchalaoux/benchmark-mac/tree/v0.3.1.dev0)

Cette préversion corrige la sortie texte des comparaisons de plus de deux
machines : chaque candidate affiche désormais son propre écart et sa propre
conclusion, tandis que la première machine est clairement indiquée comme
référence. Le protocole de mesure ne change pas.

### `v0.3.0` — stable antérieure

[Consulter le code source de `v0.3.0`](https://github.com/frchalaoux/benchmark-mac/tree/v0.3.0)

Cette version stable reprend les quatre benchmarks GPU WebGPU, la sélection
d'adaptateur, le contrôle préalable de la machine et les corrections Windows
validés dans les préversions `dev1` et `dev2`. Elle refuse les moteurs WebGPU
logiciels afin de ne pas présenter un score CPU comme une performance GPU.

Les rapports `0.3.0.dev1`, `0.3.0.dev2`, `0.3.0`, `0.3.1.dev0`, `0.3.1`,
`0.3.2.dev0`, `0.3.2`, `0.4.0.dev0`, `0.4.0.dev1`, `0.4.0.dev2`,
`0.4.0.dev3`, `0.4.0.dev4`, `0.4.0.dev5`, `0.4.0.dev6` et `0.4.0.dev7` emploient le
même protocole de mesure et peuvent être comparés entre eux. `0.3.0.dev0` reste
exclue de ce groupe de compatibilité.

### `v0.3.0.dev2` — développement antérieur

[Consulter le code source de `v0.3.0.dev2`](https://github.com/frchalaoux/benchmark-mac/tree/v0.3.0.dev2)

Cette candidate conserve les fonctionnalités GPU de `dev0` et corrige la mise
à niveau automatique de `uv` sous Windows. Le script officiel est téléchargé
dans un fichier temporaire puis exécuté dans un processus PowerShell enfant :
son éventuel `exit` ne peut plus fermer la console principale. Elle ignore
également le pseudo-processus Windows PID 0 pendant le contrôle préalable et
refuse les moteurs WebGPU logiciels classés `CPU`, tels que
`Microsoft Basic Render Driver`.

Cette révision explicite aussi la convention durable `vX.Y.Z.devK` dans les
instructions du projet, le README et les guides.

### `v0.3.0.dev1` — développement antérieur

[Consulter le code source de `v0.3.0.dev1`](https://github.com/frchalaoux/benchmark-mac/tree/v0.3.0.dev1)

Cette préversion introduit les corrections Windows reprises dans `dev2` : mise
à niveau de `uv` dans un processus PowerShell enfant, exclusion du PID 0 et
refus des moteurs WebGPU logiciels classés `CPU`.

### `v0.3.0.dev0` — développement publié

[Consulter le code source de `v0.3.0.dev0`](https://github.com/frchalaoux/benchmark-mac/tree/v0.3.0.dev0)

Cette préversion ajoute :

- quatre mesures GPU WebGPU sans Blender : FP32, mémoire, filtre d'image et raster ;
- la sélection d'un adaptateur sur les machines multi-GPU avec `--gpu INDEX` ;
- un contrôle préalable du CPU, de la mémoire, de l'échange et des processus actifs ;
- la conservation de cet état initial et de ses avertissements dans le JSON ;
- le scénario `jeu-3d` et l'intégration du GPU aux scénarios de comparaison ;
- le titre HTML « Ce que ces performances changent au quotidien » ;
- l'option globale `benchmark-mac --version` ;
- la mise à niveau automatique d'un `uv` trop ancien pour CPython 3.14.4 ;
- le schéma JSON 4.

Elle doit être validée sur plusieurs configurations macOS, Windows et Linux
avant de devenir stable. Les rapports `0.2.x` et `0.3.x` ne doivent pas être
mélangés dans une comparaison.

Sous Windows, la reprise automatique de `dev0` présente toutefois un défaut :
elle injecte l'installateur officiel de `uv` dans la session en cours. Si celui-ci
appelle `exit`, la console peut se fermer avant la reprise de `benchmark-mac`.
Mettre `uv` à niveau séparément ou utiliser `v0.3.0.dev2`.

Pour reproduire malgré tout une campagne `dev0`, après mise à niveau préalable
de `uv` sous Windows :

```bash
curl -LsSf https://raw.githubusercontent.com/frchalaoux/benchmark-mac/v0.3.0.dev0/install.sh | sh
```

```powershell
irm https://raw.githubusercontent.com/frchalaoux/benchmark-mac/v0.3.0.dev0/install.ps1 | iex
```

### `v0.2.1` — stable antérieure

[Consulter le code source de `v0.2.1`](https://github.com/frchalaoux/benchmark-mac/tree/v0.2.1)

Cette version reprend toutes les fonctions de `v0.2.0` et corrige l'échec
`WinError 32` de `application.sqlite` sous Windows. La connexion SQLite est
désormais fermée explicitement avant la suppression du répertoire temporaire.

### `v0.2.0` — stable antérieure

[Consulter le code source de `v0.2.0`](https://github.com/frchalaoux/benchmark-mac/tree/v0.2.0)

Cette version stable ajoute notamment :

- trois passages par benchmark par défaut, réglables de un à neuf ;
- médiane, valeurs brutes, minimum, maximum et dispersion dans le rapport JSON ;
- capture de l'alimentation et des conditions thermiques accessibles ;
- indices base 100, catégories techniques et six scénarios d'usage ;
- pondérations personnalisables et temps de travail équivalents ;
- comparaison de deux machines ou davantage ;
- rapport HTML autonome avec barres, carte thermique et chronologies.

Tous les rapports à comparer doivent employer des versions de protocole
compatibles, le même profil et la même version de Python.

Cette révision corrige la comparaison `cpu.multicore` : le nombre de processus
peut varier selon les processeurs logiques disponibles sur chaque machine, sans
relâcher la vérification des autres paramètres du protocole.

Sous Windows, `application.sqlite` peut néanmoins échouer avec `WinError 32`
pendant le nettoyage. Utiliser `v0.2.1` pour toute nouvelle campagne.

### `v0.2.0.dev2` — développement archivé

[Consulter le code source de `v0.2.0.dev2`](https://github.com/frchalaoux/benchmark-mac/tree/v0.2.0.dev2)

Cette préversion contient les fonctions et la correction multicœur reprises
dans `v0.2.0`. Préférer `v0.2.1` pour toute nouvelle campagne.

### `v0.2.0.dev1` — développement antérieur

[Consulter le code source de `v0.2.0.dev1`](https://github.com/frchalaoux/benchmark-mac/tree/v0.2.0.dev1)

Cette version corrige les installateurs de `dev0`, mais refuse la comparaison
`cpu.multicore` lorsque les machines possèdent un nombre différent de
processeurs logiques. Préférer `v0.2.1` pour une nouvelle campagne.

### `v0.2.0.dev0` — développement obsolète

[Consulter le code source de `v0.2.0.dev0`](https://github.com/frchalaoux/benchmark-mac/tree/v0.2.0.dev0)

Cette version contient les mêmes grandes fonctions expérimentales, mais son
README et ses installateurs ciblent `v0.1.0` par défaut. Elle reste disponible
pour reproduire une ancienne campagne ; toute nouvelle installation doit
préférer `v0.2.1`.

### `v0.1.0` — stable antérieure

[Consulter le code source de `v0.1.0`](https://github.com/frchalaoux/benchmark-mac/tree/v0.1.0)

Cette première version stable fournit :

- 12 benchmarks CPU, mémoire, stockage et applications ;
- les profils `quick`, `standard` et `thorough` ;
- l'exécution complète, par groupe ou par test ;
- l'inventaire matériel et les rapports JSON ;
- une comparaison tabulaire simple en valeurs et pourcentages.

Elle ne contient pas les répétitions automatiques, la dispersion, les scénarios
pondérés ni le rapport HTML de `v0.2.1`.

## Installer `v0.3.2`

Python n'a pas besoin d'être préinstallé. L'installateur récupère `uv` si
nécessaire, puis `uv` gère CPython 3.14.4 et remplace la version de
`benchmark-mac` éventuellement installée. Si un ancien `uv` ne connaît pas ce
Python, l'installateur met automatiquement `uv` à niveau et réessaie.

### macOS et Linux

```bash
curl -LsSf https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.3.2/install.sh | sh
```

### Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.3.2/install.ps1 | iex
```

Le contrôle suivant doit afficher `benchmark-mac 0.3.2` :

```bash
benchmark-mac --version
```

## Installer la stable `v0.3.0`

### macOS et Linux

```bash
curl -LsSf https://raw.githubusercontent.com/frchalaoux/benchmark-mac/v0.3.0/install.sh | sh
```

### Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/frchalaoux/benchmark-mac/v0.3.0/install.ps1 | iex
```

## Installer la stable `v0.2.1`

Python n'a pas besoin d'être préinstallé. L'installateur récupère `uv`, puis
`uv` gère CPython 3.14.4 et l'outil isolé.

### macOS et Linux

Copier la commande entière, sans crochets ni parenthèses Markdown :

```bash
curl -LsSf https://raw.githubusercontent.com/frchalaoux/benchmark-mac/v0.2.1/install.sh | sh
```

### Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/frchalaoux/benchmark-mac/v0.2.1/install.ps1 | iex
```

### Ancien `uv` sous Windows

L'installateur historique de `v0.2.1` réutilise le `uv` présent sans vérifier
s'il connaît CPython 3.14.4. Avec une version ancienne telle que `uv 0.5.1`, la
commande peut échouer avec `No download found`. Mettre alors `uv` à niveau et
placer sa version officielle en tête du `PATH` pour la session :

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
$env:Path = "$HOME\.local\bin;$env:Path"
uv --version
irm https://raw.githubusercontent.com/frchalaoux/benchmark-mac/v0.2.1/install.ps1 | iex
```

`v0.3.0.dev2` automatise cette reprise sans exécuter l'installateur tiers dans
la console principale.

## Installer l'ancienne `v0.2.0`

Cette version est conservée pour reproduire une campagne existante. Sous
Windows, son benchmark SQLite peut échouer pendant le nettoyage ; préférer
`v0.2.1`.

### macOS et Linux

```bash
curl -LsSf https://raw.githubusercontent.com/frchalaoux/benchmark-mac/v0.2.0/install.sh | sh
```

### Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/frchalaoux/benchmark-mac/v0.2.0/install.ps1 | iex
```

## Installer l'ancienne `v0.2.0.dev2`

Ces commandes servent uniquement à reproduire une campagne de préversion. Pour
une nouvelle comparaison, utiliser `v0.2.1`.

### macOS et Linux

```bash
curl -LsSf https://raw.githubusercontent.com/frchalaoux/benchmark-mac/v0.2.0.dev2/install.sh | sh
```

### Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/frchalaoux/benchmark-mac/v0.2.0.dev2/install.ps1 | iex
```

## Installer l'ancienne `v0.2.0.dev1`

Ces commandes servent à reproduire une campagne existante. Pour une nouvelle
comparaison entre machines, utiliser `v0.2.1`.

### macOS et Linux

```bash
curl -LsSf https://raw.githubusercontent.com/frchalaoux/benchmark-mac/v0.2.0.dev1/install.sh | sh
```

### Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/frchalaoux/benchmark-mac/v0.2.0.dev1/install.ps1 | iex
```

## Installer l'ancienne `v0.2.0.dev0`

Cette procédure sert uniquement à reproduire une campagne existante. La source
doit être imposée explicitement pour contourner l'erreur de son installateur.

### macOS et Linux

```bash
curl -LsSf https://raw.githubusercontent.com/frchalaoux/benchmark-mac/v0.2.0.dev0/install.sh \
  | BENCHMARK_MAC_SOURCE="https://github.com/frchalaoux/benchmark-mac/archive/refs/tags/v0.2.0.dev0.tar.gz" sh
```

### Windows PowerShell

```powershell
$env:BENCHMARK_MAC_SOURCE = "https://github.com/frchalaoux/benchmark-mac/archive/refs/tags/v0.2.0.dev0.tar.gz"
irm https://raw.githubusercontent.com/frchalaoux/benchmark-mac/v0.2.0.dev0/install.ps1 | iex
Remove-Item Env:BENCHMARK_MAC_SOURCE
```

## Installer `v0.1.0`

### macOS et Linux

```bash
curl -LsSf https://raw.githubusercontent.com/frchalaoux/benchmark-mac/v0.1.0/install.sh | sh
```

### Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/frchalaoux/benchmark-mac/v0.1.0/install.ps1 | iex
```

## Vérifier la version installée

`uv tool list` affiche la version du paquet installé. Les deux commandes
suivantes vérifient ensuite que l'exécutable et le catalogue fonctionnent :

```bash
benchmark-mac --version
uv tool list
benchmark-mac list
benchmark-mac describe cpu.hash
```

La commande suivante permet de vérifier la comparaison. Dans la version de
développement, son aide doit notamment présenter les options `--html` et
`--weight` :

```bash
benchmark-mac compare --help
```

## Changer de version

Les installateurs utilisent `uv tool install --reinstall`. Il suffit donc de
lancer la commande complète de la version souhaitée. Conserver dans le nom des
rapports la version utilisée et ne pas comparer directement des rapports issus
de versions différentes.

## Portée des versions

Toutes ces versions utilisent CPython 3.14.4 afin de rendre les résultats plus
comparables et prennent en charge macOS, Windows et Linux. Jusqu'à `v0.2.1`, le
GPU est seulement inventorié. La série `0.3` ajoute les mesures WebGPU communes,
mais ne couvre pas le ray tracing, les unités IA, les codecs vidéo matériels ou
un moteur de jeu complet.
