import streamlit as st
import pandas as pd
import ast
import math
import folium
from folium.plugins import BeautifyIcon
from streamlit_folium import st_folium   # 👈 librería para mostrar mapas folium en Streamlit

# -------------------------
# CONFIGURACIÓN APP
# -------------------------
st.set_page_config(layout="wide")
st.title("🏨 Hoteles en California")

# Crear pestañas
tab1, tab2 = st.tabs(["📊 Radiografía de Reseñas", "🗺️ Mapa de Hoteles"])

# -------------------------
# TAB 1: Radiografía de Reseñas (tu código original)
# -------------------------
with tab1:
    # Subir dataset principal
    df = pd.read_csv("https://github.com/melody-10/Proyecto_Hoteles_California/blob/main/final_database.csv?raw=true")

    # Funciones auxiliares
    def generate_stars(score):
        try:
            score = float(score)
            if 0 <= score <= 5:
                full_stars = math.floor(score)
                half_star = "★" if score - full_stars >= 0.5 else ""
                empty_stars = 5 - full_stars - len(half_star)
                return f"<span style='color: #FFD700;'>{'★' * full_stars}{half_star}{'☆' * empty_stars}</span> ({score})"
            else:
                return "N/A"
        except (ValueError, TypeError):
            return "N/A"

    def parse_ratings(val):
        try:
            return ast.literal_eval(val) if isinstance(val, str) else {}
        except (ValueError, SyntaxError):
            return {}

    df["ratings_parsed"] = df["ratings"].apply(parse_ratings)
    df['text'] = df['text'].astype(str)

    # Promedios de cada hotel
    df_for_avg = df[['name', 'ratings_parsed']].copy()
    ratings_df = pd.json_normalize(df_for_avg['ratings_parsed'])
    full_ratings_df = pd.concat([df_for_avg['name'], ratings_df], axis=1)
    rating_columns = ratings_df.columns
    for col in rating_columns:
        full_ratings_df[col] = pd.to_numeric(full_ratings_df[col], errors='coerce')
    average_ratings_per_hotel = full_ratings_df.groupby('name')[rating_columns].mean().round(1)

    emoji_map = {"service": "🛎️", "cleanliness": "🧼", "overall": "⭐",
                 "value": "💰", "location": "📍", "sleep quality": "💤", "rooms": "🚪"}

    st.markdown("""<style>
        .stApp { background: #f4f6f9; font-family: 'Segoe UI', sans-serif; }
        .content-box { background: white; padding: 18px; border-radius: 10px;
                       box-shadow: 0px 2px 8px rgba(0,0,0,0.07); margin-bottom: 12px; height: 100%; }
        .hotel-title { font-size: 22px; font-weight: bold; color: #2C3E50; text-align: center; }
        .review-text { font-size: 15px; color: #444; line-height: 1.5; }
        .ratings-title { font-weight: bold; font-size: 16px; margin-bottom: 10px; color: #2C3E50; }
        .rating-line { margin: 8px 0; font-size: 15px; color: #333; display: flex;
                       align-items: center; justify-content: space-between; }
    </style>""", unsafe_allow_html=True)

    # Filtros
    topics = df['topic_label'].unique().tolist()
    selected_topic = st.selectbox("📌 Selecciona un tópico", topics)
    hotel_options = ['Todos'] + sorted(df['name'].unique().tolist())
    selected_hotel = st.selectbox("🏩 Selecciona un hotel", hotel_options)
    n_reviews = st.slider("📊 Número máximo de reseñas a mostrar", 1, 20, 5)

    # Filtrado de datos
    filtered_df = df[df['topic_label'] == selected_topic]
    if selected_hotel != 'Todos':
        filtered_df = filtered_df[filtered_df['name'] == selected_hotel]
    else:
        filtered_df = filtered_df.drop_duplicates(subset=['name'])
    filtered_df = filtered_df.head(n_reviews)

    if filtered_df.empty:
        st.warning("⚠️ No se encontraron reviews.")
    else:
        for idx, row in filtered_df.iterrows():
            st.markdown(f"<div class='content-box hotel-title'>🏨 {row['name']}</div>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns([1.8, 1.3, 2])

            with col1:
                st.markdown(f"""<div class="content-box"><p class="review-text">{row['text']}</p></div>""", unsafe_allow_html=True)

            with col2:
                ratings_dict = row.get("ratings_parsed", {}).copy()
                ratings_html = '<div class="content-box">'
                ratings_html += '<p class="ratings-title">Ratings:</p>'
                if ratings_dict:
                    overall_value = ratings_dict.pop('overall', None)
                    if overall_value is not None:
                        emoji = emoji_map.get('overall', "⭐")
                        stars = generate_stars(overall_value)
                        ratings_html += f'<div class="rating-line"><span>{emoji} Overall</span> <span>{stars}</span></div>'
                    for key, value in sorted(ratings_dict.items()):
                        emoji = emoji_map.get(key, "🔹")
                        stars = generate_stars(value)
                        ratings_html += f'<div class="rating-line"><span>{emoji} {key.capitalize()}</span> <span>{stars}</span></div>'
                else:
                    ratings_html += '<p class="rating-line">No hay ratings disponibles.</p>'
                ratings_html += '</div>'
                st.markdown(ratings_html, unsafe_allow_html=True)

            with col3:
                hotel_name = row['name']
                current_ratings_dict = row.get("ratings_parsed", {})
                if current_ratings_dict and hotel_name in average_ratings_per_hotel.index:
                    hotel_scores = {k: float(v) for k, v in current_ratings_dict.items()
                                    if str(v).replace('.', '', 1).isdigit()}
                    if hotel_scores:
                        st.markdown('<div class="content-box" style="padding-bottom: 0;"><p class="ratings-title">Comparación Review vs Promedio</p></div>', unsafe_allow_html=True)
                        comparison_df = pd.DataFrame({'Review': pd.Series(hotel_scores),
                                                      'Promedio': average_ratings_per_hotel.loc[hotel_name]}).dropna()
                        stacked_df = pd.DataFrame(index=comparison_df.index)
                        stacked_df['Promedio del Hotel'] = comparison_df['Promedio']
                        stacked_df['Calificación de Reseña'] = (comparison_df['Review'] - comparison_df['Promedio']).clip(lower=0)
                        st.bar_chart(stacked_df, height=300)
                    else:
                        st.markdown('<div class="content-box"><p>No hay ratings numéricos.</p></div>', unsafe_allow_html=True)

# -------------------------
# TAB 2: Mapa de Hoteles
# -------------------------
with tab2:
    st.subheader("🗺️ Mapa interactivo de hoteles en California")

    data_url2= "https://raw.githubusercontent.com/melody-10/Proyecto_Hoteles_California/main/hotels_ca.csv"
    data_url3= "https://raw.githubusercontent.com/melody-10/Proyecto_Hoteles_California/main/BBDD_BI.csv"

    df_coordenadas=pd.read_csv(data_url2)
    df_profesor=pd.read_csv(data_url3)

    # Filtrar abiertos
    df_coordenadas = df_coordenadas[df_coordenadas["is_open"] == 1]
    df_profesor = df_profesor[df_profesor["is_open"] == 1]

    # DataFrames con columnas necesarias
    df_coord=df_coordenadas[["name","latitude","longitude", "address"]]
    df_prof=df_profesor[["name","latitude","longitude", "address"]]

    # Juntar y quitar duplicados
    df_final=pd.concat([df_coord,df_prof])
    df_final = df_final.drop_duplicates(subset=["name", "address"], keep="first")

    # Crear mapa folium
    mapa = folium.Map(location=[36.7783, -119.4179], zoom_start=6)

    for i, row in df_final.iterrows():
        if pd.notna(row["latitude"]) and pd.notna(row["longitude"]):
            folium.Marker(
                location=[row["latitude"], row["longitude"]],
                popup=f"{row['name']}<br>{row['address']}",
                icon=BeautifyIcon(icon="hotel", icon_shape="marker",
                                  background_color="darkblue", text_color="white",
                                  border_color="white", border_width=2)
            ).add_to(mapa)

    # Mostrar mapa en la app
    st_folium(mapa, width=1000, height=600)
