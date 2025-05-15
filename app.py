import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
import math

# --- Wczytanie danych ---
miejscowosci = pd.read_csv("miejscowosci_gus_sample.csv")
trasy = pd.read_csv("trasy.csv")

# --- Funkcje pomocnicze ---

def oblicz_azymut(start_lat, start_lon, end_lat, end_lon):
    # Oblicza azymut (kąt) między dwoma punktami w stopniach od północy (0-360)
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

def trasy_podobne_azymut(trasa_azymut, trasy_df, limit_km=50, limit_azymut=15):
    podobne_trasy = []
    for idx, row in trasy_df.iterrows():
        azymut_istniejacy = oblicz_azymut(row['start_lat'], row['start_lon'], row['koniec_lat'], row['koniec_lon'])
        # Sprawdz różnicę azymutu (kierunku)
        roznica_azymutu = min(abs(azymut_istniejacy - trasa_azymut), 360 - abs(azymut_istniejacy - trasa_azymut))
        if roznica_azymutu <= limit_azymut:
            # Sprawdź czy miejsce końcowe jest w promieniu limit_km
            if bliskosc_km((row['koniec_lat'], row['koniec_lon']), (wybrany_koniec_lat, wybrany_koniec_lon)) <= limit_km:
                podobne_trasy.append(row)
    return pd.DataFrame(podobne_trasy)

# --- Interfejs ---

st.title("Mapa Polski - połączenia i trasy podobne")

# Lista nazw miejscowości unikalnych do wyboru
miejscowosci_lista = miejscowosci["Nazwa"].dropna().unique()

input_z = st.selectbox("Z (miejsce startowe)", options=miejscowosci_lista)
input_do = st.selectbox("Do (miejsce docelowe)", options=miejscowosci_lista)

if input_z and input_do and input_z != input_do:

    # Pobierz współrzędne miejscowości start i koniec z miejscowosci
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

    # Oblicz azymut dla wybranej trasy
    wybrany_azymut = oblicz_azymut(wybrany_start_lat, wybrany_start_lon, wybrany_koniec_lat, wybrany_koniec_lon)

    # Znajdź trasy podobne
    podobne = trasy_podobne_azymut(wybrany_azymut, trasy)

    # Utwórz mapę na środek wybranej trasy
    srodek_lat = (wybrany_start_lat + wybrany_koniec_lat) / 2
    srodek_lon = (wybrany_start_lon + wybrany_koniec_lon) / 2
    mapa = folium.Map(location=[srodek_lat, srodek_lon], zoom_start=7)

    # Dodaj wybraną trasę
    folium.Marker([wybrany_start_lat, wybrany_start_lon], tooltip=f"Start: {input_z}", icon=folium.Icon(color='green')).add_to(mapa)
    folium.Marker([wybrany_koniec_lat, wybrany_koniec_lon], tooltip=f"Cel: {input_do}", icon=folium.Icon(color='red')).add_to(mapa)
    folium.PolyLine(locations=[[wybrany_start_lat, wybrany_start_lon], [wybrany_koniec_lat, wybrany_koniec_lon]],
                    color="blue", weight=5, opacity=0.8).add_to(mapa)

    # Dodaj podobne trasy (zielone)
    for _, r in podobne.iterrows():
        folium.Marker([r['start_lat'], r['start_lon']], tooltip=f"Start: {r['start_nazwa']}", icon=folium.Icon(color='lightgreen')).add_to(mapa)
        folium.Marker([r['koniec_lat'], r['koniec_lon']], tooltip=f"Cel: {r['koniec_nazwa']}", icon=folium.Icon(color='lightred')).add_to(mapa)
        folium.PolyLine(locations=[[r['start_lat'], r['start_lon']], [r['koniec_lat'], r['koniec_lon']]],
                        color="green", weight=4, opacity=0.6, dash_array='5').add_to(mapa)

    st_folium(mapa, width=700, height=500)

else:
    st.info("Wybierz miejscowości startową i docelową, aby wyświetlić trasę i podobne połączenia.")
    # Pusta mapa
    mapa = folium.Map(location=[52.0, 19.0], zoom_start=6)
    st_folium(mapa, width=1800, height=700)
