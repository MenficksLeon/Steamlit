import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium

# 1. Carga y extracción jerárquica
gdf = gpd.read_file("data/territorio.geojson")
parts = gdf["jerarquia"].str.split("-", n=2, expand=True)
gdf["Gerencia"] = parts[0]
gdf["Mesa"] = parts.apply(
    lambda r: f"{r[0]}-{r[1]}" if pd.notna(r[1]) and r[1] != "" else None,
    axis=1
)
gdf["Analista"] = gdf["jerarquia"].where(
    gdf["jerarquia"].str.count("-") == 2,
    None
)

# 2. Sidebar con filtros (incluye "Todos")
st.sidebar.header("Filtros")

# Gerencia
ger_ops = ["Todos"] + sorted(gdf["Gerencia"].dropna().unique().tolist())
sel_ger = st.sidebar.selectbox("Gerencia", ger_ops, index=0)

# Mesa: filtrar None y duplicados
df_ger = gdf if sel_ger == "Todos" else gdf[gdf["Gerencia"] == sel_ger]
mesa_list = sorted(df_ger["Mesa"].dropna().unique().tolist())
mesa_ops = ["Todos"] + mesa_list
sel_mes = st.sidebar.selectbox("Mesa", mesa_ops, index=0)

# Analista: filtrar None y duplicados
df_mes = df_ger if sel_mes == "Todos" else df_ger[df_ger["Mesa"] == sel_mes]
ana_list = sorted(df_mes["Analista"].dropna().unique().tolist())
ana_ops = ["Todos"] + ana_list
sel_ana = st.sidebar.selectbox("Analista", ana_ops, index=0)

# 3. Indicadores arriba (estáticos de ejemplo)
col1, col2, col3 = st.columns(3)
col1.metric("Saldo capital", "$1.23 M")
col2.metric("Número de socias", "123")
col3.metric("Mora", "7%")

# 4. Determinar subconjunto para centrar
if sel_ana != "Todos":
    df_fit = df_mes[df_mes["Analista"] == sel_ana]
elif sel_mes != "Todos":
    df_fit = df_mes
elif sel_ger != "Todos":
    df_fit = df_ger
else:
    df_fit = gdf

b = df_fit.total_bounds  # [minx, miny, maxx, maxy]
center_lat = (b[1] + b[3]) / 2
center_lon = (b[0] + b[2]) / 2

# 5. Crear mapa
m = folium.Map(location=[center_lat, center_lon], zoom_start=7)

def style_feat(feat):
    jer = feat["properties"]["jerarquia"]
    # fuera de gerencia oculta
    if sel_ger != "Todos" and not jer.startswith(sel_ger):
        return {"fillOpacity": 0, "opacity": 0}
    # opacidad base
    if sel_mes != "Todos":
        opacity = 0.6 if jer.startswith(sel_mes) else 0.2
    else:
        opacity = 0.6
    if sel_ana != "Todos":
        opacity = 0.6 if jer == sel_ana else 0.2
    return {
        "fillColor":   feat["properties"].get("fill", "#cccccc"),
        "color":       feat["properties"].get("stroke", "#000000"),
        "weight":      feat["properties"].get("stroke-width", 1),
        "fillOpacity": opacity,
        "opacity":     feat["properties"].get("stroke-opacity", 1),
    }

folium.GeoJson(
    gdf,
    style_function=style_feat,
    tooltip=folium.GeoJsonTooltip(fields=["jerarquia"])
).add_to(m)

m.fit_bounds([[b[1], b[0]], [b[3], b[2]]])

# 6. Mostrar
st_folium(m, width=700, height=500)
