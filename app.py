import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import math

def calculate_bearing(lat1, lon1, lat2, lon2):
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    diff_long = math.radians(lon2 - lon1)

    x = math.sin(diff_long) * math.cos(lat2_rad)
    y = math.cos(lat1_rad)*math.sin(lat2_rad) - (math.sin(lat1_rad)*math.cos(lat2_rad)*math.cos(diff_long))

    initial_bearing = math.atan2(x, y)
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360
    return compass_bearing

# Wczytaj dane tras z CSV
df = pd.read_csv('trasy.csv')  # start_lat,start_lon,end_lat,end_lon

st.title("Mapa Polski - wyszukiwanie tras")

input_z = st.text_input("Z (miejsce startowe) - wpisz współrzędne lat,lon")
input_do = st.text_input("Do (miejsce docelowe) - wpisz współrzędne lat,lon")

# Na start pusta mapa w centrum Polski
default_map = folium.Map(location=[52.0, 19.0], zoom_start=6)

# Pokazuj mapę dopiero po wpisaniu obu pól
if input_z and input_do:
    try:
        z_lat, z_lon = map(float, input_z.split(','))
        do_lat, do_lon = map(float, input_do.split(','))
    except Exception:
        st.error("Wprowadź współrzędne w formacie: lat,lon np. 52.2297,21.0122")
        st_folium(default_map, width=700, height=500)
        st.stop()

    azymut_wybranej = calculate_bearing(z_lat, z_lon, do_lat, do_lon)
    tolerance = 15

    podobne_trasy = []
    for _, row in df.iterrows():
        bearing = calculate_bearing(row['start_lat'], row['start_lon'], row['end_lat'], row['end_lon'])
        diff = abs(bearing - azymut_wybranej)
        diff = min(diff, 360 - diff)
        if diff <= tolerance:
            podobne_trasy.append(row)

    center_lat = (z_lat + do_lat) / 2
    center_lon = (z_lon + do_lon) / 2
    mapa = folium.Map(location=[center_lat, center_lon], zoom_start=6)

    folium.Marker([z_lat, z_lon], tooltip="Start (Twoja trasa)", icon=folium.Icon(color='green')).add_to(mapa)
    folium.Marker([do_lat, do_lon], tooltip="Cel (Twoja trasa)", icon=folium.Icon(color='red')).add_to(mapa)
    folium.PolyLine(locations=[[z_lat, z_lon], [do_lat, do_lon]], color='blue', weight=5).add_to(mapa)

    for trasa in podobne_trasy:
        folium.PolyLine(
            locations=[[trasa['start_lat'], trasa['start_lon']], [trasa['end_lat'], trasa['end_lon']]], 
            color='orange', weight=3, opacity=0.7).add_to(mapa)

    st_folium(mapa, width=700, height=500)
else:
    # Pokazujemy pustą mapę, jeśli nie wpisano danych
    st_folium(default_map, width=700, height=500)
