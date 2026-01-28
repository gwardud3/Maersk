import streamlit as st
import requests
import pandas as pd

# ---------------- Graph Auth ----------------
@st.cache_resource
def get_graph_token():
    url = f"https://login.microsoftonline.com/{st.secrets['TENANT_ID']}/oauth2/v2.0/token"

    data = {
        "client_id": st.secrets["CLIENT_ID"],
        "client_secret": st.secrets["CLIENT_SECRET"],
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials",
    }

    r = requests.post(url, data=data)
    r.raise_for_status()
    return r.json()["access_token"]

def graph_get(endpoint):
    token = get_graph_token()
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"https://graph.microsoft.com/v1.0{endpoint}", headers=headers)
    r.raise_for_status()
    return r.json()["value"]

# ---------------- Streamlit Feature ----------------
def planner_dashboard_app():
    st.header("📋 Planner Bucket Summary")

    plan_id = st.secrets["PLANNER_PLAN_ID"]

    with st.spinner("Loading Planner data..."):
        buckets = graph_get(f"/planner/plans/{plan_id}/buckets")
        tasks = graph_get(f"/planner/plans/{plan_id}/tasks")

    # Convert to DataFrames
    buckets_df = pd.DataFrame(buckets)[["id", "name"]]
    tasks_df = pd.DataFrame(tasks)[["id", "title", "bucketId"]]

    # Merge tasks → buckets
    merged = tasks_df.merge(
        buckets_df,
        left_on="bucketId",
        right_on="id",
        how="left",
        suffixes=("_task", "_bucket")
    )

    # Summary
    summary = (
        merged.groupby("name")
        .agg(
            Task_Count=("id_task", "count"),
            Tasks=("title", lambda x: ", ".join(x))
        )
        .reset_index()
        .rename(columns={"name": "Bucket"})
        .sort_values("Bucket")
    )

    st.subheader("📊 Task Summary by Bucket")
    st.dataframe(summary, use_container_width=True)

    # Optional chart
    st.subheader("📈 Task Count")
    st.bar_chart(
        summary.set_index("Bucket")["Task_Count"]
    )
