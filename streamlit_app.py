import streamlit as st
import datetime
import pandas as pd
import io

# --- FUNCIÓN PARA CONVERTIR DATAFRAME A EXCEL EN MEMORIA ---
@st.cache_data
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Cotizacion')
    processed_data = output.getvalue()
    return processed_data

# --- TÍTULO DE LA APP ---
st.title("Cotizador Uix")

# --- CONFIGURACIÓN DEL CATÁLOGO ---
CATALOGO = {
    "UX Designer": 1000,
    "UI Designer": 1200,
    "UX Writer": 1100,
    "UX/UI Designer": 1500,
    "UX Research": 2000
}

fecha = st.date_input(
    "Selecciona la fecha para la cotización",
    datetime.date.today()
)
# --- INICIALIZACIÓN DEL DATAFRAME EN SESSION STATE ---
# Si no existe un dataframe en la sesión, lo creamos.
if 'df_cotizacion' not in st.session_state:
    st.session_state.df_cotizacion = pd.DataFrame(columns=['Fecha', 'Cliente', 'Perfil', 'Precio/Hora', 'Personas', 'Horas', 'Total'])

st.write("Fecha seleccionada:", fecha)
# --- FORMULARIO PARA AÑADIR ITEMS ---
st.header("Añadir nuevo producto/servicio")
with st.form("formulario_item", clear_on_submit=True):
    fecha = st.date_input("Fecha", datetime.date.today())
    cliente = st.text_input("Nombre del Cliente")
    
    perfil = st.selectbox("Selecciona el Perfil", options=list(CATALOGO.keys()))
    personas = st.number_input("Cantidad de Personas", min_value=1, step=1)
    horas = st.number_input("Cantidad de Horas por persona", min_value=1, step=1)

    # Botón para enviar el formulario
    submitted = st.form_submit_button("Añadir a la Cotización")

    if submitted:
        if not cliente:
            st.warning("Por favor, completa el nombre del cliente.")
        else:
            precio_hora = CATALOGO[perfil]
            total_item = precio_hora * personas * horas
            # Creamos una nueva fila como un DataFrame
            nueva_fila = pd.DataFrame([{
                'Fecha': fecha,
                'Cliente': cliente,
                'Perfil': perfil,
                'Precio/Hora': precio_hora,
                'Personas': personas,
                'Horas': horas,
                'Total': total_item
            }])
            # Concatenamos la nueva fila al DataFrame existente en session_state
            st.session_state.df_cotizacion = pd.concat([st.session_state.df_cotizacion, nueva_fila], ignore_index=True)
            st.success("¡Producto añadido con éxito!")

# --- MOSTRAR COTIZACIÓN ACTUAL Y BOTÓN DE DESCARGA ---
st.header("Cotización Actual")
if not st.session_state.df_cotizacion.empty:
    st.dataframe(st.session_state.df_cotizacion)

    df_xlsx = to_excel(st.session_state.df_cotizacion)
    st.download_button(label='📥 Descargar Cotización en Excel',
                       data=df_xlsx,
                       file_name=f"cotizacion_{datetime.date.today().strftime('%Y%m%d')}.xlsx")
else:
    st.info("La cotización está vacía. Añade productos desde el formulario de arriba.")
