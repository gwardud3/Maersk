from streamlit.components.v1 import html
from folium.plugins import HeatMap
import geopandas as gpd
import streamlit as st
import pandas as pd
import folium as fm
import numpy as np
import time


def heatmap_app():

    st.header("Heatmap Tool 🗺️")

    # ================================
    # LOAD USER DATA
    # ================================
    uploaded_file = st.file_uploader(
        "Upload your shipment data (.xlsx)",
        type=["xlsx"],
        key="heatmap_upload"
    )

    if uploaded_file is None:
        return

    try:
        data = pd.read_excel(uploaded_file)

        required_cols = ["DestZip", "Volume"]
        missing = [c for c in required_cols if c not in data.columns]

        if missing:
            st.error(f"Missing required columns: {missing}")
            return

        data["DestZip"] = data["DestZip"].astype(str).str.zfill(5)

        st.success("File uploaded successfully ✅")
        st.dataframe(data.head())

    except Exception as e:
        st.error(f"Error reading file: {e}")
        return

    # ================================
    # OPTIONAL ORIGIN FILTER
    # ================================
    if "OriginZip" in data.columns:

        origins = ["All Origins"] + sorted(data["OriginZip"].dropna().unique())

        selected_origin = st.selectbox(
            "Select Origin",
            origins
        )

        if selected_origin == "All Origins":
            filtered_data = data
        else:
            filtered_data = data[data["OriginZip"] == selected_origin]

    else:
        filtered_data = data

    # ================================
    # HEATMAP BUTTON (CONTROLLED RUN)
    # ================================
    if st.button("Generate Heatmap"):

        with st.spinner("Building heatmap..."):

            progress = st.progress(0)

            # Load shapefile
            df_zips = gpd.read_file("tabs/heatmap_files/USA_ZIP_Code_Boundaries.shp")
            progress.progress(20)

            df_zips["ZIP_CODE"] = (
                df_zips["ZIP_CODE"]
                .astype(str)
                .str.split(".").str[0]
                .str.zfill(5)
            )

            filtered_data["DestZip"] = (
                filtered_data["DestZip"]
                .astype(str)
                .str.split(".").str[0]
                .str.zfill(5)
            )

            progress.progress(40)

            # Filter relevant zips
            zip_list = filtered_data["DestZip"].unique().tolist()
            df_zips = df_zips[df_zips["ZIP_CODE"].isin(zip_list)]

            progress.progress(60)

            # Merge geometry
            gdf = pd.merge(
                filtered_data,
                df_zips,
                left_on="DestZip",
                right_on="ZIP_CODE",
                how="left"
            )

            # Aggregate
            gdf = gdf.groupby("DestZip", as_index=False).agg({
                "Volume": "sum",
                "geometry": "first"
            })

            gdf = gdf.dropna(subset=["geometry"])

            progress.progress(75)

            # Build map
            m = fm.Map(location=[39.5, -98.35], zoom_start=4)

            heat_data = []

            for _, row in gdf.iterrows():
                if row["geometry"].is_valid:
                    centroid = row["geometry"].centroid
                    heat_data.append([
                        centroid.y,
                        centroid.x,
                        np.log(row["Volume"])
                    ])

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

            # Save to session
            st.session_state["heatmap_html"] = m.get_root().render()

        st.success("Heatmap ready!")

    # ================================
    # DISPLAY MAP
    # ================================
    if "heatmap_html" in st.session_state:

        st.components.v1.html(
            st.session_state["heatmap_html"],
            height=900
        )

        filename = st.text_input(
            "Enter file name (without .html):",
            "map"
        )

        if filename:
            st.download_button(
                label="Download HTML",
                data=st.session_state["heatmap_html"],
                file_name=f"{filename}.html",
                mime="text/html"
            )