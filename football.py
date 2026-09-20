import requests
from datetime import datetime
import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

nombres_fases = {
    "LEAGUE_STAGE": "Fase de grupos",
    "PLAYOFFS": "Playoffs",
    "LAST_16": "Octavos de final",
    "QUARTER_FINALS": "Cuartos de final",
    "SEMI_FINALS": "Semifinales",
    "FINAL": "Final"
}

st.title("Resultados La Liga")

token = st.secrets["API_TOKEN"]
cabeceras = {"X-Auth-Token": token}

competiciones_disponibles = {
    "La Liga": "PD",
    "Champions League": "CL",
    "Premier League": "PL",
    "Bundesliga": "BL1",
    "Serie A": "SA",
    "Ligue 1": "FL1"
}

competicion_elegida = st.selectbox("¿Qué competición quieres ver?", list(competiciones_disponibles.keys()))
codigo_competicion = competiciones_disponibles[competicion_elegida]

@st.cache_data(ttl=600)
def obtener_partidos(codigo):
    respuesta = requests.get(f"https://api.football-data.org/v4/competitions/{codigo}/matches", headers=cabeceras)
    datos = respuesta.json()
    return datos["matches"]

@st.cache_data(ttl=600)
def obtener_clasificacion(codigo):
    respuesta = requests.get(f"https://api.football-data.org/v4/competitions/{codigo}/standings", headers=cabeceras)
    datos = respuesta.json()
    return datos["standings"][0]["table"]

partidos = obtener_partidos(codigo_competicion)
tabla_posiciones_completa = obtener_clasificacion(codigo_competicion)


tab1, tab2, tab3 = st.tabs(["Por jornada", "Por equipo", "Clasificación"])

with tab1:
    if codigo_competicion == "CL":
        fases_disponibles = sorted(set(partido["stage"] for partido in partidos))
        fase_elegida = st.selectbox(
            "¿Qué fase quieres ver?",
            fases_disponibles,
            format_func=lambda fase: nombres_fases.get(fase, fase)
        )
        if fase_elegida == "LEAGUE_STAGE":
            jornadas_disponibles = sorted(set(
                partido["matchday"] for partido in partidos if partido["stage"] == "LEAGUE_STAGE"
            ))
            jornada_actual_cl = partidos[0]["season"]["currentMatchday"]
            indice_jornada_actual = jornadas_disponibles.index(jornada_actual_cl) if jornada_actual_cl in jornadas_disponibles else 0
            jornada_buscada = st.selectbox(
                "¿Qué jornada?",
                index=indice_jornada_actual,
            )
        else:
            jornada_buscada = None
            jornada_actual_cl = None
    else:
        jornada_actual = partidos[0]["season"]["currentMatchday"]
        jornada_buscada = st.number_input(
            "¿Qué jornada quieres ver?",
            min_value=1,
            max_value=38,
            step=1,
            value=jornada_actual
        )
        jornada_actual_cl = None

    buscar = st.button("Buscar", key="buscar_jornada") or \
        (codigo_competicion != "CL" and jornada_buscada == jornada_actual) or \
        (codigo_competicion == "CL" and jornada_buscada == jornada_actual_cl)

    if buscar:
        if codigo_competicion == "CL":
            st.subheader(nombres_fases.get(fase_elegida, fase_elegida))
        else:
            st.subheader(f"Jornada {jornada_buscada}")

        filas = []

        for partido in partidos:
            if codigo_competicion == "CL":
                if jornada_buscada is not None:
                    coincide = partido["stage"] == fase_elegida and partido["matchday"] == jornada_buscada
                else:
                    coincide = partido["stage"] == fase_elegida
            else:
                coincide = partido["matchday"] == jornada_buscada

            if coincide:
                equipo_local = partido["homeTeam"]["name"]
                equipo_visitante = partido["awayTeam"]["name"]
                escudo_local = partido["homeTeam"]["crest"]
                escudo_visitante = partido["awayTeam"]["crest"]
                goles_local = partido["score"]["fullTime"]["home"]
                goles_visitante = partido["score"]["fullTime"]["away"]
                estado = partido["status"]

                fecha = datetime.fromisoformat(partido["utcDate"])
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
        )

equipo_favorito = "Real Madrid"

with tab2:
    nombres_equipos = sorted([equipo["team"]["name"] for equipo in tabla_posiciones_completa])

    indice_favorito = nombres_equipos.index(equipo_favorito) if equipo_favorito in nombres_equipos else 0

    equipo_buscado = st.selectbox(
        "¿De qué equipo quieres ver los resultados?",
        nombres_equipos,
        index=indice_favorito
    )

    buscar = st.button("Buscar", key="buscar_equipo") or equipo_buscado == equipo_favorito
    
    if buscar:
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
        )

with tab3:
    st.subheader("Clasificación La Liga")

    filas = []

    for equipo in tabla_posiciones_completa:
        diferencia_goles = equipo["goalsFor"] - equipo["goalsAgainst"]

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
            "DG": diferencia_goles,
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
    )