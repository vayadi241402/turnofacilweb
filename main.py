import streamlit as st
import json
import os
from datetime import datetime, timedelta
import pandas as pd
st.markdown("""
<style>
    .stApp {
        background-color: #0E1117;
    }
</style>
""", unsafe_allow_html=True)
# Configuración de la página
st.set_page_config(
    page_title="Turno Fácil Web",
    page_icon="🏥",
    layout="wide"
)
st.image("logo.png", width=250)
# Archivo donde se guardan los turnos
DATA_FILE = "data/turnos.json"


# Inicializar la base de datos si no existe
def init_data():
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump([], f)


# Cargar turnos existentes
def load_turnos():
    with open(DATA_FILE, "r") as f:
        return json.load(f)


# Guardar turnos
def save_turnos(turnos):
    with open(DATA_FILE, "w") as f:
        json.dump(turnos, f, indent=4, default=str)


# Función para generar horarios disponibles (cada 30 min, 9 a 17)
def generar_horarios(fecha):
    turnos_existentes = load_turnos()
    ocupados = [t["horario"] for t in turnos_existentes if t["fecha"] == fecha]

    horarios = []
    hora_inicio = 9
    hora_fin = 17
    for hora in range(hora_inicio, hora_fin):
        for minuto in [0, 30]:
            horario_str = f"{hora:02d}:{minuto:02d}"
            if horario_str not in ocupados:
                horarios.append(horario_str)
    return horarios


# Interfaz principal
def main():
    st.title("🏥 Turno Fácil Web")
    st.caption("Sistema digital para gestión de turnos en centros de salud")

    # Menú lateral
    menu = st.sidebar.selectbox(
        "Menú",
        ["📅 Sacar turno", "📋 Mis turnos", "🔧 Administración"]
    )

    # --- SECCIÓN SACAR TURNO ---
    if menu == "📅 Sacar turno":
        st.header("Solicitar nuevo turno médico")

        with st.form("form_turno"):
            nombre = st.text_input("Nombre completo")
            dni = st.text_input("DNI")
            especialidad = st.selectbox(
                "Especialidad",
                ["Medicina General", "Pediatría", "Cardiología", "Dermatología", "Traumatología"]
            )

            # Selección de fecha (mínimo hoy, máximo 30 días)
            min_date = datetime.now().date()
            max_date = min_date + timedelta(days=30)
            fecha = st.date_input("Fecha del turno", min_value=min_date, max_value=max_date)
            submitted = st.form_submit_button("Solicitar Turno")
            # Horarios disponibles
            fecha_str = fecha.strftime("%Y-%m-%d")
            horarios_disponibles = generar_horarios(fecha_str)

            if horarios_disponibles:
                horario = st.selectbox("Horario disponible", horarios_disponibles)
            else:
                st.warning("No hay horarios disponibles para esta fecha")
                horario = None

            submitted = st.form_submit_button("Confirmar turno")

            if submitted:
                if not nombre or not dni:
                    st.error("Completá nombre y DNI")
                elif not horario:
                    st.error("Seleccioná un horario válido")
                else:
                    turnos = load_turnos()
                    nuevo_turno = {
                        "id": len(turnos) + 1,
                        "nombre": nombre,
                        "dni": dni,
                        "especialidad": especialidad,
                        "fecha": fecha_str,
                        "horario": horario,
                        "estado": "activo"
                    }
                    turnos.append(nuevo_turno)
                    save_turnos(turnos)
                    st.success(f"✅ Turno confirmado para {nombre} el {fecha_str} a las {horario}")

    # --- SECCIÓN MIS TURNOS ---
    elif menu == "📋 Mis turnos":
        st.header("Consultar mis turnos")

        dni_busqueda = st.text_input("Ingresá tu DNI para ver tus turnos")

        if dni_busqueda:
            turnos = load_turnos()
            mis_turnos = [t for t in turnos if t["dni"] == dni_busqueda and t["estado"] == "activo"]

            if mis_turnos:
                for t in mis_turnos:
                    with st.container():
                        col1, col2, col3 = st.columns([2, 2, 1])
                        col1.write(f"**{t['especialidad']}**")
                        col2.write(f"{t['fecha']} - {t['horario']}")
                        if col3.button("Cancelar", key=f"cancel_{t['id']}"):
                            t["estado"] = "cancelado"
                            save_turnos(turnos)
                            st.rerun()
                        st.divider()
            else:
                st.info("No tenés turnos activos")

    # --- SECCIÓN ADMINISTRACIÓN ---
    else:
        st.header("Panel de Administración")
        clave = st.text_input("Clave de administrador", type="password")

        if clave == "admin123":  # Cambiá esto por una clave segura en producción
            turnos = load_turnos()

            if turnos:
                df = pd.DataFrame(turnos)
                df = df[["id", "nombre", "dni", "especialidad", "fecha", "horario", "estado"]]
                st.dataframe(df, use_container_width=True)

                # Filtro por estado
                estado_filtro = st.selectbox("Filtrar por estado", ["todos", "activo", "cancelado"])
                if estado_filtro != "todos":
                    df_filtrado = df[df["estado"] == estado_filtro]
                    st.dataframe(df_filtrado)

                # Exportar a CSV
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Exportar a CSV", csv, "turnos.csv", "text/csv")

                # Eliminar turnos antiguos
                if st.button("🗑️ Eliminar turnos pasados"):
                    hoy = datetime.now().date()
                    turnos_activos = [t for t in turnos if datetime.strptime(t["fecha"], "%Y-%m-%d").date() >= hoy]
                    save_turnos(turnos_activos)
                    st.success(f"Se eliminaron {len(turnos) - len(turnos_activos)} turnos vencidos")
                    st.rerun()
            else:
                st.info("No hay turnos registrados")
        elif clave:
            st.error("Clave incorrecta")


if __name__ == "__main__":
    init_data()
    main()