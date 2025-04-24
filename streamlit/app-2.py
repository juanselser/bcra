import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import yfinance as yf

st.title("Indicadores Económicos Argentina (BCRA)")

# =============================
# OBTENER VARIABLES DISPONIBLES
# =============================
url_var_info = "https://api.bcra.gob.ar/estadisticas/v3.0/monetarias"
res_info = requests.get(url_var_info, verify=False)

if res_info.status_code != 200:
    st.stop("No se pudieron obtener las variables disponibles desde la API del BCRA.")

df_info = pd.DataFrame(res_info.json()["results"])
df_info = df_info.sort_values("descripcion")

# =============================
# FUNCIONES REUTILIZABLES
# =============================
def get_bcra_variable(id_variable, fecha_inicio, fecha_fin):
    url = f"https://api.bcra.gob.ar/estadisticas/v3.0/monetarias/{id_variable}"
    params = {"desde": fecha_inicio.strftime("%Y-%m-%d"), 
              "hasta": fecha_fin.strftime("%Y-%m-%d"), 
              "limit": 3000}
    r = requests.get(url, params=params, verify=False)
    if r.status_code == 200:
        df = pd.DataFrame(r.json()["results"])
        df["fecha"] = pd.to_datetime(df["fecha"])
        return df[["fecha", "valor"]]
    else:
        raise Exception(f"Error al obtener variable {id_variable}")

def get_usd_oficial(fecha_inicio, fecha_fin):
    url = "https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones/USD"
    params = {"fechadesde": fecha_inicio.strftime("%Y-%m-%d"),
              "fechahasta": fecha_fin.strftime("%Y-%m-%d"),
              "limit": 1000}
    r = requests.get(url, params=params, verify=False)
    data = r.json()["results"]
    registros = []
    for d in data:
        fecha = d["fecha"]
        for cot in d["detalle"]:
            registros.append({"fecha": fecha, "usd_oficial": cot["tipoCotizacion"]})
    df = pd.DataFrame(registros)
    df["fecha"] = pd.to_datetime(df["fecha"])
    return df.groupby("fecha").mean().reset_index()

def get_usd_blue():
    url = "https://api.bluelytics.com.ar/v2/evolution.json"
    r = requests.get(url)
    data = r.json()
    blue_data = [entry for entry in data if entry["source"] == "Blue"]
    df = pd.DataFrame(blue_data)
    df["fecha"] = pd.to_datetime(df["date"])
    df["usd_blue"] = (df["value_buy"] + df["value_sell"]) / 2
    return df[["fecha", "usd_blue"]]

def get_merval(fecha_inicio, fecha_fin):
    merval = yf.download("^MERV", start=fecha_inicio, end=fecha_fin)
    if isinstance(merval.columns, pd.MultiIndex):
        merval.columns = merval.columns.droplevel(1)
    merval = merval.reset_index()[['Date', 'Close']].rename(
        columns={'Date': 'fecha', 'Close': 'merval_ars'})
    return merval

# =============================
# INTERFAZ DE USUARIO
# =============================
tab1, tab2, tab3 = st.tabs([
    "Variable vs USD", 
    "Respaldo Cambiario", 
    "Merval en USD"
])

with tab1:
    # Contenido de la pestaña original
    descripcion_seleccionada = st.selectbox("Seleccioná una variable monetaria", df_info["descripcion"])
    id_variable = df_info[df_info["descripcion"] == descripcion_seleccionada].iloc[0]["idVariable"]

    hoy = datetime.today()
    fecha_inicio = st.date_input("Fecha de inicio", datetime(2024, 1, 1))
    fecha_fin = st.date_input("Fecha de fin", hoy)

    if fecha_inicio > fecha_fin:
        st.warning("La fecha de inicio no puede ser posterior a la fecha de fin.")
        st.stop()

    # Cargar datos
    df_v = get_bcra_variable(id_variable, fecha_inicio, fecha_fin).rename(columns={"valor": "valor_variable"})
    df_usd = get_usd_oficial(fecha_inicio, fecha_fin)
    
    # Unir datos
    df = pd.merge(df_v, df_usd, on="fecha", how="inner")
    if df.empty:
        st.warning("No hay datos para el período seleccionado.")
    else:
        # Gráfico
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["fecha"], y=df["valor_variable"],
            mode='lines', name=descripcion_seleccionada, yaxis="y1"
        ))
        fig.add_trace(go.Scatter(
            x=df["fecha"], y=df["usd_oficial"],
            mode='lines', name="Tipo de Cambio USD", yaxis="y2"
        ))
        fig.update_layout(
            title=f"{descripcion_seleccionada} vs Tipo de Cambio USD (BCRA)",
            xaxis=dict(title="Fecha"),
            yaxis=dict(title=descripcion_seleccionada, tickfont=dict(color="blue")),
            yaxis2=dict(title="Tipo de Cambio USD", tickfont=dict(color="red"), 
                       overlaying="y", side="right"),
            legend=dict(x=0.01, y=0.99),
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("Respaldo y presión cambiaria")
    
    # IDs de variables fijas para este análisis
    id_base_monetaria = 15  # Base monetaria
    id_reservas = 1         # Reservas internacionales
    
    # Descargar datos
    try:
        df_base = get_bcra_variable(id_base_monetaria, fecha_inicio, fecha_fin).rename(columns={"valor": "base_monetaria"})
        df_reservas = get_bcra_variable(id_reservas, fecha_inicio, fecha_fin).rename(columns={"valor": "reservas"})
        df_usd_blue = get_usd_blue()
        
        # Unir datos
        df = pd.merge(df_base, df_reservas, on="fecha", how="outer")
        df = pd.merge(df, get_usd_oficial(fecha_inicio, fecha_fin), on="fecha", how="outer")
        df = pd.merge(df, df_usd_blue, on="fecha", how="outer")
        df = df.sort_values("fecha").dropna(subset=["base_monetaria", "reservas", "usd_oficial"])
        
        # Calcular indicadores
        df["base_usd"] = df["base_monetaria"] / df["usd_oficial"]
        
        # Gráfico
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=df["fecha"], y=df["base_usd"],
            name="Base monetaria en USD", mode="lines", line=dict(color="royalblue")))
        fig2.add_trace(go.Scatter(
            x=df["fecha"], y=df["reservas"],
            name="Reservas netas internacionales", mode="lines", line=dict(color="firebrick")))
        fig2.add_trace(go.Scatter(
            x=df["fecha"], y=df["usd_blue"],
            name="Tipo de cambio paralelo (Blue)", mode="lines", yaxis="y2", line=dict(color="seagreen")))
        fig2.add_trace(go.Scatter(
            x=df["fecha"], y=df["usd_oficial"],
            name="Tipo de cambio oficial", mode="lines", yaxis="y2",
            line=dict(color="mediumseagreen", dash="dot")))
        
        fig2.update_layout(
            title="Respaldo y presión cambiaria",
            xaxis=dict(title="Fecha", rangeslider=dict(visible=True)),
            yaxis=dict(title="Reservas / Base Monetaria (en USD)", titlefont=dict(color="royalblue")),
            yaxis2=dict(title="Tipo de cambio (ARS/USD)", titlefont=dict(color="seagreen"),
                       overlaying="y", side="right"),
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
            height=600
        )
        st.plotly_chart(fig2, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error al generar el gráfico: {str(e)}")

with tab3:
    st.header("Confianza del mercado: Merval en USD")
    
    try:
        # Obtener datos
        df_merval = get_merval(fecha_inicio, fecha_fin)
        df_usd_blue = get_usd_blue()
        
        # Unir y calcular
        df = pd.merge(df_merval, df_usd_blue, on="fecha", how="inner")
        df["merval_usd"] = df["merval_ars"] / df["usd_blue"]
        
        # Gráfico
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=df["fecha"], y=df["merval_usd"],
            mode="lines", name="Merval en USD", line=dict(color="darkblue")))
        
        fig3.update_layout(
            title="Merval en dólares blue",
            xaxis=dict(title="Fecha", rangeslider=dict(visible=True)),
            yaxis=dict(title="Índice Merval (USD)"),
            height=500
        )
        st.plotly_chart(fig3, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error al obtener datos del Merval: {str(e)}")