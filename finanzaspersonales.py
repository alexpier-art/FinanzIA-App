import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuración de página
st.set_page_config(page_title="FinanzIA", layout="wide")

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)


def leer_datos():
    try:
        # Buscamos 'Hoja 1' que es como la tienes en tu Google Sheets
        df = conn.read(worksheet="Hoja 1", ttl="0")
        if df.empty:
            return pd.DataFrame(columns=['fecha', 'tipo', 'categoria', 'monto', 'descripcion', 'usuario', 'password'])
        return df
    except Exception:
        # Si falla la lectura, devolvemos un DataFrame vacío con las columnas correctas
        return pd.DataFrame(columns=['fecha', 'tipo', 'categoria', 'monto', 'descripcion', 'usuario', 'password'])


def guardar_fila(nueva_fila):
    df_actual = leer_datos()
    df_nuevo = pd.concat([df_actual, pd.DataFrame([nueva_fila])], ignore_index=True)
    # Guardamos en 'Hoja 1'
    conn.update(worksheet="Hoja 1", data=df_nuevo)
    st.cache_data.clear()


# --- CARGA INICIAL DE DATOS ---
df_datos = leer_datos()

# Gestión de Sesión
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
    st.session_state['usuario'] = ""

# --- INTERFAZ DE ACCESO ---
if not st.session_state['autenticado']:
    st.title("🔐 Acceso a FinanzIA Permanente")

    tab_login, tab_reg = st.tabs(["Iniciar Sesión", "Registrarse"])

    with tab_login:
        user_log = st.text_input("Usuario", key="l_user")
        pass_log = st.text_input("Contraseña", type="password", key="l_pass")
        if st.button("Entrar"):
            # Validamos contra el Google Sheet
            if not df_datos.empty and 'usuario' in df_datos.columns:
                validar = df_datos[(df_datos['usuario'] == user_log) & (df_datos['password'] == pass_log)]
                if not validar.empty:
                    st.session_state['autenticado'] = True
                    st.session_state['usuario'] = user_log
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos")
            else:
                st.error("No hay usuarios registrados aún.")

    with tab_reg:
        user_reg = st.text_input("Crea un Usuario", key="r_user")
        pass_reg = st.text_input("Crea una Contraseña", type="password", key="r_pass")
        if st.button("Registrarme"):
            if user_reg == "" or pass_reg == "":
                st.warning("Por favor llena todos los campos")
            elif not df_datos.empty and user_reg in df_datos['usuario'].values:
                st.error("Este usuario ya existe, elige otro.")
            else:
                nueva_cuenta = {
                    "fecha": datetime.now().strftime("%Y-%m-%d"),
                    "tipo": "REGISTRO",
                    "categoria": "SISTEMA",
                    "monto": 0,
                    "descripcion": "Nuevo Usuario",
                    "usuario": user_reg,
                    "password": pass_reg
                }
                guardar_fila(nueva_cuenta)
                st.success("¡Cuenta creada con éxito! Ya puedes iniciar sesión.")

else:
    # --- APLICACIÓN PRINCIPAL ---
    st.sidebar.title(f"Bienvenido, {st.session_state['usuario']}")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state['autenticado'] = False
        st.rerun()

    st.title("💰 Mi Dashboard de Gastos (Google Sheets)")

    # Formulario de Gastos
    with st.expander("➕ Registrar Nuevo Movimiento"):
        with st.form("registro"):
            col1, col2 = st.columns(2)
            tipo = col1.selectbox("Tipo", ["Gasto", "Ingreso"])
            monto = col1.number_input("Monto ($)", min_value=0.0)
            cat = col2.selectbox("Categoría", ["Comida", "Salud", "Transporte", "Hogar", "Otros"])
            det = st.text_input("Detalle")

            if st.form_submit_button("Guardar en la Nube"):
                nuevo_movimiento = {
                    "fecha": datetime.now().strftime("%Y-%m-%d"),
                    "tipo": tipo,
                    "categoria": cat,
                    "monto": monto,
                    "descripcion": det,
                    "usuario": st.session_state['usuario'],
                    "password": ""  # Dejamos el password vacío para movimientos
                }
                guardar_fila(nuevo_movimiento)
                st.success("¡Datos guardados en Google Sheets!")
                st.rerun()

    # Mostrar Historial
    st.subheader("📜 Tus movimientos guardados")
    mis_datos = df_datos[df_datos['usuario'] == st.session_state['usuario']]
    # Quitamos la fila de registro para que no ensucie el historial
    mis_datos = mis_datos[mis_datos['tipo'] != "REGISTRO"]

    if not mis_datos.empty:
        st.dataframe(mis_datos[['fecha', 'tipo', 'categoria', 'monto', 'descripcion']], use_container_width=True)
    else:
        st.info("Aún no tienes movimientos. ¡Registra el primero arriba!")