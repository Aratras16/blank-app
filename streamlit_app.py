import streamlit as st
import datetime
import pandas as pd
import io
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# --- FUNCIÓN PARA CONVERTIR DATAFRAME A EXCEL EN MEMORIA ---
@st.cache_data
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Cotizacion')
    processed_data = output.getvalue()
    return processed_data

# --- FUNCIÓN PARA ENVIAR EMAIL ---
def send_email_with_attachment(recipient_email, subject, body, attachment_data, filename):
    # --- CONFIGURACIÓN DE EMAIL (Usa st.secrets para producción) ---
    # 1. Crea un archivo secrets.toml en la carpeta .streamlit
    # 2. Añade tus credenciales así:
    # EMAIL_SENDER = "tu_email@gmail.com"
    # EMAIL_PASSWORD = "tu_contraseña_de_aplicacion"
    
    try:
        sender_email = st.secrets["EMAIL_SENDER"]
        password = st.secrets["EMAIL_PASSWORD"]
    except FileNotFoundError:
        st.error("Archivo secrets.toml no encontrado. No se puede enviar el email.")
        return False
    except KeyError:
        st.error("Credenciales de email no configuradas en secrets.toml. No se puede enviar el email.")
        return False

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    part = MIMEApplication(attachment_data, Name=filename)
    part['Content-Disposition'] = f'attachment; filename="{filename}"'
    msg.attach(part)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(sender_email, password)
        smtp.send_message(msg)
    
    return True

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
    
# --- FORMULARIO PARA AÑADIR ITEMS ---
st.header("Añadir nuevo producto/servicio")
with st.form("formulario_item"):
    cliente = st.text_input("Nombre del Cliente")
    descripcion_proyecto = st.text_area("Descripción del Proyecto")
    st.markdown("---")

    # Crear una sección para cada perfil del catálogo
    for perfil, precio in CATALOGO.items():
        st.subheader(f"Perfil: {perfil} (${precio:,.2f}/hora)")
        if st.checkbox(f"Añadir {perfil}", key=f"check_{perfil}"):
            col1, col2 = st.columns(2)
            with col1:
                st.number_input("Cantidad de Personas", min_value=1, step=1, key=f"personas_{perfil}")
            with col2:
                st.number_input("Cantidad de Horas", min_value=1, step=1, key=f"horas_{perfil}")
        st.markdown("---")
    
    # --- CONFIRMACIÓN Y ENVÍO ---
    st.subheader("Confirmación y Envío")
    email_destinatario = st.text_input("Email para enviar la cotización", "ejemplo@cliente.com")
    confirmacion_envio = st.checkbox("¿Estás seguro? Marcar para enviar la cotización por correo al finalizar.")

    # Botón para enviar el formulario
    submitted = st.form_submit_button("Añadir a la Cotización")

    if submitted:
        if not cliente or not descripcion_proyecto:
            st.warning("Por favor, completa el nombre del cliente y la descripción del proyecto.")
        else:
            items_added = 0
            for perfil in CATALOGO.keys():
                if st.session_state[f"check_{perfil}"]:
                    personas = st.session_state[f"personas_{perfil}"]
                    horas = st.session_state[f"horas_{perfil}"]
                    precio_hora = CATALOGO[perfil]
                    total_item = precio_hora * personas * horas
                    
                    nueva_fila = pd.DataFrame([{'Fecha': fecha, 'Cliente': cliente, 'Perfil': perfil, 'Precio/Hora': precio_hora, 'Personas': personas, 'Horas': horas, 'Total': total_item}])
                    st.session_state.df_cotizacion = pd.concat([st.session_state.df_cotizacion, nueva_fila], ignore_index=True)
                    items_added += 1
            
            if items_added > 0:
                st.success(f"¡Se añadieron {items_added} perfiles a la cotización!")

                if confirmacion_envio:
                    st.info("Preparando el envío del correo...")
                    df_xlsx = to_excel(st.session_state.df_cotizacion)
                    file_name = f"cotizacion_{cliente.replace(' ', '_')}_{fecha.strftime('%Y%m%d')}.xlsx"
                    email_body = f"Hola {cliente},\n\nAdjunto la cotización para el proyecto:\n'{descripcion_proyecto}'\n\nSaludos cordiales."
                    if send_email_with_attachment(email_destinatario, f"Cotización de Servicios UX/UI para {cliente}", email_body, df_xlsx, file_name):
                        st.success(f"¡Correo enviado con éxito a {email_destinatario}!")

# --- MOSTRAR COTIZACIÓN ACTUAL Y BOTÓN DE DESCARGA ---
st.header("Cotización Actual")
if not st.session_state.df_cotizacion.empty:
    st.dataframe(st.session_state.df_cotizacion)

    df_xlsx = to_excel(st.session_state.df_cotizacion)
    st.download_button(label='📥 Descargar Cotización en Excel',
                       data=df_xlsx, 
                       file_name=f"cotizacion_{st.session_state.df_cotizacion['Cliente'].iloc[0].replace(' ', '_')}_{fecha.strftime('%Y%m%d')}.xlsx")
else:
    st.info("La cotización está vacía. Añade productos desde el formulario de arriba.")
