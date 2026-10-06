# Stratégie de publication

Cette fiche décrit comment une modification devient une version installable et
comment vérifier que la version est réellement intégrée au dépôt.

## Les objets Git et GitHub

| Objet | Rôle | Peut-il changer de cible ? |
| --- | --- | --- |
| Branche de travail, par exemple `feat/nom` | Regroupe les commits d'une fonctionnalité en cours. | Oui, elle avance avec de nouveaux commits. |
| Branche de release, par exemple `release/0.4.0` | Porte le contenu final de la version et permet de l'intégrer par PR. | Oui, jusqu'à sa clôture. |
| Commit | Instantané précis de fichiers suivis. | Non : un nouveau contenu crée un nouveau commit. |
| Tag, par exemple `v0.4.0` | Désigne le commit exact d'une version publiée. | Il doit rester immuable après publication. |
| GitHub Release | Fiche publique, notes et archives associées à un tag. | Les notes peuvent être corrigées ; le tag et son code ne doivent pas être déplacés. |
| `main` | Branche par défaut, dont GitHub affiche le README sur la page d'accueil. | Elle avance par fusion de PR. |

Un fichier présent dans le dossier de travail mais non commité n'appartient à
aucun commit, tag ni release. Avant une publication, distinguer les changements
du produit et de sa documentation utilisateur des notes locales, fichiers
d'éditeur et mémoires de branche. Seuls les premiers doivent entrer dans le
périmètre de release.

## Déroulé d'une stable

1. **Fixer le périmètre.** Inventorier le diff et le statut Git. Vérifier que
   chaque changement produit attendu est suivi et commité ; laisser explicitement
   de côté les rapports privés, sorties générées, réglages locaux et notes
   transitoires.
2. **Préparer la version.** Depuis les changements fonctionnels validés, aligner
   la version du paquet, les installateurs, le verrou de dépendances, les tests,
   le README et la documentation. Les installateurs doivent cibler le tag annoncé.
3. **Valider le commit candidat.** Exécuter les tests, le lint et le formatage
   adaptés au risque, construire les distributions, inspecter leur contenu et
   faire un smoke test de la version exacte. Ne pas répéter les validations sans
   changement pertinent.
4. **Publier la référence.** Après annonce précise et confirmation explicite,
   pousser la branche qui contient le commit, puis créer et pousser le tag
   annoté sur le SHA vérifié. La branche est publiée avant ou avec le tag afin
   que le commit reste intégrable par pull request.
5. **Créer la release GitHub.** L'associer au tag existant, écrire des notes
   vérifiées et marquer une stable comme stable — jamais comme préversion.
6. **Intégrer à `main`.** Ouvrir une PR documentée de la branche de release vers
   `main`. Attendre les contrôles configurés, puis fusionner si ceux-ci passent.
   La publication du tag ne met pas automatiquement à jour `main`.
7. **Vérifier la clôture.** Contrôler le SHA du tag, la fiche Release, l'état de
   la PR et le contenu distant de `main`, notamment le README et ses liens. Le
   travail n'est terminé qu'une fois l'intégration vérifiée.

Si un contrôle échoue ou qu'un état distant diffère de celui annoncé, arrêter la
séquence et réévaluer avant toute autre écriture distante. Une confirmation
explicite peut couvrir une séquence annoncée en entier, mais n'autorise pas à en
élargir le périmètre.

## Tester les installateurs avant publication

Pour tester les installateurs sans publier de tag ou de Release, intégrer
d'abord les changements dans `main`, puis lancer **Actions → Package desktop
installers → Run workflow** en choisissant `main`. Le workflow produit les
archives macOS, Windows et Linux, le paquet Ubuntu / Debian `.deb` et les
désinstallateurs autonomes sous la forme d'un artefact Actions temporaire
(conservation de 14 jours).

Chaque paquet contient le SHA complet de son commit source et une URL d'archive
GitHub épinglée sur ce SHA ; son installateur utilise cette URL plutôt qu'une
version antérieure par tag. L'artefact global inclut un manifeste indiquant le
SHA source, la version du paquet et les empreintes SHA-256 des fichiers. Vérifier
ce manifeste, puis tester exactement ces fichiers dans les VM et sur le Mac.
Ne pas créer de préversion ou de Release pour ce parcours interne.

La promotion d'un artefact Actions déjà testé vers une Release n'est pas encore
automatisée. Le workflow déclenché par une Release reconstruit les paquets ; ne
pas l'utiliser pour publier les résultats des essais tant que la promotion des
mêmes fichiers n'est pas disponible.

## Préversions

Les préversions utilisent la forme `vX.Y.Z.devK`, par exemple `v0.4.0.dev7` ;
la version du paquet est identique sans le `v`. README, installateurs,
documentation et liens doivent employer exactement la même version. Les
préversions ne remplacent pas la stable recommandée.

## Exemple : `v0.4.0`

- Le tag annoté `v0.4.0` désigne le commit de release `cabeb2f`.
- La GitHub Release **PerfComparator v0.4.0** est associée à ce tag.
- La PR #23 a intégré ce commit à `main` dans le commit de fusion `ba962a0`.
- Le tag n'a pas été déplacé sur le commit de fusion : celui-ci contient le
  commit tagué comme parent, et le README de `main` annonce désormais la stable.

Cette distinction permet de retrouver le commit exact de la version publiée
tout en gardant une intégration documentée dans la branche par défaut.
