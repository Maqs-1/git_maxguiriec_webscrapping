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
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time

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
</style>
""", unsafe_allow_html=True)

st.title("Analyse Interactive des Données Immobilières")

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
        
        # Filtrer les données invalides
        df = df.dropna(subset=['prix', 'surface', 'prix_m2'])
        df = df[(df['prix'] > 0) & (df['surface'] > 0) & (df['prix_m2'] > 0)]
        
        # Convertir creationDate en datetime si elle existe
        if 'creationDate' in df.columns:
            df['creationDate'] = pd.to_datetime(df['creationDate'], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement des données : {e}")
        return None

# Chargement des données
df = load_data()

if df is not None:
    # ============================================
    # FILTRES ET MÉTRIQUES DANS LA PAGE
    # ============================================
    # # Deuxième ligne : Filtres principaux
    st.subheader("Filtres de recherche")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Filtre par source
        sources = ['Tous'] + list(df['source'].unique()) if 'source' in df.columns else ['Tous']
        selected_source = st.selectbox("Source", sources)
    
    with col2:
        # Filtre par type de bien
        if 'type_bien' in df.columns:
            types_bien = ['Tous'] + list(df['type_bien'].dropna().unique())
            selected_type = st.selectbox("Type de bien", types_bien)
        else:
            selected_type = 'Tous'
    
    with col3:
        # Filtre par ville
        if 'ville' in df.columns:
            villes = ['Toutes'] + sorted([str(v) for v in df['ville'].dropna().unique() if pd.notna(v)])
            selected_ville = st.selectbox("Ville", villes[:100])  # Limiter à 100 pour les performances
        else:
            selected_ville = 'Toutes'
    
    with col4:
        # Filtre par département
        if 'departement' in df.columns:
            departements = ['Tous'] + sorted([str(d) for d in df['departement'].dropna().unique()])
            selected_dept = st.selectbox("Département", departements)
        else:
            selected_dept = 'Tous'
    
    # Troisième ligne : Filtres numériques
    col1, col2, col3 = st.columns(3)
    
    with col1:
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
    
    with col2:
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
    
    with col3:
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
        df_filtered = df_filtered[df_filtered['type_bien'] == selected_type]
    if selected_ville != 'Toutes':
        df_filtered = df_filtered[df_filtered['ville'] == selected_ville]
    if selected_dept != 'Tous':
        df_filtered = df_filtered[df_filtered['departement'] == str(selected_dept)]
    if surface_range:
        df_filtered = df_filtered[(df_filtered['surface'] >= surface_range[0]) & (df_filtered['surface'] <= surface_range[1])]
    if prix_range:
        df_filtered = df_filtered[(df_filtered['prix'] >= prix_range[0]) & (df_filtered['prix'] <= prix_range[1])]
    if selected_pieces != 'Tous':
        df_filtered = df_filtered[df_filtered['nb_pieces'] == int(selected_pieces)]
    
    # Métriques après filtrage
    st.markdown("---")
    st.subheader("Résultats après filtrage")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Nombre d'annonces", f"{len(df_filtered):,}")
    
    with col2:
        if len(df_filtered) > 0:
            st.metric("Prix moyen", f"{df_filtered['prix'].mean():,.0f} €")
        else:
            st.metric("Prix moyen", "N/A")
    
    with col3:
        if len(df_filtered) > 0:
            st.metric("Prix/m² moyen", f"{df_filtered['prix_m2'].mean():,.0f} €/m²")
        else:
            st.metric("Prix/m² moyen", "N/A")
    
    with col4:
        if len(df_filtered) > 0:
            st.metric("Surface moyenne", f"{df_filtered['surface'].mean():.1f} m²")
        else:
            st.metric("Surface moyenne", "N/A")
    
    st.markdown("---")
    
    if len(df_filtered) == 0:
        st.warning("⚠️ Aucune donnée ne correspond aux filtres sélectionnés.")
    else:
        # ============================================
        # 1. HISTOGRAMME DU PRIX AU M² PAR VILLE
        # ============================================
        st.header("Prix au m² par ville")
        
        if 'ville' in df_filtered.columns and 'prix_m2' in df_filtered.columns:
            # Calculer le prix moyen par ville (top 20)
            prix_par_ville = df_filtered.groupby('ville')['prix_m2'].mean().sort_values(ascending=False).head(20)
            
            fig_hist = px.bar(
                x=prix_par_ville.values,
                y=prix_par_ville.index,
                orientation='h',
                labels={'x': 'Prix au m² (€)', 'y': 'Ville'},
                title="Top 20 des villes par prix au m² moyen",
                color=prix_par_ville.values,
                color_continuous_scale='viridis'
            )
            fig_hist.update_layout(height=600, showlegend=False)
            st.plotly_chart(fig_hist, use_container_width=True)
        
        st.markdown("---")
        
        # ============================================
        # 2. CARTE DES ANNONCES GÉOLOCALISÉES
        # ============================================
        st.header("Carte des annonces géolocalisées")
        
        @st.cache_data
        def geocode_address(ville, cp):
            """Géocode une adresse (ville + code postal) avec cache Streamlit"""
            try:
                geolocator = Nominatim(user_agent="streamlit_immobilier_app", timeout=10)
                # Essayer d'abord avec code postal + ville
                address = f"{cp}, {ville}, France"
                location = geolocator.geocode(address, country_codes='fr')
                
                if location:
                    # Vérifier que les coordonnées sont en France
                    lat, lon = location.latitude, location.longitude
                    if 41.0 <= lat <= 51.5 and -5.0 <= lon <= 10.0:
                        time.sleep(1)  # Respecter les limites de l'API Nominatim (1 req/sec)
                        return (lat, lon)
                
                # Si échec, essayer juste avec le code postal
                if cp and len(str(cp)) == 5:
                    address2 = f"{cp}, France"
                    location2 = geolocator.geocode(address2, country_codes='fr')
                    if location2:
                        lat, lon = location2.latitude, location2.longitude
                        if 41.0 <= lat <= 51.5 and -5.0 <= lon <= 10.0:
                            time.sleep(1)
                            return (lat, lon)
                
                return None
            except (GeocoderTimedOut, GeocoderServiceError, Exception):
                return None
        
        # Préparer les données pour la carte
        df_map = df_filtered.copy()
        
        # Utiliser les coordonnées GPS si disponibles, sinon géocoder les adresses
        if 'latitude' in df_map.columns and 'longitude' in df_map.columns:
            # Filtrer les données avec coordonnées GPS valides
            df_map_gps = df_map.dropna(subset=['latitude', 'longitude'])
            df_map_gps = df_map_gps[(df_map_gps['latitude'] >= 41) & (df_map_gps['latitude'] <= 51) & 
                                   (df_map_gps['longitude'] >= -5) & (df_map_gps['longitude'] <= 10)]
        else:
            df_map_gps = pd.DataFrame()
        
        # Pour les données sans GPS, utiliser les adresses (ville + cp)
        if 'ville' in df_map.columns and 'cp' in df_map.columns:
            df_map_no_gps = df_map[(df_map['latitude'].isna() | df_map['longitude'].isna()) if 'latitude' in df_map.columns else True]
            df_map_no_gps = df_map_no_gps.dropna(subset=['ville', 'cp'])
            
            if len(df_map_no_gps) > 0:
                # Géocoder un échantillon limité pour éviter les timeouts (max 50 pour la première fois)
                sample_size = min(len(df_map_no_gps), 50)
                df_map_no_gps_sample = df_map_no_gps.head(sample_size).copy()
                
                st.info(f"Géocodage de {sample_size} adresses... (cela peut prendre {sample_size} secondes)")
                
                # Géocoder les adresses avec cache
                coordinates = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for idx, (i, row) in enumerate(df_map_no_gps_sample.iterrows()):
                    coords = geocode_address(str(row['ville']), str(row['cp']))
                    coordinates.append(coords)
                    progress = (idx + 1) / sample_size
                    progress_bar.progress(progress)
                    status_text.text(f"Géocodage {idx + 1}/{sample_size}: {row['ville']} {row['cp']}")
                
                # Ajouter les coordonnées géocodées
                df_map_no_gps_sample['latitude'] = [c[0] if c else None for c in coordinates]
                df_map_no_gps_sample['longitude'] = [c[1] if c else None for c in coordinates]
                
                # Filtrer les résultats valides
                df_map_no_gps_sample = df_map_no_gps_sample.dropna(subset=['latitude', 'longitude'])
                df_map_no_gps_sample = df_map_no_gps_sample[
                    (df_map_no_gps_sample['latitude'] >= 41) & (df_map_no_gps_sample['latitude'] <= 51) & 
                    (df_map_no_gps_sample['longitude'] >= -5) & (df_map_no_gps_sample['longitude'] <= 10)
                ]
                
                progress_bar.empty()
                status_text.empty()
                
                # Combiner avec les données GPS
                if len(df_map_gps) > 0:
                    df_map = pd.concat([df_map_gps, df_map_no_gps_sample], ignore_index=True)
                else:
                    df_map = df_map_no_gps_sample
                
                if len(df_map_no_gps_sample) > 0:
                    st.success(f"✅ {len(df_map_no_gps_sample)} adresses géocodées avec succès !")
            else:
                df_map = df_map_gps
        else:
            df_map = df_map_gps
        
        if len(df_map) > 0:
                # Créer la carte centrée sur la France avec limites géographiques
                # Coordonnées de la France métropolitaine
                france_bounds = [[41.0, -5.0], [51.5, 10.0]]
                
                m = folium.Map(
                    location=[46.6034, 2.2137],  # Centre de la France
                    zoom_start=6,
                    tiles='CartoDB positron',  # Style plus clair et professionnel
                    min_zoom=5,
                    max_bounds=True  # Limiter la vue à la France
                )
                
                # Ajouter des limites pour forcer la vue sur la France
                m.fit_bounds(france_bounds)
                
                # Limiter le nombre de points pour les performances
                max_points = 1000
                if len(df_map) > max_points:
                    df_map_sample = df_map.sample(n=max_points, random_state=42)
                    st.info(f"ℹ️ Affichage de {max_points} points sur {len(df_map)} annonces pour des raisons de performance.")
                else:
                    df_map_sample = df_map
                    
                # Créer un cluster de marqueurs avec style personnalisé
                marker_cluster = MarkerCluster(
                    name='Annonces immobilières',
                    overlay=True,
                    control=True
                ).add_to(m)
                
                # Définir des couleurs selon le prix au m²
                def get_color(prix_m2):
                    """Retourne une couleur selon le prix au m²"""
                    if prix_m2 < 2000:
                        return 'green'
                    elif prix_m2 < 4000:
                        return 'blue'
                    elif prix_m2 < 6000:
                        return 'orange'
                    else:
                        return 'red'
                
                # Ajouter les marqueurs avec couleurs personnalisées
                for idx, row in df_map_sample.iterrows():
                    popup_text = f"""
                <div style="font-family: Arial; min-width: 200px;">
                    <h4 style="margin: 5px 0; color: #1f77b4;">Annonce Immobilière</h4>
                    <hr style="margin: 5px 0;">
                    <p style="margin: 3px 0;"><b>Prix:</b> {row['prix']:,.0f} €</p>
                    <p style="margin: 3px 0;"><b>Surface:</b> {row['surface']:.0f} m²</p>
                    <p style="margin: 3px 0;"><b>Prix/m²:</b> {row['prix_m2']:.0f} €/m²</p>
                    """
                    if 'ville' in row and pd.notna(row['ville']):
                        popup_text += f'<p style="margin: 3px 0;"><b>Ville:</b> {row["ville"]}</p>'
                    if 'cp' in row and pd.notna(row['cp']):
                        popup_text += f'<p style="margin: 3px 0;"><b>Code postal:</b> {row["cp"]}</p>'
                    if 'type_bien' in row and pd.notna(row['type_bien']):
                        popup_text += f'<p style="margin: 3px 0;"><b>Type:</b> {row["type_bien"]}</p>'
                    if 'nb_pieces' in row and pd.notna(row['nb_pieces']):
                        popup_text += f'<p style="margin: 3px 0;"><b>Pièces:</b> {row["nb_pieces"]}</p>'
                    popup_text += "</div>"
                    
                    # Créer l'adresse complète pour le tooltip
                    address = f"{row.get('ville', '')} {row.get('cp', '')}".strip()
                    tooltip_text = f"{row['prix']:,.0f} € - {row['surface']:.0f} m² ({row['prix_m2']:.0f} €/m²)"
                    if address:
                        tooltip_text += f" - {address}"
                    
                    # Couleur selon le prix au m²
                    color = get_color(row['prix_m2'])
                    
                    folium.CircleMarker(
                        location=[row['latitude'], row['longitude']],
                        radius=6,
                        popup=folium.Popup(popup_text, max_width=250),
                        tooltip=tooltip_text,
                        color='white',
                        weight=1,
                        fill=True,
                        fillColor=color,
                        fillOpacity=0.7
                    ).add_to(marker_cluster)
                    
                # Ajouter un contrôle de couches pour changer le style de carte
                folium.TileLayer('OpenStreetMap').add_to(m)
                folium.TileLayer('CartoDB positron').add_to(m)
                folium.TileLayer('CartoDB dark_matter').add_to(m)
                folium.LayerControl().add_to(m)
                
                # Ajouter une légende pour les couleurs
                legend_html = '''
                <div style="position: fixed; 
                            bottom: 50px; right: 50px; width: 150px; height: 120px; 
                            background-color: white; border:2px solid grey; z-index:9999; 
                            font-size:14px; padding: 10px">
                <p style="margin: 0 0 5px 0;"><b>Prix au m²</b></p>
                <p style="margin: 2px 0;"><i class="fa fa-circle" style="color:green"></i> &lt; 2000 €</p>
                <p style="margin: 2px 0;"><i class="fa fa-circle" style="color:blue"></i> 2000-4000 €</p>
                <p style="margin: 2px 0;"><i class="fa fa-circle" style="color:orange"></i> 4000-6000 €</p>
                <p style="margin: 2px 0;"><i class="fa fa-circle" style="color:red"></i> &gt; 6000 €</p>
                </div>
                '''
                m.get_root().html.add_child(folium.Element(legend_html))
                
                # Afficher la carte
                with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as tmp_file:
                    m.save(tmp_file.name)
                    tmp_file_path = tmp_file.name
                
                with open(tmp_file_path, 'r', encoding='utf-8') as f:
                    map_html = f.read()
                os.unlink(tmp_file_path)
                st_html(map_html, height=600)
        else:
            st.warning("⚠️ Aucune donnée géolocalisée disponible pour les filtres sélectionnés.")
        st.info("💡 La carte utilise les coordonnées GPS si disponibles, sinon elle géocode les adresses (ville + code postal).")
        
        st.markdown("---")
        
        # ============================================
        # 3. ÉVOLUTION TEMPORELLE DU PRIX MOYEN
        # ============================================
        st.header("Évolution temporelle du prix moyen")
        
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
                    title="Évolution du prix au m² moyen dans le temps",
                    markers=True
                )
                fig_evolution.update_traces(line_color='#1f77b4', line_width=3)
                fig_evolution.update_layout(height=400)
                st.plotly_chart(fig_evolution, use_container_width=True)
            else:
                st.warning("⚠️ Aucune donnée temporelle disponible.")
        else:
            st.info("ℹ️ Colonne 'creationDate' non disponible. L'évolution temporelle ne peut pas être affichée.")
        
        st.markdown("---")
        
        # ============================================
        # 4. DIAGRAMME DE CORRÉLATION SURFACE/PRIX
        # ============================================
        st.header("🔗 Corrélation entre surface et prix")
        
        if 'surface' in df_filtered.columns and 'prix' in df_filtered.columns:
            # Filtrer les valeurs aberrantes
            df_corr = df_filtered[(df_filtered['surface'] <= 500) & (df_filtered['prix'] <= 5000000)]
            
            if len(df_corr) > 0:
                # Scatter plot avec Plotly
                fig_scatter = px.scatter(
                    df_corr,
                    x='surface',
                    y='prix',
                    color='prix_m2',
                    size='prix',
                    hover_data=['ville', 'type_bien'] if 'ville' in df_corr.columns else [],
                    labels={'surface': 'Surface (m²)', 'prix': 'Prix (€)', 'prix_m2': 'Prix/m² (€)'},
                    title="Relation entre surface et prix",
                    color_continuous_scale='viridis',
                    opacity=0.6
                )
                fig_scatter.update_layout(height=600)
                st.plotly_chart(fig_scatter, use_container_width=True)
                
                # Calculer le coefficient de corrélation
                correlation = df_corr['surface'].corr(df_corr['prix'])
                st.metric("Coefficient de corrélation", f"{correlation:.3f}")
                
                # Graphiques de distribution
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_hist_surface = px.histogram(
                        df_corr,
                        x='surface',
                        nbins=50,
                        labels={'surface': 'Surface (m²)', 'count': 'Nombre d\'annonces'},
                        title="Distribution des surfaces"
                    )
                    st.plotly_chart(fig_hist_surface, use_container_width=True)
                
                with col2:
                    fig_hist_prix = px.histogram(
                        df_corr,
                        x='prix',
                        nbins=50,
                        labels={'prix': 'Prix (€)', 'count': 'Nombre d\'annonces'},
                        title="Distribution des prix"
                    )
                    st.plotly_chart(fig_hist_prix, use_container_width=True)

else:
    st.error("❌ Impossible de charger les données. Vérifiez que le fichier existe dans DATA/Fusion_notaires_seloger/")


