import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime


# --- 1. CONFIGURACIÓN DE LA BASE DE DATOS ---
def crear_db():
    conn = sqlite3.connect('finanzas_personales.db')
    cursor = conn.cursor()
    # Tabla de Movimientos
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS movimientos
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       fecha
                       TEXT,
                       tipo
                       TEXT,
                       categoria
                       TEXT,
                       monto
                       REAL,
                       descripcion
                       TEXT,
                       usuario
                       TEXT
                   )
                   ''')
    # Tabla de Usuarios
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS usuarios
                   (
                       username
                       TEXT
                       PRIMARY
                       KEY,
                       password
                       TEXT
                   )
                   ''')
    conn.commit()
    conn.close()


def registrar_usuario(user, pw):
    conn = sqlite3.connect('finanzas_personales.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO usuarios (username, password) VALUES (?, ?)", (user, pw))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def validar_usuario(user, pw):
    conn = sqlite3.connect('finanzas_personales.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE username = ? AND password = ?", (user, pw))
    resultado = cursor.fetchone()
    conn.close()
    return resultado


def guardar_movimiento(tipo, categoria, monto, detalle, usuario):
    conn = sqlite3.connect('finanzas_personales.db')
    cursor = conn.cursor()
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO movimientos (fecha, tipo, categoria, monto, descripcion, usuario) VALUES (?,?,?,?,?,?)",
                   (fecha, tipo, categoria, monto, detalle, usuario))
    conn.commit()
    conn.close()


# --- 2. INICIALIZACIÓN Y SESIÓN ---
crear_db()
st.set_page_config(page_title="FinanzIA PRO", layout="wide")

if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
    st.session_state['usuario'] = ""

# --- 3. LÓGICA DE ACCESO (LOGIN/REGISTRO) ---
if not st.session_state['autenticado']:
    st.title("🔐 Bienvenido a FinanzIA")
    col_log, col_img = st.columns([1, 1])

    with col_log:
        opcion = st.radio("Acción", ["Iniciar Sesión", "Registrarse"])
        user = st.text_input("Usuario")
        pw = st.text_input("Contraseña", type='password')

        if opcion == "Registrarse":
            if st.button("Crear mi cuenta"):
                if registrar_usuario(user, pw):
                    st.success("¡Cuenta creada! Ya puedes iniciar sesión.")
                else:
                    st.error("El usuario ya existe.")
        else:
            if st.button("Entrar"):
                if validar_usuario(user, pw):
                    st.session_state['autenticado'] = True
                    st.session_state['usuario'] = user
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas.")

else:
    # --- 4. LA APLICACIÓN (PARA USUARIOS LOGUEADOS) ---
    usuario_actual = st.session_state['usuario']

    with st.sidebar:
        st.title(f"👤 {usuario_actual}")
        if st.button("Cerrar Sesión"):
            st.session_state['autenticado'] = False
            st.rerun()
        st.divider()
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre",
                 "Noviembre", "Diciembre"]
        mes_sel = st.selectbox("Mes a consultar", meses, index=datetime.now().month - 1)
        mes_num = str(meses.index(mes_sel) + 1).zfill(2)
        presupuesto_limite = st.number_input("Límite mensual ($)", value=1000.0)
        porcentaje_ahorro = st.slider("Meta Ahorro (%)", 0, 50, 10)

    st.title("💰 Tu Panel Financiero Personal")
    t1, t2, t3 = st.tabs(["📝 Registrar", "📊 Dashboard", "📜 Historial"])

    with t1:
        with st.form("registro"):
            c1, c2 = st.columns(2)
            tipo = c1.selectbox("Tipo", ["Gasto", "Ingreso"])
            monto = c1.number_input("Monto", min_value=0.0)
            cat = c2.selectbox("Rubro",
                               ["Alimentación", "Salud", "Diversión", "Vivienda", "Transporte", "Educación", "Otro"])
            det = st.text_input("Nota")
            if st.form_submit_button("Guardar"):
                guardar_movimiento(tipo, cat, monto, det, usuario_actual)
                st.success("Guardado correctamente.")

    with t2:
        conn = sqlite3.connect('finanzas_personales.db')
        # FILTRO CRÍTICO: Solo datos del usuario actual y del mes seleccionado
        query = f"SELECT * FROM movimientos WHERE usuario = '{usuario_actual}' AND fecha LIKE '2026-{mes_num}%'"
        df = pd.read_sql_query(query, conn)
        conn.close()

        if not df.empty:
            ing = df[df['tipo'] == 'Ingreso']['monto'].sum()
            gas = df[df['tipo'] == 'Gasto']['monto'].sum()
            ahorro = ing * (porcentaje_ahorro / 100)

            st.metric("Disponible tras Ahorro", f"${(ing - gas - ahorro):,.2f}", delta=f"Meta: ${ahorro:,.2f}")

            c_g1, c_g2 = st.columns(2)
            c_g1.plotly_chart(
                px.pie(df[df['tipo'] == 'Gasto'], values='monto', names='categoria', hole=0.4, title="Tus Gastos"))
            c_g2.write("### Estado del Límite")
            c_g2.progress(min(gas / presupuesto_limite, 1.0))
        else:
            st.info("No hay datos para este mes.")

    with t3:
        conn = sqlite3.connect('finanzas_personales.db')
        df_h = pd.read_sql_query(
            f"SELECT id, fecha, tipo, categoria, monto, descripcion FROM movimientos WHERE usuario = '{usuario_actual}' ORDER BY fecha DESC",
            conn)
        st.dataframe(df_h, use_container_width=True)
        id_del = st.number_input("ID a borrar", step=1, min_value=1)
        if st.button("Eliminastreamlitr"):
            cursor = conn.cursor()
            cursor.execute("DELETE FROM movimientos WHERE id = ? AND usuario = ?", (id_del, usuario_actual))
            conn.commit()
            conn.close()
            st.rerun()