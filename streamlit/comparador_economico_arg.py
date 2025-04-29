
import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import plotly.graph_objects as go
import yfinance as yf

st.title("Comparador de Variables Económicas Argentinas")

# ============ CONFIG INICIAL =============
fecha_inicio = st.date_input("Fecha de inicio", datetime(2022, 1, 1))
fecha_fin = st.date_input("Fecha de fin", datetime.today())

if fecha_inicio > fecha_fin:
    st.warning("La fecha de inicio no puede ser posterior a la fecha de fin.")
    st.stop()

# ============ FUNCIONES =============
@st.cache_data
def get_bcra_vars():
    url = "https://api.bcra.gob.ar/estadisticas/v3.0/monetarias"
    r = requests.get(url, verify=False)
    return pd.DataFrame(r.json()["results"]) if r.status_code == 200 else None

def get_bcra_variable(id_variable):
    url = f"https://api.bcra.gob.ar/estadisticas/v3.0/monetarias/{id_variable}"
    params = {"desde": fecha_inicio.strftime("%Y-%m-%d"), "hasta": fecha_fin.strftime("%Y-%m-%d"), "limit": 3000}
    r = requests.get(url, params=params, verify=False)
    df = pd.DataFrame(r.json()["results"])
    df["fecha"] = pd.to_datetime(df["fecha"])
    return df[["fecha", "valor"]].rename(columns={"valor": f"var_{id_variable}"})

def get_usd_oficial():
    url = "https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones/USD"
    params = {"fechadesde": fecha_inicio.strftime("%Y-%m-%d"), "fechahasta": fecha_fin.strftime("%Y-%m-%d")}
    r = requests.get(url, params=params, verify=False)
    data = r.json()["results"]
    registros = [{"fecha": d["fecha"], "usd_oficial": cot["tipoCotizacion"]}
                 for d in data for cot in d["detalle"] if isinstance(cot["tipoCotizacion"], (int, float))]
    df = pd.DataFrame(registros)
    df["fecha"] = pd.to_datetime(df["fecha"])
    return df.groupby("fecha").mean().reset_index()

def get_usd_blue():
    r = requests.get("https://api.bluelytics.com.ar/v2/evolution.json")
    data = [d for d in r.json() if d["source"] == "Blue"]
    df = pd.DataFrame(data)
    df["fecha"] = pd.to_datetime(df["date"])
    df["usd_blue"] = (df["value_buy"] + df["value_sell"]) / 2
    return df[["fecha", "usd_blue"]]

def get_merval_usd():
    merval = yf.download("^MERV", start=fecha_inicio, end=fecha_fin)["Close"].reset_index()
    merval = merval.rename(columns={"Date": "fecha", "Close": "merval_ars"})
    df_blue = get_usd_blue()
    df = pd.merge(merval, df_blue, on="fecha", how="inner")
    df["merval_usd"] = df["merval_ars"] / df["usd_blue"]
    return df[["fecha", "merval_usd"]]

# ============ PREPARAR LISTADO VARIABLES ============
bcra_vars = get_bcra_vars()
if bcra_vars is None:
    st.error("No se pudo obtener el listado de variables del BCRA.")
    st.stop()

ids_interes = [1, 15, 6, 27]
bcra_vars = bcra_vars[bcra_vars["idVariable"].isin(ids_interes)].copy()
manual_vars = pd.DataFrame([
    {"idVariable": "usd_oficial", "descripcion": "Dólar Oficial"},
    {"idVariable": "usd_blue", "descripcion": "Dólar Blue"},
    {"idVariable": "merval_usd", "descripcion": "Merval en USD"},
])
var_opciones = pd.concat([bcra_vars[["idVariable", "descripcion"]], manual_vars], ignore_index=True)

# ============ SELECTBOXES ============
col1, col2 = st.columns(2)
var1 = col1.selectbox("Elegí la primera variable", var_opciones["descripcion"])
var2 = col2.selectbox("Elegí la segunda variable", var_opciones["descripcion"], index=1)

# ============ CARGAR DATOS ============
def cargar_variable(id_variable):
    if id_variable == "usd_oficial":
        return get_usd_oficial().rename(columns={"usd_oficial": id_variable})
    elif id_variable == "usd_blue":
        return get_usd_blue().rename(columns={"usd_blue": id_variable})
    elif id_variable == "merval_usd":
        return get_merval_usd().rename(columns={"merval_usd": id_variable})
    else:
        return get_bcra_variable(id_variable)

id1 = var_opciones[var_opciones["descripcion"] == var1].iloc[0]["idVariable"]
id2 = var_opciones[var_opciones["descripcion"] == var2].iloc[0]["idVariable"]
df1 = cargar_variable(id1)
df2 = cargar_variable(id2)

df = pd.merge(df1, df2, on="fecha", how="inner").dropna()

# ============ GRAFICAR ============
fig = go.Figure()

fig.add_trace(go.Scatter(x=df["fecha"], y=df[df.columns[1]],
                         name=var1, yaxis="y1", mode="lines"))

fig.add_trace(go.Scatter(x=df["fecha"], y=df[df.columns[2]],
                         name=var2, yaxis="y2", mode="lines"))

fig.update_layout(
    title=f"Comparación: {var1} vs {var2}",
    xaxis=dict(title="Fecha"),
    yaxis=dict(title=var1, titlefont=dict(color="blue"), tickfont=dict(color="blue")),
    yaxis2=dict(title=var2, titlefont=dict(color="red"), tickfont=dict(color="red"),
                overlaying="y", side="right"),
    legend=dict(x=0.01, y=0.99),
    height=600
)

st.plotly_chart(fig, use_container_width=True)
