# Ce fichier contient les fonctions pour récupérer les identifiants des départements de France
# Si on execute directement ce fichier, on récupère les identifiants de tous les départements de France
# et on enregistre le résultat dans un fichier CSV
# Si on importe ce fichier dans un autre fichier, 
# on peut récupérer les identifiants d'un département en particulier en appelant la fonction get_id_dep(dep_name) avec le nom du département en paramètre
# on peut aussi récupérer tous les départements avec leurs identifiants en appelant la fonction get_departements() 
import requests
import pandas as pd
from config import headers, cookies, payload_search_id_dep, departements, DEPARTEMENTS_DIR

def get_id_dep(dep_name = 'paris'):
    try:
        url = "https://www.seloger.com/search-mfe-bff/autocomplete"
        payload = payload_search_id_dep
        payload['text'] = dep_name

        result = requests.post(url = url, headers = headers, json = payload_search_id_dep, cookies = cookies)
        
        print('\n', dep_name, '| code réponse |', result)
        return result.json()[0]['id']

    except Exception:
        print('Erreur Récupération id dep:', dep_name)
        return ''

def get_departements():
    for dep in departements:
    ## Récupération des identifiants de chaque departement
        dep['id'] = get_id_dep(dep['nom'])
        print(dep)
    return departements

def execution():
    departements = get_departements()
        
    dep_df = pd.DataFrame(departements)

    # Enregistrement du fichier CSV
    output_path = 'seloger_departements_id.csv'
    dep_df.to_csv(output_path, index=False)
    print(f'Fichier CSV enregistré dans : {output_path}')

if __name__ == '__main__':
    get_departements()