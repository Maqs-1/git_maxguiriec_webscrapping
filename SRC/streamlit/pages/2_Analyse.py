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
</style>
""", unsafe_allow_html=True)

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
        
        # Ajouter la colonne des types de biens regroupés
        df['type_bien_categorie'] = df['type_bien'].apply(categorize_property_type)
        
        # Ajouter les coordonnées GPS si elles ne sont pas présentes
        if 'latitude' not in df.columns or df['latitude'].isna().all():
            df = add_geolocation_data(df)
        
        return df
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement des données : {e}")
        return None

@st.cache_data
def add_geolocation_data(df):
    """Ajoute les coordonnées GPS aux données en utilisant un fichier de codes postaux"""
    try:
        # Charger le fichier des codes postaux
        geo_path = DATA_PATH.parent.parent / "base-officielle-codes-postaux.csv"
        
        if not geo_path.exists():
            st.warning("⚠️ Fichier de géolocalisation non trouvé. Les cartes ne pourront pas s'afficher.")
            return df
        
        # Charger et préparer les données géographiques
        geo = pd.read_csv(geo_path, sep=",", engine="python")
        
        # Normaliser les noms de colonnes selon le format du fichier
        if 'nom_de_la_commune' in geo.columns:
            geo["ville_clean"] = (
                geo["nom_de_la_commune"]
                .astype(str)
                .str.lower()
                .apply(lambda x: ''.join(c for c in x if c.isalnum() or c.isspace()))
            )
        else:
            # Essayer d'autres noms de colonnes possibles
            ville_col = None
            for col in geo.columns:
                if 'ville' in col.lower() or 'commune' in col.lower() or 'nom' in col.lower():
                    ville_col = col
                    break
            if ville_col:
                geo["ville_clean"] = (
                    geo[ville_col]
                    .astype(str)
                    .str.lower()
                    .apply(lambda x: ''.join(c for c in x if c.isalnum() or c.isspace()))
                )
        
        # Préparer les codes postaux
        cp_col = None
        for col in geo.columns:
            if 'code_postal' in col.lower() or 'cp' in col.lower():
                cp_col = col
                break
        
        if cp_col:
            geo["cp"] = geo[cp_col].astype(str).str.zfill(5)
            geo_clean = geo[["ville_clean", "cp", "latitude", "longitude"]].drop_duplicates()
        else:
            st.warning("⚠️ Colonnes de codes postaux non trouvées dans le fichier géographique.")
            return df
        
        # Préparer les données immobilières pour la fusion
        df['ville_clean'] = (
            df['ville']
            .astype(str)
            .str.lower()
            .apply(lambda x: ''.join(c for c in x if c.isalnum() or c.isspace()))
        )
        
        if 'cp' in df.columns:
            df['cp'] = df['cp'].astype(str).str.zfill(5)
        else:
            df['cp'] = None
        
        # Fusionner avec les données géographiques
        df_geo_merged = df.merge(
            geo_clean,
            how="left",
            left_on=["ville_clean", "cp"],
            right_on=["ville_clean", "cp"]
        )
        
        # Nettoyer les colonnes de coordonnées
        if 'latitude_y' in df_geo_merged.columns:
            df_geo_merged = df_geo_merged.rename(columns={
                "latitude_y": "latitude",
                "longitude_y": "longitude"
            })
            # Supprimer les colonnes dupliquées
            cols_to_drop = [col for col in df_geo_merged.columns if col.endswith('_x') or col.endswith('_y')]
            df_geo_merged = df_geo_merged.drop(columns=cols_to_drop)
        
        st.info(f"✅ Géolocalisation ajoutée : {df_geo_merged[['latitude', 'longitude']].notna().all(axis=1).sum()} annonces géolocalisées sur {len(df_geo_merged)}")
        
        return df_geo_merged
        
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
        st.header("🔍 Filtres de recherche")
        
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
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Filtre par ville
            if 'ville' in df.columns:
                villes = ['Toutes'] + sorted([str(v) for v in df['ville'].dropna().unique() if pd.notna(v)])
                selected_ville = st.selectbox("Ville", villes[:100])  # Limiter à 100 pour les performances
            else:
                selected_ville = 'Toutes'
        
        with col2:
            # Filtre par département
            if 'departement' in df.columns:
                departements = ['Tous'] + sorted([str(d) for d in df['departement'].dropna().unique()])
                selected_dept = st.selectbox("Département", departements)
            else:
                selected_dept = 'Tous'
        
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
        df_filtered = df_filtered[df_filtered['departement'] == str(selected_dept)]
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
    
    # Métriques après filtrage
    st.subheader("📊 Résultats après filtrage")
    
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
                    title=f"Top 20 des villes par prix au m² moyen (min. 50 annonces)",
                    color=prix_par_ville['prix_moyen'].values,
                    color_continuous_scale='viridis'
                )
                fig_hist.update_layout(height=600, showlegend=False)
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
        st.header("Cartes des annonces géolocalisées")

        if len(df_filtered) > 0:
            # ============================================
            # SOUS-SECTION 1: CARTE CHOROPLÈTHE PAR DÉPARTEMENT
            # ============================================
            st.subheader("1️⃣ Prix au m² moyen par département")

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
            st.subheader("2️⃣ Carte avec clusters de marqueurs")

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
            st.info("ℹ️ **Données temporelles non disponibles**")
            st.write("Les données actuelles ne contiennent pas d'informations de date (colonne 'creationDate').")
            st.write("💡 **Suggestion :** Pour analyser l'évolution temporelle, il faudrait ajouter des dates de création ou de mise à jour des annonces.")

            # Alternative : Analyse par source de données
            if 'source' in df_filtered.columns:
                st.markdown("---")
                st.subheader("📊 Analyse alternative : Prix moyen par source de données")

                prix_par_source = df_filtered.groupby('source')['prix_m2'].agg(['mean', 'count']).round(2)
                prix_par_source = prix_par_source.sort_values('mean', ascending=False)

                fig_source = px.bar(
                    prix_par_source,
                    x=prix_par_source.index,
                    y='mean',
                    labels={'mean': 'Prix au m² moyen (€)', 'source': 'Source'},
                    title="Prix au m² moyen par source de données",
                    color='mean',
                    color_continuous_scale='viridis'
                )
                fig_source.update_layout(height=400)
                st.plotly_chart(fig_source, use_container_width=True)

                # Tableau des résultats
                st.write("**Détails par source :**")
                prix_par_source_display = prix_par_source.copy()
                prix_par_source_display.columns = ['Prix moyen (€/m²)', 'Nombre d\'annonces']
                st.dataframe(prix_par_source_display)
        
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
                    hover_data=['ville', 'type_bien_categorie'] if 'ville' in df_corr.columns else ['type_bien_categorie'],
                    labels={'surface': 'Surface (m²)', 'prix': 'Prix (€)', 'prix_m2': 'Prix/m² (€)'},
                    title="Relation entre surface et prix",
                    color_continuous_scale='viridis',
                    range_color=[0, 250000],  # Limiter l'échelle de couleur à 250k €/m² pour une meilleure différenciation
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


