# data_fetching.py

import requests
import pandas as pd
import yfinance as yf

# --- Funciones para obtención de datos ---

def get_bcra_variable(id_variable, start_date, end_date):
    url = f"https://api.bcra.gob.ar/estadisticas/v3.0/monetarias/series/{id_variable}/datos/{start_date}/{end_date}"
    response = requests.get(url, verify=False)
    if response.status_code == 200:
        data = response.json()['results']
        df = pd.DataFrame(data)
        df['fecha'] = pd.to_datetime(df['fecha'])
        df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
        return df
    else:
        raise Exception("Error en la API del BCRA")

def get_usd_oficial(start_date, end_date):
    url = "https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones/USD"
    params = {"fechadesde": start_date, "fechahasta": end_date, "limit": 1000}
    r = requests.get(url, params=params, verify=False)
    if r.status_code == 200:
        data = r.json()['results']
        registros = []
        for d in data:
            fecha = d['fecha']
            for cot in d['detalle']:
                registros.append({"fecha": fecha, "usd_oficial": cot['tipoCotizacion']})
        df = pd.DataFrame(registros)
        df['fecha'] = pd.to_datetime(df['fecha'])
        return df.groupby('fecha').mean().reset_index()
    else:
        raise Exception("Error al obtener USD Oficial")

def get_usd_blue():
    url = "https://api.bluelytics.com.ar/v2/evolution.json"
    r = requests.get(url)
    if r.status_code == 200:
        data = r.json()['blue']
        df = pd.DataFrame(data)
        df['fecha'] = pd.to_datetime(df['date'])
        df['usd_blue'] = (df['value_avg'])
        return df[['fecha', 'usd_blue']]
    else:
        raise Exception("Error al obtener USD Blue")

def get_cny_oficial(start_date, end_date):
    url = "https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones/CNY"
    params = {"fechadesde": start_date, "fechahasta": end_date, "limit": 1000}
    r = requests.get(url, params=params, verify=False)
    if r.status_code == 200:
        data = r.json()['results']
        registros = []
        for d in data:
            fecha = d['fecha']
            for cot in d['detalle']:
                registros.append({"fecha": fecha, "cny_oficial": cot['tipoCotizacion']})
        df = pd.DataFrame(registros)
        df['fecha'] = pd.to_datetime(df['fecha'])
        return df.groupby('fecha').mean().reset_index()
    else:
        raise Exception("Error al obtener CNY Oficial")

def get_inflacion(start_date, end_date):
    return get_bcra_variable(27, start_date, end_date)

def get_tasa_monetaria(start_date, end_date):
    return get_bcra_variable(6, start_date, end_date)

def get_reservas(start_date, end_date):
    return get_bcra_variable(1, start_date, end_date)

def get_tipo_cambio(start_date, end_date):
    df_usd_oficial = get_usd_oficial(start_date, end_date)
    df_usd_blue = get_usd_blue()
    df_usd_blue = df_usd_blue[df_usd_blue['fecha'].between(start_date, end_date)]
    df = pd.merge(df_usd_oficial, df_usd_blue, on='fecha', how='outer')
    df = df.sort_values('fecha').reset_index(drop=True)
    return df

def get_cny(start_date, end_date):
    df_cny = get_cny_oficial(start_date, end_date)
    df_cny = df_cny[df_cny['fecha'].between(start_date, end_date)].reset_index(drop=True)
    return df_cny

def get_merval(start_date, end_date):
    merval = yf.download("^MERV", start=start_date, end=end_date)["Close"].reset_index()
    merval = merval.rename(columns={"Date": "fecha", "Close": "merval_ars"})
    df_usd_blue = get_usd_blue()
    df_usd_blue = df_usd_blue[df_usd_blue['fecha'].between(start_date, end_date)]
    df = pd.merge(merval, df_usd_blue, on='fecha', how='inner')
    df['merval_usd'] = df['merval_ars'] / df['usd_blue']
    return df

def get_cedears(start_date, end_date):
    tickers = ["YPFD.BA", "GGAL.BA", "BMA.BA", "MELI.BA"]
    data = yf.download(tickers, start=start_date, end=end_date)["Close"]
    df = data.reset_index().rename(columns={"Date": "fecha"})
    for ticker in tickers:
        df[ticker] = (df[ticker] / df[ticker].iloc[0]) * 100
    df = df.dropna().sort_values("fecha").reset_index(drop=True)
    return df
