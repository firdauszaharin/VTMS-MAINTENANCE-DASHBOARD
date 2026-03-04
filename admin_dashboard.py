import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz
import re

# 1. PAGE CONFIGURATION
st.set_page_config(
    page_title="EDM VTMS Management Dashboard",
    layout="wide",
    page_icon="📊"
)

# --- SET MALAYSIA TIMEZONE ---
msia_tz = pytz.timezone('Asia/Kuala_Lumpur')
waktu_msia = datetime.now(msia_tz)

# 2. MODERN CORPORATE CSS
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #002d5a !important; color: white !important; }
    [data-testid="stSidebar"] .stMarkdown p { color: white !important; }
    
    /* Metric Cards */
    [data-testid="stMetric"] {
        background: white !important;
        padding: 25px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important;
        border-left: 6px solid #ffc107 !important;
    }

    .hero-container {
        background: linear-gradient(135deg, #004a99 0%, #002d5a 100%);
        padding: 40px; border-radius: 20px; margin-bottom: 30px; color: white;
        border-bottom: 5px solid #ffc107;
    }
    </style>
""", unsafe_allow_html=True)

# 3. DATA LINKS
SHEET_REPORT_URL = "https://docs.google.com/spreadsheets/d/1WB76n71wxMT3i5ZCaoCBIyb888il-qBydY8OEgC81Q8/export?format=csv&gid=296214979"
SHEET_EQUIP_URL = "https://docs.google.com/spreadsheets/d/1QeQgEA--b1TX3Q8LPgmog7XP97Tg0dHSr3gIAAGXV4g/export?format=csv&gid=416421947"
PDF_COL = "UPLOAD REPORT" 

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

# --- ICON MAP ---
icon_map = {
    "MET REPORT": "https://cdn-icons-png.flaticon.com/512/1146/1146869.png",
    "OPERATOR WORKSTATION": "https://cdn-icons-png.flaticon.com/512/689/689382.png",
    "WALL DISPLAY REPORT": "https://cdn-icons-png.flaticon.com/512/1035/1035688.png",
    "VHF PTP FLOOR 8": "https://cdn-icons-png.flaticon.com/512/3126/3126505.png",
    "SERVER ROOM REPORT (PTP/LPJ)": "https://cdn-icons-png.flaticon.com/512/2333/2333241.png"
}

# 4. SIDEBAR (LOGO FIX)
with st.sidebar:
    # Guna URL Logo jika file lokal 'logo.png' tiada
    logo_url = "https://www.zakatselangor.com.my/wp-content/uploads/2017/06/logo-lzt-2.png" 
    st.image(logo_url, width=180) # Pastikan logo nampak
    
    st.markdown("---")
    st.markdown(f"🕒 **Last Sync:** {waktu_msia.strftime('%H:%M:%S')}")
    st.markdown("---")
    
    sel_year = st.selectbox("📅 Pilih Tahun:", ["Semua Tahun"] + sorted(list(df_raw['Year'].dropna().unique()), reverse=True)) if not df_raw.empty else "Semua Tahun"
    search_report = st.text_input("🔎 Cari Laporan:")

# 5. HERO SECTION
st.markdown(f"""
    <div class="hero-container">
        <h1 style="margin:0;">EDM VTMS MANAGEMENT</h1>
        <p style="margin:0; opacity:0.8;">Sistem Inventori & Penyelenggaraan LPJ/PTP</p>
    </div>
""", unsafe_allow_html=True)

# 6. TABS
tab1, tab2 = st.tabs(["📋 LAPORAN", "📦 INVENTORI"])

with tab1:
    if not df_raw.empty:
        df = df_raw.copy()
        
        # --- FIX WARNA STATUS (HIGHLIGHT FUNCTION) ---
        def style_status(val):
            color = ''
            if str(val).upper() == 'REJECTED':
                color = 'background-color: #ffcccc; color: #990000; font-weight: bold;'
            elif str(val).upper() == 'APPROVED':
                color = 'background-color: #d4edda; color: #155724;'
            elif str(val).upper() == 'PENDING':
                color = 'background-color: #fff3cd; color: #856404;'
            return color

        # Filter Data
        if sel_year != "Semua Tahun": df = df[df['Year'] == sel_year]
        if search_report: df = df[df['REPORT CHECKLIST'].str.contains(search_report, case=False, na=False)]

        # Map Icon
        if 'REPORT CHECKLIST' in df.columns:
            df.insert(0, 'ICON', df['REPORT CHECKLIST'].map(icon_map).fillna("https://cdn-icons-png.flaticon.com/512/2991/2991108.png"))

        # Paparkan Dataframe dengan Styling
        st.subheader("Senarai Rekod Penyelenggaraan")
        
        # Guna .style.applymap untuk mewarnakan sel mengikut status
        styled_df = df.style.applymap(style_status, subset=['STATUS']) if 'STATUS' in df.columns else df

        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "ICON": st.column_config.ImageColumn("Jenis"),
                PDF_COL: st.column_config.LinkColumn("Report File", display_text="OPEN PDF 📄")
            }
        )

with tab2:
    st.write("Bahagian Inventori (Sila rujuk kod sebelum ini untuk visual)")
