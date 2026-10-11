# Guide développeur

Pour comprendre les mots techniques employés dans le code et les plans, voir le
[lexique technique PerfComparator](lexique-technique.md).

Le paquet sépare les responsabilités :

- `models.py` définit le schéma versionné des rapports ;
- `system_info.py` collecte l'inventaire multiplateforme ;
- `benchmarks.py` contient profils, catalogue et charges ;
- `gpu_benchmarks.py` contient les pipelines WebGPU hors écran ;
- `executor.py` exécute une demande de campagne sur l'hôte local ;
- `service.py` résout une sélection et conserve le rapport pour la CLI ;
- `tasks.py` orchestre une campagne Web à la fois et persiste son état et ses
  événements dans SQLite ;
- `repository.py` persiste les rapports atomiquement ;
- `comparison.py` calcule indices, scénarios, incertitudes et formulations ;
- `html_report.py` produit un document autonome sans ressource distante ;
- `cli.py` expose les commandes, pondérations et formats de comparaison.

Un benchmark reçoit un `BenchmarkContext` et retourne un `BenchmarkResult`. Il
doit employer des données déterministes, exclure sa préparation du chronométrage,
borner ses ressources avec le profil et nettoyer ses fichiers temporaires. Son
identifiant reste stable afin que les rapports puissent être comparés.

Le service répète chaque runner séparément, puis stocke la médiane comme
`value`. Les valeurs brutes ne doivent jamais être supprimées : l'analyse en a
besoin pour signaler les plages min–max chevauchantes.

Chaque identifiant possède aussi une entrée dans `BENCHMARK_DOCUMENTATION`.
Méthode, limites et références sont embarquées dans le rapport JSON et exposées
par `perfcomparator describe`.

Ajouter ensuite sa `BenchmarkDefinition` à `DEFINITIONS`. Les groupes et le
catalogue en découlent automatiquement. Toute évolution incompatible du JSON
doit incrémenter `schema_version`.
Le schéma privé 7 ajoute `execution_status` afin qu'un rapport partiel conservé
après annulation soit explicite. L'export public doit refuser tout rapport dont
cet état vaut `cancelled`. Cette métadonnée ne change pas les mesures ; les
rapports des schémas 6 et 7 restent comparables.

Trois versions ont des responsabilités distinctes dans un rapport :

- `suite_version` identifie exactement le logiciel qui l'a produit ;
- `schema_version` identifie la structure JSON ;
- `protocol_version` identifie la méthode de mesure et décide de la
  compatibilité comparative.

Une correction de CLI peut donc incrémenter `suite_version` sans changer
`protocol_version`. Toute modification des charges, paramètres ou règles de
calcul susceptibles de changer les scores doit au contraire créer une nouvelle
version de protocole. Le champ `protocol_version`, optionnel pour préserver le
schéma 4, est toujours écrit par les nouvelles campagnes. Pour les archives qui
le précèdent, `comparison.py` conserve une table historique explicite ; ne
jamais déduire la compatibilité d'un simple préfixe de version.

Le contrôle préalable repose sur `psutil`. Il ne bloque jamais une campagne :
il produit un `ReadinessSnapshot`, affiché par la CLI, persisté dans le schéma 4
et repris par l'analyse comparative. Toute évolution des seuils doit rester
documentée dans la méthodologie et testée sans attente réelle.

`system.model_year` est un champ facultatif dérivé de l'identifiant Apple et,
si nécessaire, de sa référence commerciale. Il indique l'année de
commercialisation, jamais l'année de fabrication ; il reste nul si le modèle
est inconnu ou ambigu.

Les validations locales sont :

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv build
```

Pour préparer et tester les installateurs avant une publication, suivre la
[stratégie de publication](strategie-publication.md). Elle décrit les contrôles
des artefacts Actions, les essais manuels sur les systèmes cibles et la
promotion en Release des mêmes fichiers testés, sans reconstruction.

Pour produire un PDF mêlant texte et diagrammes Mermaid avec une orientation de
page adaptée à chaque diagramme, suivre le
[guide d'export Markdown en PDF](export-markdown-pdf.md).
