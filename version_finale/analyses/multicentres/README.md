# Comparaison multicentres CAMELYON17

**Ouvrir le [notebook de synthèse](notebooks/03_multicentres.ipynb).** Cette contribution compare les images originales, Reinhard et Macenko, puis présente le test de la méthode retenue sur un autre établissement. La validation utilise les centres 0 et 4 ; le test utilise le centre 2.

**Pour consulter et recalculer les métriques : aucun téléchargement de lame ni de modèle.** Le notebook principal ne fait que lire et vérifier les CSV inclus. Il peut être exécuté de haut en bas après installation des dépendances de lecture.

## Organisation et provenance

- `notebooks/` : lecture des résultats déjà obtenus ; aucune nouvelle inférence.
- `notebooks/reproduction/` : code complet commenté pour recalculer avec les données locales.
- `resultats/` : CSV et JSON historiques conservés pour vérifier les chiffres.
- `scripts/` : contrôles ou préparation associés à cette tâche.

Origine : prototype, expériences complémentaires exécutées par Élodie et archive de travail du 16 novembre 2026. Mise en forme, commentaires et contrôles complémentaires préparés avec l’aide de ChatGPT ; la relecture, la compréhension et la validation de la chaîne finale relèvent du groupe. Cette expérience utilise les patchs du prototype. La version finale du projet possède son propre découpage.

Sources des outils : CAMELYON17 (https://camelyon17.grand-challenge.org/), PyTorch/Torchvision (https://pytorch.org/), scikit-learn (https://scikit-learn.org/). Les fichiers `configuration.json` et `environnement.json`, lorsqu’ils sont présents, précisent les versions historiques. Les listes requirements sont fonctionnelles, non verrouillées : une installation neuve identique sur tous les systèmes n’est pas garantie.

## Installation pour lire et vérifier

Depuis la racine du dépôt, dans un terminal PowerShell Windows, avec Python installé :

```powershell
python -m venv .venv
& ".\.venv\Scripts\python.exe" -m pip install -r "analyses/multicentres/requirements-lecture.txt"
```

Si `.venv` existe déjà, garder cet environnement ou choisir un autre nom ; ne pas le recréer pour rien. Dans VS Code, ouvrir le notebook, cliquer sur le choix du noyau en haut à droite et sélectionner `.venv`.

Les deux illustrations sont intégrées directement au notebook de synthèse. Les commandes Python servent à exécuter les cellules et les contrôles. Un noyau neuf signifie « Redémarrer le noyau » avant d’exécuter les cellules dans l’ordre ; cela évite les variables laissées par une ancienne exécution.

Pour vérifier les tableaux indépendamment :

```powershell
& ".\.venv\Scripts\python.exe" .\analyses\multicentres\scripts\verifier_resultats.py
```

## Recalculer l’expérience depuis les lames

Ce parcours est facultatif pour relire la contribution, mais nécessaire pour valider une reproduction complète. Installer :

```powershell
& ".\.venv\Scripts\python.exe" -m pip install -r .\analyses\multicentres\requirements-calcul.txt
& ".\.venv\Scripts\python.exe" -c "import openslide, torch, torchstain; print('Imports OK')"
```

Depuis la racine du dépôt, initialiser les inventaires seulement s’ils sont absents :

```powershell
New-Item -ItemType Directory -Force .\data\multi_centres\inventaire | Out-Null
foreach ($nom in @('inventaire_lames.csv', 'selection_multicentres.csv')) {
    $destination = Join-Path '.\data\multi_centres\inventaire' $nom
    if (-not (Test-Path $destination)) {
        Copy-Item (Join-Path '.\analyses\multicentres\resultats\inventaire' $nom) $destination
    }
}
```

Afficher le volume et vérifier les objets distants, sans télécharger :

```powershell
& ".\.venv\Scripts\python.exe" .\analyses\multicentres\scripts\preparer_donnees_multicentres.py
```

Télécharger le développement, puis les lames de test pour reproduire aussi ce résultat historique :

```powershell
& ".\.venv\Scripts\python.exe" .\analyses\multicentres\scripts\preparer_donnees_multicentres.py --telecharger
& ".\.venv\Scripts\python.exe" .\analyses\multicentres\scripts\preparer_donnees_multicentres.py --telecharger --inclure-test
```

Les volumes observés étaient 12,81 Gio pour le développement et 18,59 Gio au total, masques et annotations compris. Prévoir aussi de la place pour les patchs et calculs. Le script conserve 20 Gio de marge ; la reprise vérifie la taille des fichiers, pas leur empreinte cryptographique. Le téléchargement dépend de l’accès au stockage public d’origine. Les TIFF sont placés dans `data/multi_centres/raw/images/` et les masques dans `raw/masks/` ; ils ne sont jamais à ajouter à Git.

Élodie possède déjà les 14 lames et leurs masques : elle peut utiliser son dossier initial. Un clone distinct doit avoir accès à ces mêmes sous-dossiers ; copier les données une fois ou lancer les calculs dans le dépôt qui les contient. Il n’est pas nécessaire de retélécharger des fichiers déjà présents au bon emplacement.

## Ordre de calcul

1. Ouvrir `notebooks/reproduction/03_multicentres_calcul.ipynb` depuis le dépôt ; sélectionner le bon noyau et le redémarrer.
2. Passer `EXECUTER_CALCULS` à `True`. Exécuter les imports, la configuration, les contrôles, l’extraction, la normalisation et l’entraînement jusqu’à la comparaison de validation.
3. Examiner les contrôles et les tableaux. Conserver les méthodes qui détectent au moins 95 % des patchs tumoraux dans chacun des deux centres de validation. Parmi elles, retenir la meilleure spécificité moyenne par centre (proportion de patchs sains correctement classés), puis la meilleure AUC moyenne en cas d’égalité. Passer `FIGER_CHOIX` à `True` et exécuter cette cellule pour enregistrer le choix.
4. Passer `EXECUTER_TEST` à `True`, puis exécuter le test et l’analyse suivante. Ne pas modifier les réglages en fonction du résultat.

Les nouvelles sorties sont dans `data/reproductions_multicentres/<configuration>_<date>/`. Elles n’écrasent pas l’expérience publiée. Ne pas réexécuter la cellule de configuration au milieu d’une reprise : elle crée une autre session. Le dossier imprimé par cette cellule est celui à conserver et à comparer aux résultats historiques.

Le réseau ImageNet reste fixe ; le notebook réentraîne les régressions. Les patchs sont relus et normalisés par lots, mais les temps et la mémoire dépendent du matériel. Les durées du rapport ne sont pas une promesse de durée totale.

## Validation et limites

Le notebook de synthèse et les vérifications de CSV sont exécutables sans données lourdes et ont été testés. Le notebook de calcul a été contrôlé syntaxiquement ; l’extraction et le CNN avec les nouveaux chemins n’ont pas été réexécutés dans l’audit. Une exécution locale depuis un noyau neuf est encore requise avant de déclarer la reproduction de bout en bout validée.

Le texte de l’analyse de la micrométastase décrit l’expérience historique. Une nouvelle exécution peut donner d’autres chiffres ; mettre à jour la discussion à partir de ses propres exports. Le test du centre 2 a déjà été consulté ; cette reproduction ne constitue pas une nouvelle évaluation indépendante. Cette expérience est au niveau patch et ne calcule pas un pN complet.

Outils supplémentaires : OpenSlide (https://openslide.org/), torchstain (https://github.com/EIDOSLAB/torchstain). Les deux normalisations sont fournies par torchstain et ne sont pas réimplémentées dans le projet.
