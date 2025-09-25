import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from folium.plugins import BeautifyIcon
from streamlit_folium import st_folium
# Configuración de la página para que ocupe todo el ancho
st.set_page_config(layout="wide")

# Subir dataset
df = pd.read_csv("https://github.com/melody-10/Proyecto_Hoteles_California/blob/main/final_database.csv?raw=true")

# Crear estrellas
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

# Convertir columna ratings a diccionario
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

# Emojis para cada atributo
emoji_map = {"service": "🛎️", "cleanliness": "🧼", "overall": "⭐","value": "💰", "location": "📍", "sleep quality": "💤", "rooms": "🚪"}

# Estilos y diseño
st.markdown("""<style>
    /* Fondo General */
    .stApp { background: #f4f6f9; font-family: 'Segoe UI', sans-serif; }
    /* Título Hotel */
    .content-box { background: white; padding: 18px; border-radius: 10px; box-shadow: 0px 2px 8px rgba(0,0,0,0.07); margin-bottom: 12px; height: 100%; }
    .hotel-title { font-size: 22px; font-weight: bold; color: #2C3E50; text-align: center; }
    /* Reseña */
    .review-text { font-size: 15px; color: #444; line-height: 1.5; }
    /* Ratings */
    .ratings-title { font-weight: bold; font-size: 16px; margin-bottom: 10px; color: #2C3E50; }
    .rating-line { margin: 8px 0; font-size: 15px; color: #333; display: flex; align-items: center; justify-content: space-between; }
    </style>""", unsafe_allow_html=True)

# Título principal de la aplicación
st.title("🏨 Radiografía de un Hotel")

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

# Comprobación y Muestra de Resultados
if filtered_df.empty:
    st.warning("⚠️ No se encontraron reviews que coincidan con los filtros seleccionados. Por favor, intenta con otra combinación.")
else:
    for idx, row in filtered_df.iterrows():
        st.markdown(f"<div class='content-box hotel-title'>🏨 {row['name']}</div>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1.8, 1.3, 2])

        # Columna 1: Review
        with col1:
            st.markdown(f"""<div class="content-box"><p class="review-text">{row['text']}</p></div>""", unsafe_allow_html=True)

        # Columna 2: Ratings
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

        # Columna 3: Gráfico Comparativo
        with col3:
            hotel_name = row['name']
            current_ratings_dict = row.get("ratings_parsed", {})
            
            if current_ratings_dict and hotel_name in average_ratings_per_hotel.index:
                hotel_scores = {key: float(value) for key, value in current_ratings_dict.items() if str(value).replace('.', '', 1).isdigit()}
                
                if hotel_scores:
                    st.markdown('<div class="content-box" style="padding-bottom: 0; margin-bottom: 0;"><p class="ratings-title">Calificación de la Review vs. Promedio del Hotel</p></div>', unsafe_allow_html=True)
                    comparison_df = pd.DataFrame({'Review': pd.Series(hotel_scores), 'Promedio': average_ratings_per_hotel.loc[hotel_name]}).dropna()
                    stacked_df = pd.DataFrame(index=comparison_df.index)
                    stacked_df['Promedio del Hotel'] = comparison_df['Promedio']
                    stacked_df['Calificación de Reseña'] = (comparison_df['Review'] - comparison_df['Promedio']).clip(lower=0)
                    
                    st.bar_chart(stacked_df, height=300)
                else:
                    st.markdown('<div class="content-box"><p>No hay ratings numéricos para graficar.</p></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="content-box"><p>No hay ratings disponibles para comparar.</p></div>', unsafe_allow_html=True)
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
