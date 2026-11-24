# Détection de métastases du cancer du sein (CAMELYON17)

Ce projet vise à détecter les métastases du cancer du sein dans des lames de ganglions lymphatiques (jeu de données public CAMELYON17), puis en déduire le stade pN de chaque patiente.

La chaîne de traitement :
1. découper les lames en petits carrés (patchs) de 112 µm, étiquetés sain ou tumoral grâce aux annotations des pathologistes
2. modèle de patch : caractéristiques d'un ResNet18 pré-entraîné (non modifié), puis régression logistique
3. lame entière : carte de chaleur, recherche des lésions et mesure de la plus grande, classe de la lame (négative, ITC, micro, macro)
4. patiente : stade pN à partir de ses lames, comparé au vrai stade avec le kappa pondéré

Deux analyses complémentaires étudient le domain shift (un modèle face à un hôpital qu'il n'a jamais vu) : un centre mis de côté à l'entraînement, et la normalisation des couleurs (Reinhard, Macenko).


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
        02_modelisation_evaluation.ipynb   modèle de patch, lames entières, patientes, test et analyse des erreurs (Grad-CAM)
    analyses/
        domain_shift/analyse_domain_shift.ipynb   modèle final avec un centre mis de côté à l'entraînement
        multicentres/                              normalisation des couleurs (Reinhard, Macenko) sur les patchs du prototype
            multicentres.ipynb                     résultats et conclusions (relit predictions.csv)
            predictions.csv                        prédictions de chaque méthode pour chaque patch
            README.md                              utilisation de l'analyse
    data/          annotations XML, stages.csv et sélection des lames (ignoré par Git)
    patches/       patchs PNG découpés, par variante et par niveau (ignoré par Git)
    cartes/        caractéristiques ResNet18 de tout le tissu des lames de validation et de test (ignoré par Git)
    resultats/     caractéristiques des patchs, modèle final, réglages figés, résultats du test (ignoré par Git)
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

Le notebook est `decouverte_prototype/01_decouverte_et_prototype.ipynb`. Dans VS Code (avec les extensions Python et Jupyter) ou dans Jupyter, choisir l'environnement `.venv` comme noyau (kernel), puis exécuter les cellules dans l'ordre.
Attention, l'exécution du notebook complet prend plus d'une heure.

Le notebook télécharge lui-même ses données avec AWS CLI (installé par `requirements.txt`) :

- `decouverte_prototype/data/raw/` : `README.md` et `stages.csv` du jeu de données ;
- `decouverte_prototype/data/prototype/images/`, `masks/`, `annotations/` : les 9 lames du prototype avec leurs masques et annotations.

## Version finale

Les commandes se lancent dans un terminal depuis le dossier `version_finale`, et les notebooks s'y placent eux-mêmes (les chemins sont donc les mêmes partout). Les lames sont lues directement sur AWS, sans les télécharger : seuls les annotations XML et `stages.csv` sont téléchargés dans `version_finale/data/CAMELYON17/`.

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
6. **Notebook `02_modelisation_evaluation`, partie 6** (lames de validation) : choix du seuil de la carte et de la taille
   minimale des lésions, Grad-CAM des fausses alertes, puis les réglages sont figés dans `resultats/reglages_figes.json`.
7. **Notebook `02_modelisation_evaluation`, parties 7 et 8** : test (une seule fois, avec les réglages figés) et analyse
   des erreurs, de la patiente aux patchs (Grad-CAM).

Fichiers produits dans `version_finale` :

| Fichier | Produit par | Contenu |
|---|---|---|
| `data/CAMELYON17/selection_lames.csv` | notebook 01, partie 2 | lames choisies et leur set (entraînement, validation, test) |
| `patches/<variante>/niveau_<n>/` | `extract_patches.py` | patchs PNG d'entraînement et de validation, `patches.csv`, aperçus des lames |
| `resultats/caracteristiques/<variante>_niveau_<n>.npz` | notebook 02, partie 2 | 512 caractéristiques ResNet18 de chaque patch découpé |
| `resultats/classifieur_final.joblib` | notebook 02, partie 4 | modèle de patch final (StandardScaler + régression logistique) |
| `resultats/predictions_patchs_validation.csv` | notebook 02, partie 4 | probabilité de chaque patch de validation |
| `cartes/niveau_<n>/<lame>.npz` | `cartes_chaleur.py` | caractéristiques de chaque position de tissu d'une lame (validation et test) |
| `resultats/reglages_figes.json` | notebook 02, partie 6.4 | réglages figés avant le test |
| `resultats/test_lames.csv`, `test_patientes.csv` | notebook 02, partie 7 | résultats du test par lame et par patiente |
| `resultats/domain_shift_un_centre_de_cote.csv` | analyse `domain_shift` | AUC par centre, centre vu ou jamais vu |

Les lames de test ne sont pas découpées en PNG : elles ne passent que par les cartes de chaleur.

## Analyses complémentaires (domain shift)

Les 5 hôpitaux de CAMELYON17 n'ont ni les mêmes scanners ni exactement la même coloration.

- **`analyses/domain_shift/analyse_domain_shift.ipynb`** : pour chaque centre, l'AUC de ses patchs de validation avec le modèle
  entraîné sur les 5 centres (centre vu) et sur les 4 autres seulement (centre jamais vu). Ne recalcule rien de long, mais
  demande d'avoir lancé le découpage de la variante `retenue` et les parties 2 et 6.4 du notebook 02. Résultat : l'AUC ne
  baisse presque pas (écart moyen +0,005) ; le centre 1 est difficile qu'il soit vu ou non.
- **`analyses/multicentres/multicentres.ipynb`** : sur les patchs du prototype (centres 0 et 4), comparaison des couleurs
  d'origine et des normalisations Reinhard et Macenko, à rappel égal (95 %). Pas de gain d'AUC et plus de fausses alertes :
  les couleurs d'origine sont gardées. La méthode est ensuite testée sur le centre 2, jamais vu. Le notebook relit
  `predictions.csv` (seul pandas est nécessaire, voir son `README.md`) ; le code de calcul d'origine est conservé dans
  l'historique Git (commit `3c864eb`).

## Données

Les données viennent du jeu de données public CAMELYON17, hébergé sur AWS S3 et accessible sans compte. Elles ne sont pas
dans le dépôt. Pour vérifier l'accès :

```bash
aws s3 ls --no-sign-request s3://camelyon-dataset/CAMELYON17/
```
