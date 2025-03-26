import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go

st.title("Comparativa: Variable Monetaria vs Tipo de Cambio USD (BCRA)")

# =============================
# OBTENER VARIABLES DISPONIBLES
# =============================
url_var_info = "https://api.bcra.gob.ar/estadisticas/v3.0/monetarias"
res_info = requests.get(url_var_info, verify=False)

if res_info.status_code != 200:
    st.stop("❌ No se pudieron obtener las variables disponibles desde la API del BCRA.")

df_info = pd.DataFrame(res_info.json()["results"])
df_info = df_info.sort_values("descripcion")

# Selección de variable desde selectbox
descripcion_seleccionada = st.selectbox("Seleccioná una variable monetaria", df_info["descripcion"])
id_variable = df_info[df_info["descripcion"] == descripcion_seleccionada].iloc[0]["idVariable"]

# =============================
# SELECCIÓN DE FECHAS
# =============================
hoy = datetime.today()
fecha_inicio = st.date_input("Fecha de inicio", datetime(2024, 1, 1))
fecha_fin = st.date_input("Fecha de fin", hoy)

if fecha_inicio > fecha_fin:
    st.warning("La fecha de inicio no puede ser posterior a la fecha de fin.")
    st.stop()

# =============================
# CARGAR VARIABLE MONETARIA
# =============================
url_data = f"https://api.bcra.gob.ar/estadisticas/v3.0/monetarias/{id_variable}"
params = {"desde": fecha_inicio.strftime("%Y-%m-%d"), "hasta": fecha_fin.strftime("%Y-%m-%d"), "limit": 3000}
r = requests.get(url_data, params=params, verify=False)

if r.status_code != 200:
    st.stop("Error al obtener los datos de la variable monetaria.")

data = r.json()["results"]
df_v = pd.DataFrame(data)
df_v["fecha"] = pd.to_datetime(df_v["fecha"])
df_v = df_v[["fecha", "valor"]].rename(columns={"valor": "valor_variable"})

# =============================
# COTIZACIÓN USD
# =============================
url_usd = "https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones/USD"
params_usd = {
    "fechadesde": fecha_inicio.strftime("%Y-%m-%d"),
    "fechahasta": fecha_fin.strftime("%Y-%m-%d"),
    "limit": 1000
}
r_usd = requests.get(url_usd, params=params_usd, verify=False)

if r_usd.status_code != 200:
    st.stop("Error al obtener el tipo de cambio USD.")

data_usd = r_usd.json()["results"]
usd_registros = []
for dia in data_usd:
    fecha = dia["fecha"]
    for cot in dia["detalle"]:
        if isinstance(cot["tipoCotizacion"], (int, float)):
            usd_registros.append({"fecha": fecha, "tipoCotizacion": cot["tipoCotizacion"]})

df_usd = pd.DataFrame(usd_registros)
df_usd["fecha"] = pd.to_datetime(df_usd["fecha"])
df_usd = df_usd.groupby("fecha").mean(numeric_only=True).reset_index()

# =============================
# UNIR DATOS
# =============================
df = pd.merge(df_v, df_usd, on="fecha", how="inner")
if df.empty:
    st.stop("No hay datos para el período seleccionado.")

# =============================
# GRAFICAR
# =============================
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df["fecha"],
    y=df["valor_variable"],
    mode='lines',
    name=descripcion_seleccionada,
    yaxis="y1"
))

fig.add_trace(go.Scatter(
    x=df["fecha"],
    y=df["tipoCotizacion"],
    mode='lines',
    name="Tipo de Cambio USD",
    yaxis="y2"
))

try:
    fig.update_layout(
        title=f"{descripcion_seleccionada} vs Tipo de Cambio USD (BCRA)",
        xaxis=dict(title="Fecha"),
        yaxis=dict(title=descripcion_seleccionada, titlefont=dict(color="blue"), tickfont=dict(color="blue")),
        yaxis2=dict(title="Tipo de Cambio USD", titlefont=dict(color="red"),
                    tickfont=dict(color="red"), overlaying="y", side="right"),
        legend=dict(x=0.01, y=0.99),
        height=500,
        width=900
    )
except Exception as e:
    st.error(f"Error al actualizar el layout: {e}")
    st.stop()

st.plotly_chart(fig, use_container_width=True)
