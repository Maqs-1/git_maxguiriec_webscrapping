# Ce fichier contient les fonctions pour récupérer les annonces des départements de France
# Si on execute directement ce fichier, on récupère les annonces de tous les départements de France
# et on enregistre le résultat dans un fichier CSV dans le dossier DEPARTEMENTS_DIR
# En cas de blocage de la part du site (captcha, expiration du cookie ...),
# il faudrais consulter le site sur un naviguateur,
# récuperer les cookies, et les transformer en dictionaire python où lesc clés et les valeurs sont des strings
# et remplacer la valeur de la variable cookies dans le fichier config.py
import requests
import pandas as pd
import random
import copy
from time import sleep
from config import headers, cookies, annonces_filters, DEPARTEMENTS_DIR
from scrapper_seloger_departements import get_departements

# Cette fonction permet de récupérer les identifiants des annonces d'un lieu donné
# placeId: identifiant du lieu
# page: numéro de la page
# return: liste des identifiants des annonces
def get_annonces_id(placeId, page):
    # Copie profonde pour éviter de modifier le dictionnaire original
    filters = copy.deepcopy(annonces_filters)
    filters['criteria']['location']['placeIds'] = [placeId]
    filters['paging']['page'] = page
    
    try: 
        result = requests.post("https://www.seloger.com/serp-bff/search", headers=headers, cookies=cookies, json=filters)
        print('placeId:', placeId, '| page:', page, '\ncode réponse:', result.status_code)
        
        # Vérification du statut HTTP
        if result.status_code != 200:
            print(f"Erreur HTTP {result.status_code}")
            return []
        
        result_json = result.json()
        
        # Vérification de l'existence de la clé 'classifieds'
        if 'classifieds' not in result_json:
            print(f"Clé 'classifieds' absente dans la réponse")
            return []
        
        return [elt['id'] for elt in result_json['classifieds'] if 'id' in elt]
    except Exception as e:
        print(f"\nErreur Récupération ids d'annonce: placeId {placeId}, page {page}")
        print(f"Type d'erreur: {type(e).__name__}")
        print(f"Message d'erreur: {str(e)} \n")
        return []
    
# Cette fonction permet de récupérer les informations des annonces d'un lieu donné
# placeIds: liste des identifiants des annonces
# return: liste des informations des annonces
def get_annonces(placeIds):
    # Vérification que placeIds n'est pas vide
    if not placeIds or len(placeIds) == 0:
        print("Erreur: placeIds est vide")
        return []
    
    # Vérification que tous les éléments sont des strings
    if not all(isinstance(pid, str) for pid in placeIds):
        print("Erreur: placeIds doit contenir uniquement des strings")
        return []
    
    baseUrl = "https://www.seloger.com/classifiedList/"
    url = baseUrl + ','.join(placeIds)    
    try:
        result = requests.get(url=url, headers=headers, cookies=cookies)
        
        # Vérification du statut HTTP
        if result.status_code != 200:
            print(f"Erreur HTTP {result.status_code}")
            return []
        
        result_json = result.json()
        
        # Vérification que result_json est une liste
        if not isinstance(result_json, list):
            print(f"Erreur: la réponse n'est pas une liste (type: {type(result_json)})")
            return []
        
        datas = []
        
        for elt in result_json:
            eltDict = {
                'id': elt.get('id', ''),
                'creationDate': elt.get('metadata', {}).get('creationDate', ''),
                'city': elt.get('location', {}).get('address', {}).get('city', ''),
                'district': elt.get('location', {}).get('address', {}).get('district', ''),
                'zipCode': elt.get('location', {}).get('address', {}).get('zipCode', 0),
                'distributionType': elt.get('rawData', {}).get('distributionType', ''),
                'propertyType': elt.get('rawData', {}).get('propertyType', ''),
                'price': elt.get('rawData', {}).get('price', 0), # Prix par défaut à 0 (chiffre)
                'surface': elt.get('rawData', {}).get('surface', {}).get('main', 0), # Surface par défaut à 0 (chiffre)
                'nbroom': elt.get('rawData', {}).get('nbroom', ''), 
                'nbbedroom': elt.get('rawData', {}).get('nbbedroom', ''), 
                'description': elt.get('mainDescription', {}).get('description', ''),
            }
            datas.append(eltDict)
            
        return datas
    except Exception as e:
        print(f"\nErreur Récupération des annonces: placeIds {placeIds}")
        print(f"Type d'erreur: {type(e).__name__}")
        print(f"Message d'erreur: {str(e)} \n")
        return []

def execution():
    # Étape 1: Récupération des identifiants de tout les département de France
    departements_file = 'seloger_departements_id.csv'
    departements_list = []
    
    try:
        df_departement = pd.read_csv(departements_file)
        departements_list = df_departement.to_dict('records')
    except FileNotFoundError:
        print(f'le fichier {departements_file} n\'est pas present', "\nRécupération depuis le site web...\n")
        departements_list = get_departements()
        if departements_list:
            df_departement = pd.DataFrame(departements_list)
            DEPARTEMENTS_DIR.mkdir(parents=True, exist_ok=True)
            df_departement.to_csv(departements_file, index=False)
    
    # Étape 2: Pour chaque département on
    # 2.1- on récupère les identifiants des annonces, 
    # 2.2- on extrait les informations utiles des annonces 
    # 2.3- on enregistre les informations extraites sous forme de csv
    for dep in departements_list:
        # Vérification de l'existence de dep['id']
        if 'id' not in dep or not dep['id']:
            print(f"Erreur: pas d'id pour le département {dep.get('nom', 'inconnu')}")
            continue
        
        has_more_pages = True
        total_departement_annonces = []
        page = 1
        print(f"RECUPERATION ANNONCES >>> {dep['nom']}")
        try:
            while has_more_pages:
                print(f"\n>>> {dep['nom']} | {page} <<<")
                placeIds = get_annonces_id(dep['id'], page)

                if len(placeIds) == 0:
                    has_more_pages = False
                    print(f"FIN DE LA RECUPERATION DES ANNONCES >>> {dep['nom']}")
                    break
                
                annonces = get_annonces(placeIds)
                
                # Vérification que annonces est bien une liste
                if annonces is None:
                    print(f"Erreur: get_annonces a retourné None pour le département {dep['nom']} à la page {page}")
                    page += 1
                    continue
                
                if len(annonces) == 0:
                    print(f"Aucune annonce trouvée pour le département {dep['nom']} à la page {page}")
                    page += 1
                    continue

                total_departement_annonces.extend(annonces)
                page += 1
                
                # Délai aléatoire entre 1 et 10 secondes pour éviter la surcharge du serveur et la detection de bot
                #delay = random.uniform(1, 10)
                #print(f"Pause de {delay:.2f} secondes...\n")
                #sleep(delay)
            
            print(f"FIN DE LA RECUPERATION DES ANNONCES >>> {dep['nom']}\nTOTAL DES ANNONCES: {len(total_departement_annonces)}")
        except Exception as e:
            print(f"Erreur lors de la récupération des annonces pour le département {dep['nom']} à la page {page}")
            print(f"Type d'erreur: {type(e).__name__}")
            print(f"Message d'erreur: {str(e)} \n")
            continue

        # Enregistrement des annonces dans un fichier CSV dans le dossier DEPARTEMENTS_DIR
        if len(total_departement_annonces) > 0:
            df_annonces = pd.DataFrame(total_departement_annonces)
            # Remplacement des caractères spéciaux dans le nom de fichier
            filename = f'seloger_dep_{dep["numero"]}_{dep['nom']}.csv'
            DEPARTEMENTS_DIR.mkdir(parents=True, exist_ok=True)
            df_annonces.to_csv(DEPARTEMENTS_DIR / filename, index=False)
            print(f"annonces enregistrées dans le fichier: {filename} \n")
if __name__ == '__main__':
    execution()