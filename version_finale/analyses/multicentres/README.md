# Comparaison multicentre des colorations — CAMELYON17

Cette étude du prototype compare les couleurs originales aux normalisations Reinhard et Macenko sur les mêmes patchs des centres 0 et 4. La méthode retenue est ensuite évaluée sur le centre 2.

## Utilisation

1. Garder [multicentres.ipynb](multicentres.ipynb) et [predictions.csv](predictions.csv) dans ce dossier.
2. Ouvrir le notebook dans VS Code et sélectionner un noyau Python avec pandas. Les résultats enregistrés sont visibles à l’ouverture.
3. Cliquer sur **Tout exécuter** pour recalculer les tableaux à partir du CSV. Si nécessaire, installer les dépendances dans l’environnement choisi avec `python -m pip install pandas ipykernel`.

Chaque ligne du CSV correspond à la prédiction d’une méthode sur un patch. Le notebook compare les prédictions aux annotations et présente les résultats par établissement et par lame. Les illustrations sont intégrées au notebook.

Le [code de reproduction de l’expérience initiale](https://github.com/JoelleFranco/camelyon17/tree/3c864eb/version_finale/analyses/multicentres) est conservé dans l’historique du projet.
