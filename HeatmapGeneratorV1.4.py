import streamlit as st
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.patches as mpatches
import os

# ---------------- Resource path ----------------
def resource_path(relative_path: str) -> str:
    base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# ---------------- Heavy processing function ----------------
def process_data(origin_list, customer_name):
    progress_text = st.empty()

    # Step 1: Load Excel
    progress_text.info("Loading Excel file...")
    excel_path = resource_path("Maersk Zones.xlsx")
    MasterZone_df = pd.read_excel(excel_path)

    # Step 2: Process Data
    progress_text.info("Processing zone data...")
    MasterZone_df['OriginZip'] = MasterZone_df['Set_ID'].astype(str).str.zfill(3)
    MasterZone_df['DestZipMin'] = MasterZone_df['Min_Zip_Int'].astype(int)
    MasterZone_df['DestZipMax'] = MasterZone_df['Max_Zip_Int'].astype(int)
    MasterZone_df['Zone'] = MasterZone_df['Zone'].astype(int)

    filtered = MasterZone_df[MasterZone_df['OriginZip'].isin(origin_list)].copy()
    filtered['DestZipRange'] = filtered.apply(lambda r: range(r.DestZipMin, r.DestZipMax + 1), axis=1)
    expanded_df = filtered.explode('DestZipRange')
    expanded_df['zip3'] = expanded_df['DestZipRange'].astype(str).str.zfill(3)
    expanded_df = expanded_df[['zip3', 'Zone', 'OriginZip']].reset_index(drop=True)

    min_zones = expanded_df.groupby("zip3")["Zone"].min().reset_index()
    min_zone_df = expanded_df.merge(min_zones, on=["zip3", "Zone"])
    expanded_df = (
        min_zone_df.groupby(["zip3", "Zone"])["OriginZip"]
        .agg(lambda x: ', '.join(sorted(set(x))))
        .reset_index()
        .rename(columns={"OriginZip": "OriginWithMinZone"})
    )

    # Step 3: Load Maps
    progress_text.info("Loading map files...")
    progress_text.info("Loading ZIP3 map shapes...")
    zip3_shapes = gpd.read_file(resource_path("shapefiles/zip3_simplified.gpkg"))

    # Ensure zip3 is string
    zip3_shapes["zip3"] = zip3_shapes["zip3"].astype(str).str.zfill(3)
    expanded_df["zip3"] = expanded_df["zip3"].astype(str).str.zfill(3)

    # Merge zone results directly onto ZIP3 polygons
    zip3_shapes = zip3_shapes.merge(expanded_df, on="zip3", how="left")

    # Step 4: Plot
    progress_text.info("Rendering map...")
    zone_colors = {
        1: "#001624", 2: "#00243D", 3: "#004A73", 4: "#0073AB",
        5: "#2392BE", 6: "#42B0D5", 7: "#72C8E3", 8: "#A1D8EF", 9: "#B5E0F5"
    }

    fig, ax = plt.subplots(figsize=(15, 10))
    states = gpd.read_file(resource_path("shapefiles/states_preprocessed.gpkg"))
    states.boundary.plot(ax=ax, linewidth=0.5, edgecolor='black')
    ax.set_facecolor("#a3a3a3")

    zip3_plot_colors = zip3_shapes["Zone"].map(zone_colors).fillna("#CCCCCC")
    zip3_shapes.plot(color=zip3_plot_colors, ax=ax, linewidth=0)
    used_zones = sorted(zip3_shapes["Zone"].dropna().unique())
    legend_handles = [mpatches.Patch(color=zone_colors[z], label=str(z)) for z in used_zones]
    ax.legend(handles=legend_handles, title="Zone", loc="lower left", fontsize="small")

    ax.set_title(f"Zone Map - {customer_name}", fontsize=16)
    ax.axis("off")
    plt.tight_layout()

    progress_text.success("Done!")

    return fig, expanded_df


# ---------------- Streamlit UI ----------------
st.set_page_config(layout="wide")
st.title("📦 Zone Map Generator")

origin_input = st.text_input("Enter 3-Digit Origin ZIPs (comma separated)")
customer_name = st.text_input("Customer Name")

if st.button("Generate Map"):
    origin_list = [o.strip().zfill(3) for o in origin_input.split(',') if o.strip().isdigit() and len(o.strip()) <= 3]

    if not origin_list:
        st.error("Please enter at least one valid 3-digit Origin ZIP.")
    elif not customer_name:
        st.error("Please enter a Customer Name.")
    else:
        with st.spinner("Processing... this can take a bit"):
            fig, expanded_df = process_data(origin_list, customer_name)

        st.pyplot(fig)

        csv = expanded_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Zone Data CSV",
            data=csv,
            file_name="expanded_zone_data.csv",
            mime="text/csv"
        )