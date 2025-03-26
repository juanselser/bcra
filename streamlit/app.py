import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

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
fig, ax1 = plt.subplots(figsize=(12, 6))

ax1.set_xlabel('Fecha')
ax1.set_ylabel(nombre_variable, color='tab:blue')
ax1.plot(df["fecha"], df[nombre_variable], color='tab:blue', label=nombre_variable)
ax1.tick_params(axis='y', labelcolor='tab:blue')

ax2 = ax1.twinx()
ax2.set_ylabel('Tipo de Cambio USD', color='tab:red')
ax2.plot(df["fecha"], df["tipoCotizacion"], color='tab:red', label="USD")
ax2.tick_params(axis='y', labelcolor='tab:red')

plt.title(f"{nombre_variable} vs Tipo de Cambio USD (BCRA)")
plt.grid(True)
plt.tight_layout()
plt.show()
