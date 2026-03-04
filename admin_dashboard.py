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
        border-right: 1px solid rgba(0,0,0,0.05);
    }
    [data-testid="stMetric"] {
        background: white !important;
        padding: 20px !important;
        border-radius: 20px !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.03) !important;
        border: 1px solid rgba(0,0,0,0.05) !important;
    }
    .stTabs [aria-selected="true"] {
        background: #0984E3 !important;
        color: white !important;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] { background: transparent !important; }
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
    except Exception:
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
    # Fix Logo: Guna URL jika file lokal xda
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.image("https://www.zakatselangor.com.my/wp-content/uploads/2017/06/logo-lzt-2.png", width=180)
    
    st.divider()
    st.markdown(f"🕒 **Last Sync:** {waktu_msia.strftime('%H:%M:%S')}")
    st.divider()
    
    st.markdown("### 🔍 GLOBAL FILTERS")
    year_opts = ["All Years"]
    if not df_raw.empty and 'Year' in df_raw.columns:
        year_opts += sorted([int(x) for x in df_raw['Year'].dropna().unique()], reverse=True)
    sel_year = st.selectbox("📅 Select Year:", year_opts)
        
    search_report = st.text_input("🔎 Report Type:", placeholder="MET, SERVER...")
    search_staff = st.text_input("👤 Staff Name:")
    st.divider()
    st.link_button("📂 Open Drive Folder", "https://drive.google.com/drive/folders/1lG9eKZ69hpT6q-aqXpNxyd0HMcXdr3A4jUaXLCpDpOPffFzG0XK-MGBLaGHcBMcyqWjyLy", use_container_width=True)

# 6. EXECUTIVE SUMMARY (HERO)
st.title("EDM VTMS LPJ/PTP Management Dashboard")

if not df_equip.empty:
    month_cols = [c for c in df_equip.columns if any(yr in c for yr in ["2025", "2026"])]
    latest_month = month_cols[-1] if month_cols else None
    
    if latest_month:
        status_check = df_equip[latest_month].astype(str).str.strip().str.upper()
        faulty_data = df_equip[status_check.isin(['FAULTY', 'MISSING'])]
        
        # Modern Hero Section with Clock
        st.markdown(f"""
            <div style="background: linear-gradient(90deg, #0984E3, #6c5ce7); padding: 30px; border-radius: 20px; color: white; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h1 style="margin:0; font-size: 30px; color: white;">EDM VTMS LPJ/PTP</h1>
                    <p style="margin:0; opacity: 0.8; font-size: 18px;">Management Dashboard</p>
                </div>
                <div style="text-align: right;">
                    <h2 style="margin: 0; font-family: monospace; font-size: 40px; color: white;">{waktu_msia.strftime('%H:%M')}</h2>
                    <p style="margin: 0; font-size: 14px; opacity: 0.8;">{waktu_msia.strftime('%d %b %Y')}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.write("") # Spacer

# 7. MAIN CONTENT TABS
tab1, tab2 = st.tabs(["📝 Maintenance Reports", "⚙️ Equipment Status"])

with tab1:
    if not df_raw.empty:
        df = df_raw.copy()
        if sel_year != "All Years": df = df[df['Year'] == sel_year]
        if search_report: df = df[df['REPORT CHECKLIST'].str.contains(search_report, case=False, na=False)]
        if search_staff: df = df[df['Name'].str.contains(search_staff, case=False, na=False)]
        
        # Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Reports", len(df))
        m2.metric("Approved ✅", len(df[df['STATUS'] == 'APPROVED']) if 'STATUS' in df.columns else 0)
        m3.metric("Rejected ❌", len(df[df['STATUS'] == 'REJECTED']) if 'STATUS' in df.columns else 0)
        m4.metric("Pending ⏳", len(df[~df['STATUS'].isin(['APPROVED', 'REJECTED'])]) if 'STATUS' in df.columns else 0)

        # GRAF SECTION
        st.markdown("### 🎯 Performance Overview")
        col_p, col_b = st.columns(2)
        with col_p:
            # Pie Chart
            chart_df = df.dropna(subset=['STATUS'])
            if not chart_df.empty:
                st.plotly_chart(px.pie(chart_df, names='STATUS', hole=0.4, title="Status Distribution",
                                      color_discrete_map={'APPROVED':'#2ecc71', 'REJECTED':'#e74c3c'}), use_container_width=True)
        with col_b:
            # Histogram
            if 'REPORT CHECKLIST' in df.columns:
                st.plotly_chart(px.histogram(df, x='REPORT CHECKLIST', color='STATUS', title="Report by Type",
                                          color_discrete_map={'APPROVED':'#2ecc71', 'REJECTED':'#e74c3c'}), use_container_width=True)

        st.divider()
        
        # Fix: Status Merah/Hijau
        def style_status(row):
            styles = [''] * len(row)
            if 'STATUS' in row.index:
                val = str(row['STATUS']).upper()
                idx = row.index.get_loc('STATUS')
                if val == 'REJECTED': styles[idx] = 'background-color: #F8D7DA; color: #721C24; font-weight: bold'
                elif val == 'APPROVED': styles[idx] = 'background-color: #D4EDDA; color: #155724;'
            return styles

        if 'REPORT CHECKLIST' in df.columns:
            df.insert(0, 'ICON', df['REPORT CHECKLIST'].map(icon_map).fillna("https://cdn-icons-png.flaticon.com/512/2991/2991108.png"))

        st.dataframe(
            df.style.apply(style_status, axis=1), 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "ICON": st.column_config.ImageColumn("Type"),
                PDF_COL: st.column_config.LinkColumn("Report File", display_text="OPEN PDF 📄")
            }
        )

with tab2:
    if not df_equip.empty:
        month_cols = [c for c in df_equip.columns if any(yr in c for yr in ["2025", "2026"])]
        selected_month = st.selectbox("📅 Select Month:", month_cols, index=len(month_cols)-1, key="inv_month")
        
        status_s = df_equip[selected_month].astype(str).str.strip().str.upper()
        
        me1, me2, me3 = st.columns(3)
        me1.metric("Equipment OK", len(df_equip[status_s == 'OK']))
        me2.metric("Faulty ⚠️", len(df_equip[status_s == 'FAULTY']))
        me3.metric("Missing ❌", len(df_equip[status_s == 'MISSING']))

        # Graf Inventori
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.pie(df_equip, names=selected_month, hole=0.5, title="Condition",
                                   color_discrete_map={'OK':'#2ecc71','FAULTY':'#f1c40f','MISSING':'#e74c3c'}), use_container_width=True)
        with c2:
            if 'Site' in df_equip.columns:
                st.plotly_chart(px.histogram(df_equip, x='Site', color=selected_month, barmode='group',
                                          color_discrete_map={'OK':'#2ecc71','FAULTY':'#f1c40f','MISSING':'#e74c3c'}), use_container_width=True)

        st.divider()
        
        # Inventory Table Style
        def style_inv(row):
            styles = [''] * len(row)
            val = str(row[selected_month]).upper()
            idx = row.index.get_loc(selected_month)
            if val == 'OK': styles[idx] = 'background-color: #D4EDDA'
            elif val == 'MISSING': styles[idx] = 'background-color: #F8D7DA'
            elif val == 'FAULTY': styles[idx] = 'background-color: #FFF3CD'
            return styles

        st.dataframe(df_equip.style.apply(style_inv, axis=1), use_container_width=True, hide_index=True)
