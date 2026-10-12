import sqlite3

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="UK Grid Carbon Tracker", page_icon="🌱", layout="wide")
st.title("🌱 UK Grid Carbon Tracker")
st.caption("Source: National Grid ESO Carbon Intensity API. Intensity is in gCO2 per kWh (lower is greener).")


@st.cache_data(ttl=300)
def load():
    con = sqlite3.connect("carbon.db")
    inten = pd.read_sql("SELECT * FROM intensity ORDER BY from_ts", con, parse_dates=["from_ts", "to_ts"])
    mix = pd.read_sql("SELECT * FROM mix ORDER BY from_ts", con, parse_dates=["from_ts"])
    con.close()
    return inten, mix


try:
    inten, mix = load()
except Exception:
    st.error("No data yet. Run `python collector.py backfill` first.")
    st.stop()

if inten.empty:
    st.warning("Database is empty. Run `python collector.py backfill`.")
    st.stop()

# Use actual when available, otherwise the forecast
inten["value"] = inten["actual"].fillna(inten["forecast"])
inten["hour"] = inten["from_ts"].dt.hour
inten["weekday"] = inten["from_ts"].dt.day_name()
inten["is_weekend"] = inten["from_ts"].dt.dayofweek >= 5

latest = inten.iloc[-1]
avg = inten["value"].mean()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Now (gCO2/kWh)", int(latest["value"]), f"{int(latest['value'] - avg):+d} vs average", delta_color="inverse")
c2.metric("Rating", str(latest["idx"]).title())
best = inten.groupby("hour")["value"].mean()
c3.metric("Greenest hour (avg)", f"{best.idxmin():02d}:00")
c4.metric("Dirtiest hour (avg)", f"{best.idxmax():02d}:00")

st.subheader("Carbon intensity over time")
fig = px.line(inten, x="from_ts", y=["actual", "forecast"], labels={"value": "gCO2/kWh", "from_ts": ""})
st.plotly_chart(fig, use_container_width=True)

left, right = st.columns(2)

with left:
    st.subheader("Average intensity by hour of day")
    by_hour = inten.groupby("hour", as_index=False)["value"].mean()
    st.plotly_chart(px.bar(by_hour, x="hour", y="value", color="value",
                           color_continuous_scale="RdYlGn_r", labels={"value": "gCO2/kWh"}),
                    use_container_width=True)

with right:
    st.subheader("Weekday vs weekend")
    wk = inten.groupby(["hour", "is_weekend"], as_index=False)["value"].mean()
    wk["type"] = wk["is_weekend"].map({True: "Weekend", False: "Weekday"})
    st.plotly_chart(px.line(wk, x="hour", y="value", color="type", labels={"value": "gCO2/kWh"}),
                    use_container_width=True)

st.subheader("Where the electricity comes from")
if not mix.empty:
    st.plotly_chart(px.area(mix, x="from_ts", y="perc", color="fuel",
                            labels={"perc": "% of generation", "from_ts": ""}),
                    use_container_width=True)

st.subheader("Intensity by day and hour")
heat = inten.pivot_table(index="weekday", columns="hour", values="value", aggfunc="mean")
order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
heat = heat.reindex([d for d in order if d in heat.index])
st.plotly_chart(px.imshow(heat, color_continuous_scale="RdYlGn_r", aspect="auto",
                          labels={"color": "gCO2/kWh", "x": "Hour", "y": ""}),
                use_container_width=True)
