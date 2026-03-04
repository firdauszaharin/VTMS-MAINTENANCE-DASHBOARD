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

# 2. MODERN CORPORATE CSS (E-ZAKAT STYLE)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    
    .stApp {
        background-color: #f4f7f9;
        font-family: 'Inter', sans-serif;
    }

    /* Sidebar Background & Text */
    [data-testid="stSidebar"] {
        background-color: #002d5a !important;
    }
    [data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] h3 {
        color: white !important;
    }

    /* Metric Cards Styling */
    [data-testid="stMetric"] {
        background: white !important;
        padding: 25px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important;
        border-left: 6px solid #ffc107 !important;
    }

    /* Hero Header */
    .hero-container {
        background: linear-gradient(135deg, #004a99 0%, #002d5a 100%);
        padding: 40px;
        border-radius: 20px;
        margin-bottom: 30px;
        color: white;
        border-bottom: 5px solid #ffc107;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
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

    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background: transparent !important;}
    </style>
""", unsafe_allow_html=True)

# 3. DATA LINKS
SHEET_REPORT_URL = "https://docs.google.com/spreadsheets/d/1WB76n71wxMT3i5ZCaoCBIyb888il-qBydY8OEgC81Q8/export?format=csv&gid=296214979"
SHEET_EQUIP_URL = "https://docs.google.com/spreadsheets/d/1QeQgEA--b1TX3Q8LPgmog7XP97Tg0dHSr3gIAAGXV4g/export?format=csv&gid=416421947"
PDF_COL = "UPLOAD REPORT" 

# 4. LOAD DATA FUNCTION
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

# 5. SIDEBAR (LOGO & FILTERS)
with st.sidebar:
    # Logo Fix: Guna URL jika file lokal tiada
    st.image("https://www.zakatselangor.com.my/wp-content/uploads/2017/06/logo-lzt-2.png", width=180)
    st.markdown("<h3 style='text-align:center;'>VTMS PORTAL</h3>", unsafe_allow_html=True)
    st.divider()
    
    st.markdown(f"🕒 **Sistem Aktif:** {waktu_msia.strftime('%H:%M:%S')}")
    st.divider()
    
    st.markdown("### 🔍 GLOBAL FILTERS")
    if not df_raw.empty and 'Year' in df_raw.columns:
        year_list = sorted(df_raw['Year'].dropna().unique(), reverse=True)
        sel_year = st.selectbox("📅 Pilih Tahun:", ["Semua Tahun"] + [int(t) for t in year_list])
    else:
        sel_year = "Semua Tahun"
        
    search_report = st.text_input("🔎 Cari Laporan:", placeholder="Contoh: MET...")
    search_staff = st.text_input("👤 Nama Kakitangan:")
    
    st.divider()
    st.link_button("📂 Open Drive Folder", "https://drive.google.com/drive/folders/...", use_container_width=True)

# 6. HERO HEADER
st.markdown(f"""
    <div class="hero-container">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h1 style="margin:0; font-size: 35px; font-weight: 800;">EDM VTMS LPJ/PTP</h1>
                <p style="margin:0; opacity: 0.9; font-size: 18px;">Sistem Pengurusan Penyelenggaraan Dashboard</p>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 40px; font-weight: 900; font-family: monospace;">{waktu_msia.strftime('%H:%M')}</div>
                <div style="color: #ffc107; font-size: 12px; letter-spacing: 2px;">STATUS: ONLINE</div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# 7. MAIN TABS
tab1, tab2 = st.tabs(["📋 LAPORAN", "📦 INVENTORI"])

# --- TAB 1: MAINTENANCE REPORTS ---
with tab1:
    if not df_raw.empty:
        df = df_raw.copy()
        
        # Function Warna Status
        def style_status(val):
            val_str = str(val).upper()
            if val_str == 'REJECTED': return 'background-color: #F8D7DA; color: #721C24; font-weight: bold;'
            if val_str == 'APPROVED': return 'background-color: #D4EDDA; color: #155724;'
            if val_str == 'PENDING': return 'background-color: #FFF3CD; color: #856404;'
            return ''

        # Apply Filters
        if sel_year != "Semua Tahun": df = df[df['Year'] == sel_year]
        if search_report: df = df[df['REPORT CHECKLIST'].str.contains(search_report, case=False, na=False)]
        if search_staff: df = df[df['Name'].str.contains(search_staff, case=False, na=False)]
        
        # Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Laporan", len(df))
        m2.metric("Disahkan ✅", len(df[df['STATUS'] == 'APPROVED']) if 'STATUS' in df.columns else 0)
        m3.metric("Ditolak ❌", len(df[df['STATUS'] == 'REJECTED']) if 'STATUS' in df.columns else 0)
        m4.metric("Pending ⏳", len(df[~df['STATUS'].isin(['APPROVED', 'REJECTED'])]) if 'STATUS' in df.columns else 0)

        # Visuals
        st.markdown("### 📊 Status Overview")
        c_p, c_b = st.columns(2)
        with c_p:
            st.plotly_chart(px.pie(df, names='STATUS', hole=0.4, color_discrete_map={'APPROVED':'#2ecc71', 'REJECTED':'#e74c3c'}), use_container_width=True)
        with c_b:
            st.plotly_chart(px.histogram(df, x='REPORT CHECKLIST', color='STATUS', color_discrete_map={'APPROVED':'#2ecc71', 'REJECTED':'#e74c3c'}), use_container_width=True)

        st.divider()
        st.subheader("📋 Rekod Penyelenggaraan")
        
        # Insert Icons
        if 'REPORT CHECKLIST' in df.columns:
            df.insert(0, 'ICON', df['REPORT CHECKLIST'].map(icon_map).fillna("https://cdn-icons-png.flaticon.com/512/2991/2991108.png"))

        # Render Table with Status Colors
        styled_df = df.style.applymap(style_status, subset=['STATUS']) if 'STATUS' in df.columns else df
        
        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "ICON": st.column_config.ImageColumn("Jenis"),
                PDF_COL: st.column_config.LinkColumn("Report File", display_text="OPEN PDF 📄"),
                "Year": None
            }
        )

# --- TAB 2: EQUIPMENT STATUS ---
with tab2:
    if not df_equip.empty:
        month_cols = [c for c in df_equip.columns if any(yr in c for yr in ["2025", "2026"])]
        selected_month = st.selectbox("📅 Pilih Bulan Inventori:", month_cols, index=len(month_cols)-1)
        
        # Status Color Function for Inventory
        def style_inventory(val):
            val_str = str(val).upper()
            if val_str == 'OK': return 'background-color: #D4EDDA;'
            if val_str == 'FAULTY': return 'background-color: #FFF3CD;'
            if val_str == 'MISSING': return 'background-color: #F8D7DA;'
            return ''

        status_series = df_equip[selected_month].astype(str).str.strip().str.upper()
        
        me1, me2, me3 = st.columns(3)
        me1.metric("Peralatan OK", len(df_equip[status_series == 'OK']))
        me2.metric("Rosak (Faulty)", len(df_equip[status_series == 'FAULTY']))
        me3.metric("Hilang (Missing)", len(df_equip[status_series == 'MISSING']))

        # Inventory Table
        st.divider()
        st.subheader("📦 Senarai Aset Terperinci")
        search_eq = st.text_input("🔍 Cari SN atau Nama Asset:")
        
        df_eq_show = df_equip.copy()
        if search_eq:
            df_eq_show = df_eq_show[df_eq_show.astype(str).apply(lambda x: x.str.contains(search_eq, case=False)).any(axis=1)]
        
        st.dataframe(
            df_eq_show.style.applymap(style_inventory, subset=[selected_month]),
            use_container_width=True,
            hide_index=True
        )

# Footer
st.markdown(f"""
    <div style="text-align:center; padding: 20px; color: #666; font-size: 11px; margin-top: 50px; border-top: 1px solid #ddd;">
        © 2026 Maintenance Dashboard | Inspired by Zakat Selangor UI
    </div>
""", unsafe_allow_html=True)
