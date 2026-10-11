# Méthodologie

## Reproductibilité

Chaque rapport conserve séparément la version exacte de la suite et la version
du protocole de mesure, ainsi que le profil, la version et le chemin de Python,
l'OS et l'inventaire matériel. Deux versions de suite différentes peuvent être
comparées lorsqu'elles déclarent le même protocole. Les anciens rapports sans
ce champ utilisent une table de compatibilité historique explicite.
L'installation officielle doit utiliser CPython 3.14.4 géré par `uv` afin
d'éviter qu'un Python système différent modifie les scores.

Le logiciel réalise trois passages par défaut et retient leur médiane. Il
conserve les valeurs individuelles, le minimum, le maximum et l'étendue relative.
Pour une étude importante, demander cinq passages du profil `standard`, dans les
mêmes conditions d'alimentation et de refroidissement.

La suite capture aussi, lorsque le système l'expose sans privilège, la source
d'alimentation, la limitation thermique du CPU et une température avant/après.
Elle avertit en cas de batterie, changement d'alimentation, limitation de
fréquence, hausse d'au moins 10 °C ou température finale d'au moins 85 °C. Ces
informations restent indisponibles sur certaines machines.

Avant la campagne, un échantillon d'une seconde contrôle la charge de départ.
Un avertissement est produit à partir de 15 % de CPU total, en dessous de 20 %
de mémoire disponible, à partir de 10 % d'échange occupé ou lorsqu'un processus
atteint 10 % de CPU. Les processus dépassant 2 % de CPU ou 3 % de mémoire sont
conservés, dans la limite des cinq plus actifs. Ces seuils sont des heuristiques
de reproductibilité, pas une définition scientifique universelle du repos.
Le contrôle est non bloquant, ponctuel et limité aux informations accessibles
sans privilège. Ses résultats sont conservés dans `readiness` et réaffichés
comme avertissements lors d'une comparaison. La collecte multiplateforme repose
sur l'API documentée de [psutil](https://psutil.readthedocs.io/). Le PID 0 de
Windows est un pseudo-processus représentant l'inactivité du CPU ; il est exclu
de la liste des tâches concurrentes.

Le benchmark `cpu.multicore` mesure volontairement le débit agrégé avec un
processus par processeur logique disponible. Son paramètre `workers` décrit donc
la machine et peut différer entre deux rapports. Les autres paramètres de
protocole doivent rester identiques.

Une différence est déclarée non concluante lorsque les plages min–max de deux
machines se chevauchent. Les termes « équivalent », « légère », « nette »,
« importante » et « changement de catégorie » correspondent respectivement aux
seuils 5 %, 15 %, 30 % et 60 %. Ce vocabulaire facilite la lecture ; il ne
constitue pas une loi générale de perception humaine.

## Agrégation et temps équivalents

Chaque score est divisé par celui de la première machine, qui devient l'indice
100. Les scénarios combinent ensuite leurs rapports par moyenne géométrique
pondérée. L'utilisateur peut pondérer les scénarios ; aucune pondération n'est
présentée comme universelle.

Pour une métrique de débit, le temps équivalent est calculé par
`temps référence / rapport de performance`. Il illustre une quantité de travail
identique, mais ne prédit pas exactement la durée d'une application réelle.

## Ce que mesurent les groupes

Le groupe CPU mélange du Python pur et des bibliothèques natives afin de couvrir
la réactivité de l'interpréteur, les flottants, la cryptographie, la compression
et la montée en charge multicœur. Le test mémoire mesure une copie séquentielle.
Le stockage utilise des fichiers temporaires sur le chemin choisi, avec
synchronisation des écritures. JSON et SQLite représentent des traitements
applicatifs fréquents. Le groupe GPU utilise des shaders WGSL hors écran via
`wgpu-py` : calcul FP32, copie de tampons, filtre spatial et remplissage raster.
Le même code de charge est présenté à Metal, Direct3D 12 ou Vulkan selon la
plateforme, et le moteur graphique effectivement choisi est enregistré.
Quand plusieurs adaptateurs sont présents, une campagne n'en mesure qu'un. La
sélection automatique privilégie le premier adaptateur dédié, puis le premier
intégré ; `--gpu INDEX` permet de la remplacer. L'indice, le nom, le type et le
backend sont attachés aux résultats. L'indice sert uniquement à sélectionner un
GPU localement et n'entre pas dans le protocole comparatif entre machines.
Un adaptateur WebGPU classé `CPU`, notamment `Microsoft Basic Render Driver`
dans certaines machines virtuelles, est refusé : son débit serait produit par
le processeur et ne constituerait pas une mesure du matériel graphique.

## Limites

Les caches du système peuvent augmenter le résultat de lecture disque. Les
scores GPU synthétiques ne mesurent pas le ray tracing, les unités IA, les
codecs vidéo matériels, un moteur de jeu complet ni une application créative.
WebGPU et les pilotes peuvent aussi employer des chemins différents selon l'OS.
La suite ne mesure pas l'autonomie ni les performances thermiques prolongées.
