import requests
import json
import pandas as pd
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import sleep
import os

ACCESS_TOKEN = "6pxl7iSPpm85BIulDGhlWfxL9risL9485Pk7Bp7/I5o="
SESSION_ID = "692444614e7d4a00b454d4ed"

# Liste des départements FR
DEPARTEMENTS = [
    "01","02","03","04","05","06","07","08","09",
    "10","11","12","13","14","15","16","17","18","19",
    "2A","2B",
    "21","22","23","24","25","26","27","28","29",
    "30","31","32","33","34","35","36","37","38","39",
    "40","41","42","43","44","45","46","47","48","49",
    "50","51","52","53","54","55","56","57","58","59",
    "60","61","62","63","64","65","66","67","68","69",
    "70","71","72","73","74","75","76","77","78","79",
    "80","81","82","83","84","85","86","87","88",
    "89","90","91","92","93","94","95"
]

# Base des filtres (sans geography)
BASE_FILTERS = {
    "size": 24,
    "from": 0,
    "filterType": "buy",
    "propertyType": ["house", "flat", "loft", "castle", "townhouse"],
    "page": 1,
    "sortBy": "relevance",
    "sortOrder": "desc",
    "onTheMarket": [True],
    "newProperty": False,
    "blurInfoType": ["disk", "exact"]
}

# Création du dossier de sortie
os.makedirs("departements", exist_ok=True)

def get_dep_from_cp(cp):
    cp = str(cp).zfill(5)
    return cp[:2]

def fetch_page(page):
    filters = BASE_FILTERS.copy()
    filters["page"] = page
    filters["from"] = (page - 1) * filters["size"]

    filters_encoded = quote(json.dumps(filters))

    url = (
        "https://www.bienici.com/realEstateAds.json"
        f"?filters={filters_encoded}"
        f"&access_token={ACCESS_TOKEN}:{SESSION_ID}"
        f"&id={SESSION_ID}"
    )

    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)

    if r.status_code != 200:
        return None

    return r.json()

def scrape_page(page):
    data = fetch_page(page)
    if not data or "realEstateAds" not in data:
        return []

    ads = data["realEstateAds"]
    print(f"[+] Page {page} → {len(ads)} annonces")
    return ads

def save_by_departments(ads):
    by_dep = {}

    for ad in ads:
        dep = get_dep_from_cp(ad.get("postalCode", ""))

        if dep not in by_dep:
            by_dep[dep] = []

        by_dep[dep].append(ad)

    # Append dans les CSV par département
    for dep, items in by_dep.items():
        df = pd.json_normalize(items)
        fpath = f"departements/bienici_dep_{dep}.csv"

        # append mode
        df.to_csv(fpath, index=False, mode="a", header=not os.path.exists(fpath))

def scrape_france():
    print("🚀 SCRAPING FRANCE - MULTITHREAD + FILTRAGE LOCAL")

    max_threads = 10
    max_pages = 200  # ajustable

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(scrape_page, p) for p in range(1, max_pages + 1)]

        for f in as_completed(futures):
            ads = f.result()
            if ads:
                save_by_departments(ads)

    print("✔ FIN : fichiers départementaux générés dans /departements/")

if __name__ == "__main__":
    scrape_france()
