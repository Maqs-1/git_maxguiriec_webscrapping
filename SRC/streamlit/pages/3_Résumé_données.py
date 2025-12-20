import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Résumé des données - Analyse Immobilière",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# FONCTIONS UTILITAIRES
# ============================================

def get_departements_with_names(df):
    """Retourne les départements disponibles dans les données avec leur nom formaté 'nom(code)'"""
    try:
        # Importer la liste des départements depuis le config
        import sys
        from pathlib import Path
        config_path = Path(__file__).parent.parent.parent / 'scrapper' / 'seloger' / 'config.py'
        sys.path.append(str(config_path.parent))
        
        from config import departements as departements_config
        
        # Créer un dictionnaire numero -> nom
        dept_dict = {dept['numero']: dept['nom'] for dept in departements_config}
        
        # Obtenir les départements présents dans les données
        if 'departement' in df.columns:
            available_depts = set(str(d) for d in df['departement'].dropna().unique())
            
            # Créer la liste formatée pour les départements disponibles
            formatted_depts = []
            for dept_num in sorted(available_depts):
                dept_name = dept_dict.get(dept_num, f"Département {dept_num}")
                formatted_depts.append(f"{dept_name} ({dept_num})")
            
            return ['Tous'] + formatted_depts
        else:
            return ['Tous']
            
    except Exception as e:
        # Fallback si l'import échoue
        if 'departement' in df.columns:
            available_depts = [str(d) for d in df['departement'].dropna().unique()]
            return ['Tous'] + sorted(available_depts)
        return ['Tous']

def categorize_property_type(type_bien):
    """Regroupe les types de biens en catégories principales"""
    if pd.isna(type_bien):
        return "Non spécifié"
    
    type_upper = str(type_bien).upper()
    
    # Appartements
    if type_upper in ['APARTMENT', 'APP']:
        return "Appartement"
    
    # Maisons
    elif type_upper in ['HOUSE', 'MAI', 'PROJECT']:
        return "Maison"
    
    # Terrains
    elif type_upper in ['TER', 'AGR', 'LAC', 'VIG']:
        return "Terrain"
    
    # Locaux commerciaux
    elif type_upper in ['COM', 'IMM', 'DIV']:
        return "Local commercial"
    
    # Garages
    elif type_upper == 'GAR':
        return "Garage"
    
    # Par défaut, si un type n'est pas reconnu, le mettre dans Local commercial
    else:
        return "Local commercial"

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
    
    /* Style professionnel pour toute l'application */
    .main-header {
        color: #1a365d !important;
        font-weight: 600 !important;
        margin-bottom: 1rem !important;
    }
    
    .sub-header {
        color: #2d3748 !important;
        font-weight: 500 !important;
        border-bottom: 2px solid #e2e8f0 !important;
        padding-bottom: 0.5rem !important;
        margin-bottom: 1rem !important;
    }
    
    /* Améliorer les métriques */
    .metric-container {
        background: linear-gradient(135deg, #f8fafc 0%, #e9ecef 100%) !important;
        border-radius: 12px !important;
        padding: 20px !important;
        margin: 8px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07) !important;
        border: 1px solid #e2e8f0 !important;
        transition: transform 0.2s ease !important;
    }
    
    .metric-container:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px rgba(0,0,0,0.1) !important;
    }
    
    /* Style des info/warning boxes */
    .stAlert {
        border-radius: 8px !important;
        border: none !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
    }
    
    /* Améliorer les boutons et contrôles */
    .stButton button {
        border-radius: 6px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
    }
    
    /* Améliorer les radio buttons */
    .stRadio > div {
        background: #f8fafc !important;
        padding: 15px !important;
        border-radius: 8px !important;
        border: 1px solid #e2e8f0 !important;
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
    st.markdown('<h2 class="main-header">Informations générales</h2>', unsafe_allow_html=True)
    
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
    st.markdown('<h2 class="main-header">Origines des données</h2>', unsafe_allow_html=True)
    
    if 'source' in df.columns:
        # Toggle pour choisir entre diagramme et tableau
        view_mode_source = st.radio(
            "Affichage pour les origines des données:",
            ["Diagramme", "Tableau"],
            horizontal=True,
            key="source_view_mode"
        )
        
        if view_mode_source == "Diagramme":
            # Répartition par source - Version améliorée
            source_counts = df['source'].value_counts()
            fig_source = px.pie(
                values=source_counts.values,
                names=source_counts.index,
                title="Répartition par source de données",
                template='plotly_white',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_source.update_layout(
                height=600,
                font=dict(size=14, family='Arial'),
                title_font=dict(size=18, family='Arial', color='darkblue'),
                margin=dict(l=20, r=20, t=60, b=20)
            )
            fig_source.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_source, use_container_width=True)
        else:
            # Tableau détaillé - Version améliorée
            source_stats = df.groupby('source').agg({
                'prix': ['count', 'mean', 'median'],
                'prix_m2': 'mean',
                'surface': 'mean'
            }).round(2)
            source_stats.columns = ['Nombre', 'Prix moyen (€)', 'Prix médian (€)', 'Prix/m² moyen (€)', 'Surface moyenne (m²)']
            
            # Style amélioré pour le dataframe
            st.dataframe(
                source_stats.style.format({
                    'Nombre': '{:,.0f}',
                    'Prix moyen (€)': '{:,.0f} €',
                    'Prix médian (€)': '{:,.0f} €',
                    'Prix/m² moyen (€)': '{:,.0f} €',
                    'Surface moyenne (m²)': '{:.1f} m²'
                }).background_gradient(cmap='Greens', subset=['Nombre']),
                use_container_width=True,
                height=400
            )
    else:
        st.info("ℹ️ Information sur les sources non disponible.")
    
    st.markdown("---")
    
    # ============================================
    # STATISTIQUES DESCRIPTIVES
    # ============================================
    st.markdown('<h2 class="main-header">Statistiques descriptives</h2>', unsafe_allow_html=True)
    
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
    # RÉPARTITION PAR TYPE DE BIEN
    # ============================================
    st.markdown('<h2 class="main-header">Répartition par type de bien</h2>', unsafe_allow_html=True)
    
    if 'type_bien_categorie' in df.columns:
        # Toggle pour choisir entre diagramme et tableau
        view_mode_type = st.radio(
            "Affichage pour les types de biens:",
            ["Diagramme", "Tableau"],
            horizontal=True,
            key="type_view_mode"
        )
        
        if view_mode_type == "Diagramme":
            type_counts = df['type_bien_categorie'].value_counts()
            fig_type = px.pie(
                values=type_counts.values,
                names=type_counts.index,
                title="Répartition par type de bien (regroupé)",
                template='plotly_white',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_type.update_layout(
                height=600,
                font=dict(size=14, family='Arial'),
                title_font=dict(size=18, family='Arial', color='darkblue'),
                margin=dict(l=20, r=20, t=60, b=20)
            )
            fig_type.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_type, use_container_width=True)
        else:
            # Statistiques par type de bien - Version améliorée
            if 'prix' in df.columns and 'prix_m2' in df.columns:
                type_stats = df.groupby('type_bien_categorie').agg({
                    'prix': ['count', 'mean'],
                    'prix_m2': 'mean',
                    'surface': 'mean'
                }).round(2)
                type_stats.columns = ['Nombre', 'Prix moyen (€)', 'Prix/m² moyen (€)', 'Surface moyenne (m²)']
                
                # Style amélioré pour le dataframe
                st.dataframe(
                    type_stats.style.format({
                        'Nombre': '{:,.0f}',
                        'Prix moyen (€)': '{:,.0f} €',
                        'Prix/m² moyen (€)': '{:,.0f} €',
                        'Surface moyenne (m²)': '{:.1f} m²'
                    }).background_gradient(cmap='Blues', subset=['Nombre']),
                    use_container_width=True,
                    height=400
                )
    
    st.markdown("---")
    
    # ============================================
    # EXPORT DES DONNÉES
    # ============================================
    st.markdown('<h2 class="main-header">Export des données</h2>', unsafe_allow_html=True)
    
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

