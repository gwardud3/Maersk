import streamlit as st
from features.zone_map import zone_map_app
from features.warehouse_map import warehouse_map_app

st.set_page_config(page_title="Pricing Map Tools", layout="wide")

st.title("📊 Pricing & Network Mapping Tools")

menu = st.sidebar.radio(
    "Select a Tool",
    ["Zone Map", "Warehouse Map"]
)

if menu == "Zone Map":
    zone_map_app()

elif menu == "Warehouse Map":
    warehouse_map_app()

st.sidebar.markdown("---")
st.sidebar.info("More tools coming soon 🚀")
