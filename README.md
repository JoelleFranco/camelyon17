# Détection de métastases du cancer du sein (CAMELYON17)

Projet de deep learning (MBA 2) : détecter les métastases du cancer du sein dans des lames de ganglions lymphatiques
(jeu de données public CAMELYON17), puis en déduire le stade pN de chaque patiente.

La chaîne de traitement :
1. découper les lames en petits carrés (patchs) de 112 µm, étiquetés sain ou tumoral grâce aux annotations des pathologistes ;
2. modèle de patch : caractéristiques d'un ResNet18 pré-entraîné (non modifié), puis régression logistique ;
3. lame entière : carte de chaleur, recherche des lésions et mesure de la plus grande, classe de la lame (négative, ITC, micro, macro) ;
4. patiente : stade pN à partir de ses lames, comparé au vrai stade avec le kappa pondéré.

## Organisation du dépôt

```
decouverte_prototype/
    01_decouverte_et_prototype.ipynb   découverte des données et prototype sur 9 lames
    data/                              données du prototype (ignorées par Git)
version_finale/
    camelyon_data.py                   accès aux données : index des lames, annotations XML, lecture des lames sur AWS
    extract_patches.py                 découpage des lames en patchs
    parametres_decoupage.py            réglages du découpage et variantes testées
    modele_patch.py                    ResNet18 partagé par le notebook 02 et cartes_chaleur.py
    cartes_chaleur.py                  caractéristiques de tout le tissu des lames de validation et de test
    notebooks/
        01_preparation_donnees.ipynb       index, sélection des lames, détection du tissu, choix de l'étiquetage
        02_modelisation_evaluation.ipynb   modèle de patch, lames entières, patientes, test et analyse des erreurs
    data/, patches/, cartes/, resultats/   fichiers produits par les scripts (ignorés par Git)
requirements.txt
```

## Installation

### Prérequis

- Python 3.13
- Git
- Environ 8 Go d'espace disque pour les lames du prototype (téléchargées par le notebook). La version finale lit les lames directement sur AWS : elle n'a besoin que de place pour les patchs et les cartes (quelques Go).
- Le projet a été développé sous Windows 11 avec une carte graphique Intel Arc (PyTorch version XPU). Sans carte Intel, voir la remarque sur PyTorch plus bas.

### 1. Récupérer le projet

```bash
git clone https://github.com/JoelleFranco/camelyon17.git
cd camelyon17
```

### 2. Créer un environnement virtuel

```bash
python -m venv .venv
```

Puis l'activer :

- Windows (PowerShell) : `.venv\Scripts\Activate.ps1`
- Windows (invite de commandes) : `.venv\Scripts\activate.bat`
- macOS / Linux : `source .venv/bin/activate`


### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

Le fichier `requirements.txt` commence par la ligne `--extra-index-url https://download.pytorch.org/whl/xpu` : elle indique à pip d'aller chercher PyTorch sur le site de PyTorch, dans sa version pour cartes graphiques Intel (XPU).

**Sans carte graphique Intel** : retirer les lignes `torch`, `torchvision` et les paquets Intel (`intel-*`, `onemkl-*`, `mkl`, `dpcpp-cpp-rt`, `intel-pti`) du fichier, installer le reste, puis installer PyTorch pour sa machine en suivant https://pytorch.org/get-started/locally/. Le code choisit automatiquement la carte Intel si elle est disponible, et le processeur sinon.

OpenSlide est installé par pip avec ses fichiers système (`openslide-bin`) : rien d'autre à installer.

## Prototype

Le notebook est `decouverte_prototype/01_decouverte_et_prototype.ipynb`. Dans VS Code (avec les extensions Python et Jupyter)
ou dans Jupyter, choisir l'environnement `.venv` comme noyau (kernel), puis exécuter les cellules dans l'ordre.
Attention, l'exécution du notebook complet prend plus d'une heure.

Le notebook télécharge lui-même ses données avec AWS CLI (installé par `requirements.txt`) :

- `decouverte_prototype/data/raw/` : `README.md` et `stages.csv` du jeu de données ;
- `decouverte_prototype/data/prototype/images/`, `masks/`, `annotations/` : les 9 lames du prototype avec leurs masques et annotations.

## Version finale

Les commandes se lancent dans un terminal depuis le dossier `version_finale`, et les notebooks s'y placent eux-mêmes
(les chemins sont donc les mêmes partout). Les lames sont lues directement sur AWS, sans les télécharger :
seuls les annotations XML et `stages.csv` sont téléchargés dans `version_finale/data/CAMELYON17/`.

Ordre d'exécution :

1. **Notebook `01_preparation_donnees`, parties 1 à 4** : index des lames, sélection des lames (entraînement, validation, test,
   enregistrée dans `data/CAMELYON17/selection_lames.csv`), taille des pixels par centre, réglage de la détection du tissu.
2. **Découpage** (environ 45 minutes par variante) :
   ```
   python extract_patches.py --variante base centre niveaux     (variantes à comparer)
   python extract_patches.py --variante retenue                 (variante choisie : étiquetage "centre", niveau 2)
   ```
3. **Notebook `01_preparation_donnees`, partie 6** : comparaison des variantes d'étiquetage.
4. **Notebook `02_modelisation_evaluation`, parties 1 à 4** : caractéristiques des patchs, comparaison des variantes
   avec le modèle, modèle de patch final.
5. **Cartes de chaleur** (environ 3 minutes par lame, un peu plus de 2 heures pour les 50 lames ; les lames déjà faites
   sont sautées si on relance) :
   ```
   python cartes_chaleur.py --niveau 2
   ```
6. **Notebook `02_modelisation_evaluation`, partie 6** (lames de validation) : choix du seuil, puis les réglages sont figés
   dans `resultats/reglages_figes.json`.
7. **Notebook `02_modelisation_evaluation`, parties 7 et 8** : test (une seule fois, avec les réglages figés) et analyse des erreurs.

## Données

Les données viennent du jeu de données public CAMELYON17, hébergé sur AWS S3 et accessible sans compte. Elles ne sont pas
dans le dépôt. Pour vérifier l'accès :

```bash
aws s3 ls --no-sign-request s3://camelyon-dataset/CAMELYON17/
```
