# Propositions de décisions — phase 0 PCE/PCWEB

## Statut

Ce document rassemble les choix recommandés pour fermer le cadrage des phases
0 à 2 avant l’implémentation. Les noms du dépôt et du paquet PCWEB sont
confirmés par l’utilisateur. Le dépôt public `frchalaoux/perfcomparator-web`
a été créé ; son code local reste à publier après revue et confirmation
explicite.

La recommandation cherche à respecter les deux objectifs déjà exprimés :
reprendre les frontières de SMB et SMB-WEB, et garder un premier parcours local
simple à installer et à lancer.

## Décisions recommandées

| Sujet | Décision recommandée | Motif |
| --- | --- | --- |
| Processus | Deux processus FastAPI distincts, démarrés et arrêtés par `perfcomparator web`. | Frontières nettes PCE/PCWEB, panne isolable et évolution future vers des agents. |
| Dépôts | PCE reste dans le dépôt `perfcomparator` ; PCWEB aura le dépôt `perfcomparator-web` ; `perfcomparator-results` reste le catalogue public. **Noms confirmés.** | Suit la séparation SMB/SMB-WEB et le souhait de construire PCWEB comme composant autonome. |
| Distributions | PCE conserve la distribution `perfcomparator` et son CLI ; son module Python est `perfcomparator`. PCWEB utilise la distribution et le module Python `perfcomparatorweb`. **Noms confirmés.** | Conserve la commande et le nom de distribution PCE, tout en alignant le paquet racine sur le modèle SMB. |
| Paquet Python PCE | Nom de distribution et paquet Python `perfcomparator`, installé depuis le dossier racine `perfcomparator/`, comme `sizemybike/` dans SMB. PCWEB conserve son propre paquet `perfcomparatorweb/`. | Aligne les deux composants sur le modèle SMB et garde la communication PCE–PCWEB à la frontière HTTP. |
| Lancement | `perfcomparator web start|stop|status` gère les deux processus ; `perfcomparator engine start|stop|status` gère PCE seul ; `perfcomparatorweb start|stop|status` gère PCWEB seul. `perfcomparator web` reste un raccourci de démarrage. | Une commande simple pour l’usage courant, avec gestion indépendante pour le développement et l’exploitation. |
| API | PCE est l’autorité du contrat JSON `/api/v1`, des codes d’erreur et du document OpenAPI. PCWEB utilise un repository HTTP partagé et des DTO validés contre ce contrat. | Contrat explicite et versionné, conforme au modèle SMB-WEB. |
| Authentification locale | Secret aléatoire créé à chaque lancement, transmis de l’orchestrateur à PCWEB puis envoyé en Bearer à PCE ; jamais dans une URL ou un journal. Écoute loopback uniquement, `Host`/`Origin` stricts, CORS désactivé. | Protège le port PCE des requêtes locales forgées sans introduire de comptes dans le MVP. |
| Interface Web | Pages HTML rendues par PCWEB, avec JavaScript natif limité ; toutes les ressources sont embarquées. **Choix confirmé.** | Suit SMB-WEB et évite une chaîne de construction frontend et une dépendance réseau. |
| Progression | SSE de PCE vers PCWEB puis le navigateur ; `GET /jobs/{id}` reste la source de vérité et permet la reprise après reconnexion. | Flux unidirectionnel adapté aux campagnes, avec récupération robuste par état. |
| Persistance des tâches | SQLite introduit en phase 2 pour tâches, idempotence et événements bornés ; les rapports JSON restent l’archive de référence. Garder les événements 30 jours, avec un plafond de 1 000 événements par tâche. **Choix confirmé.** | Reprise au rafraîchissement et état d’interruption au redémarrage, sans base serveur. |
| Concurrence | Une seule campagne matérielle active. Une seconde création renvoie `409 engine_busy`, sans être mise en file. | Empêche de dégrader les scores et conserve le worker mono-campagne déjà prévu. |
| Demande de campagne | Accepter profil, groupes/IDs de benchmarks, répétitions (1 à 9), libellé et ID GPU provenant de l’inventaire PCE. Ne jamais accepter chemin de travail, commande shell ou chemin de fichier libre. | Reprend les options utilisateur utiles tout en gardant les chemins et capacités sous contrôle de PCE. |
| Disponibilité | Les avertissements de charge et de mémoire sont des avertissements, pas un blocage automatique ; PCWEB demande une confirmation explicite avant le lancement. Une capacité GPU manquante bloque seulement les benchmarks GPU concernés. | Conserve la possibilité d’agir tout en rendant le risque visible. |
| Annulation | Annulation coopérative entre unités exécutées. La tâche termine en `cancelled` et conserve un rapport privé partiel avec un état d’exécution explicite ; les tests non commencés ne sont pas transformés en échecs. Les rapports annulés ne sont pas exportables publiquement par défaut. | Ne confond pas annulation utilisateur et échec du runner. Cela nécessite une évolution du schéma privé, sans changer le protocole de mesure. |
| Rapports existants | Pour le Web qui remplace Tk, conserver `~/Documents/PerfComparator` comme répertoire de rapports par défaut et offrir une configuration explicite. Ne pas déplacer les fichiers ni changer le chemin historique de la CLI. **Dossiers distincts confirmés.** | Préserve les rapports du bureau ; la CLI garde son comportement `data/results` actuel. |
| État applicatif | Placer SQLite et les journaux d’exécution dans le répertoire d’état utilisateur défini par plateforme (`platformdirs`), séparé des rapports. | Sépare données temporaires et archives utilisateur. |

## Mise en œuvre ordonnée

1. Définir les fabriques PCE et PCWEB, le lancement des processus, la
   configuration, l’authentification locale et la disponibilité (`/health`).
2. Publier le schéma OpenAPI PCE v1 comme référence du client PCWEB ; convenir
   d’une vérification de compatibilité entre les deux dépôts.
3. Implémenter les lectures PCE et les pages PCWEB de la phase 1, sans SQLite
   de tâches ni mutations.
4. Ajouter en phase 2 SQLite, l’idempotence, le worker mono-campagne, les
   événements SSE, l’annulation et le rapport privé partiel.
5. Distribuer les deux composants sous forme de paire compatible dans les
   installateurs locaux. L’installation indépendante du seul PCWEB reste
   possible pour le développement, mais n’est pas le parcours utilisateur.

Les noms `perfcomparator-web` et `perfcomparatorweb` sont des choix confirmés.
Le dépôt GitHub `perfcomparator-web` est créé en public. Le push de la branche
locale contenant PCWEB nécessitera une confirmation explicite après annonce de
la branche et du commit concernés.

## Décisions de nommage confirmées

- **Où sera le code PCWEB ?** Dans un dépôt GitHub distinct appelé
  `perfcomparator-web`, séparé du dépôt moteur `perfcomparator`.
- **Quel nom pour le paquet Python PCWEB ?** `perfcomparatorweb`, utilisé à la
  fois pour le paquet installable et le module importé en Python.
- **Quel nom pour le moteur PCE ?** Il reste `perfcomparator`.

## Compatibilité Python, FastAPI et installateurs

Vérification des métadonnées et des scripts du dépôt effectuée le 7 octobre
2026. Le projet exige actuellement Python `>=3.14,<3.15` et les installateurs
gèrent CPython `3.14.4`. Les métadonnées publiées de FastAPI et Uvicorn
déclarent Python `>=3.10` et incluent Python 3.14 dans leurs classificateurs.
Leurs distributions principales sont indépendantes du système d’exploitation.
Le choix de Python 3.14 ne bloque donc pas l’ajout de ces deux dépendances sur
macOS, Windows ou Linux. [FastAPI sur PyPI](https://pypi.org/project/fastapi/),
[Uvicorn sur PyPI](https://pypi.org/project/uvicorn/).

Recommandation de dépendances pour PCWEB : FastAPI, `uvicorn` sans extra
`standard`, HTTPX, Jinja2 et `platformdirs`. L’extra `standard` d’Uvicorn
ajouterait des dépendances facultatives natives dont le bénéfice n’est pas
nécessaire pour ce serveur local initial. Garder la contrainte Pydantic
`>=2.10,<3` cohérente avec PCE ; le solveur de l’environnement partagé devra
résoudre une seule version compatible. Les versions effectivement retenues
seront verrouillées lors de la création du paquet PCWEB.

Les installateurs actuels macOS, Windows et Linux installent PCE dans un
environnement `uv tool` isolé avec Python 3.14.4. La même stratégie peut
installer PCWEB et ses commandes dans cet environnement en passant
`perfcomparatorweb @ <URL>` à `uv tool install --with-executables-from`, sans
créer un deuxième environnement Python ni modifier le lanceur qui localise
l’environnement PCE.
[Documentation uv — outils et exécutables associés](https://docs.astral.sh/uv/concepts/tools/).
Le paquet PCWEB devra être fourni par une référence de version immuable (tag
ou commit), et les métadonnées des trois installateurs devront enregistrer les
versions exactes de PCE et PCWEB. L’uninstallateur actuel retire déjà tout
l’environnement `perfcomparator` : il retirera donc les deux paquets ensemble,
ce qui correspond au parcours utilisateur installé comme une paire.

Le premier commit PCWEB est épinglé actuellement dans les scripts directs
macOS/Linux et Windows (`6bb98c77a8c54b2471bb623e848bfaaf704733b7`, version
`0.1.0`). Les archives d’installation prennent la référence SHA fournie au
workflow et enregistrent aussi la version lue dans le `pyproject.toml` du
commit. À chaque mise à jour de PCWEB destinée aux scripts directs, leur SHA
par défaut devra être mis à jour avec le code associé.

**Conclusion : pas d’incompatibilité de version identifiée.** La compatibilité
est établie au niveau des contraintes Python et des artefacts déclarés. Le
smoke test local macOS a confirmé l’installation et les deux modes de
lancement/arrêt. Le workflow de construction comporte maintenant des smoke
tests d’installation et de cycle de vie sur macOS, Windows et Linux ; ils
pourront être exécutés quand le commit PCWEB sera accessible depuis GitHub.
Windows et Debian ne sont pas testables sur la machine de développement
actuelle.

## Commandes proposées pour gérer les processus

Commandes utilisateur retenues pour l’implémentation :

| Action | Commande |
| --- | --- |
| Démarrer PCE et PCWEB ensemble | `perfcomparator web start` |
| Arrêter les deux, PCWEB puis PCE | `perfcomparator web stop` |
| Voir l’état des deux | `perfcomparator web status` |
| Démarrer, arrêter ou vérifier PCE seul | `perfcomparator engine start`, `perfcomparator engine stop`, `perfcomparator engine status` |
| Démarrer, arrêter ou vérifier PCWEB seul | `perfcomparatorweb start`, `perfcomparatorweb stop`, `perfcomparatorweb status` |

Pour conserver l’usage déjà décrit dans le plan, `perfcomparator web` sans
sous-commande équivaudra à `perfcomparator web start`. Les commandes `start`
lanceront les serveurs en arrière-plan ; `stop` demandera une fermeture
ordonnée et attendra la fin du processus ; `status` indiquera notamment si le
serveur répond sur son port local. Les PID, ports et secrets de gestion seront
conservés dans le répertoire d’état privé de l’utilisateur, distinct des
rapports.

La fermeture ordonnée devra passer par un canal de contrôle authentifié lié à
la boucle locale et appeler l’arrêt ASGI de chaque serveur. Il ne faut pas
faire reposer l’arrêt normal uniquement sur la terminaison forcée du processus,
car celle-ci ne garantit pas le même nettoyage sous Windows. La commande
PCWEB utilisée seule recevra l’URL PCE et son secret par options ou fichier de
configuration privé ; le démarrage groupé transmettra ces paramètres
temporaires automatiquement. Si PCE est arrêté alors que PCWEB tourne,
`engine stop` avertira et refusera par défaut ; `web stop` arrêtera dans
l’ordre inverse du démarrage.

Cette convention fixe l’interface CLI proposée, mais le mécanisme de contrôle
et de lancement reste un détail d’implémentation à vérifier par smoke tests
sur macOS, Windows et Linux. La documentation Python rappelle que
`Popen.terminate()` appelle `TerminateProcess()` sous Windows, d’où la
nécessité d’un arrêt applicatif coopératif.
[Documentation Python — subprocess](https://docs.python.org/3/library/subprocess.html).

## Choix déjà confirmés pour le fonctionnement

- **Deux processus**, avec le lancement groupé habituel et des commandes
  séparées pour gérer PCE et PCWEB indépendamment. Les commandes proposées et
  leur comportement sont consignés dans « Commandes proposées pour gérer les
  processus » ; leur réalisation reste à valider par smoke tests.
- **Une seule campagne matérielle à la fois** ; si elle est occupée, une
  nouvelle demande reçoit un message et n’attend pas dans une file.
- **SQLite local pour l’état des tâches**, avec conservation des notifications
  pendant 30 jours et plafond de 1 000 notifications par tâche.
- **Dossiers de rapports distincts** pour PCWEB et la CLI par défaut ; aucun
  déplacement ou regroupement automatique.
- **Interface HTML locale simple**, avec JavaScript limité aux interactions
  utiles et sans dépendance à des ressources téléchargées.
- **Accès local uniquement**, avec un secret temporaire entre PCWEB et PCE.
- **API PCE versionnée** et progression en direct par SSE, récupérable en
  relisant l’état de la tâche.
- **Annulation coopérative** et conservation d’un rapport privé partiel
  clairement marqué.

## Explications des choix confirmés et détails à implémenter

### Campagnes : ce que SQLite conserverait

SQLite serait un fichier local, pas un serveur de base de données. Il garderait
les informations nécessaires pour retrouver une campagne : son identifiant,
ses paramètres, son état, ses heures de début et de fin, les notifications de
progression et la référence du rapport JSON. Le rapport complet et les mesures
resteraient dans les archives JSON.

Concrètement, le navigateur pourrait être actualisé sans perdre l’état de la
campagne. Si l’application s’arrête brutalement pendant une mesure, la tâche
serait marquée « interrompue » et ne repartirait pas seule. Les anciennes
notifications seraient supprimées après 30 jours, au maximum 1 000 étant
conservées par tâche ; cela ne supprimerait pas le rapport JSON associé. Ce
stockage local et cette règle de conservation sont confirmés.

### Rapports : un dossier Web et un dossier CLI

Aujourd’hui, l’interface de bureau écrit dans `~/Documents/PerfComparator`,
tandis que la CLI écrit dans `data/results` relativement au dossier depuis
lequel elle est lancée. Cette différence existe déjà ; il n’y a pas un dossier
CLI unique à découvrir automatiquement.

La proposition est que le Web reprenne le dossier de l’interface de bureau,
afin d’y retrouver ses anciens rapports, et que la CLI garde son comportement
actuel. Conséquence : un rapport produit par la CLI ne s’afficherait pas
automatiquement dans l’historique Web. L’utilisateur pourrait configurer un
dossier commun, sans déplacement automatique des rapports.

Le maintien de ces dossiers distincts est confirmé. Le dossier de données des
tâches restera séparé des rapports.

### Interface : à quoi ressembleraient les pages

PCWEB fabriquerait les pages HTML sur l’ordinateur. Le navigateur recevrait le
HTML, le style et un peu de JavaScript depuis PCWEB ; rien ne serait téléchargé
depuis un CDN. Il n’y aurait pas d’application JavaScript séparée à construire
ou à mettre à jour. Les pages pourraient tout de même afficher la progression
en direct et actualiser la liste des résultats.

Le formulaire de campagne proposerait profil, groupes ou benchmarks, nombre de
répétitions, libellé et, si un GPU est détecté, le choix parmi les GPU listés
par PCE. Il ne proposerait pas les chemins de fichiers ou les commandes du
système. Le nombre de workers resterait automatique au départ.

Cette interface Web simple et autonome est confirmée pour le premier
incrément. Une interface JavaScript dédiée ne sera envisagée que si les besoins
de présentation l’exigent plus tard.

### Gestion séparée des serveurs

Le lancement courant démarrerait PCE et PCWEB ensemble. Des commandes
indépendantes permettront aussi de démarrer ou arrêter chaque serveur seul.
Le nom de ces commandes et leur fonctionnement (serveur au premier plan ou
service en arrière-plan) restent à définir.

Les agents distants restent hors de ce premier incrément, conformément au
scénario déjà confirmé.

## À garder hors de la phase 0

Les sujets suivants sont reportés aux phases qui en ont besoin :

- authentification publique, reverse proxy et exploitation serveur : phase 7 ;
- agents distants, enrôlement et protocole inter-hôtes : phase 8 ;
- multi-utilisateur, quotas équitables et PostgreSQL : étude dédiée après le
  serveur mono-utilisateur ;
- suppression et corbeille : phase 3 ;
- synchronisation du catalogue communautaire hors ligne : phase 4 ;
- image OCI : après validation de l’installation locale et du comportement des
  benchmarks en conteneur ;
- remplacement de Tk : après coexistence et validation d’une version stable.

## Vérifications préalables avant de figer

- Ajouter les dépendances FastAPI/Uvicorn et résoudre/verrouiller leur paire
  avec Pydantic dans PCWEB.
- Adapter les métadonnées des installateurs aux deux versions et valider le
  démarrage/arrêt de la paire sur macOS, Windows et Linux.
- Confirmer la règle d’évolution du schéma privé nécessaire aux rapports
  annulés et son interaction avec l’export public.
- Vérifier que le chemin `Documents/PerfComparator` peut être résolu de façon
  fiable sur chaque plateforme et permettre un répertoire configuré.
