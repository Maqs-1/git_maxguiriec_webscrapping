import requests
import pandas as pd
from tqdm import tqdm

BASE_URL = "https://www.immobilier.notaires.fr/pub-services/inotr-www-annonces/v1/annonces"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

def get_page(page=1, par_page=50):
    params = {
        "offset": 0,
        "page": page,
        "parPage": par_page,
        "perimetre": 0,
        "departements": 75,
        "typeTransaction": "VENTE,VNI,VAE"
    }

    r = requests.get(BASE_URL, params=params, headers=HEADERS)

    # si l'API renvoie 400 → on s'arrête
    if r.status_code == 400:
        print(f"Page {page} → 400 Bad Request (probablement plus de pages).")
        return None

    r.raise_for_status()
    return r.json()


def scrape_paris(max_pages=200, par_page=50):
    all_rows = []

    for page in tqdm(range(1, max_pages+1), desc="Scraping Paris"):
        data = get_page(page, par_page)

        if data is None:
            print(f"Arrêt du scraping à la page {page}.")
            break

        annonces = data.get("annonceResumeDto", [])

        if not annonces:
            print(f"Aucune annonce renvoyée à la page {page}. Fin du scraping.")
            break

        print(f"Page {page} → {len(annonces)} annonces.")

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

    df = pd.DataFrame(all_rows)
    df.to_csv("notaires_paris_api.csv", index=False)
    print(f"Export → notaires_paris_api.csv ({len(df)} lignes)")
    return df


if __name__ == "__main__":
    df = scrape_paris()
    print(df.head())
