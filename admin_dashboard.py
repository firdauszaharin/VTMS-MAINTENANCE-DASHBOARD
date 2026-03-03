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
def local_css():
    st.markdown("""
        <style>
        .stApp { background-color: #FFFFFF; color: #2D3436; }
        .login-wrapper { display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; width: 100%; }
        h1 { color: #0984E3 !important; font-family: 'Segoe UI', sans-serif; font-weight: 800; }
        /* Form Styling */
        .stForm [data-testid="stFormSubmitButton"] button {
            width: 100% !important; background-color: #D63031; color: white; border-radius: 8px; font-weight: bold; border: none; padding: 10px 0px;
        }
        /* Dashboard Cards */
        div[data-testid="stMetric"] { 
            background: #F8F9FA; padding: 20px; border-radius: 12px; 
            border-top: 4px solid #0984E3; box-shadow: 0 2px 10px rgba(0,0,0,0.05); 
        }
        /* PDF Container */
        .pdf-view-container { 
            border: 2px solid #0984E3; border-radius: 12px; overflow: hidden; 
            margin-top: 20px; background-color: #f1f2f6; 
        }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)

# 3. SISTEM LOGIN (KEKAL LOGIN & ENTER KEY)
def check_admin_password():
    local_css()
    if "admin_auth" not in st.session_state:
        st.session_state["admin_auth"] = False

    if not st.session_state["admin_auth"]:
        _, col_mid, _ = st.columns([1, 1.3, 1])
        with col_mid:
            st.write("<br><br><br>", unsafe_allow_html=True)
            with st.container():
                st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
                if os.path.exists("logo.png"): st.image("logo.png", width=250)
                st.markdown("<h1>🛡️ VTMS DASHBOARD</h1>", unsafe_allow_html=True)
                st.markdown('<p style="color: #636E72;">SISTEM PENGURUSAN LAPORAN</p>', unsafe_allow_html=True)
                
                with st.form("login_form"):
                    pwd = st.text_input("Password", type="password", placeholder="Masukkan Kata Laluan...", label_visibility="collapsed")
                    if st.form_submit_button("MASUK"):
                        if pwd == "DausVTMS2026":
                            st.session_state["admin_auth"] = True
                            st.rerun() 
                        else:
                            st.error("❌ Password Salah!")
                st.markdown('</div>', unsafe_allow_html=True)
        return False
    return True

if not check_admin_password():
    st.stop()

# --- 4. DATA LOADING ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSEHHkyeSHjGBSi3wp-T5eE0vCZtgZ2mpWmUktMZiUHqfvb9Aow1r8OK_ZTq9wCQrxg62xTUX2DpgS_/pub?gid=296214979&single=true&output=csv"

# NAMA KOLUM PDF (Pastikan ejaan sama seperti di Google Sheets)
PDF_COL = "UPLOAD REPORT" 

@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url)
        data['Timestamp'] = pd.to_datetime(data['Timestamp'])
        data['Tahun'] = data['Timestamp'].dt.year
        return data
    except Exception as e:
        st.error(f"Gagal memuatkan data: {e}")
        return pd.DataFrame()

df_raw = load_data(SHEET_URL)
if df_raw.empty:
    st.stop()

df = df_raw.copy()

# --- 5. SIDEBAR NAVIGATION & FILTER ---
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    
    st.markdown("### 🔍 TAPISAN DATA")
    
    # Filter Tahun
    tahun_list = sorted(df['Tahun'].unique(), reverse=True)
    sel_tahun = st.selectbox("📅 Pilih Tahun:", ["Semua Tahun"] + list(tahun_list))
    
    # Carian Report & Staff
    search_report = st.text_input("🔎 Cari Jenis Report:", placeholder="MET, SERVER, etc...")
    search_staff = st.text_input("👤 Cari Nama Staff:", placeholder="Nama staff...")
    
    st.divider()
    if st.button("🔒 LOGOUT"):
        st.session_state["admin_auth"] = False
        st.rerun()

# Logik Penapisan
if sel_tahun != "Semua Tahun":
    df = df[df['Tahun'] == sel_tahun]
if search_report:
    df = df[df['REPORT CHECKLIST'].str.contains(search_report, case=False, na=False)]
if search_staff:
    df = df[df['Name'].str.contains(search_staff, case=False, na=False)]

# --- 6. MAIN DASHBOARD ---
st.title("📊 VTMS Management Dashboard")
st.write(f"Tahun: **{sel_tahun}** | Masa: **{waktu_msia.strftime('%d/%m/%Y %H:%M')}**")

st.divider()

# Metrics Row
m1, m2, m3, m4 = st.columns(4)
m1.metric("Laporan", len(df))
m2.metric("Approved ✅", len(df[df['STATUS'] == 'APPROVED']) if 'STATUS' in df.columns else 0)
m3.metric("Rejected ❌", len(df[df['STATUS'] == 'REJECTED']) if 'STATUS' in df.columns else 0)
m4.metric("Staff", df['Name'].nunique() if 'Name' in df.columns else 0)

# --- 7. JADUAL INTERAKTIF ---
st.write("##")
st.subheader("📋 Rekod Laporan (Klik baris untuk Preview PDF)")

# Konfigurasi Link Kolum
column_config = {}
if PDF_COL in df.columns:
    column_config[PDF_COL] = st.column_config.LinkColumn(
        "Fail Report",
        display_text="Buka PDF 📄"
    )

display_df = df.sort_values(by="Timestamp", ascending=False)

# Render Jadual
event = st.dataframe(
    display_df,
    use_container_width=True,
    height=400,
    column_config=column_config,
    on_select="rerun",
    selection_mode="single-row"
)

# --- 8. PDF PREVIEW LOGIK ---
if len(event.selection.rows) > 0:
    row_idx = event.selection.rows[0]
    selected_data = display_df.iloc[row_idx]
    
    if PDF_COL in selected_data and isinstance(selected_data[PDF_COL], str):
        link = selected_data[PDF_COL]
        if "drive.google.com" in link:
            st.markdown("---")
            st.subheader(f"📄 Preview: {selected_data.get('REPORT CHECKLIST', 'Laporan')}")
            
            # Ekstrak ID Drive secara selamat
            match = re.search(r'[-\w]{25,}', link)
            if match:
                file_id = match.group()
                pdf_preview_url = f"https://drive.google.com/file/d/{file_id}/preview"
                
                # Paparan Preview
                st.markdown(f'''
                    <div class="pdf-view-container">
                        <iframe src="{pdf_preview_url}" width="100%" height="800px" allow="autoplay; encrypted-media"></iframe>
                    </div>
                ''', unsafe_allow_html=True)
                
                # Butang Backup
                st.link_button("📥 Klik Sini Jika Preview Tidak Keluar", link)
            else:
                st.warning("⚠️ ID Fail tidak dapat dikenal pasti.")
        else:
            st.info("ℹ️ Tiada pautan fail Google Drive.")

# --- 9. GRAF ANALITIK ---
st.divider()
c1, c2 = st.columns([1, 1.5])

with c1:
    if 'STATUS' in df.columns:
        fig_pie = px.pie(df, names='STATUS', title='Pecahan Status', hole=0.4, 
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_pie, use_container_width=True)

with c2:
    if 'REPORT CHECKLIST' in df.columns:
        report_counts = df['REPORT CHECKLIST'].value_counts().reset_index()
        report_counts.columns = ['Jenis', 'Bil']
        fig_bar = px.bar(report_counts, x='Jenis', y='Bil', title='Jumlah Jenis Laporan',
                         color='Jenis', text='Bil')
        st.plotly_chart(fig_bar, use_container_width=True)

# --- 10. DOWNLOAD DATA ---
st.divider()
csv = df.to_csv(index=False).encode('utf-8')
st.download_button("📥 Download Report (CSV)", data=csv, file_name=f"VTMS_Data_{sel_tahun}.csv", mime="text/csv")