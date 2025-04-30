# app.py

import streamlit as st
import datetime

from data_fetching import (
    get_inflacion, get_tasa_monetaria, get_reservas,
    get_tipo_cambio, get_cny, get_merval, get_cedears
)
from plotting import (
    plot_inflacion, plot_tasa_monetaria, plot_reservas,
    plot_tipo_cambio, plot_cny, plot_merval, plot_cedears
)

# Configurar la página
st.set_page_config(page_title="Monitor Financiero", layout="wide")

# Sidebar - Selección de Fechas
st.sidebar.title("Configuración de Fechas")
today = datetime.date.today()

start_date = st.sidebar.date_input(
    "Fecha de inicio",
    value=datetime.date(2024, 8, 1),
    min_value=datetime.date(2020, 1, 1),
    max_value=today
)

end_date = st.sidebar.date_input(
    "Fecha de fin",
    value=today,
    min_value=start_date,
    max_value=today
)

# Título principal
st.title("Monitor Financiero de la Economía Argentina")

# --- Cargar Datos ---
with st.spinner('Descargando datos...'):
    df_inflacion = get_inflacion(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    df_tasa = get_tasa_monetaria(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    df_reservas = get_reservas(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    df_tc = get_tipo_cambio(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    df_cny = get_cny(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    df_merval = get_merval(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    df_cedears = get_cedears(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))

# --- Layout ---
col1, col2, col3 = st.columns(3)

with col1:
    st.plotly_chart(plot_inflacion(df_inflacion), use_container_width=True)
    st.plotly_chart(plot_tasa_monetaria(df_tasa), use_container_width=True)

with col2:
    st.plotly_chart(plot_reservas(df_reservas), use_container_width=True)
    st.plotly_chart(plot_tipo_cambio(df_tc), use_container_width=True)
    st.plotly_chart(plot_cny(df_cny), use_container_width=True)

with col3:
    st.plotly_chart(plot_merval(df_merval), use_container_width=True)
    st.plotly_chart(plot_cedears(df_cedears), use_container_width=True)

    st.markdown("""
    ### Comentarios y Análisis
    - Evolución de la inflación: ...
    - Comportamiento de las reservas: ...
    - Dinámica cambiaria oficial y paralela: ...
    - Evolución del mercado accionario argentino: ...
    """)


def test_yfinance_download():
    import yfinance as yf
    st.subheader("🧪 Prueba directa de yfinance")
    try:
        test_df = yf.download("^MERV", start="2024-01-01", end="2024-01-10").reset_index()
        if test_df.empty:
            st.error("⚠️ No se obtuvieron datos del Merval con yfinance.")
        else:
            st.success(f"✅ yfinance devolvió {test_df.shape[0]} filas.")
            st.write("Columnas:", test_df.columns.tolist())
            st.dataframe(test_df.head())
    except Exception as e:
        st.error(f"❌ Error al ejecutar yf.download: {e}")


# Footer
st.caption(f"Actualizado el {today.strftime('%d/%m/%Y')}")

