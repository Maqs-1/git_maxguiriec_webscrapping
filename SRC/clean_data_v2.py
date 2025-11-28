import pandas as pd
import numpy as np
import os

# ============================================================
# CONFIGURATION
# ============================================================

DATA_DIR = r"C:\Users\phili\OneDrive\Bureau\DU DATA ANALYST\COURS PYTHON\WEB SCRAPING\PROJET_IMMOBILIER\DATA"

INPUT_FILE = os.path.join(DATA_DIR, "notaires_france.csv")
OUTPUT_FILE = os.path.join(DATA_DIR, "notaires_france_clean_v2.csv")

# Dictionnaire département → région (simplifié mais fiable)
REGIONS = {
    1: "Auvergne-Rhône-Alpes", 2: "Hauts-de-France", 3: "Auvergne-Rhône-Alpes", 4: "Provence-Alpes-Côte d’Azur",
    5: "Provence-Alpes-Côte d’Azur", 6: "Provence-Alpes-Côte d’Azur", 7: "Auvergne-Rhône-Alpes", 8: "Grand Est",
    9: "Occitanie", 10: "Grand Est", 11: "Occitanie", 12: "Occitanie", 13: "Provence-Alpes-Côte d’Azur",
    14: "Normandie", 15: "Auvergne-Rhône-Alpes", 16: "Nouvelle-Aquitaine", 17: "Nouvelle-Aquitaine",
    18: "Centre-Val de Loire", 19: "Nouvelle-Aquitaine", 21: "Bourgogne-Franche-Comté",
    22: "Bretagne", 23: "Nouvelle-Aquitaine", 24: "Nouvelle-Aquitaine", 25: "Bourgogne-Franche-Comté",
    26: "Auvergne-Rhône-Alpes", 27: "Normandie", 28: "Centre-Val de Loire", 29: "Bretagne",
    30: "Occitanie", 31: "Occitanie", 32: "Occitanie", 33: "Nouvelle-Aquitaine",
    34: "Occitanie", 35: "Bretagne", 36: "Centre-Val de Loire", 37: "Centre-Val de Loire",
    38: "Auvergne-Rhône-Alpes", 39: "Bourgogne-Franche-Comté", 40: "Nouvelle-Aquitaine",
    41: "Centre-Val de Loire", 42: "Auvergne-Rhône-Alpes", 43: "Auvergne-Rhône-Alpes",
    44: "Pays de la Loire", 45: "Centre-Val de Loire", 46: "Occitanie", 47: "Nouvelle-Aquitaine",
    48: "Occitanie", 49: "Pays de la Loire", 50: "Normandie", 51: "Grand Est", 52: "Grand Est",
    53: "Pays de la Loire", 54: "Grand Est", 55: "Grand Est", 56: "Bretagne", 57: "Grand Est",
    58: "Bourgogne-Franche-Comté", 59: "Hauts-de-France", 60: "Hauts-de-France",
    61: "Normandie", 62: "Hauts-de-France", 63: "Auvergne-Rhône-Alpes", 64: "Nouvelle-Aquitaine",
    65: "Occitanie", 66: "Occitanie", 67: "Grand Est", 68: "Grand Est", 69: "Auvergne-Rhône-Alpes",
    70: "Bourgogne-Franche-Comté", 71: "Bourgogne-Franche-Comté", 72: "Pays de la Loire",
    73: "Auvergne-Rhône-Alpes", 74: "Auvergne-Rhône-Alpes", 75: "Île-de-France", 76: "Normandie",
    77: "Île-de-France", 78: "Île-de-France", 79: "Nouvelle-Aquitaine", 80: "Hauts-de-France",
    81: "Occitanie", 82: "Occitanie", 83: "Provence-Alpes-Côte d’Azur", 84: "Provence-Alpes-Côte d’Azur",
    85: "Pays de la Loire", 86: "Nouvelle-Aquitaine", 87: "Nouvelle-Aquitaine",
    88: "Grand Est", 89: "Bourgogne-Franche-Comté", 90: "Bourgogne-Franche-Comté",
    91: "Île-de-France", 92: "Île-de-France", 93: "Île-de-France", 94: "Île-de-France",
    95: "Île-de-France", 971: "Guadeloupe", 972: "Martinique",
    973: "Guyane", 974: "La Réunion", 976: "Mayotte"
}

TYPE_BIEN_MAP = {
    "APP": "Appartement",
    "MAI": "Maison",
    "IMM": "Immeuble",
    "BAT": "Bâtiment",
    "TER": "Terrain",
    "LOC": "Local professionnel",
}

# ============================================================
# NETTOYAGE ET ENRICHISSEMENT
# ============================================================

def clean_notaires_france_v2(input_path=INPUT_FILE, output_path=OUTPUT_FILE):

    print("📥 Chargement du dataset national…")
    df = pd.read_csv(input_path)
    print(f"➡️ Données initiales : {df.shape[0]} lignes, {df.shape[1]} colonnes\n")

    # 1) Suppression NA critiques
    df = df.dropna(subset=["prix", "surface_m2"])

    # 2) Surfaces aberrantes
    df = df[(df["surface_m2"] >= 8) & (df["surface_m2"] <= 300)]

    # 3) Prix aberrants
    df = df[(df["prix"] >= 20_000) & (df["prix"] <= 5_000_000)]

    # 4) Recalcul prix/m²
    df["prix_m2"] = (df["prix"] / df["surface_m2"]).round(2)

    # 5) Filtre prix/m² aberrants
    df = df[(df["prix_m2"] >= 300) & (df["prix_m2"] <= 20000)]

    # 6) Classe surface
    df["classe_surface"] = pd.cut(
        df["surface_m2"],
        bins=[0, 30, 60, 90, 120, 300],
        labels=["0-30", "30-60", "60-90", "90-120", "120+"]
    )

    # 7) Classe prix
    df["classe_prix"] = pd.cut(
        df["prix"],
        bins=[0, 150000, 300000, 500000, 900000, 5_000_000],
        labels=["<150k", "150-300k", "300-500k", "500-900k", ">900k"]
    )

    # 8) Ajout région
    df["region"] = df["departement"].map(REGIONS)

    # 9) Ajout type_bien propre
    df["type_bien_clean"] = df["type_bien"].map(TYPE_BIEN_MAP).fillna("Autre")

    # 10) Conversion date
    df["date_maj"] = pd.to_datetime(df["date_maj"], errors="coerce")

    # 11) Extraction arrondissement (Paris, Lyon, Marseille)
    def extract_arrondissement(cp):
        try:
            cp = int(cp)
            dept = cp // 1000
            arr = cp % 100
            if dept in [75, 69, 13]:
                return arr
        except:
            return None
        return None

    df["arrondissement"] = df["cp"].apply(extract_arrondissement)

    # 12) Réinitialisation index
    df = df.reset_index(drop=True)

    # 13) Export final
    df.to_csv(output_path, index=False)
    print(f"\n📤 Export terminé → {output_path}")
    print(f"📊 Dataset final : {df.shape[0]} lignes, {df.shape[1]} colonnes")

    return df

# ============================================================
# EXECUTION
# ============================================================
if __name__ == "__main__":
    clean_notaires_france_v2()
