# Désinstaller PerfComparator

Les désinstallateurs retirent PerfComparator du compte courant et les lanceurs
créés par son installateur. Ils conservent `uv`, CPython géré par `uv`, les
rapports de benchmark et les journaux d'installation. Cette conservation évite
de casser d'autres outils `uv` et protège les données de l'utilisateur.

Utilisez le désinstallateur inclus dans l'archive PerfComparator correspondant
à votre système. Il demande une confirmation ; l'option `--yes` (ou `-Yes` sous
PowerShell) permet de confirmer explicitement sans question interactive.
Les anciennes archives ne sont pas modifiées rétroactivement. Si votre archive
ne contient pas le script, téléchargez-le depuis le
[dépôt GitHub](https://github.com/frchalaoux/perfcomparator/tree/main) avant de
le lancer.

## macOS

Dans Terminal, depuis le dossier extrait de l'archive macOS :

```sh
bash ./uninstall.sh
```

Pour un Mac administré à distance en SSH, c'est la même commande. Elle retire
`~/Applications/PerfComparator.app`, le raccourci du Bureau s'il pointe vers
cette application et l'outil installé par `uv`.

## Windows 10, Windows 11 et Windows Server Core

Ouvrez PowerShell dans le dossier extrait de l'archive Windows et lancez :

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\uninstall.ps1
```

Cette commande fonctionne avec Windows PowerShell 5.1 ; PowerShell 7 n'est pas
requis. Sur Server Core, elle se lance depuis la session PowerShell du compte
qui a installé PerfComparator. Aucun bureau graphique n'est nécessaire. Le
désinstallateur enlève l'outil `uv` PerfComparator et son raccourci s'il
correspond bien au lanceur de l'application.

Pour confirmer sans invite :

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\uninstall.ps1 -Yes
```

## Linux

Depuis le dossier extrait de l'archive Linux, dans un terminal :

```sh
bash ./uninstall.sh
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

Les rapports JSON restent dans `data/results` sous les répertoires où les
campagnes ont été lancées ; le désinstallateur ne peut pas les retrouver ni les
supprimer sans risque. Les journaux Windows restent dans
`%LOCALAPPDATA%\PerfComparator\logs`. L'installation de `uv` et de Python reste
disponible pour les autres outils ou projets qui pourraient en dépendre.
