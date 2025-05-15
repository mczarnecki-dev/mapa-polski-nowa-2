import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
import math

st.set_page_config(layout="wide")

# --- Wczytanie danych ---
miejscowosci = pd.read_csv("miejscowosci_gus_sample.csv")
trasy = pd.read_csv("trasy.csv")

# --- Jeśli brak dat w pliku, można dodać testowe daty ---
# trasy['data_wyjazdu'] = '2025-05-10'
# trasy['data_przyjazdu'] = '2025-05-11'

# --- Funkcje pomocnicze ---

def oblicz_azymut(start_lat, start_lon, end_lat, end_lon):
    lat1 = math.radians(start_lat)
    lat2 = math.radians(end_lat)
    diff_lon = math.radians(end_lon - start_lon)
    x = math.sin(diff_lon) * math.cos(lat2)
    y = math.cos(lat1)*math.sin(lat2) - math.sin(lat1)*math.cos(lat2)*math.cos(diff_lon)
    initial_bearing = math.atan2(x, y)
    bearing = math.degrees(initial_bearing)
    compass_bearing = (bearing + 360) % 360
    return compass_bearing

def bliskosc_km(p1, p2):
    return geodesic(p1, p2).km

def trasy_podobne_azymut(trasa_azymut, trasy_df, wybrany_koniec_lat, wybrany_koniec_lon, limit_km=50, limit_azymut=15):
    podobne_trasy = []
    for idx, row in trasy_df.iterrows():
        azymut_istniejacy = oblicz_azymut(row['start_lat'], row['start_lon'], row['koniec_lat'], row['koniec_lon'])
        roznica_azymutu = min(abs(azymut_istniejacy - trasa_azymut), 360 - abs(azymut_istniejacy - trasa_azymut))
        if roznica_azymutu <= limit_azymut:
            if bliskosc_km((row['koniec_lat'], row['koniec_lon']), (wybrany_koniec_lat, wybrany_koniec_lon)) <= limit_km:
                podobne_trasy.append(row)
    return pd.DataFrame(podobne_trasy)

def dystans_trasy(lat1, lon1, lat2, lon2):
    return bliskosc_km((lat1, lon1), (lat2, lon2))

# --- Styl CSS wymuszający rozmiar mapy ---
st.markdown(
    """
    <style>
    .folium-map {
        width: 100% !important;
        height: 900px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🗺️ Mapa Polski - połączenia i trasy podobne")

miejscowosci_lista = miejscowosci["Nazwa"].dropna().unique()

input_z = st.selectbox("Z (miejsce startowe)", options=miejscowosci_lista)
input_do = st.selectbox("Do (miejsce docelowe)", options=miejscowosci_lista)

# Dodatkowe suwaki do regulacji filtrów
limit_km = st.slider("Promień wyszukiwania podobnych tras (km)", min_value=10, max_value=200, value=50, step=5)
limit_azymut = st.slider("Maksymalna różnica azymutu (stopnie)", min_value=0, max_value=50, value=15, step=1)

if input_z and input_do and input_z != input_do:
    try:
        start_data = miejscowosci[miejscowosci["Nazwa"] == input_z].iloc[0]
        koniec_data = miejscowosci[miejscowosci["Nazwa"] == input_do].iloc[0]
    except IndexError:
        st.error("Nie znaleziono współrzędnych dla wybranych miejscowości.")
        st.stop()

    wybrany_start_lat = start_data["Lat"]
    wybrany_start_lon = start_data["Lon"]
    wybrany_koniec_lat = koniec_data["Lat"]
    wybrany_koniec_lon = koniec_data["Lon"]

    wybrany_azymut = oblicz_azymut(wybrany_start_lat, wybrany_start_lon, wybrany_koniec_lat, wybrany_koniec_lon)
    podobne = trasy_podobne_azymut(wybrany_azymut, trasy, wybrany_koniec_lat, wybrany_koniec_lon, limit_km=limit_km, limit_azymut=limit_azymut)

    srodek_lat = (wybrany_start_lat + wybrany_koniec_lat) / 2
    srodek_lon = (wybrany_start_lon + wybrany_koniec_lon) / 2

    kol1, kol2 = st.columns([3, 1])

    with kol1:
        mapa = folium.Map(location=[srodek_lat, srodek_lon], zoom_start=7)

        folium.Marker([wybrany_start_lat, wybrany_start_lon], tooltip=f"Start: {input_z}", icon=folium.Icon(color='green')).add_to(mapa)
        folium.Marker([wybrany_koniec_lat, wybrany_koniec_lon], tooltip=f"Cel: {input_do}", icon=folium.Icon(color='red')).add_to(mapa)
        folium.PolyLine(locations=[[wybrany_start_lat, wybrany_start_lon], [wybrany_koniec_lat, wybrany_koniec_lon]],
                        color="blue", weight=5, opacity=0.8).add_to(mapa)

        for _, r in podobne.iterrows():
            folium.Marker([r['start_lat'], r['start_lon']], tooltip=f"Start: {r['start_nazwa']}", icon=folium.Icon(color='lightgreen')).add_to(mapa)
            folium.Marker([r['koniec_lat'], r['koniec_lon']], tooltip=f"Cel: {r['koniec_nazwa']}", icon=folium.Icon(color='lightred')).add_to(mapa)
            folium.PolyLine(locations=[[r['start_lat'], r['start_lon']], [r['koniec_lat'], r['koniec_lon']]],
                            color="green", weight=4, opacity=0.6, dash_array='5').add_to(mapa)

        st_folium(mapa, width=900, height=700)

    with kol2:
        st.markdown("<div style='font-size:12px;'>", unsafe_allow_html=True)

        st.markdown("<div style='font-size:16px; font-weight:bold; margin-bottom: 10px;'>🧭 Informacje o wybranej trasie</div>", unsafe_allow_html=True)
        dystans_wybranej = dystans_trasy(wybrany_start_lat, wybrany_start_lon, wybrany_koniec_lat, wybrany_koniec_lon)
        st.write(f"🚩 Start: **{input_z}**")
        st.write(f"🏁 Cel: **{input_do}**")
        st.write(f"📏 Dystans: **{dystans_wybranej:.2f} km**")
        st.write(f"🧭 Azymut: **{wybrany_azymut:.1f}°**")

        # Dodane daty wybranej trasy
        st.write(f"📅 Data wyjazdu: **{start_data.get('data_wyjazdu', 'brak danych')}**")
        st.write(f"📅 Data przyjazdu: **{koniec_data.get('data_przyjazdu', 'brak danych')}**")

        st.markdown("---")

        st.markdown("<div style='font-size:16px; font-weight:bold; margin-bottom: 10px;'>🔍 Podobne trasy</div>", unsafe_allow_html=True)
        if podobne.empty:
            st.write("😕 Brak podobnych tras w zadanym zakresie.")
        else:
            for i, r in podobne.iterrows():
                d = dystans_trasy(r['start_lat'], r['start_lon'], r['koniec_lat'], r['koniec_lon'])
                az = oblicz_azymut(r['start_lat'], r['start_lon'], r['koniec_lat'], r['koniec_lon'])
                st.write(f"➡️ **{r['start_nazwa']}** → **{r['koniec_nazwa']}**")
                st.write(f"📏 Dystans: {d:.2f} km")
                st.write(f"🧭 Azymut: {az:.1f}°")

                # Dodane daty dla podobnych tras
                st.write(f"📅 Data wyjazdu: **{r.get('data_wyjazdu', 'brak danych')}**")
                st.write(f"📅 Data przyjazdu: **{r.get('data_przyjazdu', 'brak danych')}**")

                st.markdown("---")

        st.markdown("</div>", unsafe_allow_html=True)

else:
    st.info("🔎 Wybierz miejscowości **startową** i **docelową**, aby wyświetlić trasę oraz podobne połączenia na mapie.")
    mapa = folium.Map(location=[52.0, 19.0], zoom_start=6)
    st_folium(mapa, width=900, height=700)
