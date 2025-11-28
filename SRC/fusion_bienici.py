import os
import pandas as pd
from tqdm import tqdm

# 📁 Chemin vers ton dossier departements
DEPART_DIR = r"C:\Users\phili\OneDrive\Bureau\DU DATA ANALYST\COURS PYTHON\WEB SCRAPING\PROJET_IMMOBILIER\SRC\departements"

# 📁 Fichier final fusionné
OUTPUT_FILE = "bienici_france_clean.csv"

def fusionner_donnees():
    print("🚀 Fusion de tous les fichiers départementaux...")

    # Liste les fichiers CSV dans le dossier
    fichiers = [f for f in os.listdir(DEPART_DIR) if f.endswith(".csv")]

    print(f"📦 {len(fichiers)} fichiers trouvés")

    df_list = []

    # 🔄 Charger chaque CSV
    for fichier in tqdm(fichiers, desc="Chargement des fichiers"):
        path = os.path.join(DEPART_DIR, fichier)

        try:
            df = pd.read_csv(path, dtype=str)  # charge tout en string (safe)
            df_list.append(df)
        except Exception as e:
            print(f"❌ Erreur sur {fichier} :", e)

    # 🧱 Fusion
    df_full = pd.concat(df_list, ignore_index=True)

    print("✔ Fusion terminée")
    print("Nombre de lignes AVANT dédoublonnage :", len(df_full))

    # 🧽 Dédoublonnage (sur id si dispo)
    if "id" in df_full.columns:
        df_full = df_full.drop_duplicates(subset="id")
        print("✔ Dédoublonnage effectué sur la colonne 'id'")
    else:
        df_full = df_full.drop_duplicates()
        print("✔ Colonne 'id' introuvable → dédoublonnage global")

    print("Nombre de lignes APRÈS dédoublonnage :", len(df_full))

    # 💾 Sauvegarde finale
    df_full.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    print(f"💾 Export terminé → {OUTPUT_FILE}")

if __name__ == "__main__":
    fusionner_donnees()
