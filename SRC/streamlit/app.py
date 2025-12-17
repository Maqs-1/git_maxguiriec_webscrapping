import streamlit as st
from pathlib import Path

# Configuration de la page
st.set_page_config(
    page_title="Analyse Immobilière",
    page_icon="🏠",
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

# Titre principal
st.title("🏠 Analyse du Marché Immobilier Français")
st.markdown("---")

st.markdown("""
### Bienvenue sur l'application d'analyse du marché immobilier français

Cette application vous permet d'explorer et d'analyser les données immobilières collectées depuis 
plusieurs sources (SeLoger, Notaires.fr).

**Navigation :** Utilisez le menu latéral pour accéder aux différentes pages :
- 📊 **Analyse** : Visualisations interactives avec filtres
- 📈 **Résumé des données** : Statistiques et informations sur les données
""")
st.markdown("---")

# Section Projet
st.header("À propos du projet")

st.markdown("""
Ce projet a pour objectif de collecter, analyser et visualiser les données du marché immobilier français 
en agrégeant des informations provenant de plusieurs sources majeures :

- **SeLoger.com** : Annonces immobilières par département
- **Notaires.fr** : Données officielles des notaires

L'application permet d'explorer ces données à travers des visualisations interactives, des cartes 
géolocalisées et des analyses statistiques pour mieux comprendre les tendances du marché immobilier français.
""")

st.markdown("---")

# Section Membres
st.header("Membres de l'équipe")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Max Guiriec")
    st.markdown("""
    - **Rôle** : Développeur / Data Analyst
    - **Contribution** : Développement des scrapers, collecte de données
    """)

with col2:
    st.subheader("Said Mansour")
    st.markdown("""
    - **Rôle** : Développeur / Data Analyst
    - **Contribution** : Développement des scrapers, collecte de données
    """)

st.markdown("---")

# Section Technologies
st.header("Technologies utilisées")

st.markdown("""
- **Python** : Langage de programmation principal
- **Streamlit** : Framework pour l'interface web interactive
- **Pandas** : Manipulation et analyse de données
- **Plotly** : Visualisations interactives
- **Folium** : Cartes géolocalisées
- **Requests** : Web scraping
- **Git LFS** : Gestion des gros fichiers de données
""")

st.markdown("---")

# Section Structure
st.header("Structure du projet")

st.markdown("""
```
git_maxguiriec_webscrapping/
├── DATA/                    # Données collectées
│   ├── Seloger/            # Données SeLoger par département
│   ├── Notaires/           # Données Notaires.fr
│   └── Fusion_notaires_seloger/  # Base fusionnée
├── SRC/
│   ├── scrapper/           # Scripts de scraping
│   ├── Clean/              # Scripts de nettoyage
│   └── streamlit/          # Application Streamlit
└── NOTEBOOKS/              # Analyses exploratoires
```
""")
