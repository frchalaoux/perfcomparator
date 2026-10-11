# Format des rapports publics

## Portée

Le format `perfcomparator-public-report`, version `3`, est le format courant du
catalogue communautaire. Il est construit depuis un rapport privé par
`perfcomparator export-public`; le fichier privé ne doit jamais être ajouté au
catalogue. Les rapports publics historiques en versions `1` et `2` restent
acceptés et conservent exactement leur identifiant de contenu.

La version `3` accepte les schémas privés `3` à `6` du protocole de mesure
`0.3.0`. Le schéma `5` ajoute l'identité commerciale non unique de la machine et
le schéma `6` sa référence commerciale facultative.
Pour un ancien rapport, PerfComparator propose un nom à partir des informations
encore disponibles. Le schéma `3` ne contenant pas le contrôle préalable, son
état de préparation est publié avec la valeur `null`. Un format inconnu, un
protocole incompatible, un benchmark inconnu, un résultat dupliqué ou un
rapport sans résultat est refusé plutôt que d'être exporté avec une
anonymisation incertaine.

## Liste blanche

Le fichier public conserve seulement :

- l'identifiant et la version du format public ;
- la licence `CC0-1.0` et l'état `community-unverified` ;
- les versions du schéma source, de la suite et du protocole ;
- le profil, le nombre de passages et les benchmarks demandés ;
- la famille du système, l'architecture, le processeur, les nombres de cœurs,
  la quantité de mémoire, les GPU et l'environnement Python ;
- le fabricant, le nom commercial confirmé avant publication et l'identifiant
  non unique du modèle ;
- la référence commerciale ou SKU, facultative et non unique ;
- le booléen indiquant si le contrôle initial était satisfaisant ;
- les scores, unités, paramètres comparatifs, échantillons et dispersions ;
- les identifiants des benchmarks en échec, sans leur message libre.

Tout champ non déclaré est interdit par le schéma public. Les intitulés des
benchmarks sont repris du catalogue de la suite, et non du texte potentiellement
modifié dans le rapport source.

Sont notamment absents :

- le label libre et la date de la campagne ;
- le chemin de l'exécutable Python ;
- les PID, noms de processus et métriques de charge détaillées ;
- les avertissements et messages d'erreur libres ;
- la version détaillée du système et du noyau ;
- les capacités totale et libre du disque ;
- les instantanés d'alimentation et de température ;
- le numéro de série, les UUID matériels et le nom d'hôte.

Le nom commercial est une déclaration communautaire modifiable avant l'export,
pas une donnée certifiée par le constructeur. `perfcomparator contribute` en
propose un et demande sa confirmation. Dans le parcours manuel, il peut être
précisé explicitement :

```bash
perfcomparator export-public rapport-prive.json \
  --output rapport-public.json \
  --machine-name "Apple MacBook Pro 15 pouces (2018)" \
  --machine-sku "MR942FN/A" \
  --accept-cc0
```

La référence peut indiquer une configuration et une région de vente. Elle est
donc facultative. Pour Apple, une référence complète se termine par `/A` ; une
forme contenant `xx`, telle que `MGPC3xx/A`, désigne plusieurs régions et est
refusée. Aucun numéro de série ne doit être saisi à sa place.

La détection utilise `SystemSKUNumber` sous Windows et le champ DMI
`product_sku` sous Linux. Sous macOS, elle se limite à une référence directement
exposée par Informations système ; PerfComparator ne transmet jamais le numéro
de série à un service de recherche. Les firmwares pouvant laisser le SKU vide
ou générique, la confirmation humaine reste nécessaire.

## Identifiant déterministe

`report_id` est la somme SHA-256 du contenu public canonique, préfixée par
`sha256:`. Elle sert à détecter les doublons et change si une donnée comparative
change. Elle n'est dérivée d'aucun compte, adresse réseau, numéro de série ou
identifiant matériel. Le même rapport source produit donc exactement le même
export et le même identifiant.

## Licence, consentement et authenticité

L'export exige `--accept-cc0`. Cette confirmation indique que l'auteur accepte
la diffusion des données exportées sous [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/).
La commande écrit uniquement le chemin demandé et n'effectue aucune connexion
réseau.

Le matériel et les scores restent naturellement descriptifs d'une configuration.
L'export retire les données locales inutiles, mais ne promet pas l'anonymat face
à une combinaison matérielle rare. Il faut relire le JSON avant publication.

Enfin, un rapport conforme peut être falsifié. `community-unverified` signifie
que le schéma est exploitable, pas que les performances ou la machine ont été
certifiées.

## Validation d'un fichier reçu

La commande suivante effectue les contrôles prévus pour les futures
contributions au catalogue :

```bash
perfcomparator validate-public rapport-public.json
```

Elle refuse notamment :

- un fichier supérieur à 2 Mio ou contenant un champ inconnu ;
- un format, schéma source, protocole, système ou environnement Python inconnu ;
- un benchmark, profil, groupe, intitulé, unité ou paramètre incohérent ;
- des résultats dupliqués, manquants ou également déclarés en échec ;
- des échantillons non finis, non positifs ou incompatibles avec la médiane,
  le minimum, le maximum et la dispersion annoncés ;
- un chemin utilisateur dans un texte autorisé ;
- un UUID ou une référence Apple incomplète dans `product_sku` ;
- un `report_id` qui ne correspond pas exactement au contenu canonique.

La commande ne réalise aucune connexion réseau et ne modifie pas le fichier.
