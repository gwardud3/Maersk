from streamlit.components.v1 import html
from folium.plugins import HeatMap
import geopandas as gpd
import streamlit as st
import pandas as pd
import folium as fm
import numpy as np
import branca.colormap as cm


def style_function(feature):
    zip3 = feature["properties"]["ZIP3"]
    
    row = gdf[gdf["ZIP3"] == zip3]

    if row.empty or pd.isna(row["log_volume"].values[0]):
        return {
            "fillColor": "lightgray",   # 👈 missing data
            "color": "black",
            "weight": 0.2,
            "fillOpacity": 0.4
        }

    val = row["log_volume"].values[0]

    return {
        "fillColor": colormap(val),
        "color": "black",
        "weight": 0.2,
        "fillOpacity": 0.7
    }
# ================================
# 📂 LOAD GEOSPATIAL FILES (CACHED)
# ================================
@st.cache_data
def load_zip3_shapes():
    gdf = gpd.read_file("shapefiles/zip3_simplified.gpkg")

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

        with st.form("origin_filter_form"):
            selected_origin = st.selectbox("Filter by Origin", origins)
            apply_filter = st.form_submit_button("Apply Filter")

        # Only update after submit
        if "selected_origin" not in st.session_state:
            st.session_state["selected_origin"] = "All Origins"

        if apply_filter:
            st.session_state["selected_origin"] = selected_origin

        selected_origin = st.session_state["selected_origin"]

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
            progress.progress(20)
    
            # Aggregate to ZIP3
            agg = (
                filtered_data.groupby("Dest3", as_index=False)["Volume"]
                .sum()
            )
            progress.progress(40)
    
            # Merge (KEEP ALL SHAPES)
            gdf = pd.merge(
                zip3_shapes,
                agg,
                left_on="ZIP3",
                right_on="Dest3",
                how="left"
            )
    
            # Clean geometries
            gdf = gdf[
                gdf["GEOMETRY"].notna() &
                (~gdf["GEOMETRY"].is_empty) &
                (gdf["GEOMETRY"].is_valid)
            ]
    
            progress.progress(60)
    
            # Log transform (keep NaN for missing ZIPs)
            gdf["log_volume"] = gdf["Volume"].apply(
                lambda v: np.log10(v) if pd.notnull(v) and v > 0 else None
            )
    
            # Create colormap
            colormap = cm.linear.YlOrRd_09.scale(
                gdf["log_volume"].min(skipna=True),
                gdf["log_volume"].max(skipna=True)
            )
    
            # Faster lookup dict
            zip_to_val = dict(zip(gdf["ZIP3"], gdf["log_volume"]))
    
            # Style function
            def style_function(feature):
                zip3 = feature["properties"]["ZIP3"]
                val = zip_to_val.get(zip3)
    
                if val is None or pd.isna(val):
                    return {
                        "fillColor": "lightgray",
                        "color": "black",
                        "weight": 0.2,
                        "fillOpacity": 0.4
                    }
    
                return {
                    "fillColor": colormap(val),
                    "color": "black",
                    "weight": 0.2,
                    "fillOpacity": 0.7
                }
    
            # Create map
            m = fm.Map(location=[39.5, -98.35], zoom_start=4)
    
            # Add polygons
            fm.GeoJson(
                gdf,
                style_function=style_function,
                tooltip=fm.GeoJsonTooltip(
                    fields=["ZIP3", "Volume"],
                    aliases=["ZIP3:", "Total Volume:"],
                    localize=True
                )
            ).add_to(m)
    
            # Add legend
            colormap.caption = "Log Scaled Volume (ZIP3)"
            colormap.add_to(m)
    
            progress.progress(100)
    
            # Save HTML
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
