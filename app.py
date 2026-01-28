import streamlit as st

from features.zone_map import zone_map_app
from features.warehouse_map import warehouse_map_app
from features.prioritization_board import prioritization_board_app
from features.daily_meme import daily_meme_app

st.set_page_config(
    page_title="Pricing Map Tools",
    layout="wide"
)

st.title("📊 Pricing Team Tools for Sales")

menu = st.sidebar.radio(
    "Select a Tool",
    ["Zone Map", "Warehouse Map", "Prioritization Board", "Daily Meme"]
)

if menu == "Zone Map":
    zone_map_app()

elif menu == "Warehouse Map":
    warehouse_map_app()

elif menu == "Prioritization Board":
    prioritization_board_app()

elif menu == "Daily Meme":
    daily_meme_app()
