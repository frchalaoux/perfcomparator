# Guide utilisateur — interface PerfComparator Web

Ce guide décrit l’application actuelle : PCE collecte et mesure la machine ;
PCWEB présente les informations dans le navigateur et pilote les campagnes.
L’application fonctionne localement, sans compte ni connexion à un service
distant. Pour l’ancienne application de bureau de `v0.5.0`, consultez
[son archive documentaire](archive/v0.5.0/index.md).

## Démarrer et arrêter les serveurs

Dans le terminal du compte ayant installé PerfComparator :

```sh
perfcomparator start
```

PCE et PCWEB démarrent, puis la page locale s’ouvre dans le navigateur. Pour
fermer proprement les deux services :

```sh
perfcomparator stop
```

Les services peuvent être gérés séparément :

| Action | Commande |
| --- | --- |
| Démarrer PCE | `perfcomparator engine start` |
| Arrêter PCE | `perfcomparator engine stop` |
| Vérifier PCE | `perfcomparator engine status` |
| Arrêter PCWEB seul | `perfcomparator web stop` |
| Vérifier PCWEB | `perfcomparator web status` |
| PCWEB seul | `perfcomparatorweb start`, `stop` ou `status` |

Pour lancer PCWEB séparément, PCE doit déjà fonctionner. `perfcomparator web
start` reste un alias qui démarre les deux services. `perfcomparator --help`
affiche les commandes installées.

## Machine

La page **Machine** montre l’inventaire détecté par PCE : modèle, année si elle
est connue, référence produit, fabricant, système, processeur, cœurs, mémoire,
version de Python et adaptateurs WebGPU. Le premier inventaire peut prendre
plus de temps, notamment sous Windows ; PCWEB affiche une jauge pendant
l’attente et réutilise le cache lors des visites suivantes.

La section **Propriétés modifiables** permet de corriger `model`,
`model_year` et `product_sku`. PCE conserve ces valeurs dans son répertoire
d’état. Elles sont reprises dans les rapports des prochaines campagnes ; les
rapports déjà créés gardent les informations qui leur appartenaient.

## Benchmarks et campagnes

La page **Benchmarks** présente le catalogue, les groupes et les détails des
tests. Dans **Nouvelle campagne**, choisissez un profil, le nombre de passages
et les tests. Vous pouvez cocher tous les tests, un groupe entier ou chaque
test séparément.

Avant le lancement, PCWEB demande à PCE de vérifier les conditions de mesure.
Lisez les avertissements et confirmez pour démarrer. Si des tests GPU sont
sélectionnés sans adaptateur compatible, le contrôle préalable le signale afin
que les échecs prévisibles soient visibles avant confirmation.

La page affiche l’état de la campagne, le nombre de tests terminés, le test en
cours et les événements de progression. À la fin, le lien **Consulter le
rapport détaillé** ouvre le rapport produit. Une campagne interrompue par
l’arrêt du moteur est indiquée comme interrompue.

## Rapports

La page **Rapports** affiche l’historique stocké par PCE, par lots de 20. Pour
rechercher une machine et préparer une comparaison, utilisez la page
**Comparer** : son champ filtre le lot affiché et le bouton de recherche
recherche dans tous les rapports. Les sélections restent disponibles pendant
la navigation entre les lots.

Une fiche de rapport contient la version de PerfComparator, le profil, les
tests demandés, les informations système, les avertissements, les scores
médianes, les passages individuels, la dispersion et les échecs éventuels. Le
groupe **Système** utilise les mêmes champs que la page **Machine**. Les
propriétés modifiables ne sont pas présentées comme un groupe séparé dans le
rapport.

## Comparer des machines

Dans **Comparer**, recherchez les machines ou rapports, parcourez les pages et
sélectionnez les rapports à comparer. Choisissez la référence ; son indice vaut
100. La comparaison affiche les informations des machines, les indices par
catégorie et scénario, les avertissements de compatibilité ainsi que les
mesures communes avec leurs unités et dispersions.

Le rapport détaillé peut être ouvert dans le navigateur, téléchargé sous forme
d’un fichier HTML autonome ou imprimé en PDF. Le fichier HTML peut être conservé
et consulté hors ligne.

## Commandes PCE complémentaires

La ligne de commande reste disponible pour les opérations détaillées :

```sh
perfcomparator info
perfcomparator list
perfcomparator describe cpu.integer
perfcomparator run --group cpu --profile quick --label "Ma machine"
perfcomparator history
```

PCE fournit également `compare` pour analyser des rapports JSON, ainsi que les
commandes d’export et de contribution au catalogue communautaire. Elles ne
remplacent pas le parcours Web de campagne et de comparaison décrit plus haut.
Voir le [tutoriel catalogue](tutoriel-catalogue.md) et le
[format de rapport public](format-rapport-public.md) pour le partage explicite
d’un export anonymisé.
