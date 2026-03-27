import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os
import random
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import numpy as np

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="AXIOM PRO", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

# --- 2. ESTILO CSS COMPLETO (DISEÑO AXIOM) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}
    [data-testid="stDecoration"] {display: none;}
    .block-container {padding-top: 0rem !important;}
    .stApp { background-color: #050508; color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #0a0a0f; border-right: 2px solid #C5A059; }
    p, span, label, h1, h2, h3, h4, h5 { color: #ffffff !important; font-family: sans-serif; }
    
    .price-card {
        background: linear-gradient(145deg, #11111d 0%, #050505 100%);
        padding: 12px; border-radius: 10px; border: 1px solid #C5A059;
        text-align: center; margin-bottom: 15px;
    }
    .ai-signal {
        padding: 15px; border-radius: 12px; border: 2px solid #C5A059;
        text-align: center; background: #0a0a1a; margin-bottom: 15px;
    }
    div.stButton > button:first-child {
        background: linear-gradient(45deg, #C5A059, #FFD700);
        color: black !important; font-weight: bold; width: 100%; height: 55px; 
        border-radius: 10px; border: none; font-size: 18px;
    }
    .acad-text { background: #11111d; padding: 20px; border-radius: 10px; border-left: 4px solid #C5A059; line-height: 1.6; margin-bottom: 15px; }
    .step-highlight { color: #C5A059; font-weight: bold; font-size: 1.1em; }
    .news-box { background: #161b22; padding: 12px; border-radius: 8px; border-left: 4px solid #C5A059; margin-bottom: 10px; font-size: 0.9em; }
    .login-box { background: #0a0a0f; padding: 40px; border-radius: 15px; border: 2px solid #C5A059; text-align: center; max-width: 400px; margin: 80px auto; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CLIENTES (NO TOCAR) ---
CLIENTES_ACTIVOS = {
    "AXIOM_MASTER": "Administrador",
    "VIP_JUAN_01": "Juan Perez",
    "VIP_MARIA_02": "Maria Gomez",
    "PRUEBA_24H": "Cliente de prueba",
    "GEMINI_PRO_999": "Gemini(subscripcion mensual)"
}

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown('<div class="login-box"><h2 style="color:#C5A059;">🔒 AXIOM PRO</h2><p>Introduce tu pase VIP.</p></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        pwd = st.text_input("Código de Acceso", type="password")
        if st.button("🗝️ DESBLOQUEAR"):
            if pwd in CLIENTES_ACTIVOS:
                st.session_state.autenticado = True
                st.rerun()
            else: st.error("❌ Código incorrecto.")
    st.stop()

# --- 4. APP PRINCIPAL ---
with st.sidebar:
    st.markdown("<h2 style='text-align:center; color:#C5A059;'>AXIOM PRO</h2>", unsafe_allow_html=True)
    st.markdown(f'''<a href="https://fxcentrum.com/registra-tu-cuenta/" target="_blank"><button style="width:100%; background:#C5A059; color:black; cursor:pointer; padding:10px; border-radius:5px; border:none; font-weight:bold;">💎 CUENTA REAL</button></a>''', unsafe_allow_html=True)
    st.markdown("---")
    balance = st.number_input("SALDO ($)", value=500, step=50)
    leverage = st.selectbox("APALANCAMIENTO", [30, 100, 500], index=2)
    risk_pct = st.slider("RIESGO (%)", 0.5, 5.0, 2.0)
    st.markdown("---")
    cat = st.selectbox("CATEGORÍA", ["🏢 Acciones", "💱 Divisas (Forex)", "📈 Índices", "🪙 Criptomonedas", "🛢️ Materias Primas"])
    
    if "Acciones" in cat: opciones = {"Tesla": "TSLA", "Nvidia": "NVDA", "Amazon": "AMZN", "Google": "GOOGL", "Apple": "AAPL"}
    elif "Divisas" in cat: opciones = {"EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X", "USD/JPY": "JPY=X"}
    elif "Índices" in cat: opciones = {"S&P 500": "^GSPC", "Nasdaq 100": "^IXIC", "IBEX 35": "^IBEX"}
    elif "Cripto" in cat: opciones = {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD"}
    else: opciones = {"Oro": "GC=F", "Petróleo": "BZ=F"}
    
    activo_nombre = st.selectbox("SELECCIONA ACTIVO", list(opciones.keys()))
    ticker = opciones[activo_nombre]
    btn_analizar = st.button("🚀 ANALIZAR MERCADO")

st.markdown("<h2 style='text-align:center; color:#C5A059; margin-bottom:20px;'>⚖️ AXIOM GLOBAL TERMINAL</h2>", unsafe_allow_html=True)

# PESTAÑAS
tab_term, tab_acad, tab_chat = st.tabs(["🖥️ TERMINAL", "🎓 ACADEMIA", "💬 ASISTENTE"])

with tab_term:
    col_chart, col_info = st.columns([1.5, 1])
    df = yf.download(ticker, period="5d", interval="15m", progress=False)
    
    if not df.empty:
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)
        with col_chart:
            fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], increasing_line_color='#00ff88', decreasing_line_color='#ff4b4b')])
            fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,t=0,b=0), xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
            
        with col_info:
            if btn_analizar:
                last_p = float(df['Close'].iloc[-1])
                h20 = float(df['High'].rolling(20).max().iloc[-1])
                l20 = float(df['Low'].rolling(20).min().iloc[-1])
                margen = last_p * 0.0007
                
                if (h20 - last_p) > margen and last_p > df['Close'].mean():
                    señal, color, tp = "COMPRA", "#00ff88", h20
                elif (last_p - l20) > margen and last_p < df['Close'].mean():
                    señal, color, tp = "VENTA", "#ff4b4b", l20
                else:
                    señal, color, tp = "NEUTRAL", "#FFD700", last_p
                
                st.markdown(f"<div class='ai-signal'><h4 style='color:#C5A059;'>🤖 SEÑAL IA</h4><h1 style='color:{color};'>{señal}</h1><p>TP Sugerido: <b>{tp:,.4f}</b></p></div>", unsafe_allow_html=True)
                
                # --- NOTICIAS RE-INSTALADAS ---
                st.markdown("<h5 style='color:#C5A059; margin-top:10px;'>📰 Noticias del Activo</h5>", unsafe_allow_html=True)
                try:
                    q_n = urllib.parse.quote(f"{activo_nombre} finanzas")
                    u_n = f"https://news.google.com/rss/search?q={q_n}&hl=es&gl=ES&ceid=ES:es"
                    req_n = urllib.request.Request(u_n, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req_n, timeout=5) as resp_n:
                        root_n = ET.fromstring(resp_n.read())
                        for item in root_n.findall('.//item')[:2]:
                            st.markdown(f"<div class='news-box'><b>News:</b> {item.find('title').text}</div>", unsafe_allow_html=True)
                except:
                    st.info("Sincronizando flujo de noticias...")

with tab_acad:
    st.markdown("<h3 style='color:#C5A059; text-align:center;'>🎓 Programa Educativo Axiom</h3>", unsafe_allow_html=True)
    n1, n2, n3 = st.tabs(["🟢 Nivel 1", "🟡 Nivel 2", "🔴 Nivel 3"])
    with n1:
        st.markdown("""<div class="acad-text">
        <p><span class="step-highlight">1. ¿Qué es el Trading?</span> Ganamos dinero por la diferencia de precio entre la compra y la venta.</p>
        <p><span class="step-highlight">2. Conceptos Básicos:</span><br>• <b>Balance:</b> Tu capital real.<br>• <b>Margen:</b> Dinero que el broker retiene para abrir la posición.</p>
        <p><span class="step-highlight">3. SL y TP:</span> El Stop Loss (SL) protege tu cuenta y el Take Profit (TP) asegura tu ganancia operativa.</p>
        </div>""", unsafe_allow_html=True)
    with n2:
        st.markdown("""<div class="acad-text">
        <p><span class="step-highlight">1. Velas Japonesas:</span> Cada vela cuenta una historia. El cuerpo indica la fuerza y la mecha el rechazo del precio.</p>
        <p><span class="step-highlight">2. Estructura de Mercado:</span> Aprendemos a identificar Tendencias Alcistas y Bajistas.</p>
        </div>""", unsafe_allow_html=True)
    with n3:
        st.markdown("""<div class="acad-text">
        <p><span class="step-highlight">1. Gestión de Riesgo:</span> Usamos apalancamiento 1:500. Es vital calcular el lotaje según tu balance.</p>
        <p><span class="step-highlight">2. Estrategia TP:1:</span> Buscamos el último máximo o mínimo relevante para fijar el objetivo de salida.</p>
        </div>""", unsafe_allow_html=True)

with tab_chat:
    st.markdown("<h3 style='color:#C5A059; text-align:center;'>💬 Asistente Virtual</h3>", unsafe_allow_html=True)
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "¡Hola! Soy el asistente Axiom. ¿Tienes dudas sobre el TP:1 o el riesgo?"}]
    
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])
    
    prompt = st.chat_input("Escribe tu duda aquí...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        t = prompt.lower()
        if "tp" in t: r = "La estrategia **TP:1** busca salir en el último máximo relevante si compras, o mínimo si vendes."
        elif "apalancamiento" in t: r = "Operamos con **1:500**. Esto permite maximizar tu capital, pero usa siempre el SL."
        else: r = "Pregúntame sobre el TP:1, el apalancamiento o cómo leer la señal de la IA."
        with st.chat_message("assistant"): st.markdown(r)
        st.session_state.messages.append({"role": "assistant", "content": r})

st.caption(f"Axiom AI Terminal v30.0 | {datetime.now().strftime('%H:%M:%S')}")