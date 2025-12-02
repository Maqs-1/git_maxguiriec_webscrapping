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
    "_gcl_au": "1.1.884435378.1764481045",
    "_ga": "GA1.1.1042987645.1764481050",
    "ry_ry-s3oa268o_realytics": "eyJpZCI6InJ5X0VBNzNCQkM3LUYxRkMtNDlGQy04NDgwLTlCNjgzQUIxREFFMiIsImNpZCI6bnVsbCwiZXhwIjoxNzk2MDE3MDUzMDg1LCJjcyI6bnVsbH0%3D",
    "_ta": "fr~1~1c27cd7cdaf3330364ddfd6a094df6ea",
    "_pin_unauth": "dWlkPU1UZzFZMkpoTkdRdFpXTmpOeTAwTXpJMkxUa3hZVFl0WldNMk0yTTBabVV3T0dFMw",
    "kameleoonVisitorCode": "r5n6kbqu7oylpjha",
    "__gsas": "ID=5b8fb91a0ec04096:T=1764481093:RT=1764481093:S=ALNI_MbkZXqSwad2rK3tTNGn09BSxp3kpg",
    "_fbp": "fb.1.1764481096192.63063741880698952",
    "_lr_env_src_ats": "false",
    "_lr_sampling_rate": "100",
    "_ga_MC53H9VE57": "GS2.1.s1764521991$o3$g1$t1764522004$j47$l0$h0",
    "page_viewed_buy": "3",
    "g_state": "{\"i_l\":0,\"i_ll\":1764522008482,\"i_b\":\"eG7bPUCWJY+fTvlXYGLqS1Lsy3s9Rapcg2L6AuODcXY\"}",
    "_tac": "false~google|not-available",
    "__rtbh.uid": "%7B%22eventType%22%3A%22uid%22%2C%22id%22%3A%22unknown%22%2C%22expiryDate%22%3A%222026-11-30T17%3A00%3A17.099Z%22%7D",
    "__rtbh.lid": "%7B%22eventType%22%3A%22lid%22%2C%22id%22%3A%22qV8rRFKUhRv76pKD0taB%22%2C%22expiryDate%22%3A%222026-11-30T17%3A00%3A17.100Z%22%7D",
    "cto_bundle": "wi9hvF9SaGF3JTJGYVM2UCUyQjdZekh0WTc0bEZ4aHc4bG04bFFMVjhJTXJkcWczcHhkUWk0S1NoeklieFNCNXRnSGFnNGpJT3g3RCUyQjNWVkwlMkZ2TXoyZk53aiUyRndUVkRPTXc5MDdweFZxTW5oSjFEdDhHZFp3WnRRS2lHWTNFVjBIMmsyZVliY3d3elB6aWF3d3pDJTJCN0NCQWxlOVNWTlElM0QlM0Q",
    "_uetvid": "ab97b5e0cdae11f09fad115818f2718b|1khwmbt|1764522037470|1|1|bat.bing.com/p/insights/c/y",
    "datadome": "haLN_RGwR8tr3bcSPo5WMK_Wx0sYIkChSSRJPSCf0AfY9TJvt15pzpWto8CWVy~NAM62k_VT49CSCoL2Erg88OtwRfa5WsKKmltTXaa1GJUCzzYo_mzE4zd7AS_Wx97R",
    "_dd_s": "aid=e31c6314-9e24-4128-8546-b5cadce416c6&logs=0&expire=1764618395534"
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
