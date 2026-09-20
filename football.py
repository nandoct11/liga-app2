import requests
from datetime import datetime
import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

st.title("Resultados La Liga")

token = st.secrets["API_TOKEN"]
cabeceras = {"X-Auth-Token": token}

@st.cache_data(ttl=600)
def obtener_partidos():
    respuesta = requests.get("https://api.football-data.org/v4/competitions/PD/matches", headers=cabeceras)
    datos = respuesta.json()
    return datos["matches"]

@st.cache_data(ttl=600)
def obtener_clasificacion():
    respuesta = requests.get("https://api.football-data.org/v4/competitions/PD/standings", headers=cabeceras)
    datos = respuesta.json()
    return datos["standings"][0]["table"]

partidos = obtener_partidos()
tabla_posiciones_completa = obtener_clasificacion()

tab1, tab2, tab3 = st.tabs(["Por jornada", "Por equipo", "Clasificación"])

with tab1:
    jornada_buscada = st.number_input("¿De qué jornada quieres ver los resultados?", min_value=1, max_value=38, step=1)

    if st.button("Buscar", key="buscar_jornada"):
        st.subheader(f"Jornada {jornada_buscada}")

        filas = []

        for partido in partidos:
            if partido["matchday"] == jornada_buscada:
                equipo_local = partido["homeTeam"]["name"]
                equipo_visitante = partido["awayTeam"]["name"]
                escudo_local = partido["homeTeam"]["crest"]
                escudo_visitante = partido["awayTeam"]["crest"]
                goles_local = partido["score"]["fullTime"]["home"]
                goles_visitante = partido["score"]["fullTime"]["away"]
                estado = partido["status"]

                fecha_original = partido["utcDate"]
                fecha = datetime.fromisoformat(fecha_original)
                dia_semana = dias_semana[fecha.weekday()]
                fecha_legible = f"{dia_semana}, {fecha.strftime('%d/%m/%Y')}"

                if estado == "FINISHED":
                    resultado = f"{goles_local} - {goles_visitante}"
                elif estado == "TIMED":
                    resultado = "Fecha confirmada"
                else:
                    resultado = "Fecha provisional"

                filas.append({
                    "Fecha": fecha_legible,
                    "Escudo Local": escudo_local,
                    "Local": equipo_local,
                    "Resultado": resultado,
                    "Visitante": equipo_visitante,
                    "Escudo Visitante": escudo_visitante
                })

        tabla = pd.DataFrame(filas)
        st.dataframe(
            tabla,
            column_config={
                "Escudo Local": st.column_config.ImageColumn(" "),
                "Escudo Visitante": st.column_config.ImageColumn(" ")
            },
            hide_index=True,
            use_container_width=True,
            height=600
        )

with tab2:
    nombres_equipos = sorted([equipo["team"]["name"] for equipo in tabla_posiciones_completa])
    equipo_buscado = st.selectbox("¿De qué equipo quieres ver los resultados?", nombres_equipos)

    if st.button("Buscar", key="buscar_equipo"):
        filas = []

        for partido in partidos:
            equipo_local = partido["homeTeam"]["name"]
            equipo_visitante = partido["awayTeam"]["name"]
            escudo_local = partido["homeTeam"]["crest"]
            escudo_visitante = partido["awayTeam"]["crest"]

            if equipo_buscado == equipo_local or equipo_buscado == equipo_visitante:
                jornada = partido["matchday"]
                goles_local = partido["score"]["fullTime"]["home"]
                goles_visitante = partido["score"]["fullTime"]["away"]
                estado = partido["status"]

                fecha_original = partido["utcDate"]
                fecha = datetime.fromisoformat(fecha_original)
                dia_semana = dias_semana[fecha.weekday()]
                fecha_legible = f"{dia_semana}, {fecha.strftime('%d/%m/%Y')}"

                if estado == "FINISHED":
                    resultado = f"{goles_local} - {goles_visitante}"
                elif estado == "TIMED":
                    resultado = "Fecha confirmada"
                else:
                    resultado = "Fecha provisional"

                filas.append({
                    "Jornada": jornada,
                    "Fecha": fecha_legible,
                    "Escudo Local": escudo_local,
                    "Local": equipo_local,
                    "Resultado": resultado,
                    "Visitante": equipo_visitante,
                    "Escudo Visitante": escudo_visitante
                })

        tabla = pd.DataFrame(filas)
        st.dataframe(
            tabla,
            column_config={
                "Escudo Local": st.column_config.ImageColumn(" "),
                "Escudo Visitante": st.column_config.ImageColumn(" ")
            },
            hide_index=True,
            use_container_width=True,
            height=600
        )

with tab3:
    st.subheader("Clasificación La Liga")

    filas = []

    for equipo in tabla_posiciones_completa:
        filas.append({
            "Pos": equipo["position"],
            "Escudo": equipo["team"]["crest"],
            "Equipo": equipo["team"]["name"],
            "PJ": equipo["playedGames"],
            "G": equipo["won"],
            "E": equipo["draw"],
            "P": equipo["lost"],
            "GF": equipo["goalsFor"],
            "GC": equipo["goalsAgainst"],
            "Pts": equipo["points"]
        })

    tabla = pd.DataFrame(filas)

    def colorear_fila(fila):
        posicion = fila["Pos"]
        if posicion <= 4:
            color = "background-color: #1e5631"
        elif posicion == 5:
            color = "background-color: #4a4a1e"
        elif posicion >= 18:
            color = "background-color: #5c1e1e"
        else:
            color = ""
        return [color] * len(fila)

    tabla_coloreada = tabla.style.apply(colorear_fila, axis=1)

    st.dataframe(
        tabla_coloreada,
        column_config={
            "Escudo": st.column_config.ImageColumn(" ")
        },
        hide_index=True,
        use_container_width=True,
        height=600
    )