# Désinstaller PerfComparator

Les désinstallateurs retirent PerfComparator du compte courant et les lanceurs
créés par son installateur. Ils conservent `uv`, CPython géré par `uv`, les
rapports de benchmark et les journaux d'installation. Cette conservation évite
de casser d'autres outils `uv` et protège les données de l'utilisateur.

Téléchargez le désinstallateur adapté depuis la
[page PerfComparator](https://frchalaoux.github.io/perfcomparator/) ou utilisez
le script inclus dans l'archive d'installation. Il demande une confirmation ;
l'option `--yes` (ou `-Yes` sous PowerShell) confirme sans invite interactive.
Les anciennes archives ne sont pas modifiées rétroactivement ; la page fournit
le désinstallateur courant même si l'archive téléchargée auparavant ne le
contenait pas.

## macOS

Dans Terminal, depuis le dossier `Téléchargements` :

```sh
bash ~/Downloads/PerfComparator-uninstall-macOS.sh
```

Pour un Mac administré à distance en SSH, c'est la même commande. Elle retire
`~/Applications/PerfComparator.app`, le raccourci du Bureau s'il pointe vers
cette application et l'outil installé par `uv`.

## Windows 10, Windows 11 et Windows Server Core

Dans PowerShell, lancez le script téléchargé :

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Downloads\PerfComparator-uninstall-Windows.ps1"
```

Cette commande fonctionne avec Windows PowerShell 5.1 ; PowerShell 7 n'est pas
requis. Sur Server Core, elle se lance depuis la session PowerShell du compte
qui a installé PerfComparator. Aucun bureau graphique n'est nécessaire. Le
désinstallateur enlève l'outil `uv` PerfComparator et son raccourci s'il
correspond bien au lanceur de l'application.

Pour confirmer sans invite :

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Downloads\PerfComparator-uninstall-Windows.ps1" -Yes
```

## Linux

Dans un terminal, lancez le script téléchargé :

```sh
bash ~/Downloads/PerfComparator-uninstall-Linux.sh
```

La commande fonctionne aussi sur un serveur sans interface graphique. Elle
retire l'outil `uv`, le lanceur du menu et le raccourci du Bureau s'ils
correspondent aux fichiers créés par PerfComparator.

Pour une installation Ubuntu/Debian faite avec une version du paquet `.deb` qui
inclut la commande de désinstallation, lancez d'abord le désinstallateur
utilisateur :

```sh
perfcomparator-uninstall
```

Le paquet Debian fournit uniquement le lanceur système « Installer
PerfComparator » ; il est indépendant de l'application et peut rester installé.
Pour le retirer aussi, après le désinstallateur utilisateur :

```sh
sudo apt remove perfcomparator-installer
```

Cette dernière commande retire le paquet système et demande les droits
administrateur. Elle ne supprime pas les rapports, les journaux, `uv` ni les
versions de Python gérées par `uv`.

## Données conservées

Les rapports produits par les campagnes PCWEB sont conservés par défaut dans
`~/Documents/PerfComparator` (ou dans le chemin défini par
`PERFCOMPARATOR_WEB_REPORTS_DIR`). Les campagnes lancées directement depuis la
CLI conservent leur comportement propre et écrivent par défaut dans
`data/results` sous le répertoire courant. Le désinstallateur ne supprime ni
ces rapports ni les fichiers d’état et les journaux de PCE. Leur emplacement
peut être modifié avec `PERFCOMPARATOR_STATE_DIR`. Sous Windows, les journaux
d’installation sont dans `%LOCALAPPDATA%\PerfComparator\logs`.

L'installation de `uv` et de Python reste disponible pour les autres outils ou
projets qui pourraient en dépendre.
