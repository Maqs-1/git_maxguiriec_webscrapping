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
- 📋 **Présentation** : Informations sur le projet et les membres
- 📊 **Analyse** : Visualisations interactives avec filtres
- 📈 **Résumé des données** : Statistiques et informations sur les données
""")
