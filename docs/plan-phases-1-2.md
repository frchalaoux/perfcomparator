# Détail des phases 1 et 2 — interface locale PCE/PCWEB

## Objet

Ce document précise les deux premiers incréments du
[plan d’évolution](plan-evolution-interface-web.md). Il transforme leurs
livrables généraux en parcours, responsabilités et contrats vérifiables. Il
reste une spécification de travail : les routes, modèles et écrans indiqués
seront confirmés en phase 0 avant leur implémentation.

Le périmètre reste local : PCWEB sert le navigateur, appelle PCE sur la boucle
locale et PCE exécute ses opérations sur la machine mesurée. La phase 1 est
strictement en lecture seule. La phase 2 ajoute les campagnes et leurs tâches.
La comparaison, la suppression et l’export public restent dans les phases
suivantes.

## Règles communes

- La CLI et PCWEB utilisent les mêmes services métier et les mêmes modèles de
  rapport. La couche HTTP ne duplique pas le moteur.
- Seul PCWEB est contacté par le navigateur. Il appelle PCE côté serveur avec
  un client HTTP partagé, des délais d’attente bornés et une authentification
  locale définie en phase 0.
- PCE et PCWEB écoutent uniquement sur les interfaces de boucle locale. Les
  contrôles `Host` et `Origin` protègent aussi l’interface locale contre les
  requêtes Web forgées.
- Les identifiants de rapport et de tâche sont opaques. Une requête ne reçoit
  jamais un chemin de fichier fourni par le navigateur.
- Les rapports privés existants restent dans leurs fichiers JSON. La phase 1
  n’exige pas SQLite ; la phase 2 l’ajoute pour l’état des jobs et leur
  progression. L’index reconstructible des rapports reste prévu en phase 3.
- Les opérations de lecture n’ont aucun effet de bord autre que les accès
  nécessaires à la lecture et à l’inventaire système. Aucune télémétrie ni
  synchronisation de catalogue n’est déclenchée implicitement.

## Phase 1 — socle Web local en lecture seule

### Parcours utilisateur

1. L’utilisateur lance `perfcomparator web` depuis son environnement installé.
2. Le lanceur démarre PCE et PCWEB, attend leurs états prêts, puis ouvre
   éventuellement le navigateur sur PCWEB.
3. Le tableau de bord présente la machine mesurée, les capacités détectées et
   les avertissements de disponibilité pertinents.
4. L’utilisateur parcourt les groupes, la liste et la fiche descriptive des
   benchmarks sans démarrer de mesure.
5. Il consulte la liste des rapports JSON déjà présents et ouvre les détails
   autorisés d’un rapport identifié par son ID.
6. Il peut rafraîchir une page ou arrêter les services ; aucune donnée de
   rapport n’est modifiée.

La phase n’ajoute ni lancement de campagne, ni suppression, ni comparaison,
ni téléchargement HTML, ni export public. L’historique se limite aux champs
utiles à son affichage : date, libellé, profil, machine, nombres de mesures et
d’échecs, versions et ID. Les détails sensibles comme le chemin de l’exécutable
Python ne sont pas affichés par défaut.

### Responsabilités

| PCE | PCWEB |
| --- | --- |
| Retourne un `SystemSnapshot` et les capacités détectées. | Assemble le tableau de bord et ses états de chargement/erreur. |
| Retourne le catalogue, les groupes, profils et descriptions issus du cœur. | Filtre et présente le catalogue sans réimplémenter ses définitions. |
| Liste les rapports archivés et expose les détails par ID opaque. | Présente l’historique et demande les détails via son repository HTTP. |
| Résout l’ID vers son archive dans le dépôt JSON. | N’accepte ni ne construit un chemin de rapport. |
| Fournit `/health` sans données privées. | Vérifie la disponibilité PCE au démarrage et traduit ses erreurs. |

La détection matérielle peut dépendre de commandes système ou de pilotes
absents. Une valeur inconnue est présentée comme indisponible, sans faire
échouer toute la page. Une indisponibilité de PCE produit un écran d’erreur
actionnable et une nouvelle tentative ; PCWEB ne bascule pas silencieusement
vers une autre source.

### Contrat HTTP indicatif

Ces routes sont des propositions de découpage, pas encore un contrat figé :

| PCE | Réponse attendue | Notes |
| --- | --- | --- |
| `GET /health` | état prêt/version de service | Sans inventaire matériel ni chemin privé. |
| `GET /api/v1/system` | `SystemSnapshot` et capacités | Pas de lancement de benchmark. |
| `GET /api/v1/benchmarks` | définitions, groupes et profils | Dérivé de `CATALOG`, `GROUPS`, `PROFILES`. |
| `GET /api/v1/benchmarks/{benchmark_id}` | description et limites | ID inconnu : erreur stable `404`. |
| `GET /api/v1/reports` | page de métadonnées et IDs | Ordre récent d’abord ; pagination bornée. |
| `GET /api/v1/reports/{report_id}` | détails validés du rapport | `404` si absent/illisible ; aucun chemin fourni par le client. |

Les erreurs partagent une enveloppe stable avec code, message lisible et ID de
requête ; elles ne révèlent ni traceback ni secrets. Les lectures de rapports
ignorent ou signalent les JSON invalides selon une règle homogène et
observable, sans les supprimer ni les corriger automatiquement.

### Interface et accessibilité

- Navigation principale : Tableau de bord, Benchmarks, Historique.
- Les états de chargement, absence de rapports, service indisponible et
  inventaire partiel sont explicitement présentés.
- Le catalogue affiche groupe, nom, résumé et disponibilité éventuelle ; la
  fiche affiche méthode, limites, unités et références déjà conservées par le
  cœur.
- Les tableaux ont des en-têtes ; toutes les actions sont utilisables au
  clavier et possèdent un libellé visible ou accessible.
- Les ressources HTML, CSS, JavaScript, icônes et polices nécessaires sont
  embarquées dans le paquet. Une installation hors ligne ne dépend pas d’un
  CDN.

### Découpage d’implémentation

1. Créer les fabriques et configurations PCE/PCWEB décidées en phase 0, les
   contrôles de boucle locale et le client HTTP PCWEB partagé.
2. Ajouter les schémas de réponse et services de lecture PCE en adaptant les
   fonctions existantes (`system_snapshot`, `CATALOG`, `GROUPS`, `PROFILES`,
   `JsonReportRepository`).
3. Ajouter les routes `/api/v1` read-only et leur validation d’IDs/pagination.
4. Ajouter les repositories/services PCWEB et les pages du parcours ci-dessus.
5. Intégrer les ressources statiques au wheel et au lanceur installé.
6. Vérifier le démarrage depuis l’artefact installé, l’isolation des deux API,
   les cas incomplets et l’absence de fuite de chemins ; voir les critères de
   sortie.

## Phase 2 — campagnes, tâches et progression

### Parcours utilisateur

1. Depuis le catalogue, l’utilisateur choisit un profil (`quick`, `standard`,
   `thorough`), des groupes et/ou des benchmarks, le nombre de répétitions et
   un libellé facultatif.
2. PCWEB affiche un résumé de la sélection et demande un contrôle préalable.
3. PCE vérifie la requête, résout la sélection contre le catalogue réel et
   exécute `machine_readiness`. PCWEB présente les avertissements et demande
   une confirmation explicite avant le lancement.
4. PCE accepte au plus une campagne matérielle à la fois. La réponse initiale
   confirme la création et fournit un ID de tâche ; elle ne garde pas la
   connexion HTTP ouverte pendant les mesures.
5. PCWEB suit l’état par SSE et peut récupérer le même état après navigation,
   rafraîchissement ou reconnexion.
6. À la fin, PCWEB affiche les scores réussis, les échecs partiels, le résumé
   système et le lien vers l’archive créée. Il ne relance jamais la campagne
   du seul fait d’une reconnexion.
7. L’utilisateur peut demander l’annulation. Celle-ci est coopérative entre
   deux benchmarks/répétitions ; un runner non interruptible est laissé se
   terminer proprement.

### Contrat de demande de campagne

La demande est sérialisable et indépendante de l’interface et du lieu futur
d’exécution. Elle contient uniquement des paramètres validés, par exemple :

```json
{
  "profile": "standard",
  "benchmark_ids": ["cpu.integer", "memory.bandwidth"],
  "repetitions": 3,
  "label": "Avant mise à niveau"
}
```

`benchmark_ids` est une sélection explicite résolue contre le catalogue PCE ;
une sélection vide ou des IDs inconnus sont rejetés avant création du job. Les
bornes de répétition et profils restent celles du cœur. Les champs `work_dir`,
commande shell, chemin arbitraire, `gpu_index` brut ou options internes ne sont
pas acceptés directement depuis le navigateur. Les capacités GPU sont
présentées depuis l’inventaire PCE et sélectionnées par un ID opaque ; le nombre
de workers CPU reste automatique pour les premières campagnes.

La requête de création porte un `Idempotency-Key` aléatoire généré par PCWEB.
Une répétition de la même requête avec la même clé renvoie la tâche existante ;
la même clé avec un contenu différent donne un conflit. Une nouvelle action
volontaire génère une nouvelle clé.

### États, événements et reprise

Le registre de tâches utilise des états terminaux et actifs sans prétendre
constituer une file distribuée :

```text
queued → running → succeeded | completed_with_errors | failed
                    └→ cancel_requested → cancelled
                    └→ interrupted (après arrêt brutal du processus)
```

Chaque événement a un numéro séquentiel monotone pour le job, une date UTC, un
type et une charge structurée bornée. Les événements minimum sont : acceptation,
démarrage, début d’un benchmark, succès/échec d’un benchmark, demande et
résultat d’annulation, fin et interruption. La progression exprime l’ID du
benchmark courant et le compte terminé/demandé ; aucun texte de terminal n’est
le contrat machine.

| Route indicative | Usage |
| --- | --- |
| `POST /api/v1/readiness` | Contrôle préalable court, sans créer de campagne. |
| `POST /api/v1/runs` | Créer une tâche, retourner `202`, ID et état initial. |
| `GET /api/v1/jobs/{id}` | Reprendre l’état, les totaux et le résultat terminal. |
| `GET /api/v1/jobs/{id}/events` | SSE avec ID d’événement et reprise `Last-Event-ID`. |
| `POST /api/v1/jobs/{id}/cancel` | Demander une annulation coopérative. |

La reconnexion rejoue les événements encore conservés à partir de l’ID connu ;
si l’historique borné a expiré, le client recharge l’état courant avant de
reprendre le flux. L’état `running` trouvé au démarrage après arrêt brutal
devient `interrupted` et n’est jamais remis automatiquement en file.

### Worker et résultat

- Un worker local borné prend une campagne à la fois. Les demandes concurrentes
  reçoivent une réponse `409` avec un code `engine_busy` et l’état courant
  minimal ; elles ne s’ajoutent pas à une file cachée.
- Le worker dépend d’une interface `BenchmarkExecutor` et convertit ses
  événements structurés en événements de tâche. L’implémentation livrée,
  `LocalBenchmarkExecutor`, exécute les runners et les relevés système sur la
  machine PCE. Elle conserve l’isolation actuelle des échecs par benchmark et
  l’agrégation médiane.
- L’annulation est vérifiée entre unités de travail. Le rapport conserve les
  benchmarks demandés, les mesures terminées et les erreurs ; la politique
  exacte de statut terminal d’un rapport annulé est à fixer dans le contrat.
- L’orchestrateur de tâches possède les IDs, l’idempotence, les transitions,
  l’annulation, les événements et la persistance. L’exécuteur ne choisit pas de
  chemin d’archive et retourne un résultat de mesure structuré. L’orchestrateur
  local le remet au repository JSON, qui garde l’écriture atomique existante.
  Le job référence un ID/nom interne produit par le repository, pas un chemin
  choisi par le navigateur.
- Les événements et messages d’erreur sont bornés en taille et n’incluent pas
  les traces Python. Un résultat terminal reste consultable même après que les
  événements de progression anciens ont été purgés.

### Frontière requise pour une évolution future avec agents

Cette frontière est une exigence de conception de la phase 2 ; elle ne crée pas
encore de protocole réseau d’agent.

- `CampaignRequest` est un modèle JSON validé contenant uniquement les choix de
  mesure portables : profil, IDs de benchmarks, répétitions et libellé. Il ne
  contient ni chemin, processus, snapshot local, identité d’agent, adresse
  réseau, objet Python ni commande système. La requête reçue par le navigateur
  reste identique quel que soit le lieu futur d’exécution.
- `BenchmarkExecutor` reçoit cette demande et une interface bornée de
  progression/annulation ; il produit un `BenchmarkReport` ou une erreur
  structurée. `LocalBenchmarkExecutor` est le seul exécuteur requis en phase 2.
  L’orchestrateur ne dépend pas directement de
  `BenchmarkContext`, des runners ou des API système.
- En mode local, l’orchestrateur PCE choisit implicitement l’exécuteur local.
  Une phase distante pourra ajouter à l’enveloppe de tâche un `target_id` et
  une affectation à un agent compatible, sans ajouter l’identité de l’agent à
  la demande métier. Si l’utilisateur doit choisir une machine cible, le
  contrat d’orchestration pourra ajouter ce routage séparément ; ce choix ne
  doit pas contaminer le modèle de demande de mesure.
- Dans ce futur mode, l’agent exécute les relevés système et les benchmarks sur
  l’hôte cible, puis retourne progression et résultat structurés à
  l’orchestrateur. L’API centrale ne prétend jamais mesurer le matériel du
  navigateur ou de l’agent depuis le serveur.
- Le rapport privé local n’est pas envoyé tel quel par défaut : il contient
  notamment `python_executable`, un chemin propre à l’hôte, et les contrôles de
  disponibilité peuvent contenir des PID et noms de processus. Un futur
  transfert devra utiliser un DTO distant explicite, à liste blanche, conserver
  les mesures nécessaires à l’équivalence des scores et exclure ces données
  locales sauf autorisation distincte.

L’implémentation actuelle ne satisfait pas encore cette frontière :
`BenchmarkService.run()` collecte directement readiness, environnement et
inventaire système, puis écrit le rapport JSON et retourne son chemin. Avant de
coder les campagnes, il faudra isoler la production du résultat de son
archivage et faire dépendre l’orchestrateur de `BenchmarkExecutor`. Ce
refactoring garde le worker local comme seul transporteur livré ; il ne demande
ni service d’enrôlement, ni authentification distante, ni protocole agent.

### Écrans et retours d’état

- Assistant : choix des groupes et benchmarks, profil, répétitions, libellé,
  durée estimée indicative et résumé avant démarrage.
- Préparation : charge CPU, mémoire disponible, swap, processus actifs
  pertinents et avertissements issus de `ReadinessSnapshot`. La disponibilité
  d’un GPU ou l’absence de droits n’est pas masquée ; elle explique les tests
  susceptibles d’échouer.
- Exécution : benchmark courant, progression, derniers résultats/échecs et
  action d’annulation. Les valeurs sont annoncées comme partielles jusqu’à la
  fin ; les scores ne sont pas comparés dans cette phase.
- Résultat : état terminal, mesures et unités, dispersion, échecs par ID,
  avertissements d’environnement, informations système et lien vers le rapport
  de l’historique.
- Les erreurs distinguent sélection invalide, moteur occupé, refus de
  disponibilité, perte de PCE, tâche interrompue et échec d’un runner. Le
  rafraîchissement restaure la tâche par ID, pas par répétition de POST.

### Arbitrages recommandés pour la phase 0

Les choix recommandés sont désormais consignés dans
[Propositions de décisions — phase 0](propositions-decisions-phase-0.md) :
SQLite borné en phase 2, SSE avec reprise par lecture d’état, `409 engine_busy`,
sélection validée par PCE et état privé explicite pour les campagnes annulées.
La phase 0 doit vérifier leur compatibilité avec le code actuel, les
installateurs et les contrats de rapport avant de les figer.

### Critères de sortie cumulatifs

La phase 1 est terminée lorsque :

- les deux applications démarrent depuis l’installation empaquetée et restent
  joignables uniquement en boucle locale ;
- le navigateur ne contacte que PCWEB et le backend PCE ne révèle pas de chemin
  arbitraire ou d’erreur interne ;
- tableau de bord, catalogue et historique affichent données présentes,
  absentes, partielles et service indisponible ;
- les ressources Web fonctionnent hors ligne et l’ancienne CLI continue
  d’utiliser le même moteur.

La phase 2 est terminée lorsque :

- une campagne valide produit un rapport JSON lisible par la CLI et un ID de
  tâche consultable jusqu’à son état terminal ;
- l’orchestrateur fonctionne avec un faux `BenchmarkExecutor` en test, tandis
  que l’exécuteur local préserve les résultats et rapports de la CLI ;
- l’interface de tâche ne dépend pas des chemins locaux ni des API système, et
  les futurs transferts distants sont séparés du rapport privé complet ;
- les sélections invalides sont rejetées sans lancer de runner ;
- une seule campagne matérielle s’exécute et une clé d’idempotence répétée ne
  crée pas un doublon ;
- progression, reprise SSE, état après rechargement et interruption après
  redémarrage sont cohérents ;
- l’annulation n’interrompt pas brutalement un runner non interruptible et
  restitue un résultat/rapport explicite ;
- les échecs partiels restent isolés et les mesures réussies sont consultables ;
- les scores et le contenu du rapport correspondent au service CLI pour la
  même demande, hors métadonnées temporelles et état d’interface.

Les validations couvrent schémas et services indépendamment de FastAPI, routes
par client ASGI, SSE et reconnexion, faux worker pour les transitions, ainsi
qu’un smoke test du lancement empaqueté. Aucun vrai benchmark lourd ne doit
être lancé dans la suite ordinaire ; les runners matériels sont remplacés par
des doublures déterministes. Les tests ne seront ajoutés/exécutés qu’au moment
de l’implémentation, selon les consignes du projet.

## Hors périmètre explicite

- Déploiement Gandi ou autre hébergement distant et écoute réseau.
- Agent distant, enrôlement, authentification inter-hôtes, protocole de
  transfert et mises à jour d’agents.
- Comptes multi-utilisateurs, quotas inter-utilisateurs, PostgreSQL et
  ordonnanceur distribué.
- Comparaison avancée, suppression, export public et contribution GitHub.
- Relance automatique d’une campagne après crash ou reprise d’un benchmark au
  milieu d’un runner.
