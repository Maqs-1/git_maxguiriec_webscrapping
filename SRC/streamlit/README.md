# 🏠 Application Streamlit - Analyse Immobilière

Application interactive pour visualiser et analyser les données immobilières collectées depuis SeLoger et Notaires.fr.

## 📋 Fonctionnalités

L'application propose 4 visualisations principales :

1. **📊 Histogramme du prix au m² par ville**
   - Top 20 des villes par prix au m² moyen
   - Graphique en barres horizontal interactif

2. **🗺️ Carte des annonces géolocalisées**
   - Carte interactive avec Folium
   - Clustering automatique des marqueurs
   - Informations détaillées au survol

3. **📈 Évolution temporelle du prix moyen**
   - Graphique linéaire montrant l'évolution du prix au m² dans le temps
   - Groupement par mois

4. **🔗 Diagramme de corrélation surface/prix**
   - Scatter plot interactif
   - Coefficient de corrélation
   - Distributions des surfaces et prix

## 🚀 Installation

1. Installer les dépendances :
```bash
pip install -r requirements_streamlit.txt
```

## ▶️ Lancement

Pour lancer l'application, exécutez :

```bash
streamlit run app_streamlit.py
```

L'application s'ouvrira automatiquement dans votre navigateur à l'adresse `http://localhost:8501`

## 📁 Structure des données

L'application cherche les données dans :
- `DATA/Fusion_notaires_seloger/base_fusionnee.csv` (priorité)
- `DATA/Fusion_notaires_seloger/base_fusionnee.parquet` (si CSV non disponible)

## 🔍 Filtres disponibles

Dans la barre latérale, vous pouvez filtrer les données par :
- **Source** : SeLoger, Notaires, ou Tous
- **Type de bien** : Maison, Appartement, etc.
- **Département** : Sélection d'un département spécifique

## 📊 Colonnes attendues dans les données

- `prix` : Prix du bien (€)
- `surface` : Surface en m²
- `prix_m2` : Prix au m² (€/m²)
- `ville` : Nom de la ville
- `latitude` / `longitude` : Coordonnées GPS
- `creationDate` : Date de création de l'annonce (pour l'évolution temporelle)
- `type_bien` : Type de bien immobilier
- `departement` : Code du département
- `source` : Source des données (seloger/notaires)

## ⚙️ Notes techniques

- L'application utilise le cache Streamlit pour améliorer les performances
- La carte limite l'affichage à 1000 points pour des raisons de performance
- Les données sont automatiquement nettoyées (valeurs nulles, valeurs aberrantes)


