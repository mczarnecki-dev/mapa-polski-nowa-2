
import streamlit as st
import pandas as pd
import folium
from folium.plugins import PolyLineTextPath
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderUnavailable

# Funkcja do geolokalizacji miejscowości
@st.cache_data
def get_location(name):
    geolocator = Nominatim(user_agent="mapa_polski_app")
    try:
        location = geolocator.geocode(name + ", Polska")
        if location:
            return location.latitude, location.longitude
    except GeocoderUnavailable:
        return None
    return None

# Wczytanie istniejących tras z pliku
df_trasy = pd.read_csv("trasy.csv")

st.title("🗺️ Mapa Polski – trasy i planowanie")

# Pola do wpisania nowej trasy
z_miasto = st.text_input("Z (miejsce startowe)")
do_miasto = st.text_input("Do (miejsce docelowe)")

# Sprawdzenie i pobranie współrzędnych
nowa_trasa = None
if z_miasto and do_miasto:
    z_coord = get_location(z_miasto)
    do_coord = get_location(do_miasto)
    if z_coord and do_coord:
        nowa_trasa = {
            "start_nazwa": z_miasto,
            "start_lat": z_coord[0],
            "start_lon": z_coord[1],
            "koniec_nazwa": do_miasto,
            "koniec_lat": do_coord[0],
            "koniec_lon": do_coord[1]
        }

# Tworzenie mapy
mapa = folium.Map(location=[52.0, 19.0], zoom_start=6)

# Rysowanie istniejących tras
for _, row in df_trasy.iterrows():
    folium.Marker([row.start_lat, row.start_lon], tooltip=row.start_nazwa, icon=folium.Icon(color="gray")).add_to(mapa)
    folium.Marker([row.koniec_lat, row.koniec_lon], tooltip=row.koniec_nazwa, icon=folium.Icon(color="darkred")).add_to(mapa)
    linia = folium.PolyLine(
        locations=[[row.start_lat, row.start_lon], [row.koniec_lat, row.koniec_lon]],
        color="gray",
        weight=2,
        opacity=0.6
    )
    linia.add_to(mapa)

# Rysowanie nowej trasy
if nowa_trasa:
    folium.Marker([nowa_trasa["start_lat"], nowa_trasa["start_lon"]],
                  tooltip="Start: " + nowa_trasa["start_nazwa"],
                  icon=folium.Icon(color="green")).add_to(mapa)
    folium.Marker([nowa_trasa["koniec_lat"], nowa_trasa["koniec_lon"]],
                  tooltip="Cel: " + nowa_trasa["koniec_nazwa"],
                  icon=folium.Icon(color="red")).add_to(mapa)
    nowa_linia = folium.PolyLine(
        locations=[
            [nowa_trasa["start_lat"], nowa_trasa["start_lon"]],
            [nowa_trasa["koniec_lat"], nowa_trasa["koniec_lon"]]
        ],
        color="blue",
        weight=5
    )
    nowa_linia.add_to(mapa)
    # Dodanie strzałki (jako tekst na linii)
    PolyLineTextPath(nowa_linia, "   ➤   ", repeat=True, offset=8, attributes={"fill": "blue", "font-weight": "bold"}).add_to(mapa)

# Wyświetlenie mapy
st_folium(mapa, width=700, height=500)
