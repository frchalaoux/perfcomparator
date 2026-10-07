# Documentation PerfComparator

Choisissez un parcours selon votre besoin. La
[page d'accueil du projet](README.md) présente l'application et le démarrage
rapide ; la [page des versions](docs/versions.md) contient l'historique et les
instructions propres à chaque version.

## Installer et utiliser

- [Installer sur macOS, Windows ou Linux](docs/installation.md), y compris en
  ligne de commande sur un serveur sans interface graphique.
- [Utiliser PerfComparator](docs/guide-utilisateur.md) : interface, campagnes,
  rapports et comparaisons.
- [Désinstaller PerfComparator](docs/desinstallation.md) et connaître les
  données conservées.
- [Choisir et installer une version](docs/versions.md) : stable, préversions,
  historique et commandes exactes.

## Mesurer et comprendre les benchmarks

- [Méthodologie](docs/methodologie.md) : reproductibilité, portée et limites
  des scores.
- [Description et références des benchmarks](docs/references-benchmarks.md) :
  mesures, protocoles et bibliographie.

## Comparer des rapports

- [Comparaison visuelle](docs/guide-utilisateur.md#rapport-visuel-et-priorités) :
  indices, pondérations et rapport HTML.

## Partager des résultats

- [Format des rapports publics](docs/format-rapport-public.md) : données
  partagées, confidentialité, licence et validation.
- [Tutoriel du catalogue communautaire](docs/tutoriel-catalogue.md) : mesurer,
  exporter, contribuer, télécharger et comparer.

## Développer, tester et publier

- [Guide développeur](docs/guide-developpeur.md) : architecture, validations
  locales (`ruff`, `pytest`, construction du paquet) et ajout d'un benchmark.
- [Référence d’architecture PerfComparator, SMB et SMB-WEB](docs/architecture-perfcomparator-smb-reference.md) : état du code, motifs réutilisables, topologies à deux composants et décisions à prendre.
- [Plan d’évolution de l’interface Web](docs/plan-evolution-interface-web.md) :
  architecture locale et serveur, sécurité, stockage, API et phases de
  réalisation.
- [Détail des phases 1 et 2](docs/plan-phases-1-2.md) : parcours locaux
  read-only, campagnes, tâches, progression, critères de sortie et décisions à
  verrouiller avant le développement.
- [Propositions de décisions — phase 0](docs/propositions-decisions-phase-0.md) :
  recommandations sur les processus, dépôts, paquets, contrats HTTP, tâches,
  sécurité locale et sujets reportés.
- [Stratégie de publication](docs/strategie-publication.md) : construction,
  contrôles des artefacts, essais sur les systèmes cibles et promotion en
  Release des mêmes fichiers testés, avec schémas Mermaid.
- [Export Markdown en PDF](docs/export-markdown-pdf.md) : mise en page des
  documents contenant des diagrammes Mermaid.
