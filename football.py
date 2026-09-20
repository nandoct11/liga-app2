#streamlit run football.py
import requests
from datetime import datetime
import streamlit as st
import pandas as pd

dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

st.title("Resultados La Liga")

token = "db0a169606a74dad8d77aefbb477156f"
cabeceras = {"X-Auth-Token": token}

@st.cache_data(ttl=600)  # NUEVO: cachea el resultado 600 segundos (10 minutos)
def obtener_partidos():  # NUEVO: envolvemos la petición en una función
    respuesta = requests.get("https://api.football-data.org/v4/competitions/PD/matches", headers=cabeceras)
    datos = respuesta.json()
    return datos["matches"]

@st.cache_data(ttl=600)  # NUEVO
def obtener_clasificacion():  # NUEVO
    respuesta = requests.get("https://api.football-data.org/v4/competitions/PD/standings", headers=cabeceras)
    datos = respuesta.json()
    return datos["standings"][0]["table"]

partidos = obtener_partidos()  # NUEVO: llamamos a la función en vez de hacer el requests.get directamente
tabla_posiciones_completa = obtener_clasificacion()  # NUEVO

st.write(f"Partidos totales recibidos: {len(partidos)}")

tipo_busqueda = st.radio("¿Cómo quieres buscar?", ["Por jornada", "Por equipo", "Clasificación"])


#POR JORNADA


if tipo_busqueda == "Por jornada":
    jornada_buscada = st.number_input("¿De qué jornada quieres ver los resultados?", min_value=1, max_value=38, step=1)

    if st.button("Buscar"):
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
            hide_index=True
        )


#POR EQUIPO


elif tipo_busqueda == "Por equipo":
    nombres_equipos = sorted([equipo["team"]["name"] for equipo in tabla_posiciones_completa])
    equipo_buscado = st.selectbox("¿De qué equipo quieres ver los resultados?", nombres_equipos)

    if st.button("Buscar"):
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
            hide_index=True
        )


#CLASIFICACIÓN


elif tipo_busqueda == "Clasificación":
    st.subheader("Clasificación La Liga")

    tabla_posiciones = tabla_posiciones_completa

    filas = []

    for equipo in tabla_posiciones:
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
    st.dataframe(
        tabla,
        column_config={
            "Escudo": st.column_config.ImageColumn(" ")
        },
        hide_index=True
    )
    st.subheader("Puntos por equipo")

    tabla_grafico = tabla.set_index("Equipo")["Pts"].sort_values(ascending=False)
    st.bar_chart(tabla_grafico)