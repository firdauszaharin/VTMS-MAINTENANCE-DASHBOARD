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

# 2. MODERN CSS (UI MODEN 2026)
st.markdown("""
    <style>
    /* Latar Belakang & Font */
    .stApp {
        background: radial-gradient(circle at top right, #f8faff, #eef2f7);
        font-family: 'Inter', sans-serif;
    }

    /* Glassmorphism Sidebar */
    [data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.8) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(0,0,0,0.05);
    }

    /* Kotak Metric Floating */
    [data-testid="stMetric"] {
        background: white !important;
        padding: 20px !important;
        border-radius: 20px !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.03) !important;
        border: 1px solid rgba(0,0,0,0.05) !important;
    }

    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: white;
        border-radius: 10px;
        padding: 8px 20px;
        border: 1px solid rgba(0,0,0,0.05);
    }
    .stTabs [aria-selected="true"] {
        background: #0984E3 !important;
        color: white !important;
    }

    /* Header Cleanup */
    header[data-testid="stHeader"] { background: transparent !important; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    .alert-box {
        background: white; border-left: 6px solid #FF4B4B;
        padding: 20px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# 3. DATA LINKS
SHEET_REPORT_URL = "https://docs.google.com/spreadsheets/d/1WB76n71wxMT3i5ZCaoCBIyb888il-qBydY8OEgC81Q8/export?format=csv&gid=296214979"
SHEET_EQUIP_URL = "https://docs.google.com/spreadsheets/d/1QeQgEA--b1TX3Q8LPgmog7XP97Tg0dHSr3gIAAGXV4g/export?format=csv&gid=416421947"
PDF_COL = "UPLOAD REPORT" 

# 4. DATA LOAD FUNCTION
@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url, on_bad_lines='skip')
        data.columns = data.columns.str.strip()
        time_col = next((c for c in data.columns if any(x in c.lower() for x in ['timestamp', 'time', 'date', 'tarikh'])), None)
        if time_col:
            data[time_col] = pd.to_datetime(data[time_col], errors='coerce')
            data['Year'] = data[time_col].dt.year
        return data
    except:
        return pd.DataFrame()

df_raw = load_data(SHEET_REPORT_URL)
df_equip = load_data(SHEET_EQUIP_URL)

# 5. SIDEBAR
with st.sidebar:
    st.markdown("## 🛡️ ADMIN PANEL")
    # Gantikan URL ini dengan URL logo anda yang sebenar jika perlu
    st.image("https://cdn-icons-png.flaticon.com/512/1063/1063140.png", width=80)
    st.divider()
    
    st.markdown("### 🔍 FILTERS")
    search_report = st.text_input("🔎 Search Checklist:", placeholder="MET, VHF, etc...")
    search_staff = st.text_input("👤 Staff Name:")
    
    st.divider()
    st.link_button("📂 Open Drive Folder", "https://drive.google.com/drive/folders/...", use_container_width=True)

# 6. EXECUTIVE SUMMARY (LOGO + TAJUK + CLOCK)
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
    ">
        <div style="display: flex; flex-direction: column; align-items: flex-start;">
            <div style="margin-bottom: 15px;">
                <img src="https://cdn-icons-png.flaticon.com/512/1063/1063140.png" 
                     style="height: 60px; filter: brightness(0) invert(1);"> 
            </div>
            
            <h1 style="
                color: white;
                font-size: 30px;
                font-weight: 800;
                margin: 0;
                letter-spacing: -1px;
                line-height: 1.1;
            ">
                EDM VTMS LPJ/PTP<br>
                <span style="font-weight: 300; opacity: 0.8; font-size: 20px;">Management Dashboard</span>
            </h1>
        </div>

        <div style="text-align: right; border-left: 2px solid rgba(255,255,255,0.2); padding-left: 30px;">
            <h2 id="clock" style="
                color: white; 
                margin: 0; 
                font-family: 'Courier New', monospace; 
                font-size: 45px; 
                font-weight: 900;
            ">00:00:00</h2>
            <p id="date" style="
                color: rgba(255,255,255,0.8); 
                margin: 5px 0 0 0; 
                font-size: 14px; 
                text-transform: uppercase;
                letter-spacing: 1px;
            "></p>
        </div>
    </div>

    <script>
    function updateClock() {
        const now = new Date();
        const tOpt = { timeZone: "Asia/Kuala_Lumpur", hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' };
        const dOpt = { timeZone: "Asia/Kuala_Lumpur", weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' };
        document.getElementById('clock').textContent = new Intl.DateTimeFormat('en-GB', tOpt).format(now);
        document.getElementById('date').textContent = new Intl.DateTimeFormat('ms-MY', dOpt).format(now);
    }
    setInterval(updateClock, 1000);
    updateClock();
    </script>
""", unsafe_allow_html=True)

# 7. MAIN TABS
tab1, tab2 = st.tabs(["📝 Maintenance Reports", "⚙️ Equipment Status"])

with tab1:
    if not df_raw.empty:
        df = df_raw.copy()
        if search_report: df = df[df['REPORT CHECKLIST'].str.contains(search_report, case=False, na=False)]
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Reports", len(df))
        m2.metric("Latest Submission", df.iloc[0]['Name'] if not df.empty else "N/A")
        m3.metric("Status", "System Active", delta="OK")

        st.subheader("📋 Recent Submissions")
        st.dataframe(df, use_container_width=True, hide_index=True)

with tab2:
    if not df_equip.empty:
        # Cari kolum bulan (2025/2026)
        month_cols = [c for c in df_equip.columns if any(yr in str(c) for yr in ["2025", "2026"])]
        
        if month_cols:
            sel_m = st.selectbox("📅 Month:", month_cols, index=len(month_cols)-1)
            
            # Data Visual
            status_data = df_equip[sel_m].astype(str).str.strip().str.upper()
            df_v = df_equip.copy()
            df_v[sel_m] = status_data
            
            # --- GRAPHS ---
            c1, c2 = st.columns(2)
            color_map = {'OK':'#2ecc71', 'FAULTY':'#f1c40f', 'MISSING':'#e74c3c'}
            
            with c1:
                fig_pie = px.pie(df_v, names=sel_m, title="Condition Overview", hole=0.5, color=sel_m, color_discrete_map=color_map)
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with c2:
                fig_bar = px.histogram(df_v, x='Site' if 'Site' in df_v.columns else df_v.columns[0], color=sel_m, barmode='group', title="Status by Site", color_discrete_map=color_map)
                st.plotly_chart(fig_bar, use_container_width=True)

            st.divider()
            st.subheader("📦 Inventory Details")
            st.dataframe(df_v[['Site', 'Type', 'Serial No', sel_m]], use_container_width=True, hide_index=True)
