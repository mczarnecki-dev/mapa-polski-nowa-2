import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from folium.plugins import PolyLineDecorator

geolocator = Nominatim(user_agent="moja_aplikacja")

def geokoduj(miejscowosc):
    try:
        location = geolocator.geocode(miejscowosc + ", Polska")
        if location:
            return location.latitude, location.longitude
        else:
            return None
    except:
        return None

st.title("Mapa Polski - wpisz miejscowości")

input_z = st.text_input("Z (miejsce startowe)")
input_do = st.text_input("Do (miejsce docelowe)")

if input_z and input_do:
    coord_z = geokoduj(input_z)
    coord_do = geokoduj(input_do)

    if coord_z is None:
        st.error(f"Nie znaleziono miejscowości: {input_z}")
    elif coord_do is None:
        st.error(f"Nie znaleziono miejscowości: {input_do}")
    else:
        # Środek mapy między dwoma punktami
        srodek_lat = (coord_z[0] + coord_do[0]) / 2
        srodek_lon = (coord_z[1] + coord_do[1]) / 2

        mapa = folium.Map(location=[srodek_lat, srodek_lon], zoom_start=6)

        folium.Marker(coord_z, tooltip="Start: " + input_z, icon=folium.Icon(color='green')).add_to(mapa)
        folium.Marker(coord_do, tooltip="Cel: " + input_do, icon=folium.Icon(color='red')).add_to(mapa)

        linia = folium.PolyLine(locations=[coord_z, coord_do], color="blue", weight=5).add_to(mapa)
        dekorator = PolyLineDecorator(linia, patterns=[dict(offset='100%', repeat='100%', symbol=folium.Symbol.arrowHead(color='blue', size=15))])
        mapa.add_child(dekorator)

        st_folium(mapa, width=700, height=500)
else:
    st.info("Wpisz miejscowości w polach 'Z' i 'Do', aby zobaczyć trasę.")
