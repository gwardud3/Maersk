import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import os
from math import radians, sin, cos, sqrt, atan2

# ---------------- Resource path (repo-root safe) ----------------
def resource_path(relative_path: str) -> str:
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        relative_path
    )

# ---------------- Distance calculation (Haversine) ----------------
def haversine_miles(lat1, lon1, lat2, lon2):
    R = 3958.8  # Earth radius in miles

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1))
        * cos(radians(lat2))
        * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

# ---------------- Load ZIP centroids ----------------
@st.cache_data
def load_zip_centroids():
    df = pd.read_csv(resource_path("zip_centroids.csv"))

    # Normalize column names
    df.columns = df.columns.str.strip().str.lower()

    required_cols = {"zip", "lat", "long"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"ZIP centroid file must contain columns: {required_cols}")

    df["zip"] = df["zip"].astype(str).str.zfill(5)
    return df

# ---------------- Streamlit Feature Entry Point ----------------
def warehouse_map_app():
    st.header("🏭 Warehouse Map")

    # --- Inputs ---
    uploaded_file = st.file_uploader(
        "Upload Warehouse Excel File",
        type=["xlsx"]
    )

    zip_input = st.text_input(
        "Enter a 5-digit ZIP code to find the nearest facilities"
    )

    if uploaded_file is None:
        st.info("Please upload an Excel file with Name, Lat, and Long columns.")
        return

    # --- Load Warehouses ---
    try:
        df = pd.read_excel(uploaded_file)

        # Normalize column names
        df.columns = df.columns.str.strip().str.lower()

        required_cols = {"name", "lat", "long"}
        if not required_cols.issubset(df.columns):
            st.error(f"Warehouse file must contain columns: {required_cols}")
            return

        warehouses = gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(df["long"], df["lat"]),
            crs="EPSG:4326"
        )

    except Exception as e:
        st.error(f"Failed to load warehouse file: {e}")
        return

    st.caption(f"{len(warehouses)} warehouses loaded")

    # --- Find nearest warehouses ---
    nearest = None
    zip_point = None

    if zip_input and zip_input.isdigit() and len(zip_input) == 5:
        try:
            zip_centroids = load_zip_centroids()
            zip_row = zip_centroids[zip_centroids["zip"] == zip_input]

            if zip_row.empty:
                st.warning("ZIP code not found in centroid file.")
            else:
                zip_lat = zip_row.iloc[0]["lat"]
                zip_lon = zip_row.iloc[0]["long"]

                zip_point = gpd.GeoDataFrame(
                    {"zip": [zip_input]},
                    geometry=gpd.points_from_xy([zip_lon], [zip_lat]),
                    crs="EPSG:4326"
                )

                warehouses["distance_miles"] = warehouses.apply(
                    lambda r: haversine_miles(
                        zip_lat,
                        zip_lon,
                        r.geometry.y,
                        r.geometry.x
                    ),
                    axis=1
                )

                nearest = warehouses.nsmallest(2, "distance_miles")

        except Exception as e:
            st.error(f"Error calculating distances: {e}")
            return

    # --- Plot ---
    fig, ax = plt.subplots(figsize=(15, 10))

    # State boundaries for context
    states = gpd.read_file(
        resource_path("shapefiles/states_preprocessed.gpkg"),
        engine="fiona"
    )
    states.boundary.plot(ax=ax, linewidth=0.5, edgecolor="black")

    # Plot all warehouses
    warehouses.plot(
        ax=ax,
        color="gray",
        markersize=40,
        alpha=0.6
    )

    # Highlight nearest warehouses
    if nearest is not None:
        nearest.plot(
            ax=ax,
            color="red",
            markersize=120,
            alpha=1,
            label="Nearest Warehouses"
        )

    # Plot ZIP location
    if zip_point is not None:
        zip_point.plot(
            ax=ax,
            color="blue",
            markersize=150,
            marker="*",
            label="Input ZIP"
        )

    # US extent
    ax.set_xlim(-130, -65)
    ax.set_ylim(24, 50)
    ax.set_aspect("equal", adjustable="box")

    ax.set_title("Warehouse Locations & Nearest Facilities", fontsize=16)
    ax.axis("off")
    plt.tight_layout()

    st.pyplot(fig)

    # --- Results Table ---
    if nearest is not None:
        st.subheader("📍 Closest Warehouses")

        result_df = (
            nearest[["name", "distance_miles"]]
            .assign(distance_miles=lambda d: d["distance_miles"].round(1))
            .rename(columns={"distance_miles": "Distance (miles)"})
            .reset_index(drop=True)
        )

        st.dataframe(result_df)
