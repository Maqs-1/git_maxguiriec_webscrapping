import pandas as pd
import glob
import os
import re

# =====================================================
# CONFIG : CHEMINS (adapte si besoin)
# =====================================================
NOTAIRES_FILE = r"C:\Users\phili\OneDrive\Bureau\DU DATA ANALYST\COURS PYTHON\WEB SCRAPING\PROJET_IMMOBILIER\DATA\Notaires\notaires_france.csv"
SELOGER_FOLDER = r"C:\Users\phili\OneDrive\Bureau\DU DATA ANALYST\COURS PYTHON\WEB SCRAPING\PROJET_IMMOBILIER\DATA\SeLoger"

# =====================================================
# OUTILS
# =====================================================

def detect_separator(filepath):
    """Détecte automatiquement le séparateur CSV."""
    with open(filepath, "r", encoding="utf-8") as f:
        first = f.readline()
        if ";" in first and "," in first:
            return ";" if first.count(";") > first.count(",") else ","
        return ";" if ";" in first else ","

def to_int(series):
    """Conversion sûre en Int64."""
    return pd.to_numeric(series, errors="coerce").round().astype("Int64")

def extract_departement_from_filename(filepath):
    """Récupère le département depuis le nom de fichier SeLoger."""
    name = os.path.basename(filepath)
    m = re.search(r"seloger_dep_([0-9A-Z]+)_", name)
    if not m:
        return None
    code = m.group(1)
    if code.isdigit():
        return code.zfill(2)
    return code  # 2A, 2B…

# =====================================================
# NETTOYAGE SELOGER
# =====================================================

def clean_seloger(df, dept_from_file):
    # Harmonisation des colonnes possibles
    rename_map = {
        "price": "prix",
        "livingArea": "surface",
        "surface": "surface",
        "rooms": "nb_pieces",
        "bedrooms": "nb_chambres",
        "propertyType": "type_bien",
        "city": "ville",
        "zipCode": "cp",
        "postalCode": "cp",
        "id": "id",
        "description": "description",
        "permalink": "url",
        "latitude": "latitude",
        "longitude": "longitude"
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # Colonnes obligatoires
    required = ["id","prix","surface","prix_m2","nb_pieces","nb_chambres",
                "type_bien","ville","cp","departement","latitude","longitude",
                "description","url"]
    for col in required:
        if col not in df.columns:
            df[col] = None

    # Conversions
    df["prix"] = to_int(df["prix"])
    df["surface"] = pd.to_numeric(df["surface"], errors="coerce")
    df["nb_pieces"] = to_int(df["nb_pieces"])
    df["nb_chambres"] = to_int(df["nb_chambres"])

    # Nettoyage du CP
    df["cp"] = df["cp"].astype(str).str.extract(r"(\d{5})")
    
    # Département : priorité au nom du fichier
    df["departement"] = dept_from_file

    # Prix / m²
    df["prix_m2"] = (df["prix"] / df["surface"]).round(2)

    df["source"] = "seloger"
    return df


# =====================================================
# NETTOYAGE NOTAIRES
# =====================================================

def clean_notaires(df):
    if df.shape[1] == 1:
        df = df[df.columns[0]].str.split(",", expand=True)

    df.columns = [
        "departement","id","prix","surface","prix_m2","nb_pieces","nb_chambres",
        "type_bien","cp","ville","localite","statut","date_maj","url","photo"
    ]

    # Suppression éventuelle de la ligne d’en-tête
    df = df[df["departement"] != "departement"]

    df["prix"] = to_int(df["prix"])
    df["surface"] = pd.to_numeric(df["surface"], errors="coerce")
    df["nb_pieces"] = to_int(df["nb_pieces"])
    df["nb_chambres"] = to_int(df["nb_chambres"])

    df["cp"] = df["cp"].astype(str).str.extract(r"(\d{5})")
    df["departement"] = df["cp"].str[:2]

    df["prix_m2"] = (df["prix"] / df["surface"]).round(2)

    df["description"] = None
    df["latitude"] = None
    df["longitude"] = None
    df["source"] = "notaires"

    return df


# =====================================================
# CHARGEMENT DES FICHIERS SELOGER
# =====================================================

def load_seloger_folder(folder):
    files = glob.glob(os.path.join(folder, "seloger_dep_*.csv"))
    all_dfs = []

    print(f"\n=== Chargement SeLoger : {len(files)} fichiers trouvés ===")

    for f in files:
        dept = extract_departement_from_filename(f)
        print(f"➡️ {os.path.basename(f)}  (département = {dept})")

        try:
            sep = detect_separator(f)
            df = pd.read_csv(f, sep=sep, engine="python")
            df_clean = clean_seloger(df, dept)
            all_dfs.append(df_clean)
        except Exception as e:
            print(f"❌ ERREUR fichier {f} : {e}")

    if not all_dfs:
        print("⚠ Aucun fichier SeLoger chargé.")
        return pd.DataFrame()

    return pd.concat(all_dfs, ignore_index=True)


# =====================================================
# CHARGEMENT NOTAIRES
# =====================================================

def load_notaires(filepath):
    print(f"\n=== Chargement Notaires ===")
    sep = detect_separator(filepath)
    df = pd.read_csv(filepath, sep=sep, engine="python", header=None)
    return clean_notaires(df)


# =====================================================
# FUSION GÉNÉRALE
# =====================================================

def merge_all():
    df_notaires = load_notaires(NOTAIRES_FILE)
    df_seloger = load_seloger_folder(SELOGER_FOLDER)

    full = pd.concat([df_notaires, df_seloger], ignore_index=True)

    # Format final
    ordered = [
        "id","prix","surface","prix_m2","nb_pieces","nb_chambres",
        "type_bien","ville","cp","departement","latitude","longitude",
        "description","url","source"
    ]

    return full[ordered]


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":
    df = merge_all()

    df.to_csv("base_fusionnee.csv", index=False)
    df.to_parquet("base_fusionnee.parquet", index=False)

    print("\n🎉 Fusion terminée !")
    print("📁 Fichiers générés : base_fusionnee.csv + base_fusionnee.parquet\n")
