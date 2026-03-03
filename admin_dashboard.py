import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz 
import os
import re

# 1. KONFIGURASI HALAMAN
st.set_page_config(
    page_title="VTMS Admin & Inventory Dashboard",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# --- SET ZON MASA MALAYSIA ---
msia_tz = pytz.timezone('Asia/Kuala_Lumpur')
waktu_msia = datetime.now(msia_tz)

# 2. CSS MODEN
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #2D3436; }
    [data-testid="stMetric"] { 
        background: #F8F9FA; padding: 15px; border-radius: 12px; 
        border-top: 4px solid #0984E3; box-shadow: 0 2px 10px rgba(0,0,0,0.05); 
    }
    .pdf-view-container { border: 2px solid #0984E3; border-radius: 12px; overflow: hidden; margin-top: 10px; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# 3. PAUTAN DATA (Gantikan URL CSV anda di sini)
# URL Laporan Harian
SHEET_REPORT_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSEHHkyeSHjGBSi3wp-T5eE0vCZtgZ2mpWmUktMZiUHqfvb9Aow1r8OK_ZTq9wCQrxg62xTUX2DpgS_/pub?gid=296214979&single=true&output=csv"
# URL Status Equipment (Pastikan anda 'Publish to Web' tab Status Equipment sebagai CSV)
SHEET_EQUIP_URL = "https://docs.google.com/spreadsheets/d/1QeQgEA--b1TX3Q8LPgmog7XP97Tg0dHSr3gIAAGXV4g/edit?usp=sharing" 

PDF_COL = "UPLOAD REPORT" 

# 4. FUNGSI LOAD DATA
@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url)
        data.columns = data.columns.str.strip()
        if 'Timestamp' in data.columns:
            data['Timestamp'] = pd.to_datetime(data['Timestamp'])
            data['Tahun'] = data['Timestamp'].dt.year
        return data
    except Exception as e:
        return pd.DataFrame()

df_raw = load_data(SHEET_REPORT_URL)
df_equip = load_data(SHEET_EQUIP_URL)

# --- MAP ICON UNTUK REPORT ---
icon_map = {
    "MET REPORT": "https://cdn-icons-png.flaticon.com/512/1146/1146869.png",
    "OPERATOR WORKSTATION": "https://cdn-icons-png.flaticon.com/512/689/689382.png",
    "WALL DISPLAY REPORT": "https://cdn-icons-png.flaticon.com/512/1035/1035688.png",
    "VHF PTP FLOOR 8": "https://cdn-icons-png.flaticon.com/512/3126/3126505.png",
    "SERVER ROOM REPORT (PTP/LPJ)": "https://cdn-icons-png.flaticon.com/512/2333/2333241.png"
}

# Initialize Session State
if "selected_row_idx" not in st.session_state:
    st.session_state.selected_row_idx = None

# 5. SIDEBAR
with st.sidebar:
    st.markdown("## 🛡️ VTMS ADMIN")
    st.image("https://cdn-icons-png.flaticon.com/512/1063/1063376.png", width=70)
    st.divider()
    
    st.markdown("### 🔍 TAPISAN")
    tahun_list = sorted(df_raw['Tahun'].dropna().unique(), reverse=True) if not df_raw.empty else []
    sel_tahun = st.selectbox("📅 Pilih Tahun:", ["Semua Tahun"] + [int(t) for t in tahun_list])
    search_report = st.text_input("🔎 Jenis Report:", placeholder="MET, SERVER...")
    search_staff = st.text_input("👤 Nama Staff:")
    
    st.divider()
    folder_url = "https://drive.google.com/drive/folders/1lG9eKZ69hpT6q-aqXpNxyd0HMcXdr3A4rAjUaXLCpDpOPffFzG0XK-MGBLaGHcBMcyqWjyLy"
    st.link_button("📂 Buka Folder Drive", folder_url, use_container_width=True)

# 6. MAIN CONTENT
st.title("📊 VTMS LPJ/PTP Management Dashboard")

# TAB SYSTEM
tab1, tab2 = st.tabs(["📝 Laporan Harian", "⚙️ Status Equipment"])

# --- TAB 1: LAPORAN ---
with tab1:
    if not df_raw.empty:
        df = df_raw.copy()
        if sel_tahun != "Semua Tahun": df = df[df['Tahun'] == sel_tahun]
        if search_report: df = df[df['REPORT CHECKLIST'].str.contains(search_report, case=False, na=False)]
        if search_staff: df = df[df['Name'].str.contains(search_staff, case=False, na=False)]
        
        display_df = df.sort_values(by="Timestamp", ascending=False).reset_index(drop=True)
        # Masukkan Icon
        display_df.insert(0, 'ICON', display_df['REPORT CHECKLIST'].map(icon_map).fillna("https://cdn-icons-png.flaticon.com/512/2991/2991108.png"))

        # Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Jumlah Laporan", len(display_df))
        m2.metric("Approved ✅", len(display_df[display_df['STATUS'] == 'APPROVED']) if 'STATUS' in display_df.columns else 0)
        m3.metric("Rejected ❌", len(display_df[display_df['STATUS'] == 'REJECTED']) if 'STATUS' in display_df.columns else 0)
        m4.metric("Jumlah Staff", display_df['Name'].nunique() if 'Name' in display_df.columns else 0)

        # Styling Status
        def style_status(val):
            if val == 'REJECTED': return 'color: red; font-weight: bold;'
            if val == 'APPROVED': return 'color: green; font-weight: bold;'
            return ''

        st.subheader("📋 Rekod Laporan")
        event = st.dataframe(
            display_df.style.map(style_status, subset=['STATUS']),
            use_container_width=True,
            column_config={
                "ICON": st.column_config.ImageColumn("Type", width="small"),
                PDF_COL: st.column_config.LinkColumn("Fail", display_text="BUKA PDF 📄")
            },
            on_select="rerun",
            selection_mode="single-row",
            hide_index=True
        )

        if len(event.selection.rows) > 0:
            st.session_state.selected_row_idx = event.selection.rows[0]

        # Preview PDF Logik
        if st.session_state.selected_row_idx is not None:
            idx = st.session_state.selected_row_idx
            if idx < len(display_df):
                row = display_df.iloc[idx]
                link = row.get(PDF_COL, "")
                st.markdown("---")
                c1, c2 = st.columns([0.9, 0.1])
                c1.subheader(f"📄 Preview: {row['REPORT CHECKLIST']}")
                if c2.button("❌ Tutup"):
                    st.session_state.selected_row_idx = None
                    st.rerun()
                
                if isinstance(link, str) and "drive.google.com" in link:
                    match = re.search(r'[-\w]{25,}', link)
                    if match:
                        file_id = match.group()
                        st.markdown(f'<div class="pdf-view-container"><iframe src="https://drive.google.com/file/d/{file_id}/preview" width="100%" height="800px"></iframe></div>', unsafe_allow_html=True)
                else: st.warning("Pautan PDF tidak sah.")

# --- TAB 2: STATUS EQUIPMENT ---
with tab2:
    if not df_equip.empty:
        st.subheader("⚙️ Inventory & Status Semasa Peralatan")
        
        # Contoh kolum status (Tukar "SEPT 2025" ikut kolum dalam sheet anda)
        status_col = "SEPT 2025" 
        
        # Metrics Equipment
        e1, e2, e3 = st.columns(3)
        if status_col in df_equip.columns:
            e1.metric("Equipment OK", len(df_equip[df_equip[status_col] == 'OK']))
            e2.metric("Faulty ⚠️", len(df_equip[df_equip[status_col] == 'FAULTY']))
            e3.metric("Missing ❌", len(df_equip[df_equip[status_col] == 'MISSING']))

        # Filter Equipment
        search_eq = st.text_input("🔍 Cari Alat (SN, Nama, IP):", placeholder="Contoh: SGH...")
        df_eq_show = df_equip.copy()
        if search_eq:
            df_eq_show = df_eq_show[df_eq_show.astype(str).apply(lambda x: x.str.contains(search_eq, case=False)).any(axis=1)]

        # Styling Row Equipment
        def style_equip(val):
            if val == 'OK': return 'background-color: #D4EDDA; color: #155724'
            if val == 'FAULTY': return 'background-color: #FFF3CD; color: #856404'
            if val == 'MISSING': return 'background-color: #F8D7DA; color: #721C24'
            return ''

        st.dataframe(
            df_eq_show.style.applymap(style_equip, subset=[status_col] if status_col in df_eq_show.columns else []),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Sila masukkan URL CSV 'Status Equipment' yang sah.")

# GRAF ANALITIK DI BAWAH
st.divider()
st.subheader("📊 Analitik Ringkas")
c_pie, c_bar = st.columns(2)
with c_pie:
    if not df_raw.empty:
        fig1 = px.pie(df_raw, names='STATUS', title='Statistik Kelulusan Laporan', hole=0.4)
        st.plotly_chart(fig1, use_container_width=True)
with c_bar:
    if not df_raw.empty:
        fig2 = px.histogram(df_raw, x='REPORT CHECKLIST', color='STATUS', title='Kekerapan Laporan mengikut Jenis')
        st.plotly_chart(fig2, use_container_width=True)


