import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from folium.plugins import BeautifyIcon
from streamlit_folium import st_folium

# -------------------------
# Cargar datos desde GitHub
# -------------------------
data_url2 = "https://raw.githubusercontent.com/melody-10/Proyecto_Hoteles_California/refs/heads/main/hotels_ca.csv"
data_url3 = "https://raw.githubusercontent.com/melody-10/Proyecto_Hoteles_California/refs/heads/main/BBDD_BI.csv"

# Leer CSV
df_coordenadas = pd.read_csv(data_url2)
df_profesor = pd.read_csv(data_url3)

# -------------------------
# Filtrar solo abiertos (si existe columna is_open)
# -------------------------
if "is_open" in df_coordenadas.columns:
    df_coordenadas = df_coordenadas[df_coordenadas["is_open"] == 1].reset_index(drop=True)

if "is_open" in df_profesor.columns:
    df_profesor = df_profesor[df_profesor["is_open"] == 1].reset_index(drop=True)

# -------------------------
# Seleccionar columnas necesarias
# -------------------------
cols = ["name", "latitude", "longitude", "address"]

df_coord = df_coordenadas[[c for c in cols if c in df_coordenadas.columns]]
df_prof = df_profesor[[c for c in cols if c in df_profesor.columns]]

# Unir bases
df_final = pd.concat([df_coord, df_prof])

# Quitar duplicados
df_final = df_final.drop_duplicates(subset=["name", "address"], keep="first")

# -------------------------
# Crear pestañas
# -------------------------
tabs = st.tabs(["Dashboard", "Exploración de datos", "Mapa de Hoteles"])

# -------------------------
# Pestaña 1: Dashboard original
# -------------------------
with tabs[0]:
    st.header("📊 Dashboard de Hoteles en California")

    # Ejemplo de métrica: total de hoteles
    total_hoteles = len(df_final)
    st.metric("Número total de hoteles", total_hoteles)

    # Si tienes columna de reviews o ratings
    if "reviews" in df_profesor.columns:
        fig = px.histogram(df_profesor, x="reviews", nbins=30, title="Distribución de Reviews")
        st.plotly_chart(fig, use_container_width=True)

    if "name" in df_final.columns and "latitude" in df_final.columns:
        st.write("Ejemplo de tabla de hoteles con coordenadas:")
        st.dataframe(df_final.head())

# -------------------------
# Pestaña 2: Exploración de datos
# -------------------------
with tabs[1]:
    st.header("🔍 Exploración de datos")

    st.write("### Vista previa del dataset combinado")
    st.dataframe(df_final)

    st.write("### Columnas disponibles en hotels_ca.csv")
    st.write(df_coordenadas.columns.tolist())

    st.write("### Columnas disponibles en BBDD_BI.csv")
    st.write(df_profesor.columns.tolist())

# -------------------------
# Pestaña 3: Mapa de Hoteles
# -------------------------
with tabs[2]:
    st.header("🗺️ Mapa de Hoteles en California")

    # Crear mapa centrado en California
    mapa = folium.Map(location=[36.7783, -119.4179], zoom_start=6)

    # Agregar marcadores
    for i, row in df_final.iterrows():
        if pd.notna(row.get("latitude")) and pd.notna(row.get("longitude")):
            folium.Marker(
                location=[row["latitude"], row["longitude"]],
                popup=f"{row.get('name', 'Sin nombre')}<br>{row.get('address', 'Sin dirección')}",
                icon=BeautifyIcon(
                    icon="hotel",
                    icon_shape="marker",
                    background_color="darkblue",
                    text_color="white",
                    border_color="white",
                    border_width=2
                )
            ).add_to(mapa)

    # Mostrar mapa en Streamlit
    st_folium(mapa, width=700, height=500)
