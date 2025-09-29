import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go

# ========== CONFIG ==========
st.set_page_config(layout="wide")
FILE_PATH = "data/RN Gender.xlsx"
YEARS = list(range(2020, 2024))

# ========== SIDEBAR ==========
st.sidebar.title("Filter")
selected_year = st.sidebar.selectbox("Select Year", YEARS)

# ========== LOAD SHAPEFILE ==========
@st.cache_resource
def load_shapefile():
    counties = gpd.read_file("tn_counties.json")
    return counties[counties["STATEFP"] == "47"]  # Tennessee only

tn_counties = load_shapefile()
tn_counties["NAME"] = tn_counties["NAME"].str.strip().str.title()

# ========== LOAD ALL YEARLY DATA ==========
@st.cache_data
def load_excel_data(file_path):
    all_data = []
    for year in YEARS:
        sheet_name = f"{year}"
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        df.columns = df.columns.str.strip()
        df = df[["County", "Female(%)"]].copy()
        df["Year"] = year
        all_data.append(df)
    return pd.concat(all_data, ignore_index=True)

df_all = load_excel_data(FILE_PATH)
print(df_all.columns.tolist())

# ========== FILTER BY YEAR ==========
df_year = df_all[df_all["Year"] == selected_year].copy()

# ========== PROCESS YEAR DATA ==========
grouped = (
    df_year.groupby("County", as_index=False)
           .agg({"Female(%)": "mean"})  # or "first" if no duplicates
)

# Optional: clean county names (if needed)
grouped["County"] = grouped["County"].str.split(',').str[0].str.strip()

# ========== MERGE WITH SHAPEFILE ==========
tn_counties["NAME_clean"] = tn_counties["NAME"].str.strip().str.lower()
grouped["County_clean"] = grouped["County"].str.strip().str.lower()

merged = tn_counties.merge(
    grouped, 
    left_on="NAME_clean", 
    right_on="County_clean", 
    how="left"

# ========== BUILD HOVER INFO ==========
def build_hover(row):
    return (
        f"County: {row['NAME']}<br>"
        f"Female(%): {row['Female(%)'] if pd.notna(row['Female(%)']) else 'N/A'}%"
    )

# ========== TOOLTIP ==========
merged["hover_text"] = merged.apply(build_hover, axis=1)

# ========== PLOTLY MAP ==========
fig = go.Figure(go.Choropleth(
    geojson=merged.__geo_interface__,
    locations=merged.index,
    z=merged["Female(%)"].fillna(0),
    text=merged["hover_text"],
    hoverinfo="text",
    colorscale="Greens",
    zmin=80,
    zmax=100,
    marker_line_color="black",
    marker_line_width=1.2,
    colorbar_title="Pass %",
))

fig.update_layout(
    margin={"r":0,"t":40,"l":0,"b":0},
    title=f"Female (%) by County - {selected_year}",
    geo=dict(
        fitbounds="locations",
        visible=True,
        scope="usa",
        projection=dict(type="albers usa")
    )
)

# ========== DISPLAY ==========
st.title("Female Nurse - RN (%) by County in Tennessee (2020–2023)")
st.plotly_chart(fig, use_container_width=True)
