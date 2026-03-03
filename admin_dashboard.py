import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz 
import os
import re

# 1. KONFIGURASI HALAMAN
st.set_page_config(
    page_title="VTMS Admin Dashboard",
    layout="wide",
    page_icon="📊"
)

# --- SET ZON MASA MALAYSIA ---
msia_tz = pytz.timezone('Asia/Kuala_Lumpur')
waktu_msia = datetime.now(msia_tz)

# 2. CSS MODEN (CLEAN & PROFESSIONAL)
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #2D3436; }
    h1 { color: #0984E3 !important; font-family: 'Segoe UI', sans-serif; font-weight: 800; }
    /* Dashboard Cards */
    div[data-testid="stMetric"] { 
        background: #F8F9FA; padding: 20px; border-radius: 12px; 
        border-top: 4px solid #0984E3; box-shadow: 0 2px 10px rgba(0,0,0,0.05); 
    }
    /* PDF Container */
    .pdf-view-container { 
        border: 2px solid #0984E3; border-radius: 12px; overflow: hidden; 
        margin-top: 10px; background-color: #f1f2f6; 
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 4. DATA LOADING ---
# Pautan Google Sheets CSV
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSEHHkyeSHjGBSi3wp-T5eE0vCZtgZ2mpWmUktMZiUHqfvb9Aow1r8OK_ZTq9wCQrxg62xTUX2DpgS_/pub?gid=296214979&single=true&output=csv"
PDF_COL = "UPLOAD REPORT" 

@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url)
        # Bersihkan nama kolum dari sebarang ruang kosong (whitespace)
        data.columns = data.columns.str.strip()
        data['Timestamp'] = pd.to_datetime(data['Timestamp'])
        data['Tahun'] = data['Timestamp'].dt.year
        return data
    except Exception as e:
        st.error(f"Gagal memuatkan data dari Google Sheets: {e}")
        return pd.DataFrame()

df_raw = load_data(SHEET_URL)

if df_raw.empty:
    st.warning("⚠️ Menunggu data dari Google Sheets atau pautan tidak sah.")
    st.stop()

# Initialize Session States untuk simpan pilihan baris
if "selected_row_idx" not in st.session_state:
    st.session_state.selected_row_idx = None
if "prev_filter_state" not in st.session_state:
    st.session_state.prev_filter_state = ""

# --- 5. SIDEBAR NAVIGATION & FILTER ---
with st.sidebar:
    st.markdown("## 🛡️ VTMS ADMIN")
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    
    st.divider()

    # --- BUTANG FOLDER GOOGLE DRIVE ---
    st.markdown("### 📂 AKSES FAIL")
    folder_url = "https://drive.google.com/drive/folders/1lG9eKZ69hpT6q-aqXpNxyd0HMcXdr3A4rAjUaXLCpDpOPffFzG0XK-MGBLaGHcBMcyqWjyLy?usp=drive_link"
    st.link_button("📁 Buka Folder Laporan (Drive)", folder_url, use_container_width=True)
    
    st.divider()
    
    st.markdown("### 🔍 TAPISAN DATA")
    
    # Filter Tahun
    tahun_list = sorted(df_raw['Tahun'].dropna().unique(), reverse=True)
    sel_tahun = st.selectbox("📅 Pilih Tahun:", ["Semua Tahun"] + [int(t) for t in tahun_list])
    
    # Carian Report & Staff
    search_report = st.text_input("🔎 Cari Jenis Report:", placeholder="MET, SERVER, etc...")
    search_staff = st.text_input("👤 Cari Nama Staff:", placeholder="Nama staff...")
    
    # Logik Reset Preview jika filter berubah
    current_filter = f"{sel_tahun}{search_report}{search_staff}"
    if current_filter != st.session_state.prev_filter_state:
        st.session_state.selected_row_idx = None
        st.session_state.prev_filter_state = current_filter

    st.divider()
    # Butang Download CSV di Sidebar
    st.markdown("### 📥 EKSPORT")
    csv_export = df_raw.to_csv(index=False).encode('utf-8')
    st.download_button("Download All Data (CSV)", csv_export, "VTMS_Data_Full.csv", "text/csv", use_container_width=True)

# --- LOGIK PENAPISAN DATA ---
df = df_raw.copy()
if sel_tahun != "Semua Tahun":
    df = df[df['Tahun'] == sel_tahun]
if search_report:
    df = df[df['REPORT CHECKLIST'].str.contains(search_report, case=False, na=False)]
if search_staff:
    df = df[df['Name'].str.contains(search_staff, case=False, na=False)]

# Urutkan mengikut masa terbaru (Timestamp)
display_df = df.sort_values(by="Timestamp", ascending=False).reset_index(drop=True)

# --- 6. MAIN DASHBOARD ---
st.title("📊 VTMS Management Dashboard")
st.write(f"Paparan Data: **{sel_tahun}** | Masa Sistem: **{waktu_msia.strftime('%d/%m/%Y %H:%M')}**")

st.divider()

# Metrics Row
m1, m2, m3, m4 = st.columns(4)
m1.metric("Jumlah Laporan", len(display_df))
m2.metric("Approved ✅", len(display_df[display_df['STATUS'] == 'APPROVED']) if 'STATUS' in display_df.columns else 0)
m3.metric("Rejected ❌", len(display_df[display_df['STATUS'] == 'REJECTED']) if 'STATUS' in display_df.columns else 0)
m4.metric("Jumlah Staff", display_df['Name'].nunique() if 'Name' in display_df.columns else 0)

# --- 7. JADUAL INTERAKTIF ---
st.subheader("📋 Rekod Laporan (Klik baris untuk Preview)")

column_config = {}
if PDF_COL in display_df.columns:
    column_config[PDF_COL] = st.column_config.LinkColumn(
        "Fail Report",
        display_text="BUKA PDF 📄"
    )

# Render Jadual
event = st.dataframe(
    display_df,
    use_container_width=True,
    height=400,
    column_config=column_config,
    on_select="rerun",
    selection_mode="single-row",
    hide_index=True
)

# Ambil index baris yang dipilih oleh user
if len(event.selection.rows) > 0:
    st.session_state.selected_row_idx = event.selection.rows[0]

# --- 8. PDF PREVIEW LOGIK ---
if st.session_state.selected_row_idx is not None:
    idx = st.session_state.selected_row_idx
    if idx < len(display_df):
        row = display_df.iloc[idx]
        link = row.get(PDF_COL, "")
        
        st.markdown("---")
        c_title, c_close = st.columns([0.9, 0.1])
        with c_title:
            st.subheader(f"📄 Preview Fail: {row.get('REPORT CHECKLIST', 'Laporan')}")
        with c_close:
            if st.button("❌ Tutup"):
                st.session_state.selected_row_idx = None
                st.rerun()

        if isinstance(link, str) and "drive.google.com" in link:
            # Ekstrak ID File Google Drive secara selamat
            match = re.search(r'[-\w]{25,}', link)
            if match:
                file_id = match.group()
                preview_url = f"https://drive.google.com/file/d/{file_id}/preview"
                
                # Paparan Iframe PDF
                st.markdown(f'''
                    <div class="pdf-view-container">
                        <iframe src="{preview_url}" width="100%" height="800px" allow="autoplay"></iframe>
                    </div>
                ''', unsafe_allow_html=True)
                
                # Butang Buka Original
                st.link_button("📥 Muat Turun Fail Original", link, use_container_width=True)
            else:
                st.error("Pautan fail tidak sah atau bukan pautan Google Drive.")
        else:
            st.warning("Tiada pautan fail PDF ditemui untuk rekod ini.")

# --- 9. ANALITIK RINGKAS (GRAF) ---
st.divider
