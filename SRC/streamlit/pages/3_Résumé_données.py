import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Résumé des données - Analyse Immobilière",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# FONCTIONS UTILITAIRES
# ============================================

def categorize_property_type(type_bien):
    """Regroupe les types de biens en catégories principales"""
    if pd.isna(type_bien):
        return "Non spécifié"
    
    type_upper = str(type_bien).upper()
    
    # Appartements
    if type_upper in ['APARTMENT', 'APP']:
        return "Appartement"
    
    # Maisons
    elif type_upper in ['HOUSE', 'MAI']:
        return "Maison"
    
    # Terrains
    elif type_upper == 'TER':
        return "Terrain"
    
    # Locaux commerciaux
    elif type_upper == 'COM':
        return "Local commercial"
    
    # Garages
    elif type_upper == 'GAR':
        return "Garage"
    
    # Autres types
    else:
        return "Autre"

# CSS pour forcer la sidebar à rester visible
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        min-width: 300px !important;
    }
    [data-testid="stSidebar"][aria-expanded="false"] {
        display: block !important;
        visibility: visible !important;
    }
    button[title="Close sidebar"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("Résumé des Données")

# Fonction pour trouver le chemin des données
def find_data_path():
    """Trouve le chemin vers les données en remontant depuis le fichier actuel"""
    current_file = Path(__file__).absolute()
    # Remonter: pages -> streamlit -> SRC -> racine
    base_dir = current_file.parent.parent.parent.parent
    data_path = base_dir / "DATA" / "Fusion_notaires_seloger" / "base_fusionnee.csv"
    
    # Si le fichier n'existe pas, essayer depuis le répertoire de travail
    if not data_path.exists():
        import os
        cwd = Path(os.getcwd())
        # Chercher DATA dans le répertoire courant ou ses parents
        for parent in [cwd] + list(cwd.parents)[:3]:
            alt_path = parent / "DATA" / "Fusion_notaires_seloger" / "base_fusionnee.csv"
            if alt_path.exists():
                return alt_path
    
    return data_path

DATA_PATH = find_data_path()

@st.cache_data
def load_data():
    """Charge les données avec cache pour améliorer les performances"""
    try:
        if DATA_PATH.exists():
            df = pd.read_csv(DATA_PATH)
        else:
            parquet_path = DATA_PATH.parent / "base_fusionnee.parquet"
            if parquet_path.exists():
                df = pd.read_parquet(parquet_path)
            else:
                st.error(f"❌ Fichier de données introuvable : {DATA_PATH}")
                return None
        
        # Nettoyage des données
        numeric_cols = ['prix', 'surface', 'prix_m2', 'nb_pieces', 'nb_chambres', 'latitude', 'longitude']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Ajouter la colonne des types de biens regroupés
        df['type_bien_categorie'] = df['type_bien'].apply(categorize_property_type)
        
        return df
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement des données : {e}")
        return None

# Chargement des données
df = load_data()

if df is not None:
    st.markdown("---")
    
    # ============================================
    # INFORMATIONS GÉNÉRALES
    # ============================================
    st.header("Informations générales")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Nombre total d'annonces", f"{len(df):,}")
    
    with col2:
        if 'source' in df.columns:
            nb_sources = len(df['source'].unique())
            st.metric("Nombre de sources", nb_sources)
        else:
            st.metric("Nombre de sources", "N/A")
    
    with col3:
        if 'ville' in df.columns:
            nb_villes = len(df['ville'].dropna().unique())
            st.metric("Nombre de villes", nb_villes)
        else:
            st.metric("Nombre de villes", "N/A")
    
    with col4:
        if 'departement' in df.columns:
            nb_depts = len(df['departement'].dropna().unique())
            st.metric("Nombre de départements", nb_depts)
        else:
            st.metric("Nombre de départements", "N/A")
    
    st.markdown("---")
    
    # ============================================
    # ORIGINES DES DONNÉES
    # ============================================
    st.header("Origines des données")
    
    if 'source' in df.columns:
        col1, col2 = st.columns(2)
        
        with col1:
            # Répartition par source
            source_counts = df['source'].value_counts()
            fig_source = px.pie(
                values=source_counts.values,
                names=source_counts.index,
                title="Répartition par source de données"
            )
            st.plotly_chart(fig_source, use_container_width=True)
        
        with col2:
            # Tableau détaillé
            source_stats = df.groupby('source').agg({
                'prix': ['count', 'mean', 'median'],
                'prix_m2': 'mean',
                'surface': 'mean'
            }).round(2)
            source_stats.columns = ['Nombre', 'Prix moyen (€)', 'Prix médian (€)', 'Prix/m² moyen (€)', 'Surface moyenne (m²)']
            st.dataframe(source_stats, use_container_width=True)
    else:
        st.info("ℹ️ Information sur les sources non disponible.")
    
    st.markdown("---")
    
    # ============================================
    # STATISTIQUES DESCRIPTIVES
    # ============================================
    st.header("Statistiques descriptives")
    
    if 'prix' in df.columns and 'surface' in df.columns and 'prix_m2' in df.columns:
        # Filtrer les valeurs valides
        df_stats = df[(df['prix'] > 0) & (df['surface'] > 0) & (df['prix_m2'] > 0)]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("Prix")
            prix_stats = df_stats['prix'].describe()
            st.dataframe(prix_stats.to_frame().T, use_container_width=True)
        
        with col2:
            st.subheader("Surface (m²)")
            surface_stats = df_stats['surface'].describe()
            st.dataframe(surface_stats.to_frame().T, use_container_width=True)
        
        with col3:
            st.subheader("Prix au m²")
            prix_m2_stats = df_stats['prix_m2'].describe()
            st.dataframe(prix_m2_stats.to_frame().T, use_container_width=True)
    
    st.markdown("---")
    
    # ============================================
    # RÉPARTITION GÉOGRAPHIQUE
    # ============================================
    st.header("Répartition géographique")
    
    if 'departement' in df.columns:
        col1, col2 = st.columns(2)
        
        with col1:
            # Top 20 départements par nombre d'annonces
            dept_counts = df['departement'].value_counts().head(20)
            fig_dept = px.bar(
                x=dept_counts.values,
                y=dept_counts.index,
                orientation='h',
                labels={'x': 'Nombre d\'annonces', 'y': 'Département'},
                title="Top 20 départements par nombre d'annonces"
            )
            fig_dept.update_layout(height=500)
            st.plotly_chart(fig_dept, use_container_width=True)
        
        with col2:
            # Top 20 villes par nombre d'annonces
            if 'ville' in df.columns:
                ville_counts = df['ville'].value_counts().head(20)
                fig_ville = px.bar(
                    x=ville_counts.values,
                    y=ville_counts.index,
                    orientation='h',
                    labels={'x': 'Nombre d\'annonces', 'y': 'Ville'},
                    title="Top 20 villes par nombre d'annonces"
                )
                fig_ville.update_layout(height=500)
                st.plotly_chart(fig_ville, use_container_width=True)
    
    st.markdown("---")
    
    # ============================================
    # RÉPARTITION PAR TYPE DE BIEN
    # ============================================
    st.header("Répartition par type de bien")
    
    if 'type_bien_categorie' in df.columns:
        col1, col2 = st.columns(2)
        
        with col1:
            type_counts = df['type_bien_categorie'].value_counts()
            fig_type = px.pie(
                values=type_counts.values,
                names=type_counts.index,
                title="Répartition par type de bien (regroupé)"
            )
            st.plotly_chart(fig_type, use_container_width=True)
        
        with col2:
            # Statistiques par type de bien
            if 'prix' in df.columns and 'prix_m2' in df.columns:
                type_stats = df.groupby('type_bien_categorie').agg({
                    'prix': ['count', 'mean'],
                    'prix_m2': 'mean',
                    'surface': 'mean'
                }).round(2)
                type_stats.columns = ['Nombre', 'Prix moyen (€)', 'Prix/m² moyen (€)', 'Surface moyenne (m²)']
                st.dataframe(type_stats, use_container_width=True)
    
    st.markdown("---")
    
    # ============================================
    # EXPORT DES DONNÉES
    # ============================================
    st.header("Export des données")
    
    st.markdown("""
    Les données sont stockées dans :
    - **Format CSV** : `DATA/Fusion_notaires_seloger/base_fusionnee.csv`
    - **Format Parquet** : `DATA/Fusion_notaires_seloger/base_fusionnee.parquet`
    
    Vous pouvez télécharger un échantillon des données ci-dessous.
    """)
    
    if st.button("📥 Télécharger un échantillon (1000 lignes)"):
        sample_df = df.head(1000)
        csv = sample_df.to_csv(index=False)
        st.download_button(
            label="Télécharger CSV",
            data=csv,
            file_name="echantillon_donnees_immobilieres.csv",
            mime="text/csv"
        )

else:
    st.error("❌ Impossible de charger les données. Vérifiez que le fichier existe dans DATA/Fusion_notaires_seloger/")

