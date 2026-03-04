import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz
import re
import os

# ==========================================
# 1. PAGE CONFIG & THEME
# ==========================================
st.set_page_config(
    page_title="EDM VTMS Dashboard",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# Set Timezone
msia_tz = pytz.timezone('Asia/Kuala_Lumpur')
waktu_msia = datetime.now(msia_tz)

# ==========================================
# 2. CSS STYLING (MODERN & CLEAN)
# ==========================================
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    
    /* Header Banner */
    .header-container {
        background: linear-gradient(90deg, #0984E3, #6c5ce7);
        padding: 30px;
        border-radius: 15px;
        color: white;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }
    
    /* Metrics Styling */
    [data-testid="stMetric"] {
        background: white;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    /* Sidebar Cleanup */
    header[data-testid="stHeader"] { background: transparent !important; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. DATA LOADING
# ==========================================
SHEET_REPORT_URL = "https://docs.google.com/spreadsheets/d/1WB76n71wxMT3i5ZCaoCBIyb888il-qBydY8OEgC81Q8/export?format=csv&gid=296214979"
SHEET_EQUIP_URL = "https://docs.google.com/spreadsheets/d/1QeQgEA--b1TX3Q8LPgmog7XP97Tg0dHSr3gIAAGXV4g/export?format=csv&gid=416421947"

@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url, on_bad_lines='skip')
        data.columns = data.columns.str.strip()
        # Cari kolum masa untuk filter tahun
        time_col = next((c for c in data.columns if any(x in c.lower() for x in ['timestamp', 'time', 'date'])), None)
        if time_col:
            data[time_col] = pd.to_datetime(data[time_col], errors='coerce')
            data['Year'] = data[time_col].dt.year
        return data
    except:
        return pd.DataFrame()

df_raw = load_data(SHEET_REPORT_URL)
df_equip = load_data(SHEET_EQUIP_URL)

# ==========================================
# 4. SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("## 🛡️ VTMS ADMIN")
    # Logo Sidebar (Standard)
    st.image("https://cdn-icons-png.flaticon.com/512/1063/1063140.png", width=70)
    st.divider()
    
    st.markdown("### 🔍 FILTERS")
    search_report = st.text_input("🔎 Search Checklist:", placeholder="MET, VHF, etc...")
    search_staff = st.text_input("👤 Staff Name:")
    
    st.divider()
    st.link_button("📂 Open Drive Folder", "https://drive.google.com/drive/folders/...", use_container_width=True)

# ==========================================
# 5. LIVE HEADER (LOGO + TITLE + CLOCK)
# ==========================================
# Bahagian ini yang selesaikan masalah jam & logo atas tulisan
st.markdown("""
    <div class="header-container">
        <div>
            <img src="https://cdn-icons-png.flaticon.com/512/1063/1063140.png" 
                 style="height: 50px; filter: brightness(0) invert(1); margin-bottom: 10px;">
            <div style="font-size: 28px; font-weight: 800; line-height: 1;">EDM VTMS LPJ/PTP</div>
            <div style="font-size: 18px; opacity: 0.8; font-weight: 300;">Management Dashboard</div>
        </div>
        <div style="text-align: right; border-left: 1px solid rgba(255,255,255,0.3); padding-left: 25px;">
            <div id="live_clock" style="font-family: monospace; font-size: 40px; font-weight: 900;">00:00:00</div>
            <div id="live_date" style="font-size: 14px; opacity: 0.8; text-transform: uppercase;"></div>
        </div>
    </div>

    <script>
    function updateClock() {
        const now = new Date();
        const tStr = now.toLocaleTimeString('en-GB', { hour12: false });
        const dStr = now.toLocaleDateString('ms-MY', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' });
        document.getElementById('live_clock').innerText = tStr;
        document.getElementById('live_date').innerText = dStr;
    }
    setInterval(updateClock, 1000);
    updateClock();
    </script>
""", unsafe_allow_html=True)

# ==========================================
# 6. MAIN CONTENT (TABS)
# ==========================================
tab1, tab2 = st.tabs(["📝 Maintenance Reports", "⚙️ Equipment Status"])

with tab1:
    if not df_raw.empty:
        df = df_raw.copy()
        if search_report: 
            df = df[df['REPORT CHECKLIST'].str.contains(search_report, case=False, na=False)]
        
        # Metrics Row
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Submissions", len(df))
        m2.metric("Latest Report", df.iloc[0]['Name'] if not df.empty else "N/A")
        m3.metric("System Status", "ACTIVE")

        st.subheader("📋 Recent Report Logs")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning("Data Report tidak dijumpai. Sila semak pautan Google Sheets.")

with tab2:
    if not df_equip.empty:
        # Cari kolum status bulanan
        month_cols = [c for c in df_equip.columns if any(yr in str(c) for yr in ["2025", "2026"])]
        if month_cols:
            selected_month = st.selectbox("📅 Select Month:", month_cols, index=len(month_cols)-1)
            
            # Status Metrics
            status_data = df_equip[selected_month].astype(str).str.strip().str.upper()
            c1, c2, c3 = st.columns(3)
            c1.metric("Equipment OK", len(df_equip[status_data == 'OK']))
            c2.metric("Faulty ⚠️", len(df_equip[status_data == 'FAULTY']))
            c3.metric("Missing ❌", len(df_equip[status_data == 'MISSING']))

            # Graphs
            g1, g2 = st.columns(2)
            with g1:
                fig_pie = px.pie(df_equip, names=selected_month, title="Condition Overview", hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)
            with g2:
                if 'Site' in df_equip.columns:
                    fig_bar = px.histogram(df_equip, x='Site', color=selected_month, barmode='group', title="Status by Site")
                    st.plotly_chart(fig_bar, use_container_width=True)
            
            st.divider()
            st.subheader("📦 Inventory Asset List")
            st.dataframe(df_equip[['Site', 'Type', 'Serial No', selected_month]], use_container_width=True, hide_index=True)
    else:
        st.warning("Data Equipment tidak dijumpai.")
