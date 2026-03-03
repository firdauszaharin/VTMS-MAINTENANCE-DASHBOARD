import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz
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

# 3. PAUTAN DATA (TELAH DIBAIKI KE FORMAT EXPORT CSV)
# Laporan Harian (GID 296214979)
SHEET_REPORT_URL = "https://docs.google.com/spreadsheets/d/1WB76n71wxMT3i5ZCaoCBIyb888il-qBydY8OEgC81Q8/export?format=csv&gid=296214979"
# Status Equipment (GID 416421947)
SHEET_EQUIP_URL = "https://docs.google.com/spreadsheets/d/1QeQgEA--b1TX3Q8LPgmog7XP97Tg0dHSr3gIAAGXV4g/export?format=csv&gid=416421947"

PDF_COL = "UPLOAD REPORT" 

# 4. FUNGSI LOAD DATA (DIPERTINGKATKAN)
@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url, on_bad_lines='skip')
        data.columns = data.columns.str.strip() # Buang space pada tajuk
        
        # Logik kesan kolum masa secara automatik (elakkan KeyError 'Tahun')
        time_col = next((c for c in data.columns if any(x in c.lower() for x in ['timestamp', 'time', 'date', 'tarikh'])), None)
        
        if time_col:
            data[time_col] = pd.to_datetime(data[time_col], errors='coerce')
            data['Tahun'] = data[time_col].dt.year
        else:
            data['Tahun'] = None # Cipta kolum kosong jika tiada kolum masa
            
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

if "selected_row_idx" not in st.session_state:
    st.session_state.selected_row_idx = None

# 5. SIDEBAR
with st.sidebar:
    st.markdown("## 🛡️ VTMS ADMIN")
    st.image("https://cdn-icons-png.flaticon.com/512/1063/1063376.png", width=70)
    st.divider()
    
    st.markdown("### 🔍 TAPISAN")
    # Semakan selamat untuk df_raw
    if not df_raw.empty and 'Tahun' in df_raw.columns:
        tahun_list = sorted(df_raw['Tahun'].dropna().unique(), reverse=True)
        sel_tahun = st.selectbox("📅 Pilih Tahun:", ["Semua Tahun"] + [int(t) for t in tahun_list])
    else:
        sel_tahun = st.selectbox("📅 Pilih Tahun:", ["Semua Tahun"])
        
    search_report = st.text_input("🔎 Jenis Report:", placeholder="MET, SERVER...")
    search_staff = st.text_input("👤 Nama Staff:")
    
    st.divider()
    folder_url = "https://drive.google.com/drive/folders/1lG9eKZ69hpT6q-aqXpNxyd0HMcXdr3A4rAjUaXLCpDpOPffFzG0XK-MGBLaGHcBMcyqWjyLy"
    st.link_button("📂 Buka Folder Drive", folder_url, use_container_width=True)

# 6. MAIN CONTENT
st.title("📊 VTMS LPJ/PTP Management Dashboard")

tab1, tab2 = st.tabs(["📝 Laporan Harian", "⚙️ Status Equipment"])

# --- TAB 1: LAPORAN ---
with tab1:
    if not df_raw.empty:
        df = df_raw.copy()
        # Filter Tahun
        if sel_tahun != "Semua Tahun" and 'Tahun' in df.columns: 
            df = df[df['Tahun'] == sel_tahun]
        
        # Filter Search
        if search_report and 'REPORT CHECKLIST' in df.columns: 
            df = df[df['REPORT CHECKLIST'].str.contains(search_report, case=False, na=False)]
        if search_staff and 'Name' in df.columns: 
            df = df[df['Name'].str.contains(search_staff, case=False, na=False)]
        
        # Urus paparan
        if not df.empty:
            # Gunakan kolum masa yang dikesan tadi untuk sorting
            time_col = next((c for c in df.columns if any(x in c.lower() for x in ['timestamp', 'time', 'date', 'tarikh'])), None)
            display_df = df.sort_values(by=time_col, ascending=False).reset_index(drop=True) if time_col else df.reset_index(drop=True)
            
            if 'REPORT CHECKLIST' in display_df.columns:
                display_df.insert(0, 'ICON', display_df['REPORT CHECKLIST'].map(icon_map).fillna("https://cdn-icons-png.flaticon.com/512/2991/2991108.png"))

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Jumlah Laporan", len(display_df))
            m2.metric("Approved ✅", len(display_df[display_df['STATUS'] == 'APPROVED']) if 'STATUS' in display_df.columns else 0)
            m3.metric("Rejected ❌", len(display_df[display_df['STATUS'] == 'REJECTED']) if 'STATUS' in display_df.columns else 0)
            m4.metric("Jumlah Staff", display_df['Name'].nunique() if 'Name' in display_df.columns else 0)

            def style_status_val(val):
                if val == 'REJECTED': return 'color: red; font-weight: bold;'
                if val == 'APPROVED': return 'color: green; font-weight: bold;'
                return ''

            st.subheader("📋 Rekod Laporan")
            event = st.dataframe(
                display_df.style.map(style_status_val, subset=['STATUS'] if 'STATUS' in display_df.columns else []),
                use_container_width=True,
                column_config={
                    "ICON": st.column_config.ImageColumn("Type", width="small"),
                    PDF_COL: st.column_config.LinkColumn("Fail Report", display_text="BUKA PDF 📄")
                },
                on_select="rerun",
                selection_mode="single-row",
                hide_index=True
            )

            if len(event.selection.rows) > 0:
                st.session_state.selected_row_idx = event.selection.rows[0]

            if st.session_state.selected_row_idx is not None:
                idx = st.session_state.selected_row_idx
                if idx < len(display_df):
                    row = display_df.iloc[idx]
                    link = row.get(PDF_COL, "")
                    st.markdown("---")
                    c1, c2 = st.columns([0.9, 0.1])
                    c1.subheader(f"📄 Preview: {row.get('REPORT CHECKLIST', 'Report')}")
                    if c2.button("❌ Tutup"):
                        st.session_state.selected_row_idx = None
                        st.rerun()
                    
                    if isinstance(link, str) and "drive.google.com" in link:
                        match = re.search(r'[-\w]{25,}', link)
                        if match:
                            file_id = match.group()
                            st.markdown(f'<div class="pdf-view-container"><iframe src="https://drive.google.com/file/d/{file_id}/preview" width="100%" height="800px"></iframe></div>', unsafe_allow_html=True)
        else:
            st.warning("Tiada data ditemui untuk tapisan tersebut.")
    else:
        st.error("Data Laporan gagal dimuatkan. Pastikan link CSV betul dan akses dibuka kepada 'Anyone with the link'.")

# --- TAB 2: STATUS EQUIPMENT ---
with tab2:
    if not df_equip.empty:
        st.subheader("⚙️ Inventory & Status Semasa Peralatan")
        
        cols = df_equip.columns.tolist()
        status_col = next((c for c in cols if "2025" in c or "2026" in c), cols[-1])
        
        st.info(f"Status berdasarkan kolum: **{status_col}**")

        e1, e2, e3 = st.columns(3)
        e1.metric("Equipment OK", len(df_equip[df_equip[status_col] == 'OK']) if status_col in df_equip.columns else 0)
        e2.metric("Faulty ⚠️", len(df_equip[df_equip[status_col] == 'FAULTY']) if status_col in df_equip.columns else 0)
        e3.metric("Missing ❌", len(df_equip[df_equip[status_col] == 'MISSING']) if status_col in df_equip.columns else 0)

        search_eq = st.text_input("🔍 Cari Alat (SN, Nama, Site, IP):", placeholder="Contoh: SGH atau PTP...")
        df_eq_show = df_equip.copy()
        if search_eq:
            df_eq_show = df_eq_show[df_eq_show.astype(str).apply(lambda x: x.str.contains(search_eq, case=False)).any(axis=1)]

        def style_equip_val(val):
            if val == 'OK': return 'background-color: #D4EDDA; color: #155724'
            if val == 'FAULTY': return 'background-color: #FFF3CD; color: #856404'
            if val == 'MISSING': return 'background-color: #F8D7DA; color: #721C24'
            return ''

        st.dataframe(
            df_eq_show.style.map(style_equip_val, subset=[status_col] if status_col in df_eq_show.columns else []),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.error("Data Equipment gagal dimuatkan. Sila semak akses 'Share' pada Google Sheets.")

# GRAF ANALITIK
st.divider()
st.subheader("📊 Analitik Ringkas")

# Tab untuk pilih Analitik Laporan atau Analitik Peralatan
tab_a1, tab_a2 = st.tabs(["Analitik Laporan", "Analitik Peralatan"])

with tab_a1:
    if not df_raw.empty:
        c_pie, c_bar = st.columns(2)
        with c_pie:
            if 'STATUS' in df_raw.columns:
                fig1 = px.pie(df_raw, names='STATUS', title='Statistik Kelulusan Laporan', hole=0.4,
                             color_discrete_map={'APPROVED':'#2ecc71', 'REJECTED':'#e74c3c'})
                st.plotly_chart(fig1, use_container_width=True)
        with c_bar:
            if 'REPORT CHECKLIST' in df_raw.columns:
                fig2 = px.histogram(df_raw, x='REPORT CHECKLIST', color='STATUS' if 'STATUS' in df_raw.columns else None, 
                                   title='Kekerapan Laporan mengikut Jenis')
                st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Tiada data laporan untuk dianalisis.")

with tab_a2:
    if not df_equip.empty:
        # Gunakan kolum status yang dikesan secara automatik tadi
        cols = df_equip.columns.tolist()
        status_col = next((c for c in cols if "2025" in c or "2026" in c), cols[-1])
        
        c_pie_eq, c_bar_eq = st.columns(2)
        
        with c_pie_eq:
            # Carta Pai Status Peralatan
            fig_eq1 = px.pie(df_equip, names=status_col, title=f'Ringkasan Status Peralatan ({status_col})',
                            color_discrete_map={'OK':'#2ecc71', 'FAULTY':'#f1c40f', 'MISSING':'#e74c3c'})
            st.plotly_chart(fig_eq1, use_container_width=True)
            
        with c_bar_eq:
            # Carta Bar Status mengikut Site (PTP / LPJ)
            if 'Site' in df_equip.columns:
                fig_eq2 = px.histogram(df_equip, x='Site', color=status_col, barmode='group',
                                      title='Status Peralatan mengikut Lokasi')
                st.plotly_chart(fig_eq2, use_container_width=True)
            else:
                st.warning("Kolum 'Site' tidak ditemui untuk analitik lokasi.")
    else:
        st.info("Tiada data peralatan untuk dianalisis.")

