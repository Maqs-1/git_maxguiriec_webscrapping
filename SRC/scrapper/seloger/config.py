### VARIABLES
from pathlib import Path

# Chemin vers le répertoire des départements
DEPARTEMENTS_DIR = Path(__file__).parent.parent.parent / 'departements'

# Entête des requêtes
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Content-Type": "application/json; charset=utf-8",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Priority": "u=0"
}

## Entête des requêtes
#  En cas de blocage de la part du site (captcha, expiration du cookie ...),
#  il faudrais consulter le site sur un naviguateur,
#  récuperer les cookies, et les transformer en dictionaire python où lesc clés et les valeurs sont des strings
#  et remplacer la valeur de la variable cookies ci dessous
cookies = {
    "g_state": "{\"i_l\":0,\"i_ll\":1764616694696,\"i_b\":\"duj/1fjxo92C5gOORXsQ8Oj8fF7dF/lX7LfTbRSBPTc\"}",
    "_dd_s": "aid=b7f2c70e-6bd9-44a1-acd8-2e9ed9bd2990&logs=0&expire=1764617666120"
}

## Payload de la requêtes de récupération des id d'annonces
annonces_filters = {
    "criteria": {
        "distributionTypes": [
            "Buy",
            "Buy_Auction",
            "Compulsory_Auction"
        ],
        "estateTypes": [
            "House",
            "Apartment"
        ],
        "location": {
            "placeIds": [
                "AD08FR31096" # Mettre ici l'identifiant du lieu
            ]
        },
        "projectTypes": [
            "Life_Annuity",
            "New_Build",
            "Projected",
            "Resale"
        ]
    },
    "paging": {
        "order": "Default",
        "page": 1, # Mettre ici lenumero de la page voulu
        "size": 30 # Mettre ici le nombre d'elements(annonces) voulu dans la page
    }
}

## Payload de la requêtes d'autocompletion du nom des lieux
payload_search_id_dep = {
    "limit": 10,
    "locale": "fr",
    "parentTypes": [
        "NBH1",
        "NBH3",
        "AD09",
        "NBH2",
        "AD08",
        "AD06",
        "AD04",
        "POCO",
        "AD02"
    ],
    "placeTypes": [
        "NBH1",
        "NBH3",
        "AD09",
        "NBH2",
        "AD08",
        "AD06",
        "AD04",
        "POCO",
        "AD02"
    ],
    "text": "Bouches-du-Rhône" # mettre ici le nom du departement, de la ville ...
}

## Departements de France
departements = [
    {'numero': '59', 'nom': 'Nord'},
    {'numero': '75', 'nom': 'Paris'},
    {'numero': '13', 'nom': 'Bouches-du-Rhône'},
    {'numero': '69', 'nom': 'Rhône'},
    {'numero': '93', 'nom': 'Seine-Saint-Denis'},
    {'numero': '33', 'nom': 'Gironde'},
    {'numero': '92', 'nom': 'Hauts-de-Seine'},
    {'numero': '44', 'nom': 'Loire-Atlantique'},
    {'numero': '78', 'nom': 'Yvelines'},
    {'numero': '62', 'nom': 'Pas-de-Calais'},
    {'numero': '31', 'nom': 'Haute-Garonne'},
    {'numero': '77', 'nom': 'Seine-et-Marne'},
    {'numero': '94', 'nom': 'Val-de-Marne'},
    {'numero': '91', 'nom': 'Essonne'},
    {'numero': '38', 'nom': 'Isère'},
    {'numero': '95', 'nom': 'Val-d\'Oise'},
    {'numero': '76', 'nom': 'Seine-Maritime'},
    {'numero': '34', 'nom': 'Hérault'},
    {'numero': '67', 'nom': 'Bas-Rhin'},
    {'numero': '06', 'nom': 'Alpes-Maritimes'},
    {'numero': '83', 'nom': 'Var'},
    {'numero': '35', 'nom': 'Ille-et-Vilaine'},
    {'numero': '68', 'nom': 'Haut-Rhin'},
    {'numero': '57', 'nom': 'Moselle'},
    {'numero': '974', 'nom': 'La Réunion'},
    {'numero': '42', 'nom': 'Loire'},
    {'numero': '85', 'nom': 'Vendée'},
    {'numero': '60', 'nom': 'Oise'},
    {'numero': '14', 'nom': 'Calvados'},
    {'numero': '54', 'nom': 'Meurthe-et-Moselle'},
    {'numero': '30', 'nom': 'Gard'},
    {'numero': '74', 'nom': 'Haute-Savoie'},
    {'numero': '29', 'nom': 'Finistère'},
    {'numero': '63', 'nom': 'Puy-de-Dôme'},
    {'numero': '84', 'nom': 'Vaucluse'},
    {'numero': '49', 'nom': 'Maine-et-Loire'},
    {'numero': '64', 'nom': 'Pyrénées-Atlantiques'},
    {'numero': '45', 'nom': 'Loiret'},
    {'numero': '56', 'nom': 'Morbihan'},
    {'numero': '86', 'nom': 'Vienne'},
    {'numero': '37', 'nom': 'Indre-et-Loire'},
    {'numero': '22', 'nom': 'Côtes-d\'Armor'},
    {'numero': '81', 'nom': 'Tarn'},
    {'numero': '26', 'nom': 'Drôme'},
    {'numero': '27', 'nom': 'Eure'},
    {'numero': '40', 'nom': 'Landes'},
    {'numero': '80', 'nom': 'Somme'},
    {'numero': '17', 'nom': 'Charente-Maritime'},
    {'numero': '50', 'nom': 'Manche'},
    {'numero': '51', 'nom': 'Marne'},
    {'numero': '25', 'nom': 'Doubs'},
    {'numero': '73', 'nom': 'Savoie'},
    {'numero': '16', 'nom': 'Charente'},
    {'numero': '11', 'nom': 'Aude'},
    {'numero': '21', 'nom': 'Côte-d\'Or'},
    {'numero': '72', 'nom': 'Sarthe'},
    {'numero': '39', 'nom': 'Jura'},
    {'numero': '24', 'nom': 'Dordogne'},
    {'numero': '41', 'nom': 'Loir-et-Cher'},
    {'numero': '88', 'nom': 'Vosges'},
    {'numero': '47', 'nom': 'Lot-et-Garonne'},
    {'numero': '972', 'nom': 'Martinique'},
    {'numero': '971', 'nom': 'Guadeloupe'},
    {'numero': '01', 'nom': 'Ain'},
    {'numero': '28', 'nom': 'Eure-et-Loir'},
    {'numero': '89', 'nom': 'Yonne'},
    {'numero': '07', 'nom': 'Ardèche'},
    {'numero': '71', 'nom': 'Saône-et-Loire'},
    {'numero': '58', 'nom': 'Nièvre'},
    {'numero': '08', 'nom': 'Ardennes'},
    {'numero': '18', 'nom': 'Cher'},
    {'numero': '36', 'nom': 'Indre'},
    {'numero': '87', 'nom': 'Haute-Vienne'},
    {'numero': '61', 'nom': 'Orne'},
    {'numero': '03', 'nom': 'Allier'},
    {'numero': '46', 'nom': 'Lot'},
    {'numero': '10', 'nom': 'Aube'},
    {'numero': '53', 'nom': 'Mayenne'},
    {'numero': '82', 'nom': 'Tarn-et-Garonne'},
    {'numero': '55', 'nom': 'Meuse'},
    {'numero': '65', 'nom': 'Hautes-Pyrénées'},
    {'numero': '04', 'nom': 'Alpes-de-Haute-Provence'},
    {'numero': '90', 'nom': 'Territoire de Belfort'},
    {'numero': '43', 'nom': 'Haute-Loire'},
    {'numero': '19', 'nom': 'Corrèze'},
    {'numero': '66', 'nom': 'Pyrénées-Orientales'},
    {'numero': '32', 'nom': 'Gers'},
    {'numero': '70', 'nom': 'Haute-Saône'},
    {'numero': '09', 'nom': 'Ariège'},
    {'numero': '973', 'nom': 'Guyane'},
    {'numero': '12', 'nom': 'Aveyron'},
    {'numero': '976', 'nom': 'Mayotte'},
    {'numero': '2A', 'nom': 'Corse-du-Sud'},
    {'numero': '2B', 'nom': 'Haute-Corse'},
    {'numero': '23', 'nom': 'Creuse'},
    {'numero': '52', 'nom': 'Haute-Marne'},
    {'numero': '15', 'nom': 'Cantal'},
    {'numero': '05', 'nom': 'Hautes-Alpes'},
    {'numero': '48', 'nom': 'Lozère'}
]
