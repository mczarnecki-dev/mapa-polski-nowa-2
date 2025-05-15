import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
import math

# Przykładowe trasy w pliku CSV (zakładamy, że jest 'trasy.csv' z kolumnami: start, start_lat, start_lon, end, end_lat, end_lon)
# Dla testów możesz użyć tego pliku:
# start,start_lat,start_lon,end,end_lat,end_lon
# Warszawa,52.2297,21.0122,Kraków,50.0647,19.9450
# Gdańsk,54.3520,18.6466,Wrocław,51.1079,17.0385
# Poznań,52.4064,16.9252,Lublin,51.2465,22.5684

@st.cache_data
def wczytaj_trasy():
    return pd.read_csv('trasy.csv')

def azymut(p1, p2):
    # Oblicza azymut (kąt) między dwoma punktami geograficznymi w stopniach (0-360)
    lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
    lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])
    dLon = lon2 - lon1

    x = math.sin(dLon) * math.cos(lat2)
    y = math.cos(lat1)*math.sin(lat2) - math.sin(lat1)*math.cos(lat2)*math.cos(dLon)
    brng = math.atan2(x, y)
    brng = math.degrees(brng)
    return (brng + 360) % 360

def podobny_azymut(a1, a2, tolerancja=20):
    # Sprawdza, czy dwa azymuty są podobne (w granicy ±tolerancja stopni)
    diff = abs(a1 - a2)
    return diff <= tolerancja or diff >= 360 - tolerancja

st.title("Interaktywna mapa tras w Polsce")

trasy = wczytaj_trasy()

input_z = st.text_input("Z (miejsce startowe)")
input_do = st.text_input("Do (miejsce docelowe)")

if input_z and input_do:
    # Znajdź współrzędne wpisanych miejsc (w danych tras szukamy)
    start = trasy[(trasy['start'].str.lower() == input_z.lower()) | (trasy['end'].str.lower() == input_z.lower())]
    koniec = trasy[(trasy['start'].str.lower() == input_do.lower()) | (trasy['end'].str.lower() == input_do.lower())]

    if start.empty or koniec.empty:
        st.warning("Nie znaleziono miejscowości w danych tras.")
    else:
        # Weź współrzędne miejsc z inputów (bierzemy pierwsze dopasowanie)
        def znajdz_wspolrzedne(nazwa):
            # szukaj w kolumnie start
            w = trasy[trasy['start'].str.lower() == nazwa.lower()]
            if not w.empty:
                return (w.iloc[0]['start_lat'], w.iloc[0]['start_lon'])
            # szukaj w kolumnie end
            w = trasy[trasy['end'].str.lower() == nazwa.lower()]
            if not w.empty:
                return (w.iloc[0]['end_lat'], w.iloc[0]['end_lon'])
            return None

        wsp_z = znajdz_wspolrzedne(input_z)
        wsp_do = znajdz_wspolrzedne(input_do)

        if not wsp_z or not wsp_do:
            st.warning("Nie znaleziono współrzędnych dla wybranych miejsc.")
        else:
            # Oblicz azymut wybranej trasy
            az = azymut(wsp_z, wsp_do)

            mapa = folium.Map(location=[(wsp_z[0]+wsp_do[0])/2, (wsp_z[1]+wsp_do[1])/2], zoom_start=6)

            # Dodaj linię wybranej trasy
            folium.Marker(wsp_z, tooltip="Start: " + input_z, icon=folium.Icon(color='green')).add_to(mapa)
            folium.Marker(wsp_do, tooltip="Cel: " + input_do, icon=folium.Icon(color='red')).add_to(mapa)
            folium.PolyLine(locations=[wsp_z, wsp_do], color='blue', weight=5).add_to(mapa)

            # Szukaj tras podobnych:
            for _, row in trasy.iterrows():
                p_start = (row['start_lat'], row['start_lon'])
                p_end = (row['end_lat'], row['end_lon'])
                az_trasa = azymut(p_start, p_end)

                # Sprawdź, czy trasy zmierzają w podobnym kierunku i ich końce są blisko (50 km)
                dist = geodesic(p_end, wsp_do).km
                if podobny_azymut(az, az_trasa) and dist <= 50:
                    folium.Marker(p_start, tooltip="Start istniejącej trasy: " + row['start'], icon=folium.Icon(color='gray')).add_to(mapa)
                    folium.Marker(p_end, tooltip="Koniec istniejącej trasy: " + row['end'], icon=folium.Icon(color='darkred')).add_to(mapa)
                    folium.PolyLine(locations=[p_start, p_end], color='gray', weight=3, dash_array='5').add_to(mapa)

            st_folium(mapa, width=700, height=500)

else:
    # Pusta mapa na start
    mapa = folium.Map(location=[52.237049, 21.017532], zoom_start=6)
    st_folium(mapa, width=700, height=500)
