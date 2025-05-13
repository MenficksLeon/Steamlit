import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
import numpy as np 
from streamlit_folium import st_folium



# Configuración de página SIN márgenes y layout compacto
st.set_page_config(layout="wide", page_title="Dashboard", initial_sidebar_state="collapsed")
# --- 1. Carga de datos (igual que antes) ---
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

# --- 2. Sidebar (colapsable para ahorrar espacio) ---
with st.sidebar:
    st.header("Filtros")
    ger_ops = ["Todos"] + sorted(gdf["Gerencia"].dropna().unique().tolist())
    sel_ger = st.selectbox("Gerencia", ger_ops, index=0)
    df_ger = gdf if sel_ger == "Todos" else gdf[gdf["Gerencia"] == sel_ger]
    mesa_ops = ["Todos"] + sorted(df_ger["Mesa"].dropna().unique().tolist())
    sel_mes = st.selectbox("Mesa", mesa_ops, index=0)
    df_mes = df_ger if sel_mes == "Todos" else df_ger[df_ger["Mesa"] == sel_mes]
    ana_ops = ["Todos"] + sorted(df_mes["Analista"].dropna().unique().tolist())
    sel_ana = st.selectbox("Analista", ana_ops, index=0)

# --- 3. KPIs DINÁMICOS (valores aleatorios por selección) ---
def generar_kpis(gerencia, mesa, analista):
    """Genera valores aleatorios basados en la selección actual"""
    # Semilla reproducible basada en los filtros (para que sean consistentes)
    semilla = hash(f"{gerencia}-{mesa}-{analista}") % (2**32)
    np.random.seed(semilla)
    
    return {
        "Saldo capital": f"${np.random.uniform(0.5, 2.0):.2f} M",
        "Número de socias": str(np.random.randint(8000, 15000)),
        "Mora": f"{np.random.uniform(5.0, 10.0):.1f}%",
        "Número de grupos": str(np.random.randint(100, 300))
    }

# Generar KPIs basados en los filtros actuales
kpis = generar_kpis(sel_ger, sel_mes, sel_ana)

# Mostrar KPIs en 4 columnas
cols = st.columns(4)
with cols[0]:
    st.metric("Saldo capital", kpis["Saldo capital"])
with cols[1]:
    st.metric("Número de socias", kpis["Número de socias"])
with cols[2]:
    st.metric("Mora", kpis["Mora"])
with cols[3]:
    st.metric("Número de grupos", kpis["Número de grupos"])

# --- 4. Mapa ajustado (sin espacio extra) ---
if sel_ana != "Todos":
    df_fit = df_mes[df_mes["Analista"] == sel_ana]
elif sel_mes != "Todos":
    df_fit = df_mes
elif sel_ger != "Todos":
    df_fit = df_ger
else:
    df_fit = gdf

b = df_fit.total_bounds
center_lat, center_lon = (b[1] + b[3]) / 2, (b[0] + b[2]) / 2

m = folium.Map(location=[center_lat, center_lon], zoom_start=7)

def style_feat(feat):
    jer = feat["properties"]["jerarquia"]
    opacity = 0.4  # Default
    if sel_ger != "Todos" and not jer.startswith(sel_ger):
        return {"fillOpacity": 0, "opacity": 0}
    if sel_mes != "Todos":
        opacity = 0.4 if jer.startswith(sel_mes) else 0.1
    if sel_ana != "Todos":
        opacity = 0.4 if jer == sel_ana else 0.1
    return {
        "fillColor": feat["properties"].get("fill", "#3388ff"),
        "color": "#000000",
        "weight": 1,
        "fillOpacity": opacity,
    }

folium.GeoJson(gdf, style_function=style_feat, tooltip=folium.GeoJsonTooltip(fields=["jerarquia"])).add_to(m)
m.fit_bounds([[b[1], b[0]], [b[3], b[2]]])

# --- 5. Mapa SIN scroll (altura calculada dinámicamente) ---
map_height = 600  # Ajusta este valor según tu pantalla
st_folium(m, height=map_height, use_container_width=True)
