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

# 2. MODERN CSS (THEME: PROFESSIONAL NAVY)
st.markdown("""
    <style>
    /* Latar belakang utama dashboard */
    .stApp {
        background: #f8faff;
        font-family: 'Inter', sans-serif;
    }

    /* --- SIDEBAR CUSTOM STYLE --- */
    [data-testid="stSidebar"] {
        background-color: #1e293b !important; /* Navy yang seimbang, tidak terlalu gelap */
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Warna semua teks dalam sidebar jadi putih */
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }

    /* Kemaskan kotak input (Search & Selectbox) dlm sidebar */
    [data-testid="stSidebar"] .stTextInput input, 
    [data-testid="stSidebar"] div[data-baseweb="select"] > div {
        background-color: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 10px !important;
        color: white !important;
    }

    /* --- UI DASHBOARD COMPONENTS --- */
    [data-testid="stMetric"] {
        background: white !important;
        padding: 20px !important;
        border-radius: 15px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important;
        border: 1px solid #ececec !important;
    }

    /* Warna Tab yang aktif (selaras dgn Navy Sidebar) */
    .stTabs [aria-selected="true"] {
        background: #1e293b !important; 
        color: white !important;
        border-radius: 8px;
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

# --- REPORT ICON MAPPING ---
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
    st.markdown(f"🕒 **Last Sync:** {waktu_msia.strftime('%H:%M:%S')}")
    st.divider()
    
    st.markdown("### 🔍 GLOBAL FILTERS")
    if not df_raw.empty and 'Year' in df_raw.columns:
        year_list = sorted(df_raw['Year'].dropna().unique(), reverse=True)
        sel_year = st.selectbox("📅 Select Year:", ["All Years"] + [int(t) for t in year_list])
    else:
        sel_year = st.selectbox("📅 Select Year:", ["All Years"])
        
    search_report = st.text_input("🔎 Report Type:", placeholder="MET, SERVER...")
    search_staff = st.text_input("👤 Staff Name:")
    
    st.divider()
    st.link_button("📂 Open Drive Folder", "https://drive.google.com/drive/folders/1lG9eKZ69hpT6q-aqXpNxyd0HMcXdr3A4jUaXLCpDpOPffFzG0XK-MGBLaGHcBMcyqWjyLy", use_container_width=True)

# 6. EXECUTIVE SUMMARY HEADER
if not df_equip.empty:
    month_cols = [c for c in df_equip.columns if any(yr in c for yr in ["2025", "2026"])]
    latest_month = month_cols[-1] if month_cols else None
    
    st.markdown(f"""
    <div style="background: linear-gradient(90deg, #1e293b, #334155); padding: 30px; border-radius: 20px; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center; color: white;">
        <div>
            <h1 style="margin: 0; font-size: 28px;">EDM VTMS LPJ/PTP</h1>
            <p style="margin: 0; opacity: 0.8;">Management Dashboard • {latest_month}</p>
        </div>
        <div style="text-align: right;">
            <h2 id="clock" style="margin: 0; font-family: monospace; font-size: 35px;">00:00:00</h2>
            <p id="date" style="margin: 0; font-size: 14px; opacity: 0.8;"></p>
        </div>
    </div>
    <script>
        function updateClock() {{
            const now = new Date();
            const tOpt = {{ timeZone: "Asia/Kuala_Lumpur", hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }};
            const dOpt = {{ timeZone: "Asia/Kuala_Lumpur", weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' }};
            document.getElementById('clock').textContent = new Intl.DateTimeFormat('en-GB', tOpt).format(now);
            document.getElementById('date').textContent = new Intl.DateTimeFormat('ms-MY', dOpt).format(now);
        }}
        setInterval(updateClock, 1000); updateClock();
    </script>
    """, unsafe_allow_html=True)

# 7. MAIN CONTENT TABS
tab1, tab2 = st.tabs(["📝 Maintenance Reports", "⚙️ Equipment Status"])

# --- TAB 1: REPORTS ---
with tab1:
    if not df_raw.empty:
        df = df_raw.copy()
        if sel_year != "All Years": df = df[df['Year'] == sel_year]
        if search_report: df = df[df['REPORT CHECKLIST'].str.contains(search_report, case=False, na=False)]
        if search_staff: df = df[df['Name'].str.contains(search_staff, case=False, na=False)]
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Reports", len(df))
        m2.metric("Approved ✅", len(df[df['STATUS'] == 'APPROVED']) if 'STATUS' in df.columns else 0)
        m3.metric("Rejected ❌", len(df[df['STATUS'] == 'REJECTED']) if 'STATUS' in df.columns else 0)
        m4.metric("Pending ⏳", len(df[~df['STATUS'].isin(['APPROVED', 'REJECTED'])]) if 'STATUS' in df.columns else 0)

        st.plotly_chart(px.histogram(df, x='REPORT CHECKLIST', color='STATUS', barmode='group', title='Report Activity'), use_container_width=True)

        st.subheader("📋 Submitted Reports Record")
        if 'REPORT CHECKLIST' in df.columns:
            df.insert(0, 'ICON', df['REPORT CHECKLIST'].map(icon_map).fillna("https://cdn-icons-png.flaticon.com/512/2991/2991108.png"))

        st.dataframe(df, use_container_width=True, hide_index=True, column_config={
            "ICON": st.column_config.ImageColumn("Type"),
            PDF_COL: st.column_config.LinkColumn("Report File", display_text="OPEN PDF 📄")
        })

# --- TAB 2: EQUIPMENT ---
with tab2:
    if not df_equip.empty:
        selected_month = st.selectbox("📅 Month:", month_cols, index=len(month_cols)-1)
        status_series = df_equip[selected_month].astype(str).str.strip().str.upper()
        
        me1, me2, me3 = st.columns(3)
        me1.metric("Equipment OK", len(df_equip[status_series == 'OK']))
        me2.metric("Faulty ⚠️", len(df_equip[status_series == 'FAULTY']))
        me3.metric("Missing ❌", len(df_equip[status_series == 'MISSING']))

        fig = px.pie(df_equip, names=selected_month, hole=0.5, title=f"Status Overview {selected_month}",
                     color_discrete_map={'OK':'#2ecc71','FAULTY':'#f1c40f','MISSING':'#e74c3c'})
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(df_equip[["Site", "Type", "Serial No", selected_month]], use_container_width=True)
