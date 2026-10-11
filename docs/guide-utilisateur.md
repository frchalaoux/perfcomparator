# Guide utilisateur

## Interface Web locale

L'interface Web locale affiche l'état de PCWEB et de PCE. Dans cette première
version, elle sert à vérifier que les deux serveurs locaux sont disponibles ;
les campagnes se lancent depuis la ligne de commande.

Après l'installation, double-cliquer sur l'icône ou le raccourci
**PerfComparator** créé par l'installateur. Pour démarrer les deux serveurs et
ouvrir l'interface dans le navigateur depuis un terminal :

```bash
perfcomparator start
```

L'installateur prépare `uv`, Python géré par `uv`, PCE et PCWEB, puis crée les
raccourcis. L'interface ne s'ouvre pas automatiquement à la fin de
l'installation. Le raccourci ouvre la page locale dans le navigateur. Pour les
étapes propres à chaque système, consulter le
[guide d'installation](installation.md).

Les serveurs peuvent aussi être gérés séparément : les commandes
`perfcomparator engine start`, `perfcomparator engine stop` et
`perfcomparator engine status` pilotent PCE seul. `perfcomparator web stop` et
`perfcomparator web status` pilotent PCWEB seul. `perfcomparator web start`
reste un alias historique pour démarrer les deux serveurs ; le raccourci
principal est `perfcomparator start`. `perfcomparator stop` arrête PCWEB puis
PCE.

## Préparer une machine

L'installateur GitHub installe `uv` si nécessaire. `uv` installe ensuite sa
propre version de CPython 3.14.4 et isole PerfComparator du Python du système.
Il n'est donc pas nécessaire d'installer Python séparément.

À partir de `0.3.0.dev1`, si un `uv` déjà présent est trop ancien pour connaître
CPython 3.14.4, l'installateur retente automatiquement l'opération après avoir
installé la version actuelle de `uv` dans un processus PowerShell enfant. Cette
isolation empêche l'installateur tiers de fermer la console principale et est
notamment nécessaire avec d'anciennes versions telles que `uv 0.5.1`.

La version réellement exécutée se vérifie avec :

```bash
perfcomparator --version
```

La stable actuelle et les préversions disponibles sont répertoriées dans la
[fiche des versions](versions.md). Les préversions suivent la convention
`vX.Y.Z.devK`, avec tous leurs points. La commande principale est
`perfcomparator` ; l'ancienne commande `benchmark-mac` reste un alias de
compatibilité.

Avant une mesure :

1. brancher un portable sur secteur ;
2. sélectionner le même type de mode d'alimentation sur chaque machine
   (performances, équilibré, etc.) et désactiver l'économie d'énergie ;
3. terminer les mises à jour et synchronisations, fermer les navigateurs très
   chargés, jeux, encodages, rendus, machines virtuelles et outils de compilation ;
4. attendre quelques minutes après le démarrage ou une charge soutenue afin que
   l'activité de fond et la température se stabilisent ;
5. employer des versions de protocole compatibles, le même profil, le même
   nombre de passages et des conditions ambiantes aussi proches que possible.

Juste avant les tests, le programme échantillonne pendant une seconde la charge
CPU totale, la mémoire disponible, l'échange et les processus les plus actifs.
Il signale notamment un CPU occupé à au moins 15 %, moins de 20 % de mémoire
disponible, au moins 10 % d'échange utilisé ou un processus consommant au moins
10 % de CPU. La campagne continue afin de ne pas rendre l'outil fragile, mais
il est préférable de l'interrompre et de la recommencer au repos. L'observation
et ses avertissements sont enregistrés dans le rapport JSON.

Ce contrôle est un instantané, pas une certification : une tâche peut démarrer
après l'échantillon, et certains services protégés ne livrent pas tous leurs
détails. Les processus affichés sont une aide au diagnostic ; il ne faut pas
arrêter un processus système que l'on ne reconnaît pas. Sous Windows, le
pseudo-processus PID 0 (« System Idle Process ») est ignoré : il représente le
temps CPU inoccupé et non une application concurrente.

## Choisir l'étendue

`perfcomparator list` affiche les identifiants, groupes et profils disponibles.
`perfcomparator describe IDENTIFIANT` donne le protocole détaillé, ses limites et
ses références bibliographiques.

- `perfcomparator run` lance les 16 tests ;
- `perfcomparator run --group cpu` lance le groupe CPU ;
- `perfcomparator run --group gpu` lance les quatre mesures GPU hors écran ;
- `perfcomparator run cpu.integer` lance un seul test ;
- plusieurs `--group` et plusieurs identifiants peuvent être réunis sans doublon.

### Machines équipées de plusieurs GPU

`perfcomparator info` affiche les adaptateurs WebGPU avec un indice, leur nom,
leur type et le backend utilisé. Sans option, la sélection automatique préfère
un GPU dédié, puis un GPU intégré. Elle est affichée avant toute mesure GPU.

Un rapport ne mesure qu'un seul adaptateur afin que son interprétation reste
sans ambiguïté. Pour comparer les cartes d'une même machine ou forcer le GPU
intégré d'un portable hybride, exécuter deux campagnes distinctes :

```bash
perfcomparator run --group gpu --gpu 0 --label "PC hybride — GPU 0"
perfcomparator run --group gpu --gpu 1 --label "PC hybride — GPU 1"
```

Les indices sont propres à la machine : vérifier `perfcomparator info` sur
chacune d'elles au lieu de supposer que `0` désigne toujours le GPU dédié.

Dans une machine virtuelle sans GPU transmis, `Microsoft Basic Render Driver`
peut apparaître avec le type `CPU`. Il s'agit d'un moteur logiciel. La suite
refuse alors les quatre résultats GPU afin de ne pas les confondre avec les
performances d'une carte physique, mais poursuit tous les autres groupes.

Les profils sont :

- `quick` pour vérifier rapidement une machine ;
- `standard` pour une comparaison courante ;
- `thorough` pour des mesures plus longues et des fichiers disque plus grands.

Chaque benchmark est répété trois fois par défaut. `--repeat 5` demande cinq
passages, dans la limite de neuf. Le score principal est la médiane ; le rapport
conserve aussi toutes les valeurs, le minimum, le maximum et l'étendue relative.

Le répertoire passé à `--work-dir` désigne le disque à tester. Les fichiers
temporaires sont supprimés après chaque mesure, y compris en cas d'erreur.

## Produire et comparer des rapports

Nommer clairement chaque configuration :

```bash
perfcomparator run --profile standard --label "Mac mini M4 16 Go"
perfcomparator history
```

Copier ensuite les JSON produits vers la machine qui fera la comparaison :

```bash
perfcomparator compare rapports/mac-mini.json rapports/pc-ryzen.json
```

Le pourcentage est calculé par rapport au premier fichier. Tous les scores
actuels suivent la règle « plus haut est meilleur ».

### Préparer un rapport destiné au catalogue communautaire

Cette fonction est disponible à partir de la préversion `0.4.0.dev1`.

Ne jamais publier directement le JSON produit par `run` : il contient des
informations utiles au diagnostic local, dont le chemin de Python, le label
libre, la date précise et les processus observés.

Créer à la place un export public :

```bash
perfcomparator export-public data/results/benchmark_….json \
  --output rapport-public.json \
  --machine-name "Apple MacBook Pro 15 pouces (2018)" \
  --machine-sku "MR942FN/A" \
  --accept-cc0
```

La commande ne réalise aucun envoi réseau. `--machine-name` confirme le nom
commercial public. `--machine-sku` ajoute facultativement la référence exacte
de la configuration et ne doit jamais contenir le numéro de série.
Sur Mac, la proposition de nom ajoute l'année de commercialisation lorsque
l'identifiant du modèle permet de la déterminer sans ambiguïté. Sinon, elle
conserve l'identifiant du modèle sans ajouter d'année.
Le rapport local enregistre aussi cette valeur dans `system.model_year` ; elle
vaut `null` quand les informations matérielles ne permettent pas de trancher.
Dans `contribute`, la demande du nom précise que tu peux ajouter manuellement
l'année si tu la connais, par exemple `Apple MacBook Pro 15 pouces (2018)`.
L'option `--accept-cc0` est requise pour confirmer la licence CC0 1.0 des
données destinées au partage. Relire le fichier produit avant toute
contribution. Le numéro de série, les UUID matériels et le nom d'hôte ne sont
jamais exportés. Le format et sa politique de confidentialité sont détaillés
dans [Format des rapports publics](format-rapport-public.md).

Avant de comparer ou transmettre un rapport public reçu, valider son intégrité :

```bash
perfcomparator validate-public rapport-public.json
```

Un succès confirme le format et l'identifiant de contenu, jamais l'authenticité
de la machine ni des performances.

Le [tutoriel catalogue de A à Z](tutoriel-catalogue.md) déroule ensuite la
contribution GitHub, la publication dans le catalogue, le téléchargement et la
comparaison locale d'un rapport public.

### Soumettre sans connaître Git

À partir de `0.4.0.dev2`, le parcours interactif choisit un rapport récent,
prépare son export public et automatise le fork et la pull request :

```bash
perfcomparator contribute
```

GitHub CLI est préparé sans droits administrateur dans le dossier utilisateur.
Si aucun compte n'est connecté, l'authentification ouvre le navigateur ; un
compte peut y être créé, puis son adresse vérifiée. Avant toute modification
distante, PerfComparator annonce le fork, la branche et la cible, puis demande
une confirmation séparée.

Après le consentement CC0, la commande propose un nom commercial public et une
référence commerciale facultative. Ils restent modifiables avant tout envoi.

Le message **Contribution envoyée** confirme la création de la pull request.
Le catalogue contrôle ensuite automatiquement son contenu. Si la validation
réussit et que seul le rapport attendu a été ajouté, la pull request est
fusionnée automatiquement. L'index est alors généré dans l'artefact GitHub
Pages, sans être versionné, puis le site est redéployé. Le rapport
devient alors visible dans le
[catalogue web](https://frchalaoux.github.io/perfcomparator-results/). Une
contribution invalide reste ouverte avec son erreur.
Pour une première contribution provenant d'un fork, GitHub peut demander au
mainteneur d'autoriser le démarrage de `validate`; la suite reste automatique.

Pour tester uniquement la sélection, l'export et l'aperçu public :

```bash
perfcomparator contribute --dry-run
```

Ce mode ne se connecte pas à GitHub et ne crée ni fork, ni branche, ni pull
request.

Une fois le rapport publié, cliquer sur **Télécharger le JSON** dans sa fiche,
puis comparer le fichier reçu localement :

```bash
perfcomparator compare mon-rapport-local.json rapport-telecharge.json \
  --html comparaison.html
```

Le premier fichier constitue la référence 100. Les rapports doivent employer
le même protocole, le même profil et la même version de Python.

## Rapport visuel et priorités

Le rapport HTML fonctionne hors ligne et n'envoie aucune donnée :

```bash
perfcomparator compare rapports/mac.json rapports/pc.json \
  --html comparaison.html
```

Depuis `0.4.0.dev1`, les arguments peuvent être des rapports privés produits
par `run`, des rapports publics validés, ou un mélange des deux. Un rapport
public est toujours revalidé avant la comparaison.

Il présente une référence 100, des indices par catégorie et scénario, les temps
équivalents pour des tâches de 10 secondes, 2 minutes, 30 minutes et 4 heures,
ainsi que les dispersions et conclusions prudentes.

Les scénarios disponibles sont `quotidien`, `developpement`, `calcul-intensif`,
`fichiers`, `base-de-donnees`, `creation` et `jeu-3d`. Sans réglage, ils ont le
même poids. Une pondération personnelle s'écrit ainsi :

```bash
perfcomparator compare mac.json pc.json \
  --weight developpement=50 \
  --weight creation=30 \
  --weight quotidien=20 \
  --html comparaison.html
```

La moyenne géométrique des rapports évite qu'une seule valeur très élevée
domine artificiellement l'indice. Les mesures WebGPU rendent comparables des
charges communes sur Metal, Direct3D 12 et Vulkan ; elles ne remplacent pas un
test d'un logiciel créatif ou d'un jeu précis.
