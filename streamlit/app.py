import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go

# =============================
# 🔧 PARÁMETROS – EDITÁ ACÁ
# =============================
id_variable = 15 # ID variable (Reservas = 1)
fecha_inicio = "2024-01-01"
fecha_fin = "2025-03-25"

# =============================
# DESCARGAR SERIE DE TIEMPO
# =============================

url_data = f"https://api.bcra.gob.ar/estadisticas/v3.0/monetarias/{id_variable}"
params = {"desde": fecha_inicio, "hasta": fecha_fin, "limit": 3000}
r = requests.get(url_data, params=params, verify=False)

if r.status_code == 200:
    data = r.json()["results"]
    df_v = pd.DataFrame(data)
    df_v["fecha"] = pd.to_datetime(df_v["fecha"])
    df_v = df_v[["fecha", "valor"]]
else:
    raise Exception("Error al obtener variables")

# =============================
# OBTENER COTIZACIÓN USD
# =============================

url_usd = "https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones/USD"
params_usd = {
    "fechadesde": fecha_inicio,
    "fechahasta": fecha_fin,
    "limit": 1000
}
r_usd = requests.get(url_usd, params=params_usd, verify=False)
data_usd = r_usd.json()["results"]

usd_registros = []
for dia in data_usd:
    fecha = dia["fecha"]
    for cot in dia["detalle"]:
        usd_registros.append({
            "fecha": fecha,
            "tipoCotizacion": cot["tipoCotizacion"]
        })

df_usd = pd.DataFrame(usd_registros)
df_usd["fecha"] = pd.to_datetime(df_usd["fecha"])
df_usd = df_usd.groupby("fecha").mean().reset_index()

# =============================

# =============================

# Obtener el nombre de la variable desde la API (último valor disponible)
# Para mostrarlo en el gráfico
url_var_info = "https://api.bcra.gob.ar/estadisticas/v3.0/monetarias"
res_info = requests.get(url_var_info, verify=False)
if res_info.status_code == 200:
    df_info = pd.DataFrame(res_info.json()["results"])
    nombre_variable = df_info[df_info["idVariable"] == id_variable].iloc[0]["descripcion"]
else:
    nombre_variable = f"Variable ID {id_variable}"  # fallback en caso de error

# Renombrar columna de valor con el nombre de la variable
df_v = df_v.rename(columns={"valor": nombre_variable})

# =============================
# UNIR AMBAS SERIES
# =============================
df = pd.merge(df_v, df_usd, on="fecha", how="inner")

# =============================
# GRAFICAR
# =============================

fig = go.Figure()



# Serie de la variable (ej. Reservas)
fig.add_trace(go.Scatter(
    x=df["fecha"],
    y=df[nombre_variable],
    mode='lines',
    name=nombre_variable,
    yaxis="y1"
))

# Serie del tipo de cambio USD
fig.add_trace(go.Scatter(
    x=df["fecha"],
    y=df["tipoCotizacion"],
    mode='lines',
    name='Tipo de Cambio USD',
    yaxis="y2"
))

# Layout con doble eje Y
fig.update_layout(
    title=f"{nombre_variable} vs Tipo de Cambio USD (BCRA)",
    xaxis=dict(title="Fecha"),
    yaxis=dict(title=nombre_variable, titlefont=dict(color="blue"), tickfont=dict(color="blue")),
    yaxis2=dict(title="Tipo de Cambio USD", titlefont=dict(color="red"),
                tickfont=dict(color="red"), overlaying="y", side="right"),
    legend=dict(x=0.01, y=0.99),
    height=500,
    width=900
)

# Mostrar el gráfico en Streamlit
st.plotly_chart(fig, use_container_width=True)
