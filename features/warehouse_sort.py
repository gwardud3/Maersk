import streamlit as st
import pandas as pd
from itertools import combinations

# ================================
# 📥 LOAD USER DATA
# ================================
def load_user_data():
    uploaded_file = st.file_uploader(
        "Upload your shipment data (.xlsx)",
        type=["xlsx"]
    )

    if uploaded_file is None:
        return None

    try:
        data = pd.read_excel(uploaded_file)

        required_cols = ["DestZip", "Volume"]
        missing_cols = [col for col in required_cols if col not in data.columns]

        if missing_cols:
            st.error(f"Missing required columns: {missing_cols}")
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
# 📂 LOAD STATIC FILES
# ================================
def load_static_data():
    try:
        maersk_zones = pd.read_excel("Maersk Zones.xlsx")
        warehouse_sorting_loc = pd.read_excel("Warehouse & Sorting Locations.xlsx")
        maersk_tnt = pd.read_excel("Service TNT.xlsx")

        warehouse_sorting_loc["Zip"] = warehouse_sorting_loc["Zip"].astype(str).str.zfill(5)
        warehouse_sorting_loc["ThreeOriginZip"] = warehouse_sorting_loc["Zip"].str[:3]

        return maersk_zones, warehouse_sorting_loc, maersk_tnt

    except Exception as e:
        st.error(f"Error loading static files: {e}")
        return None, None, None


# ================================
# 🗺️ BUILD ZONE LOOKUP
# ================================
def build_zone_lookup(maersk_zones, origins):
    rows = []

    filtered = maersk_zones[maersk_zones["Set_ID"].isin(origins)]

    for _, r in filtered.iterrows():
        origin = str(r["Set_ID"]).zfill(3)

        for dest in range(int(r["Min_Zip_Int"]), int(r["Max_Zip_Int"]) + 1):
            rows.append({
                "ID": f"{origin}-{str(dest).zfill(3)}",
                "Zone": r["Zone"]
            })

    return pd.DataFrame(rows)


# ================================
# 🔗 MAP ZONES TO DATA
# ================================
def add_zone_columns(data, zone_lookup, warehouse_df):
    mapping = dict(zip(
        warehouse_df["ThreeOriginZip"],
        warehouse_df["Location"]
    ))

    for origin, location in mapping.items():
        temp_col = f"from_{origin}"
        zone_col = f"{location} Zone"

        data[temp_col] = origin + "-" + data["Dest3"]

        data = data.merge(
            zone_lookup,
            left_on=temp_col,
            right_on="ID",
            how="left"
        )

        data[zone_col] = data["Zone"]
        data.drop(columns=["ID", "Zone"], inplace=True)

    data = data.drop(columns=[c for c in data.columns if c.startswith("from_")])

    return data


# ================================
# 📊 OPTIMIZATION ENGINE
# ================================
def evaluate_combinations(data, selected_locations, num_nodes):
    zone_cols = [f"{loc} Zone" for loc in selected_locations]
    results = []

    for combo in combinations(zone_cols, num_nodes):

        combo_name = [c.replace(" Zone", "") for c in combo]

        best_zone = data[list(combo)].min(axis=1)
        weighted_avg = (best_zone * data["Volume"]).sum() / data["Volume"].sum()

        # Volume split
        winner = data[list(combo)].idxmin(axis=1)

        volume_split = {}
        total_vol = data["Volume"].sum()

        for col in combo:
            vol = data.loc[winner == col, "Volume"].sum()
            volume_split[col.replace(" Zone", "")] = round(vol / total_vol * 100, 2)

        results.append({
            "Locations": " | ".join(combo_name),
            "Weighted Avg Zone": round(weighted_avg, 3),
            **volume_split
        })

    results_df = pd.DataFrame(results).sort_values("Weighted Avg Zone").reset_index(drop=True)

    return results_df


# ================================
# 📦 FINAL DISTRIBUTION
# ================================
def build_distribution(data, best_combo):
    best_cols = [f"{loc} Zone" for loc in best_combo]

    data["Best Zone"] = data[best_cols].min(axis=1)

    summary = (
        data.groupby("Best Zone", as_index=False)["Volume"]
        .sum()
    )

    total = summary["Volume"].sum()
    summary["Pct of Total"] = (summary["Volume"] / total * 100).round(2)

    return data, summary


# ================================
# 🚀 MAIN APP
# ================================
def warehouse_sort_app():
    st.header("Warehouse Sorting Tool")

    # Load data
    maersk_zones, warehouse_df, maersk_tnt = load_static_data()
    if maersk_zones is None:
        return

    data = load_user_data()
    if data is None:
        return

    st.success("All data loaded successfully 🚀")

    # Warehouse selection
    st.subheader("Select Warehouses 🏭")

    locations = warehouse_df["Location"].tolist()

    selected_locations = st.multiselect(
        "Choose locations:",
        options=locations,
        default=locations[:3]
    )

    num_nodes = st.selectbox("Number of warehouses:", [1, 2, 3])

    if st.button("Optimize"):

        if len(selected_locations) < num_nodes:
            st.warning("Select enough warehouses")
            return

        selected_df = warehouse_df[
            warehouse_df["Location"].isin(selected_locations)
        ]

        origins = selected_df["ThreeOriginZip"].tolist()

        st.subheader("DEBUG: Inputs")

        st.write("Selected Locations:", selected_locations)
        st.write("Origins:", origins)

        st.write("Warehouse DF sample:")
        st.dataframe(selected_df.head())

        st.write("Maersk Zones sample:")
        st.dataframe(maersk_zones.head())

        st.subheader("DEBUG: Data Types")

        st.write("Origins type:", type(origins[0]) if origins else "Empty")

        st.write("Set_ID dtype:", maersk_zones["Set_ID"].dtype)
        st.write("Sample Set_ID values:", maersk_zones["Set_ID"].head().tolist())

        # Build lookup
        zone_lookup = build_zone_lookup(maersk_zones, origins)

        # Add zone columns
        data = add_zone_columns(data, zone_lookup, selected_df)

        # Run optimization
        results_df = evaluate_combinations(data, selected_locations, num_nodes)

        st.subheader("Optimization Results")
        st.dataframe(results_df)

        # Best combo
        best_combo = results_df.iloc[0]["Locations"].split(" | ")

        st.success(f"Best Choice: {' & '.join(best_combo)}")

        # Distribution
        data, summary = build_distribution(data, best_combo)

        st.subheader("Zone Distribution")
        st.dataframe(summary)