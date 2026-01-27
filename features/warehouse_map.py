import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import os

# ---------------- Resource path (repo-root safe) ----------------
def resource_path(relative_path: str) -> str:
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        relative_path
    )

# ---------------- Load warehouses ----------------
@st.cache_data
def load_warehouses():
    df = pd.read_excel(resource_path("MaerskWarehouses.xlsx"))

    # Basic validation
    required_cols = {"Warehouse", "Lat", "Long"}
    if not required_cols.issubset(df.columns):
        raise ValueError(
            f"Excel file must contain columns: {required_cols}"
        )

    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["Long"], df["Lat"]),
        crs="EPSG:4326"
    )

    return gdf

# ---------------- Streamlit Feature Entry Point ----------------
def warehouse_map_app():
    st.header("🏭 Warehouse Map")

    try:
        warehouses = load_warehouses()
    except Exception as e:
        st.error(f"Failed to load warehouse file: {e}")
        return

    st.caption(f"{len(warehouses)} warehouses loaded")

    fig, ax = plt.subplots(figsize=(15, 10))

    # Load state boundaries for context
    states = gpd.read_file(
        resource_path("shapefiles/states_preprocessed.gpkg"),
        engine="fiona"
    )
    states.boundary.plot(ax=ax, linewidth=0.5, edgecolor="black")

    # Plot warehouse points
    warehouses.plot(
        ax=ax,
        color="red",
        markersize=50,
        alpha=0.8
    )

    # Label warehouses
    for _, row in warehouses.iterrows():
        ax.text(
            row.geometry.x,
            row.geometry.y,
            row["Warehouse"],
            fontsize=8,
            ha="left",
            va="bottom"
        )

    # Focus on continental US
    ax.set_xlim(-130, -65)
    ax.set_ylim(24, 50)
    ax.set_aspect("equal", adjustable="box")

    ax.set_title("Warehouse Locations", fontsize=16)
    ax.axis("off")
    plt.tight_layout()

    st.pyplot(fig)
