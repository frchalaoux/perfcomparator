# Installer PerfComparator

Ce guide décrit l'installation de PerfComparator sous macOS, Windows et Linux.
L'interface Web locale et la ligne de commande sont disponibles après
l'installation ; les campagnes restent utilisables sur un serveur sans
navigateur ni environnement graphique.
Téléchargez les installateurs depuis la
[page officielle de téléchargement](https://frchalaoux.github.io/perfcomparator/)
ou depuis la [liste des releases GitHub](https://github.com/frchalaoux/perfcomparator/releases).
La page de téléchargement choisit une release qui contient les installateurs ;
elle peut donc proposer une préversion si la version stable n'a pas encore ces
fichiers.

Les archives d'installation contiennent le lanceur du système concerné. Celui-ci
installe `uv`, CPython 3.14.4 géré par `uv`, puis PCE et PCWEB dans le compte de
l'utilisateur. Python n'a pas besoin d'être installé séparément. Une connexion
Internet est nécessaire. Les versions prises en charge et leur état (stable ou
préversion) figurent dans la
[page des versions](versions.md).
Les étapes de retrait de l'application sont dans le
[guide de désinstallation](desinstallation.md).

L'interface Web ne s'ouvre pas automatiquement à la fin de l'installation :
utilisez l'icône ou le raccourci créé par l'installateur. Il démarre les deux
serveurs locaux et ouvre l'interface dans le navigateur.

## Option : ligne de commande et serveurs sans interface graphique

La commande `perfcomparator` est installée avec l'application, quel que soit le
parcours choisi. Elle ne nécessite ni bureau graphique ni écran pour les
commandes de diagnostic, de liste et les benchmarks CPU, mémoire ou stockage.
`perfcomparator web` démarre PCE et PCWEB, puis ouvre l'interface Web dans le
navigateur. Cette commande et le raccourci graphique nécessitent un navigateur
et une session utilisateur interactive. Sur macOS et Linux, lancez les
commandes depuis Terminal ; sous Windows, depuis PowerShell ou l'invite de
commandes.

### macOS sans session graphique (serveur ou SSH)

Dans le compte macOS qui utilisera l'application, exécutez l'installateur shell
depuis Terminal ou une session SSH :

```sh
curl -LsSf https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.5.0/install.sh | sh
```

L'installation est propre au compte et ne demande pas de droits administrateur.
Après l'installation, ouvrez une nouvelle session pour actualiser le `PATH`,
puis utilisez la CLI sans lancer l'interface :

```sh
perfcomparator --version
perfcomparator info
perfcomparator run --group cpu --profile quick --label "Serveur macOS"
perfcomparator history
```

Les rapports sont écrits dans `data/results` sous le répertoire courant.
Choisissez un emplacement persistant accessible en écriture. Le démarrage de
l'interface Web nécessite une session interactive ; il n'est pas nécessaire
pour les mesures lancées en SSH.

### Windows Server Core

Server Core ne fournit pas le bureau graphique de Windows Server ; il se gère
notamment depuis PowerShell. Dans une session PowerShell ouverte sous le compte
qui utilisera PerfComparator, exécutez l'installateur de cette version :

```powershell
irm https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.5.0/install.ps1 | iex
```

PowerShell 5.1 suffit ; PowerShell 7 et l'invite de commandes ne sont pas
nécessaires pour l'installation. L'installation est propre à ce compte et
demande une connexion Internet. À la fin, ouvrez une nouvelle session
PowerShell pour actualiser le `PATH`, puis utilisez la CLI :

```powershell
perfcomparator --version
perfcomparator info
perfcomparator run --group cpu --profile quick --label "Windows Server Core"
perfcomparator history
```

Les rapports sont enregistrés dans `data/results` sous le répertoire courant.
Choisissez un répertoire persistant et accessible en écriture avant de lancer
la campagne. N'exécutez pas `perfcomparator web` sur Server Core : cette
commande ouvre l'interface dans un navigateur et demande une session
interactive. Microsoft décrit les différences entre
[Server Core et Desktop Experience](https://learn.microsoft.com/en-us/windows-server/administration/server-core/what-is-server-core).

### Linux sans interface graphique (serveur SSH)

Sur un serveur Linux x86-64, l'installation se fait dans le compte courant, sans
droits administrateur :

```sh
curl -LsSf https://raw.githubusercontent.com/frchalaoux/perfcomparator/v0.5.0/install.sh | sh
```

L'installateur prépare `uv`, CPython 3.14.4, PCE et PCWEB. Aucun serveur
d'affichage n'est nécessaire pour utiliser la CLI et lancer des campagnes. Pour
ouvrir l'interface Web, utilisez `perfcomparator web` depuis une session
disposant d'un navigateur ; les deux serveurs écoutent uniquement sur la machine
locale.

Exemple de vérification et de campagne CPU légère :

```sh
perfcomparator --version
perfcomparator info
perfcomparator list
mkdir -p "$HOME/perfcomparator"
cd "$HOME/perfcomparator"
perfcomparator run --group cpu --profile quick --label "Serveur Linux"
perfcomparator history
```

Les rapports sont écrits dans `data/results` sous le répertoire courant au
moment du lancement ; choisissez donc un répertoire où le compte peut écrire
et dont les données sont conservées. Pour mesurer le stockage, utilisez
`--work-dir` afin de désigner explicitement le disque à tester. Les mesures GPU
ne sont disponibles que si un adaptateur WebGPU compatible est accessible ;
elles ne sont pas requises pour les campagnes CPU, mémoire ou stockage. Voir le
[guide des commandes](guide-utilisateur.md#choisir-létendue) pour les options
de la CLI.

## macOS

L'archive macOS fonctionne sur les Mac Intel et Apple silicon.

1. Téléchargez `PerfComparator-macOS.zip` depuis la page officielle et ouvrez
   l'archive dans Finder.
2. Ouvrez le dossier `PerfComparator` extrait, puis double-cliquez sur
   `install.command`. Une fenêtre Terminal affiche les étapes ; laissez-la
   ouverte jusqu'au message de fin.
3. macOS peut afficher « Impossible d’ouvrir “install.command” car cette app
   provient d’un développeur non identifié ». `install.command` est un script
   d'installation qui n'est pas signé avec un certificat Apple Developer ID ni
   notarisé par Apple. Cet avertissement signifie que macOS ne peut pas vérifier
   son développeur ; ce n'est pas, à lui seul, la preuve que le fichier est
   malveillant. Vérifiez tout de même que l'archive provient bien de la page
   officielle de PerfComparator avant de continuer.

   Pour autoriser uniquement cet installateur, faites un clic droit (ou
   Ctrl-clic) sur `install.command` dans le Finder et choisissez **Ouvrir**,
   puis confirmez **Ouvrir** si macOS le propose. Si cette option n'est pas
   proposée, essayez de lancer le fichier une fois, puis ouvrez **Réglages
   Système → Confidentialité et sécurité**, descendez jusqu'à la section
   **Sécurité** et cliquez sur **Ouvrir quand même** pour `install.command`.
   Confirmez une dernière fois dans l'alerte qui réapparaît.

   Ne choisissez pas une option qui désactive Gatekeeper pour toutes les
   applications. Pour supprimer cet avertissement à l'avenir, l'installateur
   devra être signé avec un certificat Apple Developer ID et notarisé par
   Apple. Voir l'aide
   [Apple sur l'ouverture d'applications non identifiées](https://support.apple.com/en-us/102445).
4. Ouvrez **PerfComparator.app** depuis `~/Applications` ou son raccourci sur le
   Bureau, s'il a été créé.

## Windows 10 et 11

L'installateur fonctionne avec Windows PowerShell 5.1, déjà fourni avec Windows
10/11. PowerShell 7 n'est pas requis.

1. Téléchargez `PerfComparator-Windows-x64.zip`, puis choisissez **Extraire
   tout**. N'exécutez pas l'installateur directement dans l'aperçu de l'archive.
2. Dans le dossier extrait, double-cliquez sur `install.bat` et laissez la
   fenêtre ouverte jusqu'à la fin. Le lanceur utilise PowerShell 7 s'il est
   déjà installé ; sinon, il utilise automatiquement Windows PowerShell 5.1.
3. Ouvrez **PerfComparator** avec le raccourci du Bureau ou depuis le menu
   Démarrer. Si le Bureau est redirigé vers un dossier réseau, le raccourci est
   placé dans le menu Démarrer local.

L'installateur conserve un journal dans
`%LOCALAPPDATA%\PerfComparator\logs`. En cas d'échec, communiquez le fichier le
plus récent ainsi que le texte affiché dans la fenêtre.

Si Windows affiche un avertissement SmartScreen, ne désactivez pas la protection
du système. Vérifiez que le fichier vient de la release officielle avant de
choisir de poursuivre ; SmartScreen peut signaler les applications téléchargées
qui n'ont pas encore de réputation établie. Voir l'
[explication de Microsoft](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/publish-first-app).

## Linux x86-64

### Ubuntu et Debian : paquet `.deb` (lorsqu'il est proposé)

La page de téléchargement affiche cette option seulement lorsqu'une release
contient effectivement le paquet.

1. Téléchargez `PerfComparator-Ubuntu-Debian-amd64.deb` et ouvrez-le dans
   l'App Center / l'installateur de paquets.
2. Confirmez l'installation du paquet. Cette confirmation système sert à
   installer le lanceur dans le menu des applications ; `uv`, Python, PCE et
   PCWEB sont ensuite installés dans votre compte, sans exécuter leur
   installation en administrateur.
3. Dans le menu des applications, ouvrez **Installer PerfComparator**. Une
   fenêtre de terminal affiche la progression ; attendez le message de fin.
4. Ouvrez ensuite **PerfComparator** depuis le menu des applications ou le
   raccourci du Bureau.

### Autres distributions : archive `.tar.gz`

Utilisez cette méthode si votre distribution n'installe pas les paquets `.deb`,
ou si la release ne propose pas encore cette option.

1. Téléchargez et extrayez `PerfComparator-Linux-x86_64.tar.gz` dans un dossier
   local de votre compte, par exemple `Téléchargements`.
2. Pour le lancement graphique, faites un clic droit sur `install.desktop`,
   choisissez **Autoriser le lancement**, puis double-cliquez normalement. Ne
   choisissez pas **Lancer dans un terminal** pour ce fichier : `.desktop` est
   un descripteur de lanceur, pas un script shell. Le droit exécutable seul ne
   remplace pas l'autorisation demandée par certains bureaux GNOME.
3. Si vous préférez passer par le terminal, ouvrez un terminal dans le dossier
   extrait et lancez le script shell :

   ```sh
   bash ./install-linux.sh
   ```

4. Une fois l'installation terminée, ouvrez **PerfComparator** dans le menu des
   applications ou sur le Bureau.

L'interface Web Linux nécessite une session disposant d'un navigateur. Sur
Ubuntu/Debian, préférez le paquet `.deb` quand il est disponible ; l'archive
reste le choix générique pour les autres distributions.

## Vérifier et lancer l'application

Après installation, la commande `perfcomparator --version` doit afficher la
version installée. Si le terminal ne trouve pas la commande immédiatement,
fermez-le puis ouvrez-en un nouveau. Pour démarrer l'interface depuis un
terminal (le navigateur s'ouvre automatiquement) :

```sh
perfcomparator web
```

## Aide au dépannage

- **L'installateur a fini, mais aucune fenêtre ne s'est ouverte :** c'est normal ;
  ouvrez l'application avec son raccourci.
- **Linux affiche `[Desktop Entry]: not found` :** le fichier `install.desktop`
  a été interprété comme un script. Utilisez **Autoriser le lancement**, puis
  double-cliquez sur le lanceur, ou lancez `bash ./install-linux.sh`.
- **Une installation échoue :** conservez la fenêtre ouverte et copiez son
  message complet. Sous Windows, joignez aussi le journal indiqué plus haut.
- **`perfcomparator` est introuvable dans le terminal :** ouvrez un nouveau
  terminal ou utilisez l'icône créée par l'installateur.
