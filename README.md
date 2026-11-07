# Détection de métastases du cancer du sein (CAMELYON17)

## Installation

### Prérequis

- Python 3.13
- Git
- Environ 8 Go d'espace disque pour les lames du prototype (téléchargées par le notebook, voir plus bas)
- Le projet a été développé sous Windows 11 avec une carte graphique Intel Arc (PyTorch version XPU). Sans carte Intel, voir la remarque sur PyTorch plus bas.

### 1. Récupérer le projet

```bash
git clone https://github.com/JoelleFranco/camelyon17.git
cd projet-camelyon17
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

### 4. Ouvrir le notebook

Le notebook est `notebooks/01_decouverte_et_prototype.ipynb`. Dans VS Code (avec les extensions Python et Jupyter) ou dans Jupyter, choisir l'environnement `.venv` comme noyau (kernel), puis exécuter les cellules dans l'ordre.

Attention, l'exécution du notebook complet prend plus d'une heure.

### Données

Les données ne sont pas dans le dépôt (dossier `data/`, ignoré par Git). Elles viennent du jeu de données public CAMELYON17, hébergé sur AWS S3, accessible sans compte. Le notebook les télécharge lui-même avec AWS CLI (installé par `requirements.txt`) :

- `data/raw/` : `README.md` et `stages.csv` du jeu de données
- `data/prototype/images/`, `masks/`, `annotations/` : les 9 lames du prototype avec leurs masques et annotations.

Pour vérifier l'accès aux données :

```bash
aws s3 ls --no-sign-request s3://camelyon-dataset/CAMELYON17/
```
