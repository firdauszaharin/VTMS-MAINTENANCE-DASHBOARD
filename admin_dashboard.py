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

# 2. MODERN CSS (UI MODEN 2026 - GLASSMORPHISM)
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
        border-left: 5px solid #0984E3 !important;
    }
    .hero-section {
        background: linear-gradient(90deg, #0984E3, #6c5ce7);
        padding: 30px;
        border-radius: 20px;
        color: white;
        margin-bottom: 25px;
    }
    #MainMenu {visibility: hidden;}
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
        return data
    except:
        return pd.DataFrame()

df_raw = load_data(SHEET_REPORT_URL)
df_equip = load_data(SHEET_EQUIP_URL)

icon_map = {
    "MET REPORT": "https://cdn-icons-png.flaticon.com/512/1146/1146869.png",
    "OPERATOR WORKSTATION": "https://cdn-icons-png.flaticon.com/512/689/689382.png",
    "WALL DISPLAY REPORT": "https://cdn-icons-png.flaticon.com/512/1035/1035688.png",
    "VHF PTP FLOOR 8": "https://cdn-icons-png.flaticon.com/512/3126/3126505.png",
    "SERVER ROOM REPORT (PTP/LPJ)": "https://cdn-icons-png.flaticon.com/512/2333/2333241.png"
}

# 5. SIDEBAR
with st.sidebar:
    st.image("https://www.zakatselangor.com.my/wp-content/uploads/2017/06/logo-lzt-2.png", width=150)
    st.markdown(f"🕒 **Last Sync:** {waktu_msia.strftime('%H:%M:%S')}")
    st.divider()
    
    if not df_raw.empty:
        year_list = sorted(df_raw['Year'].dropna().unique(), reverse=True)
        sel_year = st.selectbox("📅 Select Year:", ["All Years"] + [int(t) for t in year_list])
    else:
        sel_year = "All Years"
        
    search_report = st.text_input("🔎 Report Type:")
    st.divider()
    st.link_button("📂 Open Drive Folder", "https://drive.google.com/drive/folders/...")

# 6. HERO SECTION
st.markdown(f"""
    <div class="hero-section">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h1 style="margin:0; font-size:30px;">EDM VTMS LPJ/PTP</h1>
                <p style="margin:0; opacity:0.8;">Admin & Inventory Management System</p>
            </div>
            <div style="text-align:right;">
                <h2 style="margin:0;">{waktu_msia.strftime('%H:%M')}</h2>
                <p style="margin:0; font-size:12px;">MALAYSIA TIME</p>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# 7. MAIN TABS
tab1, tab2 = st.tabs(["📝 Maintenance Reports", "⚙️ Equipment Status"])

# --- TAB 1: REPORTS ---
with tab1:
    if not df_raw.empty:
        df = df_raw.copy()
        if sel_year != "All Years": df = df[df['Year'] == sel_year]
        if search_report: df = df[df['REPORT CHECKLIST'].str.contains(search_report, case=False, na=False)]
        
        # Metrics Row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Reports", len(df))
        m2.metric("Approved ✅", len(df[df['STATUS'] == 'APPROVED']) if 'STATUS' in df.columns else 0)
        m3.metric("Rejected ❌", len(df[df['STATUS'] == 'REJECTED']) if 'STATUS' in df.columns else 0, delta_color="inverse")
        m4.metric("Pending ⏳", len(df[~df['STATUS'].isin(['APPROVED', 'REJECTED'])]) if 'STATUS' in df.columns else 0)

        # GRAF (TADAK HILANG DAH)
        st.markdown("### 🎯 Performance Overview")
        g1, g2 = st.columns(2)
        with g1:
            fig1 = px.pie(df, names='STATUS', title='Approval Status', hole=0.4, 
                          color_discrete_map={'APPROVED':'#2ecc71', 'REJECTED':'#e74c3c', 'PENDING':'#f1c40f'})
            st.plotly_chart(fig1, use_container_width=True)
        with g2:
            fig2 = px.histogram(df, x='REPORT CHECKLIST', color='STATUS', barmode='group', title='Reports by Category',
                                color_discrete_map={'APPROVED':'#2ecc71', 'REJECTED':'#e74c3c'})
            st.plotly_chart(fig2, use_container_width=True)

        # TABLE WITH RED COLOR FOR REJECTED
        def color_status(val):
            if str(val).upper() == 'REJECTED': return 'background-color: #ffcccc; color: #990000; font-weight: bold;'
            if str(val).upper() == 'APPROVED': return 'background-color: #d4edda; color: #155724;'
            return ''

        if 'REPORT CHECKLIST' in df.columns:
            df.insert(0, 'ICON', df['REPORT CHECKLIST'].map(icon_map).fillna("https://cdn-icons-png.flaticon.com/512/2991/2991108.png"))

        st.subheader("📋 Submitted Reports Record")
        st.dataframe(
            df.style.applymap(color_status, subset=['STATUS']) if 'STATUS' in df.columns else df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "ICON": st.column_config.ImageColumn("Type"),
                PDF_COL: st.column_config.LinkColumn("Report File", display_text="OPEN PDF 📄")
            }
        )

# --- TAB 2: EQUIPMENT ---
with tab2:
    if not df_equip.empty:
        month_cols = [c for c in df_equip.columns if any(yr in c for yr in ["2025", "2026"])]
        selected_month = st.selectbox("📅 Select Month:", month_cols, index=len(month_cols)-1)
        
        status_series = df_equip[selected_month].astype(str).str.strip().str.upper()
        
        me1, me2, me3 = st.columns(3)
        me1.metric("Equipment OK", len(df_equip[status_series == 'OK']))
        me2.metric("Faulty ⚠️", len(df_equip[status_series == 'FAULTY']))
        me3.metric("Missing ❌", len(df_equip[status_series == 'MISSING']))

        # GRAF INVENTORI
        st.markdown(f"### 📊 Inventory Overview ({selected_month})")
        ig1, ig2 = st.columns(2)
        with ig1:
            st.plotly_chart(px.pie(df_equip, names=selected_month, hole=0.5, title='Condition Pie',
                                   color_discrete_map={'OK':'#2ecc71','FAULTY':'#f1c40f','MISSING':'#e74c3c'}), use_container_width=True)
        with ig2:
            if 'Site' in df_equip.columns:
                st.plotly_chart(px.histogram(df_equip, x='Site', color=selected_month, barmode='group', title='Status by Site'), use_container_width=True)

        # TABLE INVENTORI DENGAN WARNA
        def color_inv(val):
            if val == 'OK': return 'background-color: #d4edda;'
            if val == 'MISSING': return 'background-color: #ffcccc;'
            if val == 'FAULTY': return 'background-color: #fff3cd;'
            return ''

        st.dataframe(df_equip.style.applymap(color_inv, subset=[selected_month]), use_container_width=True, hide_index=True)
