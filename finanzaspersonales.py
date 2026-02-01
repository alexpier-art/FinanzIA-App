import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="FinanzIA Eterna", layout="wide")

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)


# Función para leer datos
def leer_datos():
    return conn.read(worksheet="Hoja 1", ttl="0")


# Función para guardar una nueva fila
def guardar_fila(nueva_fila):
    df_actual = leer_datos()
    df_nuevo = pd.concat([df_actual, pd.DataFrame([nueva_fila])], ignore_index=True)
    conn.update(worksheet="Hoja 1", data=df_nuevo)


# --- LÓGICA DE USUARIOS ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
    st.session_state['usuario'] = ""

df_datos = leer_datos()

if not st.session_state['autenticado']:
    st.title("🔐 Acceso Permanente")
    opcion = st.radio("Acción", ["Entrar", "Registrarse"])
    user = st.text_input("Usuario")
    pw = st.text_input("Contraseña", type="password")

    if st.button("Confirmar"):
        if opcion == "Registrarse":
            if user in df_datos['usuario'].values:
                st.error("El usuario ya existe")
            else:
                nueva_cuenta = {"usuario": user, "password": pw, "fecha": datetime.now().strftime("%Y-%m-%d")}
                guardar_fila(nueva_cuenta)
                st.success("¡Cuenta creada para siempre!")
        else:
            # Validar Login
            validar = df_datos[(df_datos['usuario'] == user) & (df_datos['password'] == pw)]
            if not validar.empty:
                st.session_state['autenticado'] = True
                st.session_state['usuario'] = user
                st.rerun()
            else:
                st.error("Error de acceso")

else:
    # --- LA APP DE FINANZAS ---
    st.sidebar.title(f"Hola {st.session_state['usuario']}")
    if st.sidebar.button("Salir"):
        st.session_state['autenticado'] = False
        st.rerun()

    # Aquí va tu código de Registro de Gastos y Dashboard
    # PERO usando 'guardar_fila' en lugar de SQL
    st.write("¡Tus datos ahora se guardan en Google Sheets!")

    # Ejemplo de cómo guardar un gasto:
    # nueva_fila = {"fecha": "2026-02-01", "tipo": "Gasto", "monto": 50, "usuario": st.session_state['usuario']}
    # guardar_fila(nueva_fila)