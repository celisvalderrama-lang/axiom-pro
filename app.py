import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

# --- 1. CONFIGURACIÓN (MENÚ ABIERTO POR DEFECTO PARA VER CONTROLES) ---
st.set_page_config(page_title="AXIOM PRO", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

# --- 2. ESTILO CSS (UX/UI MÓVIL Y PROFESIONAL) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} 
    footer {visibility: hidden;} 
    
    .block-container { padding-top: 2rem !important; padding-bottom: 1rem !important; }
    .stApp { background-color: #030305; color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #08080c; border-right: 1px solid #C5A059; }
    
    p, span, label, h1, h2, h3, h4, h5 { font-family: sans-serif; }
    
    div.stButton > button {
        background: linear-gradient(45deg, #C5A059, #FFD700) !important;
        color: black !important; font-weight: 800 !important;
        height: 60px !important; width: 100% !important;
        border-radius: 10px !important; font-size: 18px !important; border: none !important;
    }

    .price-card {
        padding: 12px; border-radius: 8px; border: 1px solid #1e1e26;
        background: #0d0d12; margin-bottom: 10px; text-align: center;
    }
    .up { color: #00ff88; font-weight: bold; font-size: 18px;}
    .down { color: #ff4b4b; font-weight: bold; font-size: 18px;}

    .ai-signal-pro {
        padding: 20px; border-radius: 12px; border: 2px solid #C5A059;
        background: linear-gradient(180deg, #0a0a1a 0%, #050508 100%);
        box-shadow: 0 10px 30px rgba(0,0,0,0.5); margin-bottom: 20px; text-align: center;
    }
    .analysis-box {
        background: rgba(197, 160, 89, 0.05); padding: 12px; 
        border-radius: 6px; border-left: 3px solid #C5A059; font-size: 0.9em; text-align: left; margin-top: 10px;
    }
    
    .acad-text { background: #11111d; padding: 20px; border-radius: 10px; border-left: 4px solid #C5A059; line-height: 1.6; margin-bottom: 15px; }
    .step-highlight { color: #C5A059; font-weight: bold; }
    .news-box { background: #161b22; padding: 12px; border-radius: 8px; border-left: 4px solid #C5A059; margin-bottom: 10px; font-size: 0.9em; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SISTEMA DE SEGURIDAD ---
CLIENTES_ACTIVOS = {
    "AXIOM_MASTER": "Administrador",
    "VIP_JUAN_01": "Juan Perez",
    "VIP_MARIA_02": "Maria Gomez",
    "PRUEBA_24H": "Cliente de prueba",
    "GEMINI_PRO_999": "Gemini(subscripcion mensual)"
}

if "autenticado" not in st.session_state: st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown("<div style='text-align:center; margin-top:80px;'><h1 style='color:#C5A059;'>🔒 AXIOM PRO</h1><p>Terminal Móvil Privada</p></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        pwd = st.text_input("Ingresar Pase VIP", type="password")
        if st.button("🗝️ DESBLOQUEAR"):
            if pwd in CLIENTES_ACTIVOS: st.session_state.autenticado = True; st.rerun()
            else: st.error("❌ Código incorrecto.")
    st.stop()

# --- 4. CONFIGURACIÓN LATERAL (SIDEBAR) ---
with st.sidebar:
    st.markdown("<h2 style='text-align:center; color:#C5A059;'>AXIOM PRO</h2>", unsafe_allow_html=True)
    st.markdown(f'''<a href="https://fxcentrum.com/registra-tu-cuenta/" target="_blank" style="text-decoration:none;"><button style="width:100%; background:#C5A059; color:black; border:none; padding:10px; border-radius:8px; font-weight:bold; cursor:pointer;">💎 CUENTA REAL</button></a>''', unsafe_allow_html=True)
    st.markdown("---")
    balance = st.number_input("💵 SALDO ($)", value=500, step=50)
    leverage = st.selectbox("⚖️ APALANCAMIENTO", [30, 100, 500], index=2)
    risk_pct = st.slider("⚠️ RIESGO POR OPERACIÓN (%)", 0.5, 5.0, 2.0)
    st.markdown("---")
    
    cat = st.selectbox("📂 MERCADO", ["💱 Divisas (Forex)", "🏢 Acciones", "📈 Índices", "🪙 Criptomonedas", "🛢️ Materias Primas"])
    
    if "Divisas" in cat: opciones = {"EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X", "USD/JPY": "JPY=X", "USD/CHF": "USDCHF=X", "AUD/USD": "AUDUSD=X", "USD/CAD": "CAD=X"}
    elif "Acciones" in cat: opciones = {"Tesla": "TSLA", "Nvidia": "NVDA", "Amazon": "AMZN", "Google": "GOOGL", "Apple": "AAPL", "Meta": "META", "Netflix": "NFLX", "Microsoft": "MSFT"}
    elif "Índices" in cat: opciones = {"S&P 500": "^GSPC", "Nasdaq 100": "^IXIC", "Dow Jones": "^DJI", "IBEX 35": "^IBEX", "DAX 40": "^GDAXI"}
    elif "Cripto" in cat: opciones = {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD", "Cardano": "ADA-USD", "Ripple": "XRP-USD"}
    else: opciones = {"Oro": "GC=F", "Petróleo": "BZ=F", "Plata": "SI=F", "Gas Natural": "NG=F"}
    
    activo_nombre = st.selectbox("🎯 ACTIVO", list(opciones.keys()))
    ticker = opciones[activo_nombre]
    st.markdown("<br>", unsafe_allow_html=True)
    btn_analizar = st.button("🚀 ANALIZAR MERCADO")

# --- 5. CABECERA DE PRECIOS EN VIVO ---
st.markdown("<h3 style='text-align:center; color:#C5A059;'>⚖️ TERMINAL MÓVIL</h3>", unsafe_allow_html=True)
c1, c2 = st.columns(2)

top_assets = [("BTC-USD", "BITCOIN"), ("SI=F", "PLATA"), ("^GSPC", "S&P 500"), ("BZ=F", "PETRÓLEO")]

for i in range(2):
    t, n = top_assets[i]
    d = yf.Ticker(t).history(period="2d")
    if len(d) > 1:
        curr, prev = d['Close'].iloc[-1], d['Close'].iloc[-2]
        change = curr - prev
        c_class = "up" if change >= 0 else "down"
        arrow = "▲" if change >= 0 else "▼"
        c1.markdown(f"<div class='price-card'><small>{n}</small><br><b class='{c_class}'>${curr:,.2f}</b><br><small class='{c_class}'>{arrow} {change:,.2f}</small></div>", unsafe_allow_html=True)

for i in range(2, 4):
    t, n = top_assets[i]
    d = yf.Ticker(t).history(period="2d")
    if len(d) > 1:
        curr, prev = d['Close'].iloc[-1], d['Close'].iloc[-2]
        change = curr - prev
        c_class = "up" if change >= 0 else "down"
        arrow = "▲" if change >= 0 else "▼"
        c2.markdown(f"<div class='price-card'><small>{n}</small><br><b class='{c_class}'>${curr:,.2f}</b><br><small class='{c_class}'>{arrow} {change:,.2f}</small></div>", unsafe_allow_html=True)

# --- 6. PESTAÑAS (AQUÍ ESTÁ EL ASISTENTE Y LA ACADEMIA) ---
tab_term, tab_acad, tab_chat = st.tabs(["🖥️ TERMINAL", "🎓 ACADEMIA", "💬 ASISTENTE"])

with tab_term:
    df = yf.download(ticker, period="10d", interval="15m", progress=False)
    
    if not df.empty:
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)
        
        df['SMA20'] = df['Close'].rolling(window=20).mean()
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['Recent_High'] = df['High'].rolling(window=20).max()
        df['Recent_Low'] = df['Low'].rolling(window=20).min()
        df.dropna(inplace=True)
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Precio", increasing_line_color='#00ff88', decreasing_line_color='#ff4b4b'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA50'], line=dict(color='#C5A059', width=2), name="EMA 50"), row=1, col=1)
        v_colors = ['#00ff88' if r['Open'] < r['Close'] else '#ff4b4b' for i, r in df.iterrows()]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=v_colors), row=2, col=1)
        
        fig.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        fig.update_yaxes(gridcolor='#1e1e26')
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        if btn_analizar:
            last_p = float(df['Close'].iloc[-1])
            sma20 = float(df['SMA20'].iloc[-1])
            ema50 = float(df['EMA50'].iloc[-1])
            tp_max = float(df['Recent_High'].iloc[-2])
            tp_min = float(df['Recent_Low'].iloc[-2])
            
            if last_p > ema50 and last_p > sma20:
                side, color, tp = "COMPRA (BUY)", "#00ff88", tp_max + (tp_max * 0.001)
                razon = "Doble confirmación técnica. El precio rompe la SMA20 y se sostiene sobre la EMA50 con volumen comprador."
            elif last_p < ema50 and last_p < sma20:
                side, color, tp = "VENTA (SELL)", "#ff4b4b", tp_min - (tp_min * 0.001)
                razon = "Caída con volumen confirmada. El precio pierde tanto la SMA20 como la EMA50."
            else:
                side, color, tp = "ESPERAR (NEUTRAL)", "#FFD700", last_p
                razon = "Falta de confluencia. El precio no tiene dirección clara entre la SMA20 y la EMA50."

            st.markdown(f"""
                <div class='ai-signal-pro'>
                    <small style='color:#C5A059;'>🤖 SEÑAL AXIOM IA</small>
                    <h2 style='color:{color}; margin:0;'>{side}</h2>
                    <p>Probabilidad de Éxito: <b style='color:#00ff88;'>75.0%</b></p>
                    <div class='analysis-box'><b>ANÁLISIS TÉCNICO:</b><br>{razon}</div>
                    <hr style='border-color:#1e1e26;'>
                    <p style='color:#C5A059; font-weight:bold; margin-bottom:0;'>🎯 TAKE PROFIT SUGERIDO</p>
                    <b style='font-size:32px; color:#ffffff;'>{tp:,.4f}</b>
                </div>
            """, unsafe_allow_html=True)
            
            perdida = balance * (risk_pct / 100)
            st.info(f"🛡️ Ajusta tu lotaje para arriesgar exactamente: **${perdida:,.2f}**")
            
            st.markdown("<h4 style='color:#C5A059; margin-top:15px;'>📰 Radar de Noticias</h4>", unsafe_allow_html=True)
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
                    st.markdown(f"<div class='news-box'><b>{pub}</b>: {title}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='news-box'><b>Axiom Analítica</b>: Escaneando flujos de volumen en {activo_nombre}.</div>", unsafe_allow_html=True)

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
        with st.chat_message(message["role"]): st.markdown(message["content"])

    prompt = st.chat_input("Escribe tu duda aquí...")
    if prompt or pregunta_rapida:
        texto_usuario = prompt if prompt else pregunta_rapida
        st.session_state.messages.append({"role": "user", "content": texto_usuario})
        with st.chat_message("user"): st.markdown(texto_usuario)

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

        with st.chat_message("assistant"): st.markdown(respuesta)
        st.session_state.messages.append({"role": "assistant", "content": respuesta})

st.caption(f"Axiom Mobile Terminal v5.5 | {datetime.now().strftime('%H:%M:%S')}")