import pandas as pd
import numpy as np
import os

# ---------------------------------------------------------------------
# CONFIG : emplacement du fichier DATA
# ---------------------------------------------------------------------
DATA_DIR = r"C:\Users\phili\OneDrive\Bureau\DU DATA ANALYST\COURS PYTHON\WEB SCRAPING\PROJET_IMMOBILIER\DATA"

INPUT_FILE = os.path.join(DATA_DIR, "notaires_france.csv")
OUTPUT_FILE = os.path.join(DATA_DIR, "notaires_france_clean.csv")

# ---------------------------------------------------------------------
# FONCTION DE NETTOYAGE
# ---------------------------------------------------------------------

def clean_notaires_france(input_path=INPUT_FILE, output_path=OUTPUT_FILE):

    print("📥 Chargement du dataset national…")
    df = pd.read_csv(input_path)
    print(f"➡️ Données initiales : {df.shape[0]} lignes, {df.shape[1]} colonnes\n")

    # ------------------------------------------------------------
    # 1. Suppression lignes inutilisables
    # ------------------------------------------------------------
    df = df.dropna(subset=["prix", "surface_m2"])
    print(f"✔️ Après suppression NA prix/surface : {df.shape[0]} lignes")

    # ------------------------------------------------------------
    # 2. Nettoyage superficies aberrantes
    # ------------------------------------------------------------
    df = df[(df["surface_m2"] >= 8) & (df["surface_m2"] <= 300)]
    print(f"✔️ Après filtre surface (8 à 300 m²) : {df.shape[0]} lignes")

    # ------------------------------------------------------------
    # 3. Nettoyage prix aberrants
    # ------------------------------------------------------------
    df = df[(df["prix"] >= 20_000) & (df["prix"] <= 5_000_000)]
    print(f"✔️ Après filtre prix (20k à 5M) : {df.shape[0]} lignes")

    # ------------------------------------------------------------
    # 4. Recalcul prix au m²
    # ------------------------------------------------------------
    df["prix_m2"] = (df["prix"] / df["surface_m2"]).round(2)

    # ------------------------------------------------------------
    # 5. Classes de surface
    # ------------------------------------------------------------
    df["classe_surface"] = pd.cut(
        df["surface_m2"],
        bins=[0, 30, 60, 90, 120, 300],
        labels=["0-30", "30-60", "60-90", "90-120", "120+"]
    )

   # ------------------------------------------------------------
    # 6. Réinitialisation index
    # ------------------------------------------------------------
    df = df.reset_index(drop=True)

    # ------------------------------------------------------------
    # 7. Export final
    # ------------------------------------------------------------
    df.to_csv(output_path, index=False)
    print(f"\n📤 Export terminé → {output_path}")
    print(f"📊 Dataset final : {df.shape[0]} lignes, {df.shape[1]} colonnes")

    return df

# ---------------------------------------------------------------------
# EXECUTION DIRECTE
# ---------------------------------------------------------------------
if __name__ == "__main__":
    clean_notaires_france()
