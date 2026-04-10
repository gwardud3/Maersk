import streamlit as st

#from features.zone_map import zone_map_app
from features.warehouse_map import warehouse_map_app
from features.warehouse_sort import warehouse_sort_app
from features.heatmap import heatmap_app

st.set_page_config(
    page_title="Pricing Tools",
    layout="wide"
)

st.title("📊 Pricing Team Tools (for Other Teams)")

menu = st.sidebar.radio(
    "Select a Tool",
    ["Zone Map", "Warehouse Map", "Warehouse Sort", "Heatmap"]
)

if menu == "Zone Map":
    zone_map_app()

elif menu == "Warehouse Map":
    warehouse_map_app()

elif menu == "Warehouse Sort":
    warehouse_sort_app()

elif menu == "Heatmap":
    heatmap_app()

