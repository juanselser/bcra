# plotting.py

import plotly.graph_objects as go
import pandas as pd

def plot_inflacion(df):
    ultimo_valor = df["valor"].dropna().iloc[-1]
    ultimo_mes = df["fecha"].dt.strftime("%B %Y").iloc[-1]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["fecha"],
        y=df["valor"],
        fill="tozeroy",
        mode="lines",
        connectgaps=True,
        line=dict(color="#7FDBFF", width=3)
    ))
    fig.update_layout(**layout_config("Inflación mensual", ultimo_mes, f"{ultimo_valor:.1f} %"))
    return fig

def plot_tasa_monetaria(df):
    ultimo_valor = df["valor"].dropna().iloc[-1]
    ultimo_mes = df["fecha"].dt.strftime("%B %Y").iloc[-1]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["fecha"],
        y=df["valor"],
        fill="tozeroy",
        mode="lines",
        connectgaps=True,
        line=dict(color="#1E90FF", width=3)
    ))
    fig.update_layout(**layout_config("Tasa de Política Monetaria", ultimo_mes, f"{ultimo_valor:.1f} %"))
    return fig

def plot_reservas(df):
    df["reservas"] = df["valor"] / 1000
    ultimo_valor = df["reservas"].dropna().iloc[-1]
    ultimo_mes = df["fecha"].dt.strftime("%B %Y").iloc[-1]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["fecha"],
        y=df["reservas"],
        fill="tozeroy",
        mode="lines",
        connectgaps=True,
        line=dict(color="#2ECC71", width=3)
    ))
    fig.update_layout(**layout_config("Reservas Internacionales", ultimo_mes, f"{ultimo_valor:.1f} B"))
    return fig

def plot_tipo_cambio(df):
    ultimo_usd_oficial = df["usd_oficial"].dropna().iloc[-1]
    ultimo_usd_blue = df["usd_blue"].dropna().iloc[-1]
    ultimo_mes = df["fecha"].dt.strftime("%B %Y").iloc[-1]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["fecha"],
        y=df["usd_oficial"],
        fill="tozeroy",
        mode="lines",
        connectgaps=True,
        line=dict(color="#2ECC71", width=3),
        name="USD Oficial"
    ))
    fig.add_trace(go.Scatter(
        x=df["fecha"],
        y=df["usd_blue"],
        mode="lines",
        connectgaps=True,
        line=dict(color="#2ECC71", width=3, dash="dot"),
        name="USD Blue"
    ))
    fig.update_layout(**layout_config("Tipo de Cambio (USD Oficial y Blue)", ultimo_mes, f"Oficial: {ultimo_usd_oficial:.0f} | Blue: {ultimo_usd_blue:.0f}"))
    return fig

def plot_cny(df):
    ultimo_valor = df["cny_oficial"].dropna().iloc[-1]
    ultimo_mes = df["fecha"].dt.strftime("%B %Y").iloc[-1]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["fecha"],
        y=df["cny_oficial"],
        fill="tozeroy",
        mode="lines",
        connectgaps=True,
        line=dict(color="#4169E1", width=3)
    ))
    fig.update_layout(**layout_config("Tipo de Cambio (CNY/ARS)", ultimo_mes, f"{ultimo_valor:.1f}"))
    return fig

def plot_merval(df):
    ultimo_valor = "2"
    ultimo_mes = df["fecha"].dt.strftime("%B %Y").iloc[-1]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["fecha"],
        y=df["merval_usd"],
        fill="tozeroy",
        mode="lines",
        connectgaps=True,
        line=dict(color="#FF5733", width=3)
    ))
    fig.update_layout(**layout_config("Merval en USD", ultimo_mes, f"{ultimo_valor:,.0f}"))
    return fig

def plot_cedears(df):
    cedears = {"YPFD.BA": "YPF", "GGAL.BA": "Galicia", "BMA.BA": "Banco Macro", "MELI.BA": "MercadoLibre"}
    colors = ["#FF5733", "#1E90FF", "#2ECC71", "#7FDBFF"]

    fig = go.Figure()
    for i, (ticker, name) in enumerate(cedears.items()):
        fig.add_trace(go.Scatter(
            x=df["fecha"],
            y=df[ticker],
            mode="lines",
            connectgaps=True,
            name=name,
            line=dict(width=2, color=colors[i % len(colors)])
        ))
    fig.update_layout(
        paper_bgcolor="#0B2C66",
        plot_bgcolor="#0B2C66",
        font=dict(family="Segoe UI", size=13, color="white"),
        height=300,
        margin=dict(l=25, r=25, t=80, b=30),
        title=dict(
            text=f"<b>Evolución principales acciones</b>",
            x=0.01,
            y=0.92,
            xanchor='left',
            yanchor='top',
            font=dict(size=18, color="white")
        ),
        xaxis=dict(
            title="",
            showgrid=False,
            tickfont=dict(color="white"),
            ticks="outside"
        ),
        yaxis=dict(
            title="Base 100",
            showgrid=False,
            tickfont=dict(color="white"),
            ticks="outside"
        ),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            y=-0.25,
            x=0.5,
            xanchor='center',
            font=dict(size=11, color="white")
        )
    )
    return fig

# --- Configuración común de layout para los gráficos ---

def layout_config(title_text, subtitle_text, value_text):
    today = pd.Timestamp.today().strftime("%Y-%m-%d")
    return dict(
        paper_bgcolor="#0B2C66",
        plot_bgcolor="#0B2C66",
        font=dict(family="Segoe UI", size=13, color="white"),
        height=300,
        margin=dict(l=25, r=25, t=100, b=30),
        title=dict(
            text=f"<b>{title_text}</b><br><span style='font-size:14px'>{subtitle_text}</span>",
            x=0.01,
            y=0.92,
            xanchor='left',
            yanchor='top',
            font=dict(size=18, color="white")
        ),
        annotations=[
            dict(
                x=-0.035,
                y=1.35,
                xref="paper", yref="paper",
                showarrow=False,
                text=f"<span style='font-size:24px'><b>{value_text}</b></span>",
                font=dict(color="white"),
                align="left"
            )
        ],
        hovermode="x unified"
    )
