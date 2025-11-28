import requests
import json
import pandas as pd
from urllib.parse import quote
from time import sleep
from concurrent.futures import ThreadPoolExecutor, as_completed

# ============================================================
# 1️⃣ Token Bien'ici
# ============================================================

ACCESS_TOKEN = "6pxl7iSPpm85BIulDGhlWfxL9risL9485Pk7Bp7/I5o="
SESSION_ID = "692444614e7d4a00b454d4ed"


# ============================================================
# 2️⃣ Liste des départements FR
# ============================================================

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


# ============================================================
# 3️⃣ Base des filtres Bien’ici (PAS DE DÉPARTEMENT ICI)
# ============================================================

BASE_FILTERS = {
    "size": 24,
    "from": 0,
    "filterType": "buy",
    "propertyType": ["house", "flat", "loft", "castle", "townhouse"],
    "page": 1,
    "sortBy": "relevance",
    "sortOrder": "desc",
    "onTheMarket": [True],
    "limit": "u`|uGycs^?gk`SbbiP??fk`S",
    "newProperty": False,
    "blurInfoType": ["disk", "exact"]
}


# ============================================================
# 4️⃣ Appel API : département + page
# ============================================================

def fetch_page(dep, page):
    filters = BASE_FILTERS.copy()
    filters["zoneIds"] = [f"dep-{dep}"]
    filters["page"] = page
    filters["from"] = (page - 1) * filters["size"]

    filters_encoded = quote(json.dumps(filters))

    url = (
        "https://www.bienici.com/realEstateAds.json"
        f"?filters={filters_encoded}"
        f"&extensionType=extendedIfNoResult"
        f"&access_token={ACCESS_TOKEN}:{SESSION_ID}"
        f"&id={SESSION_ID}"
    )

    try:
        r = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }, timeout=10)

        if r.status_code != 200:
            print(f"❌ HTTP {r.status_code} pour {dep} page {page}")
            return None

        return r.json()

    except Exception as e:
        print(f"❌ Erreur réseau {dep} page {page} : {e}")
        return None


# ============================================================
# 5️⃣ Scraper UN département
# ============================================================

def scrape_department(dep):
    print(f"🌍 Département {dep} → START")

    all_ads = []
    page = 1

    while True:
        data = fetch_page(dep, page)

        if not data or "realEstateAds" not in data:
            print(f"⛔ Fin {dep}, erreur API ou plus de données")
            break

        ads = data["realEstateAds"]
        print(f"{dep} | page {page} → {len(ads)} annonces")

        if len(ads) == 0:
            break

        all_ads.extend(ads)

        if len(ads) < BASE_FILTERS["size"]:
            break

        page += 1
        sleep(0.2)  # sécurité anti-ban

    print(f"✔️ Département {dep} terminé → {len(all_ads)} annonces")
    return dep, all_ads


# ============================================================
# 6️⃣ MULTITHREAD : Scraping France entière
# ============================================================

def scrape_france_multithread():
    print("🚀 MULTITHREAD – Scraping France entière…")

    full_data = []

    # Tu peux changer le nb de threads (8 = bon équilibre)
    THREADS = 10

    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = {executor.submit(scrape_department, dep): dep for dep in DEPARTEMENTS}

        for future in as_completed(futures):
            dep = futures[future]
            try:
                dep_code, dep_ads = future.result()
                print(f"📦 {dep_code} terminé : {len(dep_ads)} annonces")
                full_data.extend(dep_ads)
            except Exception as e:
                print(f"❌ Erreur pendant {dep} : {e}")

    df = pd.json_normalize(full_data)
    df.to_csv("bienici_france_multithread.csv", index=False, encoding="utf-8")

    print("\n💾 Export terminé → bienici_france_multithread.csv")
    print("✔ Total annonces :", len(full_data))


# ============================================================
# 🔥 LANCEMENT
# ============================================================

scrape_france_multithread()
