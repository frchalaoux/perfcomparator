# Tutoriel complet : publier puis comparer un rapport communautaire

Ce parcours part d'une machine à mesurer et va jusqu'à une comparaison locale
avec un rapport téléchargé depuis le catalogue. Une contribution publie
uniquement l'export public sous CC0 1.0. Le rapport privé produit par `run`
reste sur votre machine.

Le catalogue accepte des rapports communautaires non certifiés. Ses contrôles
prouvent la conformité et l'intégrité du fichier, pas l'identité de la machine
ni l'exactitude de ses performances.

## Ce qui se passe réellement

`perfcomparator contribute` ne publie pas immédiatement le rapport dans le
catalogue. La commande prépare une proposition que le catalogue contrôle avant
de l'accepter :

| Étape | État du rapport | Responsable |
| --- | --- | --- |
| `perfcomparator contribute` termine | Pull request ouverte, rapport absent du site | Participant |
| Le contrôle `validate` réussit | Rapport conforme, mais toujours absent du site | GitHub Actions |
| La pull request conforme est fusionnée dans `main` | Rapport intégré au catalogue | GitHub Actions |
| Le déploiement Pages réussit | Rapport visible et téléchargeable dans l'interface web | GitHub Actions |

Le message **Contribution envoyée** signifie donc « pull request créée », pas
« rapport déjà publié ». Aucune action supplémentaire n'est demandée si le
contrôle réussit : le dépôt fusionne automatiquement une contribution qui
contient uniquement le nouveau rapport, génère l'index lors du déploiement,
puis redéploie le site. Si le contrôle échoue, la pull request reste ouverte et
affiche l'erreur.
Pour la toute première contribution provenant d'un fork, GitHub peut demander
au mainteneur d'autoriser le démarrage du contrôle. Une fois `validate` lancé,
la fusion et la publication ne demandent plus d'intervention.

L'interface publique est disponible ici :
<https://frchalaoux.github.io/perfcomparator-results/>.

## Parcours guidé recommandé

À partir de `0.4.0.dev2`, toute la contribution tient dans une commande :

```bash
perfcomparator contribute
```

Le menu choisit un rapport récent, demande le consentement CC0, puis propose un
nom commercial public et une référence commerciale facultative à confirmer ou
corriger. Il affiche les données
publiques, prépare GitHub CLI et ouvre le navigateur pour connecter ou créer le
compte GitHub. Il annonce ensuite précisément la création ou la réutilisation
du fork, la branche distante créée et la pull request, puis attend une
confirmation explicite. Conservez l'adresse de la pull request affichée à la
fin : elle permet de suivre la validation et la fusion.

Pour s'entraîner sans connexion ni modification GitHub :

```bash
perfcomparator contribute --dry-run
```

Les sections suivantes détaillent les mêmes opérations et conservent le parcours
manuel utile au diagnostic.

## 1. Installer la version qui prend en charge le catalogue

Le parcours guidé est disponible dans la stable actuelle, PerfComparator
`v0.5.0`, ainsi que dans les versions ultérieures compatibles.

Sur macOS ou Linux :

```bash
curl -LsSf https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.5.0/install.sh | sh
```

Sous Windows, dans PowerShell :

```powershell
irm https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.5.0/install.ps1 | iex
```

Contrôler l'installation :

```console
$ perfcomparator --version
PerfComparator 0.5.0
```

## 2. Mesurer la machine

Brancher un portable au secteur, fermer les tâches lourdes et conserver les
mêmes conditions sur les machines à comparer. Le profil `standard` et trois
passages constituent le parcours courant :

```bash
perfcomparator run --profile standard --repeat 3 --label "Ma machine — configuration"
```

La commande affiche le chemin du rapport privé, créé sous `data/results/` par
défaut. `perfcomparator history` permet de le retrouver. Ce fichier contient
des informations de diagnostic et ne doit jamais être ajouté au catalogue.

## 3. Créer et contrôler l'export public

Remplacer le nom ci-dessous par le chemin réellement affiché par `run` :

```bash
perfcomparator export-public data/results/benchmark_20260928_120000_000000.json \
  --output rapport-public.json \
  --machine-name "Apple MacBook Pro 15 pouces (2018)" \
  --machine-sku "MR942FN/A" \
  --accept-cc0
perfcomparator validate-public rapport-public.json
```

Sous PowerShell, écrire la première commande sur une seule ligne ou remplacer
les `\` de continuation par des accents graves. Adapter `--machine-name` au nom
sous lequel la machine est vendue et `--machine-sku` à sa référence exacte.
Omettre cette dernière si elle est inconnue ; ne jamais saisir un numéro de
série. Ces déclarations communautaires ne sont pas certifiées par le
constructeur. `--accept-cc0` donne le consentement explicite à la diffusion de
l'export sous CC0 1.0.

La validation affiche un identifiant de la forme :

```text
Identifiant : sha256:0123456789abcdef…
```

Relire le JSON même après validation. Le format retire notamment le label
libre, la date précise, les chemins, les processus, les PID, les messages
d'échec, les informations de disque, le numéro de série, les UUID matériels et
le nom d'hôte, mais une combinaison matérielle rare peut rester reconnaissable.

## 4. Préparer manuellement la contribution GitHub

1. Ouvrir le dépôt
   [`perfcomparator-results`](https://github.com/frchalaoux/perfcomparator-results)
   et utiliser **Fork**.
2. Cloner le fork, puis créer une branche :

   ```bash
   git clone https://github.com/VOTRE-COMPTE/perfcomparator-results.git
   cd perfcomparator-results
   git switch -c add/community-report
   ```

3. Renommer `rapport-public.json` avec les 64 caractères hexadécimaux de son
   `report_id`, sans `sha256:`, puis le copier sous
   `reports/protocol-0.3.0/`. Par exemple :

   ```text
   reports/protocol-0.3.0/0123456789abcdef…89abcdef.json
   ```

4. Installer les outils du dépôt et exécuter son contrôle groupé :

   ```bash
   uv sync --locked --dev
   uv run python scripts/build_catalog.py validate
   uv run pytest -q
   node --test tests/test_catalog_ui.mjs
   ```

   Le déploiement construit l'index à partir des rapports validés. Cet index
   n'est pas versionné et ne doit pas être ajouté à la contribution.

5. Vérifier que seul le rapport public attendu est ajouté, puis proposer la
   pull request :

   ```bash
   git status --short
   git add reports/protocol-0.3.0/*.json
   git commit -m "Add community benchmark report"
   git push -u origin add/community-report
   ```

   Ouvrir ensuite la pull request suggérée par GitHub. Le contrôle automatique
   répète la validation du format, du nom et de l'emplacement.

La création de la pull request termine le travail du participant. Elle ne
publie pas encore le rapport. Le contrôle `validate` vérifie les données ; si
la contribution contient uniquement le nouveau rapport, un second workflow la
fusionne automatiquement dans `main` et demande le déploiement GitHub Pages.
Celui-ci génère l'index depuis les rapports présents. Lorsque **Deploy GitHub
Pages** est vert, le rapport apparaît dans le
[catalogue public](https://frchalaoux.github.io/perfcomparator-results/).

## 5. Télécharger et comparer

1. Ouvrir le
   [catalogue public](https://frchalaoux.github.io/perfcomparator-results/).
2. Filtrer éventuellement par système ou profil.
3. Cliquer sur **Télécharger le JSON** dans la fiche choisie. Le navigateur
   enregistre un fichier dont le nom est l'identifiant du rapport.
4. Placer ce fichier dans le dossier depuis lequel la commande sera exécutée,
   ou conserver son chemin complet.

Vérifier ensuite le fichier reçu :

```bash
perfcomparator validate-public catalogue-machine.json
```

Comparer ensuite ce rapport à votre rapport privé local. Le premier fichier
reste la référence 100 :

```bash
perfcomparator compare \
  data/results/benchmark_20260928_120000_000000.json \
  catalogue-machine.json \
  --html comparaison.html
```

Deux rapports publics téléchargés peuvent être comparés de la même façon. Pour
un rapport public v2 ou v3, le nom commercial remplace le label libre retiré
lors de l'export. Les anciens rapports v1 utilisent encore le processeur comme
nom de repli.

La comparaison exige le même protocole, le même profil et la même version de
Python. Elle ne compare que les benchmarks présents dans tous les fichiers. Les
plages min–max qui se chevauchent produisent une conclusion prudente, et le
rapport HTML reste entièrement local. Si le catalogue n'affiche pas encore le
rapport, vérifier d'abord que sa pull request est fusionnée et que le workflow
**Deploy GitHub Pages** a réussi.

## En cas de refus

- **Identifiant incorrect** : le fichier a changé après son export ; refaire
  l'export au lieu de modifier manuellement le JSON.
- **Nom incorrect** : reprendre exactement les 64 caractères après
  `sha256:` dans `report_id`.
- **Emplacement incorrect** : utiliser le dossier qui correspond à
  `protocol_version`, actuellement `reports/protocol-0.3.0/`.
- **Rapports incompatibles** : refaire les campagnes avec le même profil et
  une version de PerfComparator qui emploie le même protocole.
- **Index du site incorrect** : vérifier les rapports présents dans `main`,
  puis relancer le déploiement Pages ; aucun index n'est à modifier dans Git.

Le [format public](format-rapport-public.md) détaille le contrat de données et
le [guide utilisateur](guide-utilisateur.md) explique les conditions de mesure
et l'interprétation des indices.
