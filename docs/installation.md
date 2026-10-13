# Installer PerfComparator

## Disponibilité actuelle

La release stable [`v0.5.2`](https://github.com/frchalaoux/perfcomparator/releases/tag/v0.5.2)
installe deux paquets : PCE `0.5.2` et PCWEB `0.1.1`. Ses installateurs
sont disponibles sur la [page de téléchargement](https://frchalaoux.github.io/perfcomparator/)
et dans la release GitHub. Les noms des paquets sont
`PerfComparator-macOS.zip`,
`PerfComparator-Windows-x64.zip`, `PerfComparator-Linux-x86_64.tar.gz` et,
pour Ubuntu/Debian, `PerfComparator-Ubuntu-Debian-amd64.deb`.

La `v0.5.0` correspond à l’ancienne application de bureau et ne fournit pas
l’architecture PCE/PCWEB. Pour l’installer, suivez sa
[documentation archivée](archive/v0.5.0/docs/installation.md). Les versions
publiées sont listées dans [Versions](versions.md) et sur la page des
[releases GitHub](https://github.com/frchalaoux/perfcomparator/releases).

## Ce que l’installation actuelle prépare

L’application est installée dans le compte utilisateur. Elle comprend PCE et
PCWEB, deux services locaux indépendants qui communiquent par une API HTTP.
L’installation prépare `uv`, CPython 3.14.4 si cette version n’est pas déjà
disponible, puis les paquets Python `perfcomparator` et `perfcomparatorweb`.
Elle crée le lanceur ou raccourci **PerfComparator**. L’utilisateur n’a pas à
installer Python lui-même.

Après l’installation, le raccourci ou la commande suivante démarre les deux
services et ouvre l’interface Web :

```sh
perfcomparator start
```

La commande `perfcomparator stop` les arrête. Les étapes pour gérer les services
séparément sont dans le [guide utilisateur](guide-utilisateur.md#démarrer-et-arrêter-les-serveurs).

## Vérifier une installation

Dans un terminal ouvert après l’installation :

```sh
perfcomparator --version
perfcomparator start
```

Vérifiez que le navigateur affiche les pages **Machine**, **Benchmarks**,
**Nouvelle campagne**, **Rapports** et **Comparer**. La page Machine attend la
réponse de PCE ; le premier inventaire peut prendre une trentaine de secondes
sous Windows. Une jauge indique le chargement. Une fois l’interface vérifiée,
arrêtez les services avec `perfcomparator stop`.

Si l’interface affiche PCE comme indisponible, vérifiez les deux processus et
leurs journaux dans le répertoire d’état de PerfComparator. Le chemin par défaut
est propre à la plateforme et peut être remplacé par
`PERFCOMPARATOR_STATE_DIR`. L’interface Web et le moteur ont chacun un journal.
Consultez le [guide de désinstallation](desinstallation.md) pour retirer les
paquets sans supprimer les rapports ni les journaux.

## Installation d’essai isolée

Les archives `PerfComparator-Essai` sont des paquets de validation fournis aux
testeurs avant publication. Elles installent les exécutables et les données de
l’application dans un profil séparé afin de ne pas remplacer une installation
existante. Elles ne constituent pas les installateurs officiels attachés aux
releases. Consultez le fichier `LISEZ-MOI` de l’archive d’essai pour les
commandes propres au système testé.
