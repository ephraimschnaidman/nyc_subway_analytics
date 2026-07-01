from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "mta_analytics.db"

st.set_page_config(page_title="NYC Subway Analytics", layout="wide")
st.title("NYC Subway Analytics")


@st.cache_data(ttl=60)
def read_table(query: str) -> pd.DataFrame:
    with duckdb.connect(str(DB_PATH), read_only=True) as conn:
        return conn.execute(query).fetchdf()


try:
    activity = read_table("""
        select snapshot_time, total_active_trips
        from fct_trip_activity
        order by snapshot_time desc
        limit 60
    """)
    density = read_table("""
        select snapshot_time, subway_line, active_train_count
        from fct_line_density
        where snapshot_time = (select max(snapshot_time) from fct_line_density)
        order by active_train_count desc, subway_line
    """)
except Exception as exc:
    st.error(f"Could not read dbt marts from {DB_PATH}: {exc}")
    st.stop()

latest_time = activity["snapshot_time"].max() if not activity.empty else None
latest_total = int(activity.iloc[0]["total_active_trips"]) if not activity.empty else 0

metric_cols = st.columns(3)
metric_cols[0].metric("Latest active trips", latest_total)
metric_cols[1].metric("Lines reporting", len(density))
metric_cols[2].metric("Latest snapshot", str(latest_time)[:19] if latest_time is not None else "No data")

left, right = st.columns([2, 1])

with left:
    st.subheader("System Activity")
    if activity.empty:
        st.info("No activity rows yet. Run ingestion, then dbt.")
    else:
        chart_data = activity.sort_values("snapshot_time").set_index("snapshot_time")
        st.line_chart(chart_data["total_active_trips"])

with right:
    st.subheader("Latest Line Density")
    if density.empty:
        st.info("No line density rows yet.")
    else:
        st.bar_chart(density.set_index("subway_line")["active_train_count"])

st.subheader("Recent Activity Rows")
st.dataframe(activity, use_container_width=True, hide_index=True)
