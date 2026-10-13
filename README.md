# PerfComparator

**Mesurez et comparez vos machines avec des campagnes CPU, mémoire, stockage,
applications et GPU.**

PerfComparator est une application locale composée de deux services Python :
**PerfComparator Engine (PCE)** collecte les informations de la machine, exécute
les benchmarks et conserve les rapports ; **PerfComparator Web (PCWEB)** fournit
l’interface dans le navigateur. Les deux services communiquent par une API HTTP
locale et ne nécessitent pas de compte ni de serveur distant.

## État des versions

- Dernière version stable publiée :
  [`v0.5.1`](https://github.com/frchalaoux/perfcomparator/releases/tag/v0.5.1),
  avec PCE `0.5.1` et PCWEB `0.1.1.dev0`.
- Prochaine version stable en préparation : PCE `0.5.2` avec PCWEB
  `0.1.1`. Elle n’est pas encore publiée ni installable.
- Dernière préversion publiée :
  [`v0.5.0.dev0`](https://github.com/frchalaoux/perfcomparator/releases/tag/v0.5.0.dev0),
  antérieure à l’architecture PCE/PCWEB.
- [Documentation archivée de `v0.5.0`](docs/archive/v0.5.0/index.md) · [Toutes les versions publiées](https://github.com/frchalaoux/perfcomparator/tags).

La [page de téléchargement](https://frchalaoux.github.io/perfcomparator/) propose
les installateurs de la dernière release stable. Pour l’ancienne application
de bureau `v0.5.0`, consultez sa documentation archivée.

## Démarrer l’application actuelle

Dans une installation qui contient PCE et PCWEB :

```sh
perfcomparator start
```

Cette commande démarre les deux serveurs locaux et ouvre PCWEB dans le
navigateur. L’interface propose les pages **Machine**, **Benchmarks**,
**Nouvelle campagne**, **Rapports** et **Comparer**. Pour arrêter les deux
services :

```sh
perfcomparator stop
```

Les commandes `perfcomparator engine start|stop|status` gèrent PCE. Les
commandes `perfcomparator web stop|status` gèrent PCWEB seul. La commande
`perfcomparatorweb start|stop|status` permet aussi de gérer PCWEB séparément ;
PCE doit alors être démarré avant PCWEB.

Une campagne se lance depuis PCWEB après vérification des conditions de mesure.
La page affiche sa progression et donne accès au rapport. Les rapports sont
parcourus par pages ; dans **Comparer**, on peut filtrer les machines et garder
les sélections d’un lot à l’autre. Les résultats peuvent être exportés dans un
rapport HTML détaillé. Les corrections des propriétés
`model`, `model_year` et `product_sku` sont enregistrées par PCE et utilisées
pour les nouveaux rapports.

## Benchmarks et comparaison

Le catalogue couvre les processeurs, la mémoire, le stockage, les charges
applicatives et quatre benchmarks GPU WebGPU. PCWEB permet de sélectionner tous
les tests d’un coup, un groupe entier ou des tests individuels. Si les mesures
GPU sont sélectionnées sans adaptateur compatible, le contrôle préalable
présente un avertissement avant le lancement.

La comparaison Web présente les informations de chaque machine, les résultats
communs, les catégories et les scénarios. Elle peut être téléchargée en HTML
autonome ou imprimée en PDF. Les commandes PCE de diagnostic et d’analyse
(`perfcomparator info`, `list`, `describe`, `run`, `history` et `compare`)
restent également disponibles.

## Documentation

- [Installer et désinstaller](docs/installation.md) — état des releases et
  installation du logiciel actuel lorsqu’il sera publié.
- [Guide utilisateur](docs/guide-utilisateur.md) — Machine, campagnes,
  rapports, comparaison et commandes des serveurs.
- [Références des benchmarks](docs/references-benchmarks.md) et
  [méthodologie](docs/methodologie.md).
- [Guide développeur](docs/guide-developpeur.md) et
  [lexique technique](docs/lexique-technique.md).
- [Stratégie de construction et publication des installateurs](docs/strategie-publication.md).
- [Documentation historique de `v0.5.0`](docs/archive/v0.5.0/index.md).

Les documents intitulés « plan », « proposition » ou « référence » décrivent
les décisions et l’historique de conception ; ils ne sont pas le guide
fonctionnel courant.
