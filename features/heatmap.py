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
        "Upload your shipment data (.xlsx) -- PLD Data Columns can include: OriginZip, DestZip, Weight, Length, Width, Height, Volume",
        type=["xlsx"],
        key="heatmap_upload"
    )

    if uploaded_file is None:
        return None

    try:
        data = pd.read_excel(uploaded_file)
        data.columns = [c.strip().lower() for c in data.columns]

        required_cols = ["destzip", "volume"]
        missing = [c for c in required_cols if c not in data.columns]

        if missing:
            st.error(f"Missing required columns: {missing}")
            return None

        data["volume"] = pd.to_numeric(data["volume"], errors="coerce").fillna(1)

        data["destzip"] = data["destzip"].astype(str).str.zfill(5)
        data["dest3"] = data["destzip"].str[:3]

        st.subheader("📊 Data Summary")
        
        # ================================
        # 🧮 PREP DATA
        # ================================
        
        # Ensure proper formatting
        if "originzip" in data.columns:
            data["originzip"] = data["originzip"].astype(str).str.zfill(5)
        
        # ================================
        # 📊 KPI METRICS (with charts)
        # ================================
        
        col1, col2, col3 = st.columns(3)
        
        # -------------------------------
        # 📦 Total Volume (trend or distribution)
        # -------------------------------
        with col1:
            st.subheader("Total Volume")
        
            if "volume" in data.columns:
                vol_series = pd.to_numeric(data["volume"], errors="coerce")
        
                st.line_chart(vol_series)  # 👈 simple trend
                st.caption(f"Total: {vol_series.sum():,.0f}")
            else:
                st.write("N/A")
        
        # -------------------------------
        # ⚖️ Weight Distribution
        # -------------------------------
        with col2:
            st.subheader("Weight Distribution")
        
            weight_col = None
            if "weight" in data.columns:
                weight_col = "weight"
            elif "actualwt" in data.columns:
                weight_col = "actualwt"
        
            if weight_col:
                weights = pd.to_numeric(data[weight_col], errors="coerce").dropna()
        
                # Define bins and labels
                bins = [-float("inf"), 1, 5, 10, 20, 30, float("inf")]
                labels = ["<1 lb", "1–5", "6–10", "11–20", "21–30", "31+"]
        
                weight_buckets = pd.cut(weights, bins=bins, labels=labels, right=True)

                weight_buckets = weight_buckets.astype(
                    pd.CategoricalDtype(categories=labels, ordered=True)
                )
        
                bucket_counts = weight_buckets.value_counts().reindex(labels)
        
                st.bar_chart(bucket_counts)
        
                st.caption(f"Total Shipments: {int(bucket_counts.sum()):,}")
            else:
                st.write("N/A")
        
        # -------------------------------
        # 📐 Dimension Distribution
        # -------------------------------
        with col3:
            st.subheader("Top Dimensions")
        
            if all(col in data.columns for col in ["length", "width", "height"]):
                dims = data[["length", "width", "height"]].copy()
        
                for col in ["length", "width", "height"]:
                    dims[col] = pd.to_numeric(dims[col], errors="coerce")
        
                dims = dims.dropna()
        
                if not dims.empty:
                    dims["dim_str"] = (
                        dims["length"].astype(int).astype(str) + "x" +
                        dims["width"].astype(int).astype(str) + "x" +
                        dims["height"].astype(int).astype(str)
                    )
        
                    dim_counts = dims["dim_str"].value_counts()
        
                    # Top 5 (already sorted descending)
                    top5 = dim_counts.head(5)
        
                    # Everything else
                    other_sum = dim_counts.iloc[5:].sum()
        
                    # 👇 Build final series in correct order
                    if other_sum > 0:
                        final_dims = pd.concat([
                            top5,
                            pd.Series({"Other": other_sum})
                        ])
                    else:
                        final_dims = top5
        
                    st.bar_chart(final_dims)
        
                    st.caption(f"Most common: {top5.index[0]}")
                else:
                    st.write("No valid dimensions")
            else:
                st.write("N/A")
        
        # ================================
        # 📦 VOLUME BY ORIGIN (TOP 5 + OTHER)
        # ================================
        
        if "OriginZip" in data.columns:
        
            vol_by_origin = (
                data.groupby("originzip")["volume"]
                .sum()
                .reset_index()
                .sort_values(by="volume", ascending=False)
            )
        
            total_volume = vol_by_origin["volume"].sum()
        
            # Top 5
            top5 = vol_by_origin.head(5).copy()
        
            # Remaining = "Other"
            if len(vol_by_origin) > 5:
                other_volume = vol_by_origin.iloc[5:]["volume"].sum()
        
                other_row = pd.DataFrame({
                    "originzip": ["Other"],
                    "volume": [other_volume]
                })
        
                final_df = pd.concat([top5, other_row], ignore_index=True)
            else:
                final_df = top5

            # Sort so "Other" stays at bottom naturally
            final_df = final_df.sort_values(
                by="Volume",
                ascending=False
            ).reset_index(drop=True)
            
            # Calculate %
            final_df["Volume %"] = (final_df["volume"] / total_volume) * 100
        
            # Format
            final_df["Volume %"] = final_df["Volume %"].map(lambda x: f"{x:.1f}%")
            final_df["Volume"] = final_df["volume"].map(lambda x: f"{x:,.0f}")
        
            # Display
            st.markdown("### 📍 Volume by Origin (Top 5 + Other)")
            st.dataframe(final_df, use_container_width=True)

        return data

    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None


# ================================
# 🗺️ MAIN APP
# ================================
def heatmap_app():

    st.header("Data Summary and Heatmap Tool 🗺️")
    st.caption("PLD Data Columns can include: OriginZip, DestZip, Weight, Length, Width, Height, Volume")

    # Load user data
    data = load_heatmap_data()
    if data is None:
        return

    # ================================
    # OPTIONAL ORIGIN FILTER
    # ================================
    if "originzip" in data.columns:

        origins = ["All Origins"] + sorted(data["originzip"].dropna().unique())

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
            filtered_data = data[data["originzip"] == selected_origin]

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
                filtered_data.groupby("dest3", as_index=False)["volume"]
                .sum()
            )

            progress.progress(40)

            # Merge with geometry
            gdf = pd.merge(
                agg,
                zip3_shapes,
                left_on="dest3",
                right_on="ZIP3",
                how="left"
            )

            gdf = gdf.dropna(subset=["GEOMETRY"])

            progress.progress(60)
            
            gdf["log_volume"] = gdf["volume"].apply(lambda v: np.log10(max(v, 1)))
            # Create map
            m = fm.Map(location=[39.5, -98.35], zoom_start=4)

            # Normalize (0–1 scale)
            min_val = gdf["log_volume"].min()
            max_val = gdf["log_volume"].max()
            
            if max_val == min_val:
                gdf["log_volume_norm"] = 1
            else:
                gdf["log_volume_norm"] = (gdf["log_volume"] - min_val) / (max_val - min_val)
                
            # Build heat data
            heat_data = []
            
            for _, row in gdf.iterrows():
                geom = row["GEOMETRY"]
            
                if geom is not None and geom.is_valid:
                    centroid = geom.centroid
            
                    heat_data.append([
                        centroid.y,
                        centroid.x,
                        row["log_volume_norm"]
                    ])

            progress.progress(80)

            # Add heatmap layer
            HeatMap(
                heat_data,
                radius=20,
                blur=10,
                min_opacity=0.2,
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
