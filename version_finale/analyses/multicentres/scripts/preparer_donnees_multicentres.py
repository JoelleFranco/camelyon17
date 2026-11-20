"""Inventaire et téléchargement d'une cohorte exploratoire CAMELYON17.
Depuis la racine du projet : python 03_preparer_donnees_multicentres.py
Ajouter --telecharger pour récupérer entraînement et validation.
Le centre 2 reste réservé au test ; --inclure-test permet de le récupérer plus tard.
Contrôle de taille uniquement, pas de vérification cryptographique.
"""
import argparse
import csv
import shutil
import time
from pathlib import Path

SELECTION = {
    'train': ['patient_083_node_4','patient_089_node_3','patient_096_node_0',
              'patient_005_node_0','patient_012_node_0','patient_010_node_4'],
    'validation': ['patient_092_node_1','patient_086_node_2',
                   'patient_015_node_1','patient_000_node_4'],
    'test': ['patient_044_node_4','patient_046_node_4',
             'patient_055_node_0','patient_059_node_4'],
}
GIO = 1024**3

def selectionner(inventaire):
    index = {r['lame']: r for r in inventaire}
    lignes, patients = [], {}
    for ensemble, noms in SELECTION.items():
        for nom in noms:
            r = dict(index[nom])
            patient = nom.split('_node_')[0]
            if patient in patients and patients[patient] != ensemble:
                raise ValueError('Patient dans plusieurs ensembles : '+patient)
            patients[patient] = ensemble
            if r['masque'].lower() != 'true':
                raise ValueError('Masque absent : '+nom)
            if r['classe'] != 'negative' and r['annotation_xml'].lower() != 'true':
                raise ValueError('Annotation absente : '+nom)
            if (ensemble == 'test') != (int(r['centre']) == 2):
                raise ValueError('Centre 2 non exclusif au test')
            r['ensemble'] = ensemble
            lignes.append(r)
    return lignes

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--telecharger', action='store_true')
    p.add_argument('--inclure-test', action='store_true')
    a = p.parse_args()
    racine = Path.cwd()
    base = racine/'data'/'multi_centres'
    entree = base/'inventaire'/'inventaire_lames.csv'
    if not entree.exists():
        raise FileNotFoundError('Lancer depuis camelyon17-main ; inventaire manquant : '+str(entree))
    with entree.open(encoding='utf-8-sig', newline='') as f:
        lignes = selectionner(list(csv.DictReader(f)))
    sortie = base/'inventaire'/'selection_multicentres.csv'
    with sortie.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(lignes[0]));w.writeheader();w.writerows(lignes)
    print('Cohorte exploratoire : 14 lames, 14 identifiants patients.')
    for r in lignes:
        print(f"{r['ensemble']:10} centre {r['centre']} {r['lame']} {r['classe']:8} {float(r['taille_Gio']):.3f} Gio (image)")
    import boto3
    from botocore import UNSIGNED
    from botocore.config import Config
    from boto3.s3.transfer import TransferConfig
    s3=boto3.client('s3',region_name='us-west-2',config=Config(signature_version=UNSIGNED))
    fichiers=[]
    print('\nVerification des tailles distantes (images, masques, XML)...',flush=True)
    for r in lignes:
        if r['ensemble']=='test' and not a.inclure_test:
            continue
        nom=r['lame']
        objets=[('images',nom+'.tif'),('masks',nom+'_mask.tif')]
        if r['annotation_xml'].lower()=='true':objets.append(('annotations',nom+'.xml'))
        for dossier,nom_f in objets:
            cle=f'CAMELYON17/{dossier}/{nom_f}'
            taille=s3.head_object(Bucket='camelyon-dataset',Key=cle)['ContentLength']
            dest=base/'raw'/dossier/nom_f
            if dest.exists() and dest.stat().st_size != taille:
                raise RuntimeError('Fichier existant de taille incorrecte ; verifier avant de continuer : '+str(dest))
            fichiers.append((cle,taille,dest))
    restant=sum(t for _,t,d in fichiers if not d.exists())
    libre=shutil.disk_usage(base).free
    print(f'Volume total selection active : {sum(t for _,t,_ in fichiers)/GIO:.2f} Gio')
    print(f'A telecharger : {restant/GIO:.2f} Gio ; libre : {libre/GIO:.2f} Gio')
    print('Marge conservee : 20 Gio pour le systeme et les traitements.')
    print('Selection enregistree :',sortie)
    if libre < restant+20*GIO:
        raise RuntimeError('Espace insuffisant avec la marge de 20 Gio. Aucun telechargement lance.')
    if not a.telecharger:
        print('\nBilan termine. Aucune lame telechargee. Ajouter --telecharger pour lancer.')
        return
    config=TransferConfig(max_concurrency=2)
    journal=base/'inventaire'/'journal_telechargements.csv'
    for i,(cle,taille,dest) in enumerate(fichiers,1):
        if dest.exists():
            print(f'[{i}/{len(fichiers)}] Deja present : {dest.name}',flush=True)
            continue
        dest.parent.mkdir(parents=True,exist_ok=True)
        temporaire=dest.with_name(dest.name+'.part')
        print(f'[{i}/{len(fichiers)}] {dest.name} ({taille/GIO:.2f} Gio)',flush=True)
        debut=time.monotonic()
        try:
            s3.download_file('camelyon-dataset',cle,str(temporaire),Config=config)
            if temporaire.stat().st_size!=taille:raise RuntimeError('Taille incorrecte : '+cle)
            temporaire.replace(dest)
        except BaseException:
            temporaire.unlink(missing_ok=True)
            raise
        existe=journal.exists()
        with journal.open('a',encoding='utf-8',newline='') as f:
            w=csv.writer(f)
            if not existe:w.writerow(['fichier','octets','secondes'])
            w.writerow([cle,taille,round(time.monotonic()-debut,2)])
        print('  Termine.',flush=True)
    print('\nTelechargement termine. Les fichiers termines seront conserves en cas de relance.')
    if not a.inclure_test:print('Le centre 2 reste reserve : aucune image de test telechargee.')

if __name__=='__main__':
    main()
