import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz
import re
import os

# 1. PAGE CONFIGURATION
st.set_page_config(
    page_title="EDM VTMS Dashboard",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# --- SET MALAYSIA TIMEZONE ---
msia_tz = pytz.timezone('Asia/Kuala_Lumpur')
waktu_msia = datetime.now(msia_tz)

# 2. MODERN CSS
st.markdown("""
    <style>
    .stApp {
        background: radial-gradient(circle at top right, #f8faff, #eef2f7);
        font-family: 'Inter', sans-serif;
    }
    [data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.8) !important;
        backdrop-filter: blur(10px);
    }
    [data-testid="stMetric"] {
        background: white !important;
        padding: 20px !important;
        border-radius: 20px !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.03) !important;
    }
    header[data-testid="stHeader"] { background: transparent !important; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# 3. DATA LOAD (Contoh)
SHEET_REPORT_URL = "https://docs.google.com/spreadsheets/d/1WB76n71wxMT3i5ZCaoCBIyb888il-qBydY8OEgC81Q8/export?format=csv&gid=296214979"
SHEET_EQUIP_URL = "https://docs.google.com/spreadsheets/d/1QeQgEA--b1TX3Q8LPgmog7XP97Tg0dHSr3gIAAGXV4g/export?format=csv&gid=416421947"

@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url, on_bad_lines='skip')
        data.columns = data.columns.str.strip()
        return data
    except: return pd.DataFrame()

df_raw = load_data(SHEET_REPORT_URL)
df_equip = load_data(SHEET_EQUIP_URL)

# 4. SIDEBAR
with st.sidebar:
    st.markdown("## 🛡️ VTMS DEPARTMENT")
    st.image("https://cdn-icons-png.flaticon.com/512/1063/1063140.png", width=80) # Logo di sidebar
    st.divider()
    st.markdown(f"🕒 **Last Sync:** {waktu_msia.strftime('%H:%M:%S')}")

# 5. HEADER DASHBOARD (LOGO + TAJUK + JAM)
# Bahagian ini adalah pembaikan utama untuk masalah dalam gambar anda
st.markdown("""
    <div style="
        background: linear-gradient(90deg, #0984E3, #6c5ce7);
        padding: 30px;
        border-radius: 20px;
        margin-bottom: 25px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: white;
    ">
        <div style="display: flex; flex-direction: column;">
            <img src="https://cdn-icons-png.flaticon.com/512/1063/1063140.png" 
                 style="height: 50px; width: 50px; margin-bottom: 10px; filter: brightness(0) invert(1);">
            
            <h1 style="margin: 0; font-size: 28px; font-weight: 800; line-height: 1.1;">
                EDM VTMS LPJ/PTP<br>
                <span style="font-weight: 300; opacity: 0.8; font-size: 18px;">Management Dashboard</span>
            </h1>
        </div>

        <div style="text-align: right; border-left: 2px solid rgba(255,255,255,0.2); padding-left: 30px;">
            <h2 id="live_clock" style="margin: 0; font-family: monospace; font-size: 40px; font-weight: 900;">00:00:00</h2>
            <p id="live_date" style="margin: 5px 0 0 0; font-size: 14px; opacity: 0.8; text-transform: uppercase;"></p>
        </div>
    </div>

    <script>
    function updateClock() {
        const now = new Date();
        const tStr = now.toLocaleTimeString('en-GB', { timeZone: 'Asia/Kuala_Lumpur', hour12: false });
        const dStr = now.toLocaleDateString('ms-MY', { timeZone: 'Asia/Kuala_Lumpur', weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' });
        
        document.getElementById('live_clock').innerText = tStr;
        document.getElementById('live_date').innerText = dStr;
    }
    setInterval(updateClock, 1000);
    updateClock();
    </script>
""", unsafe_allow_html=True)

# 6. TABS & CONTENT
tab1, tab2 = st.tabs(["📝 Reports", "⚙️ Status"])

with tab1:
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Reports", len(df_raw))
    st.subheader("Recent Checklist Submissions")
    st.dataframe(df_raw, use_container_width=True)

with tab2:
    st.subheader("Equipment Condition")
    # Logik chart anda di sini...
