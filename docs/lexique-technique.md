# Lexique technique PerfComparator

Ce lexique explique les mots techniques employés dans le code et la
documentation de PerfComparator. Il s’adresse à une personne qui débute en
développement : chaque définition indique aussi, quand c’est utile, à quoi le
terme sert dans PCE ou PCWEB.

Le lexique couvre les concepts du produit et de son développement. Il ne
remplace pas un dictionnaire complet de Python, du Web ou des systèmes
d’exploitation. Lorsqu’une nouvelle fonctionnalité introduit un terme
important, sa définition doit être ajoutée ici et la page doit rester liée
depuis le guide développeur et l’index de documentation.

## Les composants de l’application

| Terme | Explication simple |
| --- | --- |
| **Agent** | Petit programme installé sur une machine à mesurer. Dans l’évolution envisagée, il lancerait les benchmarks sur cette machine et transmettrait les résultats au serveur. Le protocole des agents n’est pas encore développé. |
| **Architecture** | Façon dont les parties d’un logiciel sont séparées et communiquent. PerfComparator sépare notamment le moteur PCE de l’interface Web PCWEB. |
| **Application locale** | Application qui s’exécute sur l’ordinateur de l’utilisateur. Elle peut ouvrir une page Web dans son navigateur tout en gardant les serveurs et les rapports sur cet ordinateur. |
| **Client** | Programme qui demande un service à un autre programme. PCWEB est le client HTTP de PCE ; le navigateur est le client Web de PCWEB. |
| **Composant** | Partie distincte d’une application, avec une responsabilité et une interface définies. PCE et PCWEB sont deux composants. |
| **CLI** (*Command-Line Interface*) | Interface en ligne de commande : on donne des instructions en texte dans un terminal, par exemple `perfcomparator run`. |
| **Front-end / back-end** | Le front-end est la partie avec laquelle la personne interagit ; le back-end réalise le traitement et fournit les données. Dans l’interface Web, PCWEB sert les pages et PCE exécute les campagnes. |
| **Interface graphique / GUI** (*Graphical User Interface*) | Interface composée de fenêtres, boutons et menus, utilisée avec une souris ou un clavier. |
| **Moteur** | Partie qui réalise le travail principal. PCE exécute les benchmarks et produit les rapports. |
| **PCE** (*PerfComparator Engine*) | Moteur de PerfComparator. Il collecte les informations de la machine, lance les mesures et fournit une API locale. |
| **PCWEB** (*PerfComparator Web*) | Composant Web de PerfComparator. Il sert les pages au navigateur et demande à PCE les informations ou les campagnes. |
| **Serveur** | Programme qui attend des demandes et y répond. PCE et PCWEB sont deux processus serveur séparés. |
| **SMB / SMB-WEB** | Projets de référence utilisés pour reprendre des choix d’architecture et des motifs de code. Ce ne sont pas des composants de PerfComparator. |

## Mesures et rapports

| Terme | Explication simple |
| --- | --- |
| **Benchmark** | Test reproductible qui mesure une capacité précise, par exemple le calcul du processeur ou la vitesse du stockage. |
| **Catalogue** | Liste des benchmarks disponibles, de leurs groupes et de leurs descriptions. PCE est la source de cette liste. |
| **Campagne** | Ensemble de benchmarks demandé avec un profil, un nombre de répétitions et éventuellement un libellé. Une campagne produit un rapport. |
| **Charge de travail** (*workload*) | Travail effectué par un benchmark. Deux machines ne sont comparables que si elles réalisent une charge équivalente. |
| **CPU** (*Central Processing Unit*) | Processeur principal de l’ordinateur. Il exécute les instructions générales des programmes. |
| **Dispersion** | Écart entre plusieurs mesures répétées. Une dispersion importante indique que le score a beaucoup varié pendant la campagne. |
| **Échantillon** (*sample*) | Une mesure individuelle au cours d’un benchmark répété. Trois répétitions donnent trois échantillons. |
| **GPU** (*Graphics Processing Unit*) | Processeur graphique, souvent utilisé pour les images et les calculs parallèles. Il peut être absent ou indisponible pour certains benchmarks. |
| **Adaptateur GPU** | GPU détecté avec des informations telles que son nom et le pilote utilisé. Dans PerfComparator, la liste des adaptateurs sert à montrer les capacités disponibles. |
| **Médiane** | Valeur du milieu quand on range les résultats du plus petit au plus grand. PerfComparator l’utilise comme score central pour limiter l’effet d’une mesure exceptionnellement haute ou basse. |
| **Métrique / unité** | Grandeur mesurée et unité associée, par exemple un débit en Mio/s ou un nombre d’opérations par seconde. |
| **Minimum et maximum** | Plus petite et plus grande mesures d’une série de répétitions. Elles aident à comprendre la dispersion. |
| **Profil** | Niveau de durée et de ressources d’une campagne. `quick` est court, `standard` est le choix courant et `thorough` est plus long. |
| **Répétition** | Nouvelle exécution du même benchmark afin de vérifier la stabilité de la mesure. |
| **Runner** | Fonction du programme qui exécute concrètement un benchmark et renvoie sa mesure. Le runner ne décide pas à lui seul du stockage du rapport. |
| **Score** | Résultat numérique d’un benchmark. Il n’est utile que si son unité, sa méthode et son contexte sont compris. |
| **Snapshot / instantané** | Ensemble d’informations capturées à un moment donné. `SystemSnapshot` décrit le système ; `ReadinessSnapshot` décrit son état juste avant une campagne. |
| **WebGPU** | Interface logicielle qui permet d’utiliser un GPU depuis un programme. PerfComparator l’utilise pour certains benchmarks graphiques et de calcul. |

## Serveur Web et échanges

| Terme | Explication simple |
| --- | --- |
| **API** (*Application Programming Interface*) | Contrat qui permet à deux programmes de communiquer. PCWEB utilise l’API de PCE au lieu d’accéder directement à ses fichiers ou à ses fonctions internes. |
| **ASGI** (*Asynchronous Server Gateway Interface*) | Convention Python qui permet à un serveur Web comme Uvicorn de communiquer avec une application comme FastAPI. |
| **Authentification** | Vérification qu’une demande vient d’un client autorisé. Le démarrage local fournit à PCWEB un secret à transmettre à PCE. |
| **Bearer token** | Secret envoyé dans l’en-tête HTTP `Authorization`. « Bearer » signifie que le programme qui possède le secret peut s’authentifier ; il ne faut donc pas l’écrire dans une URL ou un journal. |
| **CDN** (*Content Delivery Network*) | Réseau de serveurs qui distribue des fichiers Web, par exemple des polices ou des bibliothèques. PCWEB doit embarquer ses ressources afin de fonctionner sans CDN ni accès Internet. |
| **CORS** (*Cross-Origin Resource Sharing*) | Règle du navigateur qui contrôle si une page Web peut appeler un serveur d’une origine différente. PCE n’a pas besoin d’ouvrir CORS pour le parcours local prévu. |
| **CSS** (*Cascading Style Sheets*) | Règles qui définissent l’apparence d’une page HTML : couleurs, tailles, espacements et disposition. |
| **DTO** (*Data Transfer Object*) | Objet de données conçu pour être transmis entre deux composants. Un DTO contient uniquement les champs que l’autre composant est autorisé à recevoir. |
| **Endpoint / route** | Adresse et méthode d’une opération d’API. Exemple : `GET /api/v1/reports` demande la liste des rapports. |
| **FastAPI** | Bibliothèque Python utilisée pour définir les routes HTTP, valider les données reçues et générer la description de l’API. |
| **Middleware** | Couche placée autour des routes Web, appelée pour chaque demande. Elle peut appliquer une règle commune, par exemple vérifier l’en-tête `Host`. |
| **Requête / réponse** | La requête est le message envoyé au serveur ; la réponse est le résultat renvoyé au client. Une réponse contient un statut HTTP et peut contenir des données JSON ou une page HTML. |
| **Validation** | Vérification qu’une donnée reçue respecte les règles attendues, par exemple qu’un nombre de répétitions est positif. FastAPI s’appuie sur Pydantic pour valider les données de l’API. |
| **Pydantic** | Bibliothèque Python qui décrit la forme attendue des données et vérifie qu’elles sont valides. PCE l’utilise pour ses modèles de requête et de réponse API. |
| **HTML** (*HyperText Markup Language*) | Format qui décrit le contenu d’une page Web : titres, paragraphes, formulaires et boutons. PCWEB fabrique les pages HTML affichées par le navigateur. |
| **HTTP** (*Hypertext Transfer Protocol*) | Protocole de communication utilisé par les navigateurs et les serveurs Web. Une demande contient une méthode, une adresse, des en-têtes et parfois des données. |
| **GET / POST** | Méthodes HTTP courantes. `GET` lit une ressource ; `POST` envoie une demande qui peut créer une tâche ou déclencher un traitement. |
| **HTTPX** | Bibliothèque Python pour envoyer des demandes HTTP. PCWEB l’utilise pour demander des données à PCE. |
| **Jinja2** | Outil qui remplit un modèle HTML avec des données, par exemple le nom d’un benchmark ou l’état d’une tâche. |
| **JavaScript** | Langage exécuté par le navigateur. PCWEB peut s’en servir pour actualiser l’avancement sans reconstruire toute la page. |
| **JSON** (*JavaScript Object Notation*) | Format texte pour représenter des données avec des objets, des listes, des nombres et des chaînes. Les rapports et les échanges de l’API PCE utilisent JSON. |
| **Loopback / boucle locale** | Adresse réseau qui désigne uniquement l’ordinateur courant, généralement `127.0.0.1` ou `localhost`. Les serveurs locaux ne sont donc pas ouverts au réseau extérieur. |
| **OpenAPI** | Description lisible par des outils du contrat d’une API : routes, paramètres et réponses. FastAPI peut la produire automatiquement. |
| **Origine Web** (*Origin*) | Identité d’une page Web composée du protocole, du nom d’hôte et du port. PCWEB et PCE contrôlent l’origine pour limiter les requêtes forgées. |
| **SSE** (*Server-Sent Events*) | Flux de messages envoyé par un serveur vers un client, dans un seul sens. PCE envoie les événements de campagne à PCWEB, qui les relaie au navigateur pour afficher la progression. Le navigateur peut reprendre le flux après une coupure. |
| **`EventSource`** | Fonction du navigateur qui ouvre un flux SSE et se reconnecte automatiquement s’il est interrompu. PCWEB relaie les événements PCE à cette connexion. |
| **`Last-Event-ID`** | En-tête HTTP utilisé pour reprendre un flux SSE après une coupure. Le navigateur indique à PCWEB le numéro du dernier événement reçu ; PCWEB le transmet à PCE, qui renvoie les événements plus récents encore conservés. |
| **Statut HTTP** | Nombre qui indique le résultat d’une demande. `200` signifie généralement « réussi », `202` « accepté pour traitement », `404` « introuvable », `409` « conflit » et `422` « données invalides ». |
| **Uvicorn** | Serveur Python qui écoute les demandes Web et les transmet à l’application FastAPI. |
| **URL** (*Uniform Resource Locator*) | Adresse complète d’une ressource ou d’un serveur, par exemple `http://127.0.0.1:8765`. |
| **En-tête `Host`** | Information HTTP qui indique le nom d’hôte visé. PCE vérifie cette valeur pour refuser certains accès inattendus. |

## Campagnes, tâches et stockage

| Terme | Explication simple |
| --- | --- |
| **Annulation coopérative** | Demande d’arrêt respectée entre deux unités de travail. Si un benchmark est déjà lancé et ne peut pas être interrompu proprement, il se termine avant l’arrêt de la campagne. |
| **Appel de progression (*callback*)** | Fonction fournie à un composant pour qu’il signale un changement à celui qui l’a appelé. L’exécuteur s’en sert pour transmettre l’avancement de chaque benchmark à l’orchestrateur. |
| **Événement** | Fait important arrivé à une tâche, par exemple « acceptée », « benchmark terminé » ou « annulée ». Les événements sont datés et numérotés pour permettre la reprise. |
| **Exécuteur** (*executor*) | Composant qui reçoit une demande de campagne et lance les benchmarks. `BenchmarkExecutor` définit le contrat ; `LocalBenchmarkExecutor` mesure la machine sur laquelle tourne PCE. |
| **Historique expiré** | Situation où certains anciens événements ont été supprimés par la règle de conservation. Le client doit alors relire l’état courant de la tâche avant de reprendre le flux. |
| **Idempotence** | Propriété d’une demande répétée qui évite de faire deux fois le même travail. Si PCWEB renvoie la même demande avec la même clé d’idempotence, PCE renvoie la tâche déjà créée. |
| **Interrompue** (*interrupted*) | État d’une tâche dont le serveur s’est arrêté avant sa fin. Elle n’est pas relancée automatiquement. |
| **Clé d’idempotence** | Identifiant envoyé avec une demande de campagne. PCE s’en sert pour reconnaître une nouvelle tentative de la même demande. Une même clé avec des paramètres différents est refusée. |
| **Orchestrateur** | Composant qui coordonne les étapes d’une campagne : créer la tâche, démarrer l’exécuteur, enregistrer la progression et conserver le résultat. |
| **Rapport privé** | Rapport complet conservé localement. Il peut contenir des informations propres à la machine, comme le chemin de l’exécutable Python. |
| **Rapport public** | Version préparée pour le partage. Elle est construite à partir d’une liste limitée de champs et exclut les informations privées. |
| **Répertoire d’état** | Dossier privé où l’application conserve ses données de fonctionnement, comme la base SQLite des tâches. Il est séparé du dossier des rapports. |
| **Contrôle préalable / readiness** | Mesure courte de la charge CPU, de la mémoire et de l’activité de la machine avant une campagne. Elle donne des avertissements pour aider à décider si les conditions sont assez stables pour mesurer. |
| **Repository / dépôt de données** | Composant qui lit ou écrit un type de données sans obliger le reste du programme à connaître les détails du fichier ou de la base. `JsonReportRepository` stocke les rapports. |
| **SQLite** | Base de données intégrée à l’application et stockée dans un fichier. Il n’y a pas de serveur de base de données séparé à installer. PerfComparator l’utilise pour retrouver l’état des tâches. |
| **SQL** (*Structured Query Language*) | Langage servant à lire et modifier les tables d’une base de données. SQLite comprend les commandes SQL. |
| **Tâche** (*task/job*) | Enregistrement durable d’une campagne lancée ou en cours. Elle possède un ID, un état, une progression et éventuellement un ID de rapport. |
| **Transaction** | Groupe d’opérations de base de données qui réussissent toutes ensemble ou sont toutes annulées. Elle empêche, par exemple, deux demandes simultanées de démarrer deux campagnes. |
| **Worker** | Partie exécutée en arrière-plan qui traite une tâche sans garder la demande HTTP ouverte pendant toute la mesure. Ici, le worker local traite une campagne à la fois. |
| **WAL** (*Write-Ahead Logging*) | Mode de SQLite qui enregistre d’abord les changements dans un journal. Il facilite les lectures pendant qu’une écriture est en cours. |
| **Pool de processus** | Groupe de processus réutilisables auquel on confie des calculs. Certains benchmarks l’utilisent pour mesurer le travail réparti sur plusieurs cœurs du processeur. |

### États de tâche

| État | Signification |
| --- | --- |
| `queued` | La tâche est enregistrée et attend que le worker commence. |
| `running` | La campagne est en cours d’exécution. |
| `cancel_requested` | Une annulation a été demandée ; le worker va s’arrêter à la prochaine limite sûre. |
| `succeeded` | La campagne s’est terminée sans échec de benchmark. |
| `completed_with_errors` | La campagne est terminée, mais un ou plusieurs benchmarks ont échoué. |
| `failed` | Le traitement de la tâche a échoué avant de produire un rapport utilisable. |
| `cancelled` | La campagne a été arrêtée à la demande de l’utilisateur et un rapport partiel peut être disponible. |
| `interrupted` | Le processus PCE s’est arrêté de façon inattendue avant la fin. |

## Données et identifiants de version

| Terme | Explication simple |
| --- | --- |
| **Empreinte SHA-256** | Résumé calculé à partir du contenu d’un fichier. Une modification du fichier donne normalement une empreinte différente. PCE l’utilise comme ID opaque d’un rapport, sans montrer son chemin. |
| **ID opaque** | Identifiant qui ne révèle pas comment retrouver le fichier ou la ressource. Le navigateur reçoit un ID de rapport, jamais un chemin local. |
| **Protocole de mesure** | Règles de calcul d’un score : charge exécutée, paramètres, unité et méthode d’agrégation. Deux rapports ne sont comparables que si leurs protocoles sont compatibles. |
| **Version de schéma** (*schema version*) | Numéro qui décrit la structure des champs d’un rapport JSON. Une évolution de structure peut changer ce numéro sans changer les mesures. |
| **Version du protocole** (*protocol version*) | Numéro qui décrit la méthode de mesure. Il change quand une évolution peut modifier les scores ou leur interprétation. |
| **Version de la suite** (*suite version*) | Version du logiciel PerfComparator qui a produit le rapport. Elle n’implique pas à elle seule que la méthode de mesure a changé. |

## Développement et distribution

| Terme | Explication simple |
| --- | --- |
| **Branche Git** | Ligne de travail séparée dans l’historique du code. Elle permet de préparer une modification sans toucher immédiatement à la branche principale. |
| **CI** (*Continuous Integration*) | Vérifications automatisées exécutées par le service GitHub quand du code est proposé : formatage, tests ou construction du paquet, par exemple. |
| **Commit** | Enregistrement nommé d’un ensemble de modifications dans Git. Il permet de retrouver précisément l’état du code à un instant donné. |
| **Dépendance** | Bibliothèque externe dont le programme a besoin. FastAPI et Pydantic sont des dépendances de PCE. |
| **GitHub** | Service qui héberge des dépôts Git et exécute des contrôles automatiques. Le code source de PCE et de PCWEB y est conservé. |
| **Environnement virtuel** | Installation Python isolée pour un projet. Elle évite de mélanger ses bibliothèques avec celles d’autres projets. |
| **Release / tag Git** | Version du code marquée dans Git et présentée comme une version précise. Une release GitHub peut aussi proposer des fichiers à télécharger. |
| **Lint / linting** | Vérification automatique du code qui repère notamment certaines erreurs et incohérences de style. Ruff assure ces contrôles dans PerfComparator. |
| **MVP** (*Minimum Viable Product*) | Première version volontairement limitée, mais utilisable, qui permet de valider le parcours principal avant d’ajouter des fonctions plus avancées. |
| **Module Python** | Fichier Python importable, par exemple `perfcomparator/tasks.py`. |
| **Paquet Python** | Ensemble de modules installables sous un même nom, par exemple `perfcomparator`. Le nom d’installation et le nom utilisé dans `import` peuvent parfois différer. |
| **Protocole Python (`Protocol`)** | Description des fonctions qu’un objet doit fournir pour être utilisé à un endroit donné. `BenchmarkExecutor` décrit ainsi le contrat attendu d’un exécuteur, sans imposer sa classe concrète. |
| **Pull request / PR** | Proposition de fusionner une branche dans une autre après affichage du diff et contrôles. Elle permet de relire le changement avant son intégration. |
| **PyPI** | Catalogue public où l’on peut publier et télécharger des paquets Python. |
| **`pyproject.toml`** | Fichier de configuration du projet Python : nom, version, dépendances et outils de développement. |
| **Ruff** | Outil rapide qui vérifie le style et certaines erreurs dans le code Python. |
| **Hatchling** | Outil qui construit le paquet installable de PerfComparator à partir de sa configuration Python. |
| **Tkinter** | Bibliothèque incluse avec Python pour créer des fenêtres et des boutons. PCE l’utilise pour son interface de bureau simple. |
| **Typer** | Bibliothèque Python qui transforme des fonctions en commandes faciles à utiliser dans un terminal. PCE l’utilise pour sa CLI. |
| **`platformdirs`** | Bibliothèque qui trouve les dossiers habituels pour les données et la configuration d’une application sur macOS, Windows et Linux. |
| **`psutil`** | Bibliothèque qui lit des informations sur le système et les processus, comme la mémoire utilisée ou la charge du processeur. |
| **`wgpu` / WebGPU** | `wgpu` est la bibliothèque Python qui donne accès à WebGPU. PerfComparator l’utilise pour ses mesures de calcul et de traitement graphique sur GPU. |
| **Smoke test** | Test court du parcours réel pour vérifier que les grandes pièces démarrent et communiquent. Dans PerfComparator, il peut consister à lancer PCE et PCWEB, ouvrir une page et effectuer une petite campagne. Il ne remplace pas les tests détaillés. |
| **Test unitaire** | Test d’une petite fonction ou d’un composant isolé, souvent avec des données de remplacement. |
| **Test d’intégration** | Test de plusieurs composants qui travaillent ensemble, par exemple une route FastAPI et son stockage temporaire. |
| **`uv`** | Outil utilisé par le projet pour gérer les dépendances, les environnements Python et les commandes de développement. |
| **Wheel** | Fichier d’installation standard d’un paquet Python. Il contient le code préparé pour être installé par un outil comme `uv` ou `pip`. |
| **`pytest`** | Outil qui exécute les tests automatisés Python et affiche ceux qui réussissent ou échouent. |

## Réseau local, sécurité et processus

| Terme | Explication simple |
| --- | --- |
| **Adresse IP** | Adresse numérique utilisée pour joindre un ordinateur sur un réseau. `127.0.0.1` désigne toujours l’ordinateur courant. |
| **Hôte (*host*)** | Nom ou adresse de la machine qui reçoit une demande réseau. Pour l’application locale, l’hôte est généralement `127.0.0.1`. |
| **Port** | Numéro qui distingue les services réseau d’un même ordinateur. PCE et PCWEB peuvent écouter sur deux ports locaux différents. |
| **Processus** | Programme en cours d’exécution dans le système d’exploitation. PCE et PCWEB sont deux processus séparés. |
| **PID** (*Process Identifier*) | Numéro donné par le système à un processus. Il sert notamment à reconnaître le processus serveur à arrêter. |
| **Secret de contrôle** | Valeur temporaire qui autorise les commandes internes sensibles, comme l’arrêt propre d’un serveur local. Elle est stockée dans l’état privé de l’application. |
| **Arrêt ASGI propre** | Fermeture demandée au serveur Web par le mécanisme prévu, afin de laisser l’application terminer son nettoyage plutôt que de tuer le processus brutalement. |
| **SKU** (*Stock Keeping Unit*) | Référence commerciale d’un produit. Pour un ordinateur, elle peut distinguer deux configurations portant un nom de modèle proche. |
| **UUID** (*Universally Unique Identifier*) | Identifiant conçu pour être très improbable à dupliquer. Il peut servir de clé d’idempotence ou d’identifiant interne de tâche. |

## Comment utiliser et maintenir ce lexique

- Si un mot de la documentation ou d’une revue bloque la compréhension, chercher
  d’abord ici ; s’il manque, ajouter une définition en français simple.
- Définir un acronyme avec son nom complet à sa première occurrence.
- Expliquer le rôle du terme dans PerfComparator, pas seulement sa définition
  générale.
- Préférer une phrase et un exemple concret aux termes techniques utilisés
  pour expliquer d’autres termes.
- Garder les termes présents dans le code entre accents graves, par exemple
  `CampaignRequest` ou `execution_status`, pour qu’on puisse les retrouver.
