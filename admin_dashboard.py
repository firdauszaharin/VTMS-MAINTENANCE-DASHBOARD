import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz
import re
import os

# 1. PAGE CONFIGURATION
st.set_page_config(
    page_title="VTMS Admin & Inventory Dashboard",
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
    /* Latar belakang utama - Guna warna cerah supaya data nampak menonjol */
    .stApp {
        background: #f0f2f6;
        font-family: 'Inter', sans-serif;
    }

    /* --- SIDEBAR CUSTOM COLOR (NAVY BLUE) --- */
    [data-testid="stSidebar"] {
        background-color: #1e293b !important; 
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Warna Teks Sidebar (Putih) */
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }

    /* Warna Input & Selectbox dlm Sidebar */
    [data-testid="stSidebar"] .stTextInput input, 
    [data-testid="stSidebar"] div[data-baseweb="select"] > div {
        background-color: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        color: white !important;
        border-radius: 10px !important;
    }

    /* --- KOTAK METRIC & TABS --- */
    [data-testid="stMetric"] {
        background: white !important;
        padding: 20px !important;
        border-radius: 15px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important;
    }

    .stTabs [aria-selected="true"] {
        background: #1e293b !important; 
        color: white !important;
        border-radius: 10px !important;
    }

    header[data-testid="stHeader"] { background: transparent !important; }
    footer {visibility: hidden;}
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
        else:
            data['Year'] = None
        return data
    except Exception as e:
        return pd.DataFrame()

df_raw = load_data(SHEET_REPORT_URL)
df_equip = load_data(SHEET_EQUIP_URL)

# --- ICON MAPPING ---
icon_map = {
    "MET REPORT": "https://cdn-icons-png.flaticon.com/512/1146/1146869.png",
    "OPERATOR WORKSTATION": "https://cdn-icons-png.flaticon.com/512/689/689382.png",
    "WALL DISPLAY REPORT": "https://cdn-icons-png.flaticon.com/512/1035/1035688.png",
    "VHF PTP FLOOR 8": "https://cdn-icons-png.flaticon.com/512/3126/3126505.png",
    "SERVER ROOM REPORT (PTP/LPJ)": "https://cdn-icons-png.flaticon.com/512/2333/2333241.png"
}

if "selected_row_idx" not in st.session_state:
    st.session_state.selected_row_idx = None

# 5. SIDEBAR
with st.sidebar:
    st.markdown("## 📊 VTMS ADMIN")
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    st.divider()
    st.markdown(f"🕒 **Update:** {waktu_msia.strftime('%H:%M:%S')}")
    st.divider()
    
    st.markdown("### 🔍 FILTERS")
    if not df_raw.empty and 'Year' in df_raw.columns:
        year_list = sorted(df_raw['Year'].dropna().unique(), reverse=True)
        sel_year = st.selectbox("📅 Year:", ["All Years"] + [int(t) for t in year_list])
    else:
        sel_year = st.selectbox("📅 Year:", ["All Years"])
        
    search_report = st.text_input("🔎 Type:", placeholder="MET, SERVER...")
    search_staff = st.text_input("👤 Staff:")
    
    st.divider()
    st.link_button("📂 Open Drive", "https://drive.google.com/drive/folders/1lG9eKZ69hpT6q-aqXpNxyd0HMcXdr3A4jUaXLCpDpOPffFzG0XK-MGBLaGHcBMcyqWjyLy", use_container_width=True)

# 6. EXECUTIVE SUMMARY (BLUE HEADER)
st.title("EDM VTMS LPJ/PTP Dashboard")

if not df_equip.empty:
    month_cols = [c for c in df_equip.columns if any(yr in c for yr in ["2025", "2026"])]
    latest_month = month_cols[-1] if month_cols else None
    
    if latest_month:
        status_check = df_equip[latest_month].astype(str).str.strip().str.upper()
        faulty_data = df_equip[status_check.isin(['FAULTY', 'MISSING'])]
        
        # Header Box
        st.markdown(f"""
            <div style="background: linear-gradient(90deg, #1e293b, #334155); padding: 25px; border-radius: 15px; color: white; margin-bottom: 20px;">
                <h2 style="margin:0;">Status Overview: {latest_month}</h2>
                <p style="margin:0; opacity: 0.8;">Monitoring {len(df_equip)} items across all sites.</p>
            </div>
        """, unsafe_allow_html=True)

# 7. TABS
tab1, tab2 = st.tabs(["📝 Reports", "⚙️ Equipment"])

with tab1:
    if not df_raw.empty:
        df = df_raw.copy()
        # Apply Filters
        if sel_year != "All Years": df = df[df['Year'] == sel_year]
        if search_report: df = df[df['REPORT CHECKLIST'].str.contains(search_report, case=False, na=False)]
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Reports", len(df))
        m2.metric("Approved ✅", len(df[df['STATUS'] == 'APPROVED']) if 'STATUS' in df.columns else 0)
        m3.metric("Pending ⏳", len(df[~df['STATUS'].isin(['APPROVED', 'REJECTED'])]) if 'STATUS' in df.columns else 0)

        st.dataframe(df, use_container_width=True)

with tab2:
    if not df_equip.empty:
        st.subheader("Equipment Condition")
        st.dataframe(df_equip, use_container_width=True)
