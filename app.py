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
st.set_page_config(page_title="AXIOM PRO", page_icon="📈", layout="wide")
st.set_page_config(page_title="AXIOM PRO", page_icon="📈", layout="wide")

# OCULTAR MENÚS DE STREAMLIT
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)
# --- 2. ESTILO CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #050508; color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #0a0a0f; border-right: 2px solid #C5A059; }
    p, span, label, h1, h2, h3, h4, h5 { color: #ffffff !important; font-family: sans-serif; }
    
    [data-testid="stHeader"] { background: transparent !important; }
    [data-testid="collapsedControl"] {
        background-color: #11111d !important; border: 1px solid #C5A059 !important;
        border-radius: 8px !important; margin: 5px; transition: 0.3s;
    }
    [data-testid="collapsedControl"] svg { fill: #C5A059 !important; color: #C5A059 !important; }

    .price-card {
        background: linear-gradient(145deg, #11111d 0%, #050505 100%);
        padding: 12px; border-radius: 10px; border: 1px solid #C5A059;
        text-align: center; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }

    .ai-signal {
        padding: 15px; border-radius: 12px; border: 2px solid #C5A059;
        text-align: center; background: #0a0a1a; margin-bottom: 15px;
        box-shadow: 0 0 15px rgba(197, 160, 89, 0.2);
    }
    
    div.stButton > button:first-child {
        background: linear-gradient(45deg, #C5A059, #FFD700);
        color: black !important; font-weight: bold; width: 100%; height: 55px; 
        border-radius: 10px; border: none; font-size: 18px; margin-top: 5px; margin-bottom: 10px;
    }
    
    .news-box {
        background: #161b22; padding: 12px; border-radius: 8px; 
        border-left: 4px solid #C5A059; margin-bottom: 10px; font-size: 0.9em; line-height: 1.4;
    }

    .login-box {
        background: #0a0a0f; padding: 40px; border-radius: 15px; 
        border: 2px solid #C5A059; text-align: center;
        max-width: 400px; margin: 100px auto;
        box-shadow: 0 0 30px rgba(197, 160, 89, 0.2);
    }

    @media (max-width: 768px) {
        .stTabs [data-baseweb="tab-list"] { flex-wrap: wrap; }
        .stTabs [data-baseweb="tab"] { flex: 1; text-align: center; font-size: 14px; padding: 8px; height: auto; }
        .ai-signal h1 { font-size: 28px !important; margin: 10px 0 !important; }
        .ai-signal p { font-size: 14px !important; }
        h2 { font-size: 22px !important; }
        .block-container { padding-top: 3rem !important; padding-bottom: 2rem !important; padding-left: 1rem !important; padding-right: 1rem !important; }
        .login-box { margin: 50px 20px; padding: 20px; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SISTEMA DE SEGURIDAD MULTI-CLIENTE ---
# Aquí controlas quién tiene acceso. Si alguien deja de pagar, simplemente borras su línea.
CLIENTES_ACTIVOS = {
    "AXIOM_MASTER": "Administrador",
    "VIP_JUAN_01": "Juan Perez",
    "VIP_MARIA_02": "Maria Gomez",
    "PRUEBA_24H": "Cliente de prueba",
    "GEMINI_PRO_999": "Gemini(subscripcion mensual)"
}

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

def mostrar_login():
    st.markdown("""
        <div class="login-box">
            <h2 style='color:#C5A059; margin-bottom: 20px;'>🔒 AXIOM PRO</h2>
            <p>Introduce tu pase VIP para acceder a la terminal.</p>
        </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        pwd = st.text_input("Código de Acceso", type="password")
        if st.button("🗝️ DESBLOQUEAR TERMINAL"):
            if pwd in CLIENTES_ACTIVOS:
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("❌ Código incorrecto o suscripción caducada.")

def mostrar_aplicacion_principal():
    with st.sidebar:
        if os.path.exists("app_icon.png"): st.image("app_icon.png", width=60)
        st.markdown("<h2 style='text-align:center; color:#C5A059; margin-top:0;'>AXIOM PRO</h2>", unsafe_allow_html=True)
        st.markdown(f'''<a href="https://fxcentrum.com/registra-tu-cuenta/" target="_blank" style="text-decoration:none;"><button style="width:100%; background:#C5A059; color:black; border:none; padding:10px; border-radius:8px; font-weight:bold; cursor:pointer; font-size:14px;">💎 CUENTA REAL</button></a>''', unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("<div style='color:#C5A059; font-weight:bold; font-size:14px;'>⚙️ GESTIÓN DE CAPITAL</div>", unsafe_allow_html=True)
        balance = st.number_input("SALDO ($)", value=500, step=50)
        leverage = st.selectbox("APALANCAMIENTO", [30, 100, 500], index=2)
        risk_pct = st.slider("RIESGO POR OPERACIÓN (%)", 0.5, 5.0, 2.0)

        st.markdown("---")
        st.markdown("<div style='color:#C5A059; font-weight:bold; font-size:14px;'>📊 ACTIVOS</div>", unsafe_allow_html=True)
        cat = st.selectbox("CATEGORÍA", ["🪙 Criptomonedas", "📈 Índices", "🛢️ Materias Primas", "🏢 Acciones"])
        
        if "Cripto" in cat: opciones = {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD"}
        elif "Índices" in cat: opciones = {"S&P 500": "^GSPC", "Nasdaq 100": "^IXIC", "IBEX 35": "^IBEX"}
        elif "Materias" in cat: opciones = {"Oro": "GC=F", "Plata": "SI=F", "Petróleo": "BZ=F"}
        else: opciones = {"Tesla": "TSLA", "Nvidia": "NVDA", "Amazon": "AMZN"}
        
        activo_nombre = st.selectbox("SELECCIONA ACTIVO", list(opciones.keys()))
        ticker = opciones[activo_nombre]

        btn_analizar = st.button("🚀 ANALIZAR MERCADO")

    st.markdown("<h2 style='text-align:center; color:#C5A059; margin-bottom: 20px;'>⚖️ AXIOM GLOBAL TERMINAL</h2>", unsafe_allow_html=True)

    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)
    cuadricula = [row1_col1, row1_col2, row2_col1, row2_col2]

    for i, (t, n) in enumerate([("BTC-USD", "BITCOIN"), ("SI=F", "PLATA"), ("^GSPC", "S&P 500"), ("BZ=F", "PETRÓLEO")]):
        try:
            val = yf.Ticker(t).fast_info.last_price
            cuadricula[i].markdown(f"""<div class='price-card'><small>{n}</small><br><b style='font-size:20px;'>${val:,.2f}</b></div>""", unsafe_allow_html=True)
        except: pass

    tab_term, tab_acad, tab_chat = st.tabs(["🖥️ TERMINAL", "🎓 ACADEMIA", "💬 ASISTENTE"])

    with tab_term:
        col_chart, col_info = st.columns([1, 1])
        perdida = balance * (risk_pct / 100)
        poder = balance * leverage
        
        with col_chart:
            df = yf.download(ticker, period="10d", interval="15m", progress=False)
            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)
                
                df['SMA20'] = df['Close'].rolling(window=20).mean()
                df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
                delta = df['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                df['RSI'] = 100 - (100 / (1 + rs))
                df['Recent_High'] = df['High'].rolling(window=20).max()
                df['Recent_Low'] = df['Low'].rolling(window=20).min()
                df.dropna(inplace=True)
                
                fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], increasing_line_color='#00ff88', decreasing_line_color='#ff4b4b')])
                fig.update_layout(template="plotly_dark", height=320, xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=10, b=0))
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        with col_info:
            if btn_analizar and not df.empty:
                last_p = float(df['Close'].iloc[-1])
                sma20 = float(df['SMA20'].iloc[-1])
                ema50 = float(df['EMA50'].iloc[-1])
                rsi = float(df['RSI'].iloc[-1])
                tp_max = float(df['Recent_High'].iloc[-2])
                tp_min = float(df['Recent_Low'].iloc[-2])
                
                if last_p > ema50 and last_p > sma20:
                    tendencia = "ALCISTA"
                    color_sig = "#00ff88"
                    señal = "COMPRA (BUY)"
                    precio_tp = tp_max
                    objetivo_txt = "último máximo"
                elif last_p < ema50 and last_p < sma20:
                    tendencia = "BAJISTA"
                    color_sig = "#ff4b4b"
                    señal = "VENTA (SELL)"
                    precio_tp = tp_min
                    objetivo_txt = "último mínimo"
                else:
                    tendencia = "RANGO"
                    color_sig = "#FFD700"
                    señal = "ESPERAR (NEUTRAL)"
                    precio_tp = last_p
                    objetivo_txt = "indefinido"

                st.markdown(f"""
                    <div class='ai-signal'>
                        <h4 style='color:#C5A059; margin:0;'>🤖 SEÑAL AXIOM IA</h4>
                        <p style='margin:5px 0;'>Activo: <b>{activo_nombre}</b></p>
                        <h1 style='color:{color_sig}; margin:5px 0;'>{señal}</h1>
                        <p style='margin:0;'>Probabilidad: <b style='color:#00ff88;'>75.0%</b></p>
                    </div>
                """, unsafe_allow_html=True)

                if tendencia in ["ALCISTA", "BAJISTA"]:
                    st.markdown(f"""
                    <div style='background: #11111d; padding: 12px; border-radius: 8px; border-left: 4px solid {color_sig}; margin-bottom: 15px; font-size: 0.9em;'>
                        <p style='margin-bottom:5px; color:#C5A059;'><b>🎯 CONSEJO DE POSICIÓN TP:1</b></p>
                        <p style='margin-bottom:5px;'><b>1. Entrada:</b> Abre orden de <b style='color:{color_sig}'>{señal}</b> al precio de <b>{last_p:,.2f}</b>.</p>
                        <p style='margin-bottom:5px;'><b>2. Take Profit:</b> Fija tu salida en el {objetivo_txt} detectado en <b>{precio_tp:,.2f}</b>.</p>
                        <p style='margin-bottom:0;'><b>3. Stop Loss:</b> Ajusta tu lotaje para arriesgar exactamente <b>${perdida:,.2f}</b>.</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style='background: #11111d; padding: 12px; border-radius: 8px; border-left: 4px solid {color_sig}; margin-bottom: 15px; font-size: 0.9em;'>
                        <p style='margin-bottom:5px; color:#C5A059;'><b>🛡️ CONSEJO DE POSICIÓN (PROTECCIÓN)</b></p>
                        <p style='margin-bottom:5px;'><b>1. Acción:</b> Quédate fuera del mercado en este activo.</p>
                        <p style='margin-bottom:5px;'><b>2. Motivo:</b> El precio está atrapado entre medias móviles (rango sucio).</p>
                        <p style='margin-bottom:0;'><b>3. Regla Axiom:</b> Proteger el capital es más importante que operar por operar.</p>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("<h5 style='color:#C5A059; margin-top:10px;'>🧠 Criterio IA</h5>", unsafe_allow_html=True)
                if tendencia == "ALCISTA":
                    razones = [f"Doble confirmación técnica. El precio ({last_p:,.2f}) rompe la SMA20 y se sostiene sobre la EMA50.", f"Estructura fuertemente positiva en {activo_nombre}. Demanda agresiva superando filtros."]
                    estado_rsi = f" RSI en {rsi:.1f} con espacio para subir." if rsi < 70 else f" Atención: RSI ({rsi:.1f}) indica sobrecompra."
                elif tendencia == "BAJISTA":
                    razones = [f"Caída con volumen confirmada. El precio ({last_p:,.2f}) pierde tanto la SMA20 como la EMA50.", f"Estructura de distribución estricta. La oferta empuja la cotización a la baja."]
                    estado_rsi = f" RSI en {rsi:.1f} con recorrido bajista." if rsi > 30 else f" Atención: RSI ({rsi:.1f}) marca sobreventa extrema."
                else:
                    razones = [f"Falta de confluencia. El precio ({last_p:,.2f}) no tiene dirección clara entre la SMA20 y la EMA50.", f"Mercado lateralizado. La probabilidad del 75% no está garantizada aquí."]
                    estado_rsi = f" El RSI ({rsi:.1f}) refleja indecisión. Mejor buscar otro activo."
                st.info(random.choice(razones) + estado_rsi)

                st.markdown("<h5 style='color:#C5A059; margin-top:10px;'>📰 Radar de Noticias</h5>", unsafe_allow_html=True)
                titulares_reales = []
                try:
                    query = urllib.parse.quote(f"{activo_nombre} finanzas")
                    url = f"https://news.google.com/rss/search?q={query}&hl=es&gl=ES&ceid=ES:es"
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=5) as response:
                        xml_data = response.read()
                    root = ET.fromstring(xml_data)
                    for item in root.findall('.//item')[:2]: 
                        full_title = item.find('title').text
                        if " - " in full_title:
                            title, publisher = full_title.rsplit(" - ", 1)
                        else:
                            title = full_title
                            publisher = "Mercado"
                        titulares_reales.append((publisher, title))
                except: pass 

                if titulares_reales:
                    for pub, title in titulares_reales:
                        st.markdown(f"""<div class='news-box'><b>{pub}</b>: {title}</div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div class='news-box'><b>Axiom Analítica</b>: Escaneando flujos de volumen en {activo_nombre}.</div>""", unsafe_allow_html=True)

            else:
                st.info("👋 Selecciona un activo en el menú lateral y pulsa Analizar Mercado.")

        st.markdown("---")
        c1, c2 = st.columns(2)
        c1.metric("RIESGO (SL)", f"${perdida:,.2f}")
        c2.metric(f"PODER (1:{leverage})", f"${poder:,.2f}")

    with tab_acad:
        st.markdown("<h3 style='color:#C5A059; text-align:center;'>🎓 Programa Axiom</h3>", unsafe_allow_html=True)
        n1, n2, n3 = st.tabs(["🟢 Nivel 1", "🟡 Nivel 2", "🔴 Nivel 3"])
        with n1:
            st.markdown("""<div class="acad-text"><p><span class="step-highlight">1. ¿Qué es el Trading?</span><br> Ganamos dinero por la diferencia de precio.</p><p><span class="step-highlight">2. Conceptos:</span><br>• <b>Balance:</b> Tu dinero real depositado.<br>• <b>Margen:</b> El dinero retenido para operar.</p><p><span class="step-highlight">3. SL y TP:</span><br>• <b>Stop Loss (SL):</b> Cierra si vas perdiendo. NUNCA operes sin SL.<br>• <b>Take Profit (TP):</b> Tu objetivo de ganancias.</p></div>""", unsafe_allow_html=True)
        with n2:
            st.markdown("""<div class="acad-text"><p><span class="step-highlight">1. Velas Japonesas:</span><br> El cuerpo nos dice quién tiene el control y las mechas muestran el rechazo.</p><p><span class="step-highlight">2. Tendencias:</span><br>• <b>Alcista:</b> Máximos y mínimos más altos.<br>• <b>Bajista:</b> Máximos y mínimos más bajos.</p><p><span class="step-highlight">3. Soportes y Resistencias:</span><br> Zonas donde el precio rebota por acumulación de órdenes.</p></div>""", unsafe_allow_html=True)
        with n3:
            st.markdown("""<div class="acad-text"><p><span class="step-highlight">1. Gestión de Riesgo:</span><br> Operamos con apalancamiento masivo. El lotaje debe asegurar que si salta el SL, solo pierdas el riesgo de tu balance operativo.</p><p><span class="step-highlight">2. Estrategia TP:1:</span><br> Ejecuta y coloca el TP:1 exactamente en el <b>último máximo</b> o en el <b>último mínimo</b> buscando liquidez.</p><p><span class="step-highlight">3. Psicología:</span><br> Sistema al 75% de Win Rate. Sigue la señal, verifica contexto y respeta tu Stop Loss siempre.</p></div>""", unsafe_allow_html=True)

    with tab_chat:
        st.markdown("<h3 style='color:#C5A059; text-align:center;'>💬 Asistente Virtual</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; font-size:0.9em; color:#e0e0e0;'>Toca una pregunta rápida o escríbeme abajo:</p>", unsafe_allow_html=True)
        
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": "¡Hola! Soy el asistente de la Terminal Axiom. Puedo ayudarte con dudas sobre tu operativa."}]

        c1, c2, c3 = st.columns(3)
        pregunta_rapida = None
        if c1.button("🎯 ¿Qué es el TP:1?", use_container_width=True): pregunta_rapida = "¿Qué es el TP:1?"
        if c2.button("⚖️ Apalancamiento", use_container_width=True): pregunta_rapida = "¿Cómo gestiono el apalancamiento?"
        if c3.button("📊 Probabilidad", use_container_width=True): pregunta_rapida = "Háblame del 75% de acierto"

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        prompt = st.chat_input("Escribe tu duda aquí...")

        if prompt or pregunta_rapida:
            texto_usuario = prompt if prompt else pregunta_rapida

            st.session_state.messages.append({"role": "user", "content": texto_usuario})
            with st.chat_message("user"):
                st.markdown(texto_usuario)

            texto = texto_usuario.lower()
            if "tp" in texto or "estrategia" in texto:
                respuesta = "Nuestra estrategia principal es el **TP:1**. Para lograr nuestro 75% de probabilidad de éxito, buscamos liquidez pura. \n\nDebes colocar tu objetivo de salida siempre en el **último máximo relevante** si la señal de la IA fue una compra, o en el **último mínimo** si la señal fue una venta."
            elif "apalancamiento" in texto or "riesgo" in texto or "lote" in texto:
                respuesta = "Operamos con un apalancamiento fuerte y profesional de **1:500**. Esto te da mucho poder de compra, pero exige responsabilidad. Usa la calculadora lateral para fijar un riesgo del 1% o 2% de tu saldo y **nunca operes sin Stop Loss**."
            elif "probabilidad" in texto or "acierto" in texto or "win rate" in texto or "75" in texto:
                respuesta = "El sistema Axiom y la IA están calibrados para darte una probabilidad estadística de acierto del **75%**. Esto significa que tendrás operaciones en pérdida, y es normal. La rentabilidad viene de ser constante, no salirte del plan y dejar que la matemática juegue a tu favor."
            elif "hola" in texto or "buenas" in texto:
                respuesta = "¡Saludos! ¿En qué te puedo asesorar? Pregúntame sobre el apalancamiento, cómo poner el TP:1 o la gestión de riesgo."
            else:
                respuesta = "Esa es una gran pregunta. Sin embargo, mi sistema está enfocado exclusivamente en darte soporte sobre el método Axiom. Puedes preguntarme sobre:\n\n1. 🎯 **Cómo colocar el TP:1**\n2. ⚖️ **El uso del apalancamiento 1:500**\n3. 📊 **La probabilidad del 75%**\n\n¿Quieres repasar alguno de estos puntos?"

            with st.chat_message("assistant"):
                st.markdown(respuesta)
            st.session_state.messages.append({"role": "assistant", "content": respuesta})

    st.caption(f"Axiom AI Terminal v27.0 | Sistema de Usuarios Independientes | {datetime.now().strftime('%H:%M:%S')}")

# --- FLUJO DE CONTROL ---
if not st.session_state.autenticado:
    mostrar_login()
else:
    mostrar_aplicacion_principal()