import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.plugins import MarkerCluster
from streamlit.components.v1 import html as st_html
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import tempfile
import os
import json
import requests

st.set_page_config(
    page_title="Analyse - Analyse Immobilière",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%) !important;
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
</style>
""", unsafe_allow_html=True)

def clean_ville_name(ville_str):
    """Nettoie le nom de ville en supprimant adresses et coordonnées GPS"""
    if pd.isna(ville_str):
        return None
    
    ville = str(ville_str).strip()
    
    # Supprimer les coordonnées GPS (pattern: nombre.nombre, nombre.nombre)
    import re
    gps_pattern = r'\d+\.\d+,\s*\d+\.\d+'
    ville = re.sub(gps_pattern, '', ville).strip()
    
    # Supprimer les adresses (numéro de rue au début)
    address_pattern = r'^\d+\s+[A-Za-zÀ-ÿ]'
    if re.match(address_pattern, ville):
        # Si ça commence par un numéro, c'est probablement une adresse
        # Garder seulement la partie après la première virgule ou le dernier numéro
        parts = ville.split(',')
        if len(parts) > 1:
            ville = parts[-1].strip()  # Prendre la dernière partie (généralement la ville)
        else:
            # Essayer de trouver la ville après le numéro
            ville = re.sub(r'^\d+\s+', '', ville).strip()
    
    # Nettoyer les espaces multiples et caractères spéciaux
    ville = re.sub(r'\s+', ' ', ville)
    ville = ville.strip('.,; ')
    
    # Si la ville est vide après nettoyage, retourner None
    if not ville or ville.lower() in ['nan', 'none', 'null', '']:
        return None
    
    return ville

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

# Debug temporaire (à retirer après vérification)
if not DATA_PATH.exists():
    st.error(f"❌ Fichier introuvable. Chemin recherché: {DATA_PATH}")
    st.info("💡 Assurez-vous de lancer Streamlit depuis la racine du projet avec: `streamlit run SRC/streamlit/app.py`")

@st.cache_data
def load_data():
    """Charge les données avec cache pour améliorer les performances"""
    try:
        # Essayer d'abord le CSV
        if DATA_PATH.exists():
            df = pd.read_csv(DATA_PATH)
        else:
            # Essayer le parquet
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
        
        # Nettoyer les noms de villes
        if 'ville' in df.columns:
            df['ville'] = df['ville'].apply(clean_ville_name)
            # Supprimer les lignes où la ville est None après nettoyage
            df = df.dropna(subset=['ville'])
        
        # Filtrer les données invalides
        df = df.dropna(subset=['prix', 'surface', 'prix_m2'])
        df = df[(df['prix'] > 70000) & (df['surface'] > 0) & (df['prix_m2'] > 9)]
        
        # Convertir creationDate en datetime si elle existe
        if 'creationDate' in df.columns:
            df['creationDate'] = pd.to_datetime(df['creationDate'], errors='coerce')
        
        # Ajouter la colonne des types de biens regroupés
        df['type_bien_categorie'] = df['type_bien'].apply(categorize_property_type)
        
        # Ajouter les coordonnées GPS si elles ne sont pas présentes
        # if 'latitude' not in df.columns or df['latitude'].isna().all():
        #     df = add_geolocation_data(df)
        
        return df
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement des données : {e}")
        return None

@st.cache_data
def add_geolocation_data(df):
    """Ajoute les coordonnées GPS aux données en utilisant l'API Nominatim"""
    try:
        import time
        
        # Fonction pour géocoder une ville
        def geocode_city(ville, cp=None):
            try:
                # Nettoyer le nom de la ville
                ville_clean = str(ville).strip()
                if cp:
                    cp_clean = str(cp).strip()
                    query = f"{ville_clean}, {cp_clean}, France"
                else:
                    query = f"{ville_clean}, France"
                
                # Utiliser Nominatim API
                url = "https://nominatim.openstreetmap.org/search"
                params = {
                    'q': query,
                    'format': 'json',
                    'limit': 1,
                    'countrycodes': 'fr'
                }
                headers = {'User-Agent': 'Streamlit-App/1.0'}
                
                response = requests.get(url, params=params, headers=headers, timeout=5)
                response.raise_for_status()
                
                data = response.json()
                if data:
                    return float(data[0]['lat']), float(data[0]['lon'])
                else:
                    return None, None
                    
            except Exception as e:
                return None, None
        
        # Vérifier si nous avons besoin de géolocaliser
        needs_geocoding = df['latitude'].isna() | df['longitude'].isna()
        cities_to_geocode = df[needs_geocoding][['ville', 'cp']].drop_duplicates()
        
        if len(cities_to_geocode) == 0:
            st.info("✅ Toutes les données sont déjà géolocalisées.")
            return df
        
        st.info(f"🔄 Géocodage de {len(cities_to_geocode)} villes uniques...")
        
        # Créer un cache pour éviter les appels répétés
        geo_cache = {}
        
        # Géocoder chaque ville unique
        progress_bar = st.progress(0)
        for i, (_, row) in enumerate(cities_to_geocode.iterrows()):
            ville = row['ville']
            cp = row['cp'] if pd.notna(row['cp']) else None
            
            # Créer une clé de cache
            cache_key = f"{ville}_{cp}"
            
            if cache_key not in geo_cache:
                lat, lon = geocode_city(ville, cp)
                geo_cache[cache_key] = (lat, lon)
                
                # Petite pause pour respecter les limites de l'API
                time.sleep(0.1)
            
            # Mettre à jour la barre de progression
            progress_bar.progress((i + 1) / len(cities_to_geocode))
        
        progress_bar.empty()
        
        # Appliquer les coordonnées aux données
        def apply_geocoding(row):
            if pd.notna(row['latitude']) and pd.notna(row['longitude']):
                return row['latitude'], row['longitude']
            
            cache_key = f"{row['ville']}_{row['cp'] if pd.notna(row['cp']) else None}"
            lat, lon = geo_cache.get(cache_key, (None, None))
            return lat, lon
        
        df[['latitude', 'longitude']] = df.apply(
            lambda row: apply_geocoding(row), 
            axis=1, 
            result_type='expand'
        )
        
        geocoded_count = df[['latitude', 'longitude']].notna().all(axis=1).sum()
        st.info(f"✅ Géolocalisation terminée : {geocoded_count} annonces géolocalisées sur {len(df)}")
        
        return df
        
    except Exception as e:
        st.warning(f"⚠️ Erreur lors de l'ajout des données géographiques : {e}")
        return df

# Chargement des données
df = load_data()

if df is not None:
    # ============================================
    # SIDEBAR AVEC LES FILTRES
    # ============================================
    with st.sidebar:
        st.header("Filtres de recherche")
        
        # Filtres principaux
        st.subheader("Filtres principaux")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Filtre par source
            sources = ['Tous'] + list(df['source'].unique()) if 'source' in df.columns else ['Tous']
            selected_source = st.selectbox("Source", sources)
        
        with col2:
            # Filtre par type de bien (regroupé)
            if 'type_bien_categorie' in df.columns:
                types_bien = ['Tous'] + sorted(list(df['type_bien_categorie'].dropna().unique()))
                selected_type = st.selectbox("Type de bien", types_bien)
            else:
                selected_type = 'Tous'
        
        # Filtre par département (doit être défini avant le filtre ville)
        st.subheader("Localisation")
        if 'departement' in df.columns:
            departements_options = get_departements_with_names(df)
            selected_dept_display = st.selectbox("Département", departements_options)
            
            # Extraire le numéro de département de la sélection
            if selected_dept_display == 'Tous':
                selected_dept = 'Tous'
            else:
                # Extraire le numéro entre parenthèses
                import re
                match = re.search(r'\((\d+[A-Z]*)\)', selected_dept_display)
                selected_dept = match.group(1) if match else selected_dept_display
        else:
            selected_dept = 'Tous'
        
        # Filtre par ville (utilise toutes les villes filtrées par département)
        if 'ville' in df.columns:
            # Calculer les villes disponibles en fonction du département sélectionné
            if selected_dept != 'Tous':
                villes_disponibles = df[df['departement'].astype(str) == str(selected_dept)]['ville'].dropna().unique()
            else:
                villes_disponibles = df['ville'].dropna().unique()
            
            villes_options = ['Toutes'] + sorted([str(v) for v in villes_disponibles if pd.notna(v)])
            selected_ville = st.selectbox("Ville", villes_options)
        else:
            selected_ville = 'Toutes'
        
        # Filtres numériques
        st.subheader("Filtres numériques")
        
        if 'surface' in df.columns:
            min_surface = float(df['surface'].min())
            max_surface = float(min(df['surface'].max(), 500))  # Limiter à 500 pour éviter les valeurs aberrantes
            surface_range = st.slider(
                "Surface (m²)",
                min_value=float(min_surface),
                max_value=float(max_surface),
                value=(float(min_surface), float(max_surface)),
                step=5.0
            )
        else:
            surface_range = None
        
        if 'prix' in df.columns:
            min_prix = float(df['prix'].min())
            max_prix = float(min(df['prix'].max(), 5000000))  # Limiter à 5M€
            prix_range = st.slider(
                "Prix (€)",
                min_value=float(min_prix),
                max_value=float(max_prix),
                value=(float(min_prix), float(max_prix)),
                step=10000.0
            )
        else:
            prix_range = None
        
        if 'nb_pieces' in df.columns:
            pieces_options = ['Tous'] + sorted([str(int(p)) for p in df['nb_pieces'].dropna().unique() if pd.notna(p) and p > 0])
            selected_pieces = st.selectbox("Nombre de pièces", pieces_options)
        else:
            selected_pieces = 'Tous'
    
    # ============================================
    # APPLICATION DES FILTRES
    # ============================================
    
    df_filtered = df.copy()
    
    if selected_source != 'Tous':
        df_filtered = df_filtered[df_filtered['source'] == selected_source]
    if selected_type != 'Tous':
        df_filtered = df_filtered[df_filtered['type_bien_categorie'] == selected_type]
    if selected_ville != 'Toutes':
        df_filtered = df_filtered[df_filtered['ville'] == selected_ville]
    if selected_dept != 'Tous':
        df_filtered = df_filtered[df_filtered['departement'].astype(str) == str(selected_dept)]
    if surface_range:
        df_filtered = df_filtered[(df_filtered['surface'] >= surface_range[0]) & (df_filtered['surface'] <= surface_range[1])]
    if prix_range:
        df_filtered = df_filtered[(df_filtered['prix'] >= prix_range[0]) & (df_filtered['prix'] <= prix_range[1])]
    if selected_pieces != 'Tous':
        df_filtered = df_filtered[df_filtered['nb_pieces'] == int(selected_pieces)]
    
    # ============================================
    # CONTENU PRINCIPAL DE LA PAGE
    # ============================================
    st.title("Analyse Interactive des Données Immobilières")
    
    # Métriques après filtrage - VERSION AMÉLIORÉE AVEC PLUS DE VISIBILITÉ
    st.markdown('<h2 class="main-header">Résultats après filtrage</h2>', unsafe_allow_html=True)
    
    # CSS personnalisé pour agrandir les métriques
    st.markdown("""
    <style>
    .big-metric {
        font-size: 28px !important;
        font-weight: bold !important;
        text-align: center;
    }
    .metric-label {
        font-size: 18px !important;
        color: #333;
        margin-bottom: 10px;
        font-weight: 600;
    }
    .metric-value {
        font-size: 36px !important;
        font-weight: bold !important;
        color: #1f77b4;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    .metric-container {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 10px;
        padding: 15px;
        margin: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border: 1px solid #dee2e6;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Affichage amélioré des métriques avec plus de visibilité
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-label">Nombre d\'annonces</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{len(df_filtered):,}</div>', unsafe_allow_html=True)
    
    with col2:
        if len(df_filtered) > 0:
            prix_moyen = df_filtered['prix'].mean()
            st.markdown('<div class="metric-label">Prix moyen</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{prix_moyen:,.0f} €</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="metric-label">Prix moyen</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-value">N/A</div>', unsafe_allow_html=True)
    
    with col3:
        if len(df_filtered) > 0:
            prix_m2_moyen = df_filtered['prix_m2'].mean()
            st.markdown('<div class="metric-label">Prix/m² moyen</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{prix_m2_moyen:,.0f} €/m²</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="metric-label">Prix/m² moyen</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-value">N/A</div>', unsafe_allow_html=True)
    
    with col4:
        if len(df_filtered) > 0:
            surface_moyenne = df_filtered['surface'].mean()
            st.markdown('<div class="metric-label">Surface moyenne</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{surface_moyenne:.1f} m²</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="metric-label">Surface moyenne</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-value">N/A</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    if len(df_filtered) == 0:
        st.warning("⚠️ Aucune donnée ne correspond aux filtres sélectionnés.")
    else:
        # ============================================
        # 1. HISTOGRAMME DU PRIX AU M² PAR VILLE
        # ============================================
        st.markdown('<h3 class="sub-header">Prix au m² par ville</h3>', unsafe_allow_html=True)
        
        if 'ville' in df_filtered.columns and 'prix_m2' in df_filtered.columns:
            # Calculer le prix moyen par ville (uniquement les villes avec au moins 50 annonces)
            ville_stats = df_filtered.groupby('ville').agg({
                'prix_m2': ['mean', 'count']
            }).reset_index()
            
            # Aplatir les colonnes multi-index
            ville_stats.columns = ['ville', 'prix_moyen', 'nb_annonces']
            
            # Filtrer les villes avec au moins 50 annonces
            ville_stats_filtered = ville_stats[ville_stats['nb_annonces'] >= 50]
            
            if len(ville_stats_filtered) > 0:
                # Trier par prix moyen décroissant et prendre le top 20
                prix_par_ville = ville_stats_filtered.sort_values('prix_moyen', ascending=False).head(20)
                
                fig_hist = px.bar(
                    x=prix_par_ville['prix_moyen'].values,
                    y=prix_par_ville['ville'],
                    orientation='h',
                    labels={'x': 'Prix au m² (€)', 'y': 'Ville'},
                    title=f"Top 20 des villes par prix au m² moyen",
                    color=prix_par_ville['prix_moyen'].values,
                    color_continuous_scale='Blues',
                    template='plotly_white'
                )
                fig_hist.update_layout(
                    height=500,
                    showlegend=False,
                    font=dict(size=12, family='Arial'),
                    title_font=dict(size=16, family='Arial', color='darkblue'),
                    xaxis_title_font=dict(size=14, family='Arial'),
                    yaxis_title_font=dict(size=14, family='Arial'),
                    margin=dict(l=200, r=20, t=60, b=40)
                )
                fig_hist.update_coloraxes(showscale=False)  # Masquer la légende de couleur pour simplicité
                st.plotly_chart(fig_hist, use_container_width=True)
                
                # Afficher quelques statistiques
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Villes analysées", f"{len(ville_stats_filtered)}")
                with col2:
                    st.metric("Prix moyen max", f"{prix_par_ville['prix_moyen'].max():.0f} €/m²")
                with col3:
                    st.metric("Prix moyen min", f"{prix_par_ville['prix_moyen'].min():.0f} €/m²")
                
                st.info(f"💡 Seules les villes avec au moins 50 annonces sont affichées pour garantir la fiabilité des moyennes.")
            else:
                st.warning("⚠️ Aucune ville n'a suffisamment d'annonces (minimum 50) pour une analyse fiable.")
        
        st.markdown("---")

        # ============================================
        # 2. CARTE DES ANNONCES GÉOLOCALISÉES
        # ============================================
        # st.header("Cartes des annonces géolocalisées")

        if len(df_filtered) > 0:
            # ============================================
            # SOUS-SECTION 1: CARTE CHOROPLÈTHE PAR DÉPARTEMENT
            # ============================================
            st.markdown('<h4 style="color: #2d3748; font-weight: 500; margin-bottom: 1rem;">1️⃣ Prix au m² moyen par département</h4>', unsafe_allow_html=True)

            try:
                import json, requests

                # Charger les données géographiques des départements français
                url_geojson = "https://france-geojson.gregoiredavid.fr/repo/departements.geojson"
                geo_json = requests.get(url_geojson).json()

                # Calculer le prix moyen par département
                dep_mean = df_filtered.groupby("departement")["prix_m2"].mean().reset_index()
                dep_mean["departement"] = dep_mean["departement"].astype(str).str.zfill(2)

                # Créer la carte choroplèthe
                m1 = folium.Map(location=[46.5, 2.5], zoom_start=6)

                folium.Choropleth(
                    geo_data=geo_json,
                    data=dep_mean,
                    columns=["departement", "prix_m2"],
                    key_on="feature.properties.code",
                    fill_color="YlOrRd",
                    fill_opacity=0.8,
                    line_opacity=0.3,
                    legend_name="Prix/m² moyen (€)"
                ).add_to(m1)
 
                # Afficher la carte choroplèthe
                with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as tmp_file:
                    m1.save(tmp_file.name)
                    tmp_file_path = tmp_file.name
 
                with open(tmp_file_path, 'r', encoding='utf-8') as f:
                    map_html = f.read()
                os.unlink(tmp_file_path)
                st_html(map_html, height=600) 
                st.info("💡 Cette carte montre le prix au m² moyen par département. Les couleurs plus foncées indiquent des prix plus élevés.")
 
            except Exception as e:
                st.error(f"❌ Erreur lors de la création de la carte choroplèthe : {e}")
 
            st.markdown("---")
 
            # ============================================
            # SOUS-SECTION 2: CARTE AVEC MARQUEURS EN GRAPPE
            # ============================================
            st.markdown('<h4 style="color: #2d3748; font-weight: 500; margin-bottom: 1rem;">2️⃣ Carte avec clusters de marqueurs</h4>', unsafe_allow_html=True)
 
            # Préparer les données pour les cartes
            df_map = df_filtered.dropna(subset=['latitude', 'longitude']).copy()
            df_map = df_map[(df_map['latitude'] >= 41) & (df_map['latitude'] <= 51) &
                           (df_map['longitude'] >= -5) & (df_map['longitude'] <= 10)]
 
            if len(df_map) > 0:
                # Limiter l'échantillon pour les performances
                max_sample = 10000
                if len(df_map) > max_sample:
                    df_map_sample = df_map.sample(n=max_sample, random_state=42)
                    st.info(f"ℹ️ Affichage de {max_sample} points sur {len(df_map)} annonces (pour raisons de performance).")
                else:
                    df_map_sample = df_map
 
                # Créer la carte avec clusters
                m2 = folium.Map(location=[46.6, 2.5], zoom_start=6)
                cluster = MarkerCluster().add_to(m2)
 
                for _, row in df_map_sample.iterrows():
                    popup_text = f"{row['prix_m2']:.0f} €/m² – {row.get('ville', 'N/A')}"
                    folium.Marker(
                        location=[row['latitude'], row['longitude']],
                        popup=popup_text
                    ).add_to(cluster)
 
                # Afficher la carte avec marqueurs
                with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as tmp_file:
                    m2.save(tmp_file.name)
                    tmp_file_path = tmp_file.name
 
                with open(tmp_file_path, 'r', encoding='utf-8') as f:
                    map_html = f.read()
                os.unlink(tmp_file_path)
                st_html(map_html, height=600)
 
                st.info("💡 Cliquez sur les clusters pour zoomer et voir les annonces individuelles.")
            else:
                st.warning("⚠️ Aucune donnée géolocalisée disponible pour les filtres sélectionnés.")
        else:
            st.warning("⚠️ Aucune donnée disponible pour les filtres sélectionnés.")
        
        st.markdown("---")
        
        # ============================================
        # 3. ÉVOLUTION TEMPORELLE DU PRIX MOYEN
        # ============================================
        st.markdown('<h3 class="sub-header">📈 Évolution temporelle du prix moyen</h3>', unsafe_allow_html=True)

        if 'creationDate' in df_filtered.columns:
            df_temp = df_filtered.dropna(subset=['creationDate', 'prix_m2'])
            if len(df_temp) > 0:
                # Grouper par date (mensuel)
                df_temp['date_month'] = df_temp['creationDate'].dt.to_period('M').dt.to_timestamp()
                evolution = df_temp.groupby('date_month')['prix_m2'].mean().reset_index()

                fig_evolution = px.line(
                    evolution,
                    x='date_month',
                    y='prix_m2',
                    labels={'date_month': 'Date', 'prix_m2': 'Prix au m² moyen (€)'},
                    title="Évolution du prix au m² moyen",
                    markers=True,
                    template='plotly_white'
                )
                fig_evolution.update_traces(
                    line_color='#2563eb',
                    line_width=3,
                    marker=dict(size=8, color='#2563eb', line=dict(width=2, color='white'))
                )
                fig_evolution.update_layout(
                    height=400,
                    font=dict(size=12, family='Arial'),
                    title_font=dict(size=16, family='Arial', color='darkblue'),
                    xaxis_title_font=dict(size=14, family='Arial'),
                    yaxis_title_font=dict(size=14, family='Arial'),
                    margin=dict(l=20, r=20, t=60, b=40),
                    xaxis=dict(showgrid=True, gridcolor='lightgray'),
                    yaxis=dict(showgrid=True, gridcolor='lightgray')
                )
                st.plotly_chart(fig_evolution, use_container_width=True)
            else:
                st.warning("⚠️ Aucune donnée temporelle disponible.")
        else:
            st.info("ℹ️ **Données temporelles non disponibles**")
            st.write("Les données actuelles ne contiennent pas d'informations de date (colonne 'creationDate').")
            st.write("💡 **Suggestion :** Pour analyser l'évolution temporelle, il faudrait ajouter des dates de création ou de mise à jour des annonces.")

            # Alternative : Analyse par source de données
            if 'source' in df_filtered.columns:
                st.markdown("---")
                st.markdown('<h4 style="color: #2d3748; font-weight: 500; margin-bottom: 1rem;">📊 Analyse alternative : Prix moyen par source de données</h4>', unsafe_allow_html=True)

                prix_par_source = df_filtered.groupby('source')['prix_m2'].agg(['mean', 'count']).round(2)
                prix_par_source = prix_par_source.sort_values('mean', ascending=False)

                fig_source = px.bar(
                    prix_par_source,
                    x=prix_par_source.index,
                    y='mean',
                    labels={'mean': 'Prix au m² moyen (€)', 'source': 'Source'},
                    title="Prix au m² moyen par source de données",
                    color='mean',
                    color_continuous_scale='Blues',
                    template='plotly_white'
                )
                fig_source.update_layout(
                    height=400,
                    font=dict(size=12, family='Arial'),
                    title_font=dict(size=16, family='Arial', color='darkblue'),
                    xaxis_title_font=dict(size=14, family='Arial'),
                    yaxis_title_font=dict(size=14, family='Arial'),
                    margin=dict(l=20, r=20, t=60, b=40),
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=True, gridcolor='lightgray')
                )
                fig_source.update_coloraxes(showscale=False)  # Masquer la légende de couleur
                st.plotly_chart(fig_source, use_container_width=True)

                # Tableau des résultats
                st.write("**Détails par source :**")
                prix_par_source_display = prix_par_source.copy()
                prix_par_source_display.columns = ['Prix moyen (€/m²)', 'Nombre d\'annonces']
                st.dataframe(prix_par_source_display)
        
        st.markdown("---")
        
        # ============================================
        # 4. DIAGRAMME DE CORRÉLATION SURFACE/PRIX AU M²
        # ============================================
        st.markdown('<h3 class="sub-header">🔗 Corrélation entre surface et prix au m²</h3>', unsafe_allow_html=True)
        
        if 'surface' in df_filtered.columns and 'prix_m2' in df_filtered.columns:
            # Filtrer les valeurs aberrantes
            df_corr = df_filtered[(df_filtered['surface'] <= 500) & (df_filtered['prix_m2'] <= 25000)]
            
            if len(df_corr) > 0:                
                # Scatter plot avec Plotly - Version simplifiée et professionnelle
                fig_scatter = px.scatter(
                    df_corr,
                    x='surface',
                    y='prix_m2',
                    labels={'surface': 'Surface (m²)', 'prix_m2': 'Prix au m² (€)'},
                    title="Relation entre surface et prix au m²",
                    opacity=0.7,
                    template='plotly_white'
                )
                fig_scatter.update_traces(
                    marker=dict(
                        color='#2563eb',
                        size=6,
                        line=dict(width=1, color='white'),
                        opacity=0.7
                    )
                )
                fig_scatter.update_layout(
                    height=500,
                    font=dict(size=12, family='Arial'),
                    title_font=dict(size=16, family='Arial', color='darkblue'),
                    xaxis_title_font=dict(size=14, family='Arial'),
                    yaxis_title_font=dict(size=14, family='Arial'),
                    margin=dict(l=20, r=20, t=60, b=40),
                    xaxis=dict(showgrid=True, gridcolor='lightgray'),
                    yaxis=dict(showgrid=True, gridcolor='lightgray')
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
                
                # Calculer le coefficient de corrélation entre surface et prix_m2
                correlation = df_corr['surface'].corr(df_corr['prix_m2'])
                st.metric("Coefficient de corrélation", f"{correlation:.3f}")
                
                # Graphiques de distribution - Version simplifiée
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_hist_surface = px.histogram(
                        df_corr,
                        x='surface',
                        nbins=30,
                        labels={'surface': 'Surface (m²)', 'count': 'Nombre d\'annonces'},
                        title="Distribution des surfaces",
                        template='plotly_white',
                        color_discrete_sequence=['#2563eb']
                    )
                    fig_hist_surface.update_layout(
                        height=350,
                        font=dict(size=11, family='Arial'),
                        title_font=dict(size=14, family='Arial', color='darkblue'),
                        margin=dict(l=20, r=20, t=40, b=20),
                        xaxis=dict(showgrid=False),
                        yaxis=dict(showgrid=True, gridcolor='lightgray')
                    )
                    st.plotly_chart(fig_hist_surface, use_container_width=True)
                
                with col2:
                    fig_hist_prix_m2 = px.histogram(
                        df_corr,
                        x='prix_m2',
                        nbins=30,
                        labels={'prix_m2': 'Prix au m² (€)', 'count': 'Nombre d\'annonces'},
                        title="Distribution des prix au m²",
                        template='plotly_white',
                        color_discrete_sequence=['#2563eb']
                    )
                    fig_hist_prix_m2.update_layout(
                        height=350,
                        font=dict(size=11, family='Arial'),
                        title_font=dict(size=14, family='Arial', color='darkblue'),
                        margin=dict(l=20, r=20, t=40, b=20),
                        xaxis=dict(showgrid=False),
                        yaxis=dict(showgrid=True, gridcolor='lightgray')
                    )
                    st.plotly_chart(fig_hist_prix_m2, use_container_width=True)

else:
    st.error("❌ Impossible de charger les données. Vérifiez que le fichier existe dans DATA/Fusion_notaires_seloger/")


