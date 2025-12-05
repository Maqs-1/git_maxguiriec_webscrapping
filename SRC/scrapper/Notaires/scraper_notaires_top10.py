import requests
import pandas as pd
from tqdm import tqdm

BASE_URL = "https://www.immobilier.notaires.fr/pub-services/inotr-www-annonces/v1/annonces"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

# 10 départements représentatifs
DEPARTEMENTS = [75, 13, 69, 31, 59, 44, 34, 33, 67, 6]  # 6 -> 06

def get_page(page: int, par_page: int, departement: int):
    """
    Appelle l'API des notaires pour un département + une page donnée.
    Retourne le JSON ou None si 400 (mauvaise requête / plus de pages).
    """
    params = {
        "offset": 0,
        "page": page,
        "parPage": par_page,
        "perimetre": 0,
        "departements": f"{departement:02d}",   # ex: 6 -> "06"
        "typeTransaction": "VENTE,VNI,VAE"
    }

    r = requests.get(BASE_URL, params=params, headers=HEADERS)

    if r.status_code == 400:
        print(f"  Page {page} (département {departement:02d}) → 400 Bad Request (probablement plus de pages).")
        return None

    r.raise_for_status()
    return r.json()


def scrape_multi_departements(departements=None, max_pages=200, par_page=50):
    if departements is None:
        departements = DEPARTEMENTS

    all_rows = []

    for dep in departements:
        print(f"\n===== Département {dep:02d} =====")
        for page in tqdm(range(1, max_pages + 1), desc=f"Département {dep:02d}", leave=False):
            data = get_page(page, par_page, dep)

            if data is None:
                print(f"  Arrêt du scraping pour le département {dep:02d} à la page {page}.")
                break

            annonces = data.get("annonceResumeDto", [])

            if not annonces:
                print(f"  Aucune annonce renvoyée à la page {page} pour le département {dep:02d}. Fin pour ce département.")
                break

            print(f"  Département {dep:02d}, page {page} → {len(annonces)} annonces.")

            for a in annonces:
                prix = a.get("prixAffiche")
                surface = a.get("surface")
                prix_m2 = None

                if prix and surface:
                    try:
                        prix_m2 = round(prix / surface, 2)
                    except Exception:
                        prix_m2 = None

                row = {
                    "departement": f"{dep:02d}",
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
    df.to_csv("notaires_10_departements.csv", index=False)
    print(f"\nExport → notaires_10_departements.csv ({len(df)} lignes, {df.shape[1]} colonnes)")
    return df


if __name__ == "__main__":
    df = scrape_multi_departements()
    print(df.head())
