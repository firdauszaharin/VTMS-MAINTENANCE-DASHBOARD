import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz
import re
import os

# 1. PAGE CONFIGURATION
st.set_page_config(
    page_title="EDM VTMS Management Dashboard",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# --- SET MALAYSIA TIMEZONE ---
msia_tz = pytz.timezone('Asia/Kuala_Lumpur')
waktu_msia = datetime.now(msia_tz)

# 2. MODERN CORPORATE CSS (E-ZAKAT INSPIRED)
st.markdown("""
    <style>
    /* 1. Base Font & Background */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    
    .stApp {
        background-color: #f4f7f9;
        font-family: 'Inter', sans-serif;
    }

    /* 2. Sidebar Style */
    [data-testid="stSidebar"] {
        background-color: #002d5a !important; /* Biru Gelap Korporat */
        color: white !important;
    }
    [data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] h3 {
        color: white !important;
    }

    /* 3. Metric Cards (Zakat Style) */
    [data-testid="stMetric"] {
        background: white !important;
        padding: 25px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important;
        border-left: 6px solid #ffc107 !important; /* Jalur Emas */
    }
    
    /* Hover Effect for Metrics */
    [data-testid="stMetric"]:hover {
        box-shadow: 0 8px 20px rgba(0, 74, 153, 0.15) !important;
        transform: translateY(-2px);
        transition: all 0.3s ease;
    }

    /* 4. Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #e1e8ef;
        border-radius: 8px 8px 0px 0px;
        padding: 10px 25px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #004a99 !important;
        color: white !important;
    }

    /* 5. Header Hero Section */
    .hero-container {
        background: linear-gradient(135deg, #004a99 0%, #002d5a 100%);
        padding: 40px;
        border-radius: 20px;
        margin-bottom: 30px;
        color: white;
        border-bottom: 5px solid #ffc107;
    }

    /* Hide MainMenu & Footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background: transparent !important;}
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
    st.markdown("<h2 style='text-align:center; color:white;'>VTMS PORTAL</h2>", unsafe_allow_html=True)
    st.divider()
    st.markdown(f"🕒 **Sistem Aktif:** {waktu_msia.strftime('%d %b %Y | %H:%M')}")
    st.divider()
    
    st.markdown("### 🔍 TAPISAN DATA")
    if not df_raw.empty and 'Year' in df_raw.columns:
        year_list = sorted(df_raw['Year'].dropna().unique(), reverse=True)
        sel_year = st.selectbox("📅 Tahun:", ["Semua Tahun"] + [int(t) for t in year_list])
    else:
        sel_year = st.selectbox("📅 Tahun:", ["Semua Tahun"])
        
    search_report = st.text_input("🔎 Jenis Laporan:", placeholder="Contoh: MET...")
    search_staff = st.text_input("👤 Nama Kakitangan:")
    
    st.divider()
    st.link_button("📂 Google Drive Archive", "https://drive.google.com/drive/folders/...", use_container_width=True)

# 6. HERO HEADER (E-ZAKAT STYLE)
st.markdown(f"""
    <div class="hero-container">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h1 style="margin:0; font-size: 35px; font-weight: 800; letter-spacing: -1px;">
                    EDM VTMS LPJ/PTP
                </h1>
                <p style="margin:0; opacity: 0.9; font-size: 18px; font-weight: 300;">
                    Sistem Pengurusan Penyelenggaraan & Inventori Pusat Kawalan
                </p>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 40px; font-weight: 900; font-family: monospace;" id="live_clock">
                    {waktu_msia.strftime('%H:%M:%S')}
                </div>
                <div style="text-transform: uppercase; letter-spacing: 2px; font-size: 12px; color: #ffc107;">
                    Status: Sistem Stabil
                </div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# 7. MAIN CONTENT TABS
tab1, tab2 = st.tabs(["📋 REKOD PENYELENGGARAAN", "📦 STATUS INVENTORI"])

# --- TAB 1: REPORTS ---
with tab1:
    if not df_raw.empty:
        df = df_raw.copy()
        if sel_year != "Semua Tahun": df = df[df['Year'] == sel_year]
        if search_report: df = df[df['REPORT CHECKLIST'].str.contains(search_report, case=False, na=False)]
        if search_staff: df = df[df['Name'].str.contains(search_staff, case=False, na=False)]
        
        # Metrics Row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Jumlah Laporan", len(df))
        m2.metric("Disahkan ✅", len(df[df['STATUS'] == 'APPROVED']) if 'STATUS' in df.columns else 0)
        m3.metric("Ditolak ❌", len(df[df['STATUS'] == 'REJECTED']) if 'STATUS' in df.columns else 0)
        m4.metric("Dalam Proses ⏳", len(df[~df['STATUS'].isin(['APPROVED', 'REJECTED'])]) if 'STATUS' in df.columns else 0)

        st.markdown("### 📈 Analisis Status")
        col_p, col_b = st.columns(2)
        with col_p:
            fig_pie = px.pie(df, names='STATUS', hole=0.4, color_discrete_map={'APPROVED':'#2ecc71', 'REJECTED':'#e74c3c'})
            fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_pie, use_container_width=True)
        with col_b:
            fig_bar = px.histogram(df, x='REPORT CHECKLIST', color='STATUS', color_discrete_map={'APPROVED':'#2ecc71', 'REJECTED':'#e74c3c'})
            fig_bar.update_layout(margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_bar, use_container_width=True)

        st.divider()
        st.subheader("📑 Senarai Laporan Terperinci")
        
        if 'REPORT CHECKLIST' in df.columns:
            df.insert(0, 'ICON', df['REPORT CHECKLIST'].map(icon_map).fillna("https://cdn-icons-png.flaticon.com/512/2991/2991108.png"))

        st.dataframe(df, use_container_width=True, hide_index=True,
            column_config={
                "ICON": st.column_config.ImageColumn("Jenis"), 
                PDF_COL: st.column_config.LinkColumn("Fail PDF", display_text="BUKA LAPORAN 📄"),
                "Year": None
            })

# --- TAB 2: EQUIPMENT ---
with tab2:
    if not df_equip.empty:
        month_cols = [c for c in df_equip.columns if any(yr in c for yr in ["2025", "2026"])]
        selected_month = st.selectbox("📅 Pilih Bulan Laporan:", month_cols, index=len(month_cols)-1)
        
        status_series = df_equip[selected_month].astype(str).str.strip().str.upper()
        
        me1, me2, me3 = st.columns(3)
        # Custom Metric Styling via CSS above applied here
        me1.metric("Peralatan Baik", len(df_equip[status_series == 'OK']))
        me2.metric("Rosak (Faulty)", len(df_equip[status_series == 'FAULTY']))
        me3.metric("Hilang (Missing)", len(df_equip[status_series == 'MISSING']))

        st.markdown(f"### 📊 Ringkasan Keadaan Aset ({selected_month})")
        
        c1, c2 = st.columns(2)
        with c1:
            fig_donut = px.pie(df_equip, names=selected_month, hole=0.5, 
                               color_discrete_map={'OK':'#2ecc71','FAULTY':'#ffc107','MISSING':'#e74c3c'})
            st.plotly_chart(fig_donut, use_container_width=True)
        with c2:
            if 'Site' in df_equip.columns:
                st.plotly_chart(px.histogram(df_equip, x='Site', color=selected_month, barmode='group',
                                            color_discrete_map={'OK':'#2ecc71','FAULTY':'#ffc107','MISSING':'#e74c3c'}), use_container_width=True)

        st.divider()
        st.subheader("📦 Senarai Aset Inventori")
        search_eq = st.text_input("🔍 Cari Aset (S/N, Nama, Site):")
        
        df_eq_show = df_equip.copy()
        if search_eq:
            df_eq_show = df_eq_show[df_eq_show.astype(str).apply(lambda x: x.str.contains(search_eq, case=False)).any(axis=1)]
        
        st.dataframe(df_eq_show, use_container_width=True, hide_index=True)

# Footer Corporate
st.markdown(f"""
    <div style="text-align:center; padding: 20px; color: #666; font-size: 12px; border-top: 1px solid #ddd; margin-top: 50px;">
        © 2026 Lembaga Pelabuhan Johor (LPJ) | Dashboard Penyelenggaraan EDM VTMS<br>
        <i>Dikemaskini pada: {waktu_msia.strftime('%d/%m/%Y %H:%M:%S')}</i>
    </div>
""", unsafe_allow_html=True)
