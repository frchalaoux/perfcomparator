# Description et références des benchmarks

Tous les temps sont mesurés avec `time.perf_counter`, horloge monotone à haute
résolution définie par la PEP 418. Les données d'entrée sont déterministes et
leur préparation est placée hors de la zone chronométrée. Sauf mention
contraire, un score plus élevé est meilleur.

## `cpu.integer` — entiers mono-cœur

**Objectif.** Mesurer la vitesse de l'interpréteur pour une charge séquentielle
d'arithmétique entière et d'opérations binaires.

**Protocole.** Un seul processus met à jour un état 32 bits par la récurrence
`x = ((1664525 × x + 1013904223) XOR (x >> 13)) mod 2³²`. Le profil fixe la
durée minimale ; le score en Mop/s est le nombre de mises à jour divisé par le
temps réel.

**Interprétation et limites.** Le test cible surtout CPython et ses objets
entiers. La récurrence emprunte ses constantes à la famille de générateurs
congruentiels décrite dans *Numerical Recipes*, mais le benchmark ne prétend
tester ni la qualité statistique ni la sécurité d'un générateur aléatoire.

## `cpu.float` — flottants mono-cœur

**Objectif.** Représenter une petite charge scientifique scalaire.

**Protocole.** Un processus exécute des couples `sin`/`sqrt` sur des nombres
Python, normalement représentés en double précision IEEE 754. Le score en Mop/s
compte les itérations de la boucle.

**Interprétation et limites.** Le résultat inclut les appels Python et la
bibliothèque mathématique du système. Il ne mesure ni les FLOPS vectoriels
maximaux, ni directement les unités SIMD du processeur.

## `cpu.hash` — SHA-256

**Objectif.** Mesurer une charge cryptographique native courante.

**Protocole.** Un bloc déterministe de 1 Mio est haché successivement avec
SHA-256. Le score est le nombre de Mio d'entrée traités par seconde.

**Interprétation et limites.** Selon la construction de CPython et le matériel,
`hashlib` peut utiliser une bibliothèque native et des instructions accélérées.
Le score caractérise donc la chaîne complète, pas un cœur Python pur.

## `cpu.compression` — zlib/DEFLATE

**Objectif.** Mesurer une compression généraliste couramment utilisée.

**Protocole.** Un bloc pseudo-aléatoire déterministe de 1 Mio est compressé
plusieurs fois avec zlib au niveau 6. Le score mesure le débit des données
d'entrée en Mio/s.

**Interprétation et limites.** Le bloc est volontairement peu compressible. Un
texte, une image ou une archive produirait un rapport débit/taux de compression
différent. La version native de zlib fait partie de la configuration mesurée.

## `cpu.multicore` — entiers multicœur

**Objectif.** Observer le débit agrégé et la capacité de refroidissement sous
charge parallèle.

**Protocole.** Un processus par processeur logique est démarré et préchauffé,
puis exécute la même charge que `cpu.integer`. Le chronométrage commence après
le démarrage des processus. Le score agrège leurs mises à jour en Mop/s.

**Interprétation et limites.** Les processeurs logiques ne correspondent pas
toujours aux cœurs physiques. L'ordonnanceur, le SMT, les cœurs hétérogènes, la
puissance et la température influencent la montée en charge ; la loi d'Amdahl
rappelle en outre les limites générales du parallélisme.

## `memory.copy` — copie mémoire

**Objectif.** Estimer la bande passante soutenue d'une copie de tampon.

**Protocole.** Deux tampons de même taille sont préalloués. Une vue mémoire
copie répétitivement la source vers la destination. Le score compte une fois les
octets copiés, en Mio/s. Les tailles sont 8, 64 et 256 Mio pour les profils
`quick`, `standard` et `thorough`.

**Interprétation et limites.** Le principe est inspiré du noyau Copy de STREAM,
mais cette implémentation Python n'est pas le benchmark STREAM officiel. Les
petits tampons peuvent tenir partiellement dans les caches CPU.

## `storage.write` — écriture séquentielle

**Objectif.** Estimer le débit d'écriture du volume désigné par `--work-dir`.

**Protocole.** Un fichier temporaire de 16, 128 ou 512 Mio est écrit par blocs de
1 Mio sans tampon Python, puis `fsync` demande sa synchronisation. Le score est
la taille divisée par le temps d'écriture et de synchronisation.

**Interprétation et limites.** Le système de fichiers, ses caches, la
compression et le contrôleur restent impliqués. Contrairement au protocole SNIA
complet, ce test court ne préconditionne pas le SSD et ne garantit pas un état
stable.

## `storage.read` — lecture séquentielle

**Objectif.** Estimer le débit de lecture séquentielle du volume choisi.

**Protocole.** Un fichier temporaire est écrit et synchronisé, puis relu par
blocs de 1 Mio. Le score est la taille effectivement lue divisée par la durée.

**Interprétation et limites.** La préparation immédiate peut laisser le fichier
dans le cache de pages : le score peut donc représenter la chaîne stockage-cache
plutôt que le seul support physique.

## `storage.random-read` — lecture aléatoire 4 Kio

**Objectif.** Représenter de petites lectures dispersées, sensibles à la
latence.

**Protocole.** 512, 4 096 ou 16 384 positions sont tirées avec une graine fixe
dans le fichier temporaire. Des blocs de 4 Kio sont lus séquentiellement à
profondeur de file 1. Le score est exprimé en IOPS.

**Interprétation et limites.** Le cache du système peut intervenir. Il ne s'agit
pas d'un résultat SNIA certifié et les charges à profondeur de file élevée ne
sont pas couvertes.

## `storage.random-write` — écriture aléatoire 4 Kio

**Objectif.** Représenter de petites modifications dispersées.

**Protocole.** Des blocs déterministes de 4 Kio sont écrits aux mêmes séries de
positions que le test de lecture, à profondeur 1, puis un `fsync` final est
inclus dans la durée. Le score est exprimé en IOPS.

**Interprétation et limites.** Le test ne couvre ni l'endurance, ni le
préconditionnement, ni l'état stable, ni plusieurs profondeurs de file comme le
ferait une campagne SNIA complète.

## `application.json` — traitement JSON

**Objectif.** Représenter une transformation de données structurées fréquente.

**Protocole.** Un document fixe de 1 000 objets mêlant nombres, chaînes,
booléens, listes et dictionnaires est désérialisé puis sérialisé. Un score en
cycles/s compte ces deux opérations comme un cycle.

**Interprétation et limites.** Le document synthétique ne couvre pas toutes les
formes autorisées par la RFC 8259 et n'évalue pas les bibliothèques JSON tierces.

## `application.sqlite` — base locale

**Objectif.** Représenter une petite charge transactionnelle embarquée.

**Protocole.** Une base temporaire en mode WAL est créée ; 2 000, 20 000 ou
100 000 lignes sont insérées dans une transaction, validées, puis interrogées
par un filtre et une agrégation. Le score est le nombre de lignes insérées par
seconde sur l'ensemble du scénario.

**Interprétation et limites.** Ce résultat mélange CPU, mémoire et stockage. Il
ne couvre ni accès concurrents, ni base durable préexistante, ni requêtes
analytiques complexes.

## `gpu.compute-fp32` — calcul parallèle FP32

**Objectif.** Comparer une charge arithmétique parallèle commune aux GPU des
trois systèmes, sans installer une application 3D complète.

**Protocole.** Un shader de calcul WGSL traite 262 144 valeurs en simple
précision. Chaque invocation réalise 128 expressions multiplication-addition,
comptées par convention comme 256 opérations flottantes. Le score divise le
nombre total d'opérations par le temps mur entre soumission et lecture de
synchronisation et s'exprime en GFLOP/s.

**Interprétation et limites.** Le noyau mesure un calcul FP32 régulier. Il ne
couvre ni FP64, ni tenseurs ou unités IA, ni ray tracing. Un compilateur peut
fusionner une multiplication et une addition en FMA ; le comptage de deux
opérations suit la convention usuelle, mais le résultat n'est pas une mesure du
maximum théorique du constructeur. La soumission et la synchronisation sont
incluses, ce qui pénalise davantage les GPU rapides sur les profils courts.

## `gpu.memory` — bande passante GPU

**Objectif.** Estimer le débit d'une lecture-écriture parallèle dans la mémoire
accessible au GPU.

**Protocole.** Un shader WGSL copie un tampon source vers un tampon destination.
Le volume compté additionne quatre octets lus et quatre octets écrits par
élément. Une valeur sentinelle est relue et vérifiée après le chronométrage. Le
score est exprimé en Gio/s.

**Interprétation et limites.** Les caches, la taille du tampon, la mémoire
unifiée des SoC et les transferts implicites du pilote influencent le résultat.
Ce test ne correspond donc pas nécessairement à la bande passante physique
annoncée et ne sépare pas toutes les hiérarchies de mémoire.

## `gpu.image-filter` — filtre d'image

**Objectif.** Représenter un petit traitement d'image massivement parallèle.

**Protocole.** Pour chaque pixel, un shader de calcul combine le centre et ses
quatre voisins directs. La texture logique mesure 512², 1 024² ou 2 048² pixels
selon le profil. Le score compte les pixels traités par seconde en Mpixel/s.

**Interprétation et limites.** Cette opération synthétique couvre accès mémoire
et calcul simple, mais ni décodage, ni gestion des couleurs, ni effets multiples,
ni codecs vidéo matériels. Les données sont des flottants dans des tampons et
non une chaîne complète d'édition photo.

## `gpu.raster` — remplissage hors écran

**Objectif.** Comparer un pipeline graphique minimal et multiplateforme.

**Protocole.** Un triangle couvrant toute la cible est dessiné répétitivement
dans une texture RGBA8 hors écran de 512², 1 024² ou 2 048² pixels. Le fragment
shader calcule une couleur à partir de la position. Une lecture d'un pixel force
l'achèvement de la file GPU. Le score est exprimé en Mpixel/s.

**Interprétation et limites.** Le test privilégie le remplissage et un fragment
shader très simple. Il ne représente ni une scène riche en géométrie, ni
textures complexes, anticrénelage, transparence, ray tracing ou moteur de jeu.
L'API WebGPU garde le code de charge commun, mais son implantation utilise Metal,
Direct3D 12 ou Vulkan et reste dépendante du pilote.

## Bibliographie

1. Amdahl, G. M. (1967). *Validity of the Single Processor Approach to Achieving Large Scale Computing Capabilities*. AFIPS, 483–485. <https://doi.org/10.1145/1465482.1465560>
2. Bray, T., éd. (2017). *RFC 8259 — The JavaScript Object Notation Data Interchange Format*. IETF. <https://www.rfc-editor.org/rfc/rfc8259>
3. Deutsch, L. P. (1996). *RFC 1950 — ZLIB Compressed Data Format Specification*. IETF. <https://www.rfc-editor.org/rfc/rfc1950>
4. Deutsch, L. P. (1996). *RFC 1951 — DEFLATE Compressed Data Format Specification*. IETF. <https://www.rfc-editor.org/rfc/rfc1951>
5. IEEE (2019). *IEEE 754-2019 — Standard for Floating-Point Arithmetic*. <https://standards.ieee.org/ieee/754/6210/>
6. Langa, Ł. (2012). *PEP 418 — Add monotonic time, performance counter, and process time functions*. Python Software Foundation. <https://peps.python.org/pep-0418/>
7. McCalpin, J. D. (1995). *Memory Bandwidth and Machine Balance in Current High Performance Computers*. IEEE TCCA Newsletter, 19–25. <https://www.cs.virginia.edu/stream/ref.html>
8. NIST (2015). *FIPS PUB 180-4 — Secure Hash Standard*. <https://doi.org/10.6028/NIST.FIPS.180-4>
9. Press, W. H., Teukolsky, S. A., Vetterling, W. T. et Flannery, B. P. (2007). *Numerical Recipes: The Art of Scientific Computing*, 3e éd., chap. 7. Cambridge University Press. ISBN 978-0-521-88068-8.
10. Python Software Foundation. *Process-based parallelism*. Documentation Python 3.14. <https://docs.python.org/3.14/library/multiprocessing.html>
11. SNIA (2020). *Solid State Storage Performance Test Specification*, version 2.0.2. <https://www.snia.org/solid-state-sss>
12. SQLite Consortium. *Transaction documentation*. <https://www.sqlite.org/lang_transaction.html>
13. W3C GPU for the Web Community Group. *WebGPU Specification*. <https://gpuweb.github.io/gpuweb/>
14. W3C GPU for the Web Community Group. *WebGPU Shading Language*. <https://www.w3.org/TR/WGSL/>
15. PyGfx. *wgpu-py documentation*. <https://wgpu-py.readthedocs.io/>
