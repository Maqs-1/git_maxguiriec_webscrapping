import requests
import pandas as pd
from tqdm import tqdm

BASE_URL = "https://www.immobilier.notaires.fr/pub-services/inotr-www-annonces/v1/annonces"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

# Tous les départements France métropolitaine + DOM
DEPARTEMENTS = (
    list(range(1, 96)) + [971, 972, 973, 974, 976]
)

def get_page(page: int, par_page: int, departement):
    params = {
        "offset": 0,
        "page": page,
        "parPage": par_page,
        "perimetre": 0,
        "departements": str(departement),
        "typeTransaction": "VENTE,VNI,VAE"
    }

    r = requests.get(BASE_URL, params=params, headers=HEADERS)

    if r.status_code == 400:  # plus de pages
        return None

    r.raise_for_status()
    return r.json()


def scrape_france(max_pages=200, par_page=50):
    all_rows = []

    for dep in DEPARTEMENTS:
        print(f"\n===== 📍 Département {dep} =====")

        for page in tqdm(range(1, max_pages + 1),
                         desc=f"Département {dep}",
                         leave=False):

            data = get_page(page, par_page, dep)

            if data is None:
                print(f"  ➤ Fin du département {dep} (code 400).")
                break

            annonces = data.get("annonceResumeDto", [])

            if not annonces:
                print(f"  ➤ Aucune annonce page {page}, fin du département {dep}.")
                break

            # Log
            print(f"  Page {page} → {len(annonces)} annonces")

            # Extraction des annonces
            for a in annonces:
                prix = a.get("prixAffiche")
                surface = a.get("surface")
                prix_m2 = None

                if prix and surface:
                    try:
                        prix_m2 = round(prix / surface, 2)
                    except:
                        prix_m2 = None

                row = {
                    "departement": dep,
                    "id": a.get("id"),
                    "prix": prix,
                    "surface_m2": surface,
                    "prix_m2": prix_m2,
                    "nb_pieces": a.get("nbPieces"),
                    "nb_chambres": a.get("nbChambres"),
                    "type_bien": a.get("typeBien"),
                    "cp": a.get("codePostal"),
                    "commune": a.get("communeNom"),
                    "localite": a.get("localiteNom"),
                    "statut": a.get("statut"),
                    "date_maj": a.get("dateMaj"),
                    "url": a.get("urlDetailAnnonceFr"),
                    "photo": a.get("urlPhotoPrincipale"),
                }
                all_rows.append(row)

    # Création du DataFrame final
    df = pd.DataFrame(all_rows)
    df.to_csv("notaires_france.csv", index=False)

    print(f"\n🇫🇷 Export national terminé → notaires_france.csv ({len(df)} lignes)")
    return df


if __name__ == "__main__":
    scrape_france()
