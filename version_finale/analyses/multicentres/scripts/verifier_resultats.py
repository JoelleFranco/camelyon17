"""Vérifie les résultats enregistrés sans images, sans modèle et sans réseau."""
from pathlib import Path
import json
import hashlib
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, roc_auc_score


def mesures(df, seuil):
    vn, fp, fn, vp = confusion_matrix(df.y_vrai, df.score >= seuil, labels=[0, 1]).ravel()
    return dict(n=len(df), VP=vp, VN=vn, FP=fp, FN=fn,
                rappel=vp/(vp+fn) if vp+fn else np.nan,
                precision=vp/(vp+fp) if vp+fp else np.nan,
                specificite=vn/(vn+fp) if vn+fp else np.nan,
                auc=roc_auc_score(df.y_vrai, df.score) if df.y_vrai.nunique()==2 else np.nan)


def comparer(attendu, calcule):
    for cle, valeur in calcule.items():
        if not np.isclose(float(attendu[cle]), float(valeur), atol=1e-8, rtol=1e-7, equal_nan=True):
            raise ValueError(f'Métrique incohérente : {cle}, export={attendu[cle]}, recalcul={valeur}')


def verifier(racine=None):
    racine = Path(racine) if racine else Path(__file__).resolve().parents[1]
    exp = racine / 'resultats/multicentres'
    controles = []
    def ok(nom): controles.append((nom, 'OK'))
    choix = json.loads((exp/'choix_final.json').read_text())
    config = json.loads((exp/'configuration.json').read_text())
    assert hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()[:12] == choix['configuration']
    ok('Identifiant de configuration')
    selection = pd.read_csv(exp/'selection.csv')
    dev = pd.read_csv(exp/'patchs_developpement.csv')
    test = pd.read_csv(exp/'predictions_test.csv')
    allpatch = pd.concat([dev, test], ignore_index=True)
    assert len(selection)==14 and selection.patiente.nunique()==14
    assert selection.groupby('patiente').ensemble.nunique().max()==1
    assert allpatch.groupby('patiente').ensemble.nunique().max()==1
    assert set(selection.loc[selection.ensemble=='test','centre'])=={2}
    assert set(selection.loc[selection.ensemble!='test','centre'])=={0,4}
    assert set(allpatch.lame)==set(selection.lame)
    for r in selection.itertuples():
        g=allpatch[allpatch.lame==r.lame]
        assert set(g.ensemble)=={r.ensemble} and set(g.centre)=={r.centre} and set(g.patiente)=={r.patiente}
    assert not allpatch.duplicated(['lame','x','y']).any()
    assert allpatch.groupby('ensemble').size().to_dict()=={'test':864,'train':1325,'validation':1000}
    ok('Cohorte, effectifs, partitions et absence de coordonnées dupliquées')
    valref=dev[dev.ensemble=='validation']
    ident=['lame','x','y','y_vrai','centre','patiente','ensemble']
    def ids(df):return df[ident].sort_values(['lame','x','y']).reset_index(drop=True)
    ref=ids(valref)
    tab=pd.read_csv(exp/'metriques_validation_par_centre_recalibre.csv')
    comp=pd.read_csv(exp/'comparaison_methodes_recalibre.csv').set_index('methode')
    recherche=pd.read_csv(exp/'recherche_C.csv')
    for methode in ['original','reinhard','macenko']:
        pred=pd.read_csv(exp/f'predictions_validation_{methode}_recalibre.csv')
        initial=pd.read_csv(exp/f'predictions_validation_{methode}.csv')
        pd.testing.assert_frame_equal(ref,ids(pred))
        pd.testing.assert_frame_equal(ids(initial),ids(pred))
        a=initial.sort_values(['lame','x','y']).score.to_numpy()
        b=pred.sort_values(['lame','x','y']).score.to_numpy()
        assert np.allclose(a,b,atol=1e-10,rtol=0)
        assert np.isfinite(pred.score).all() and pred.score.between(0,1).all()
        seuil=float(comp.loc[methode,'seuil'])
        seuils=[];locaux=[]
        for centre,g in pred.groupby('centre'):
            pos=np.sort(g.loc[g.y_vrai==1,'score'].to_numpy())
            seuils.append(pos[len(pos)-int(np.ceil(.95*len(pos)))])
            met=mesures(g,seuil);locaux.append(met)
            comparer(tab[(tab.methode==methode)&(tab.centre==centre)].iloc[0],met)
            assert met['rappel']>=.95
        assert np.isclose(seuil,min(seuils),atol=1e-10,rtol=0)
        assert (pred.prediction.to_numpy()==(pred.score.to_numpy()>=seuil)).all()
        comparer(comp.loc[methode],dict(FP=sum(m['FP'] for m in locaux),FN=sum(m['FN'] for m in locaux)))
        assert np.isclose(comp.loc[methode,'specificite_moyenne'],np.mean([m['specificite'] for m in locaux]))
        assert np.isclose(comp.loc[methode,'auc_moyenne'],np.mean([m['auc'] for m in locaux]))
        meilleur=recherche[recherche.methode==methode].sort_values('auc_moyenne',ascending=False,kind='stable').iloc[0]
        assert float(meilleur.C)==float(comp.loc[methode,'C'])
        temps=pd.read_csv(exp/f'temps_developpement_{methode}.csv')
        assert temps.n.sum()==len(dev)
        assert np.isclose(comp.loc[methode,'temps_mesure_s'],temps.normalisation_s.sum()+temps.cnn_s.sum())
        ok(f'{methode} : mêmes exemples, scores, C, seuil, métriques et temps')
    gagnant=comp[comp.rappel_min>=.95].sort_values(['specificite_moyenne','auc_moyenne'],ascending=False).index[0]
    assert gagnant==choix['methode']=='original'
    assert np.isclose(choix['seuil'],comp.loc[gagnant,'seuil'],atol=1e-10,rtol=0)
    assert choix['C']==comp.loc[gagnant,'C']
    ok('Choix final conforme à la règle de validation')
    assert np.isfinite(test.score).all() and test.score.between(0,1).all()
    assert (test.prediction.to_numpy()==(test.score.to_numpy()>=choix['seuil'])).all()
    comparer(pd.read_csv(exp/'metriques_test.csv').iloc[0],mesures(test,choix['seuil']))
    par_lame=pd.read_csv(exp/'metriques_test_par_lame.csv').set_index('lame')
    for lame,g in test.groupby('lame'):comparer(par_lame.loc[lame],mesures(g,choix['seuil']))
    ok('Métriques du test globales et par lame')
    return controles

if __name__=='__main__':
    for nom,statut in verifier():print(f'{statut} — {nom}')
    print('Contrôle des tableaux terminé. Les images et poids ne sont pas inclus : aucune nouvelle inférence réalisée.')
