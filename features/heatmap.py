from streamlit.components.v1 import html
from folium.plugins import HeatMap
import geopandas as gpd
import streamlit as st
import pandas as pd
import folium as fm
import numpy as np


# ================================
# 📂 LOAD GEOSPATIAL FILES (CACHED)
# ================================
@st.cache_data
def load_zip3_shapes():
    gdf = gpd.read_file("zip3_simplified.gpkg")

    # Normalize column names
    gdf.columns = [c.upper() for c in gdf.columns]

    # 🔥 CRITICAL: Set geometry column
    if "GEOMETRY" in gdf.columns:
        gdf = gdf.set_geometry("GEOMETRY")
    else:
        st.error("No GEOMETRY column found")
        st.write(gdf.columns)
        return None

    # Clean ZIP3
    gdf["ZIP3"] = gdf["ZIP3"].astype(str).str.zfill(3)

    return gdf

@st.cache_data
def load_states():
    try:
        gdf = gpd.read_file("states_preprocessed.gpkg")
        return gdf
    except:
        return None


# ================================
# 📥 LOAD USER DATA
# ================================
def load_heatmap_data():
    uploaded_file = st.file_uploader(
        "Upload your shipment data (.xlsx)",
        type=["xlsx"],
        key="heatmap_upload"
    )

    if uploaded_file is None:
        return None

    try:
        data = pd.read_excel(uploaded_file)

        required_cols = ["DestZip", "Volume"]
        missing = [c for c in required_cols if c not in data.columns]

        if missing:
            st.error(f"Missing required columns: {missing}")
            return None

        data["DestZip"] = data["DestZip"].astype(str).str.zfill(5)
        data["Dest3"] = data["DestZip"].str[:3]

        st.success("File uploaded successfully ✅")
        st.dataframe(data.head())

        return data

    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None


# ================================
# 🗺️ MAIN APP
# ================================
def heatmap_app():

    st.header("Heatmap Tool 🗺️")

    # Load user data
    data = load_heatmap_data()
    if data is None:
        return

    # ================================
    # OPTIONAL ORIGIN FILTER
    # ================================
    if "OriginZip" in data.columns:

        origins = ["All Origins"] + sorted(data["OriginZip"].dropna().unique())

        selected_origin = st.selectbox("Filter by Origin", origins)

        if selected_origin == "All Origins":
            filtered_data = data
        else:
            filtered_data = data[data["OriginZip"] == selected_origin]

    else:
        filtered_data = data

    # ================================
    # HEATMAP BUTTON
    # ================================
    if st.button("Generate Heatmap"):

        with st.spinner("Building heatmap..."):

            progress = st.progress(0)

            # Load geospatial data
            zip3_shapes = load_zip3_shapes()
            states = load_states()

            progress.progress(20)

            # Aggregate to ZIP3
            agg = (
                filtered_data.groupby("Dest3", as_index=False)["Volume"]
                .sum()
            )

            progress.progress(40)

            # Merge with geometry
            gdf = pd.merge(
                agg,
                zip3_shapes,
                left_on="Dest3",
                right_on="ZIP3",
                how="left"
            )

            gdf = gdf.dropna(subset=["GEOMETRY"])

            progress.progress(60)

            # Create map
            m = fm.Map(location=[39.5, -98.35], zoom_start=4)

            # Optional state overlay
            if states is not None:
                fm.GeoJson(
                    states,
                    name="States",
                    style_function=lambda x: {
                        "fillColor": "none",
                        "color": "black",
                        "weight": 1
                    }
                ).add_to(m)

            # Build heat data
            heat_data = []

            for _, row in gdf.iterrows():
                geom = row["geometry"]

                if geom is not None and geom.is_valid:
                    centroid = geom.centroid

                    # Avoid log(0)
                    volume = max(row["Volume"], 1)

                    heat_data.append([
                        centroid.y,
                        centroid.x,
                        np.log(volume)
                    ])

            progress.progress(80)

            # Add heatmap layer
            HeatMap(
                heat_data,
                radius=7,
                blur=2,
                min_opacity=0.1,
                gradient={
                    0.2: "blue",
                    0.4: "cyan",
                    0.6: "lime",
                    0.8: "yellow",
                    1.0: "red"
                }
            ).add_to(m)

            progress.progress(100)

            # Save HTML to session
            st.session_state["heatmap_html"] = m.get_root().render()

        st.success("Heatmap ready!")

    # ================================
    # DISPLAY + DOWNLOAD
    # ================================
    if "heatmap_html" in st.session_state:

        st.components.v1.html(
            st.session_state["heatmap_html"],
            height=900
        )

        filename = st.text_input(
            "Enter file name (without .html):",
            "heatmap"
        )

        if filename:
            st.download_button(
                label="Download HTML",
                data=st.session_state["heatmap_html"],
                file_name=f"{filename}.html",
                mime="text/html"
            )