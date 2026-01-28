import streamlit as st

from features.zone_map import zone_map_app
from features.warehouse_map import warehouse_map_app
from features.placeholder import placeholder_app

st.set_page_config(
    page_title="Pricing Map Tools",
    layout="wide"
)

st.title("📊 Pricing & Network Mapping Tools")

menu = st.sidebar.radio(
    "Select a Tool",
    ["Zone Map", "Warehouse Map", "Placeholder"]
)

if menu == "Zone Map":
    zone_map_app()

elif menu == "Warehouse Map":
    warehouse_map_app()

elif menu == "Placeholder":
    placeholder_app()
