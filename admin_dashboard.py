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
            margin-top: 10px; background-color: #f1f2f6; 
        }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)

# 3. SISTEM LOGIN
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
    st.warning("Tiada data ditemui dalam Google Sheets.")
    st.stop()

# Initialize Session States
if "selected_row_idx" not in st.session_state:
    st.session_state.selected_row_idx = None
if "prev_filter_state" not in st.session_state:
    st.session_state.prev_filter_state = ""

# --- 5. SIDEBAR NAVIGATION & FILTER ---
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    
    st.markdown("### 🔍 TAPISAN DATA")
    
    # Filter Tahun
    tahun_list = sorted(df_raw['Tahun'].dropna().unique(), reverse=True)
    sel_tahun = st.selectbox("📅 Pilih Tahun:", ["Semua Tahun"] + [int(t) for t in tahun_list])
    
    # Carian Report & Staff
    search_report = st.text_input("🔎 Cari Jenis Report:", placeholder="MET, SERVER, etc...")
    search_staff = st.text_input("👤 Cari Nama Staff:", placeholder="Nama staff...")
    
    # Reset preview jika filter berubah
    current_filter = f"{sel_tahun}{search_report}{search_staff}"
    if current_filter != st.session_state.prev_filter_state:
        st.session_state.selected_row_idx = None
        st.session_state.prev_filter_state = current_filter

    st.divider()
    if st.button("🔒 LOGOUT"):
        st.session_state["admin_auth"] = False
        st.rerun()

# --- LOGIK PENAPISAN ---
df = df_raw.copy()
if sel_tahun != "Semua Tahun":
    df = df[df['Tahun'] == sel_tahun]
if search_report:
    df = df[df['REPORT CHECKLIST'].str.contains(search_report, case=False, na=False)]
if search_staff:
    df = df[df['Name'].str.contains(search_staff, case=False, na=False)]

# Urutkan mengikut masa terbaru
display_df = df.sort_values(by="Timestamp", ascending=False).reset_index(drop=True)

# --- 6. MAIN DASHBOARD ---
st.title("📊 VTMS Management Dashboard")
st.write(f"Paparan: **{sel_tahun}** | Masa: **{waktu_msia.strftime('%d/%m/%Y %H:%M')}**")

st.divider()

# Metrics Row
m1, m2, m3, m4 = st.columns(4)
m1.metric("Jumlah Laporan", len(display_df))
m2.metric("Approved ✅", len(display_df[display_df['STATUS'] == 'APPROVED']) if 'STATUS' in display_df.columns else 0)
m3.metric("Rejected ❌", len(display_df[display_df['STATUS'] == 'REJECTED']) if 'STATUS' in display_df.columns else 0)
m4.metric("Jumlah Staff", display_df['Name'].nunique() if 'Name' in display_df.columns else 0)

# --- 7. JADUAL INTERAKTIF ---
st.subheader("📋 Rekod Laporan")
st.info("💡 Klik pada mana-mana baris di bawah untuk melihat preview fail PDF secara automatik.")

column_config = {
    PDF_COL: st.column_config.LinkColumn("Fail Report", display_text="Buka Link 🔗")
}

# Render Jadual dengan Pemilihan Baris
event = st.dataframe(
    display_df,
    use_container_width=True,
    height=400,
    column_config=column_config,
    on_select="rerun",
    selection_mode="single-row"
)

# Kemaskini index baris yang dipilih
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
            st.subheader(f"📄 Preview: {row.get('REPORT CHECKLIST', 'Laporan')}")
        with c_close:
            if st.button("❌ Close"):
                st.session_state.selected_row_idx = None
                st.rerun()

        if isinstance(link, str) and "drive.google.com" in link:
            match = re.search(r'[-\w]{25,}', link)
            if match:
                file_id = match.group()
                preview_url = f"https://drive.google.com/file/d/{file_id}/preview"
                
                st.markdown(f'''
                    <div class="pdf-view-container">
                        <iframe src="{preview_url}" width="100%" height="700px" allow="autoplay"></iframe>
                    </div>
                ''', unsafe_allow_html=True)
                st.link_button("📥 Muat Turun / Buka Tab Baru", link)
            else:
                st.error("Format pautan Google Drive tidak sah.")
        else:
            st.warning("Tiada pautan PDF yang sah untuk baris ini.")

# --- 9. GRAF ANALITIK ---
st.divider()
col_graph1, col_graph2 = st.columns(2)

with col_graph1:
    if 'STATUS' in display_df.columns and not display_df.empty:
        fig_pie = px.pie(display_df, names='STATUS', title='Statistik Status Kelulusan', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

with col_graph2:
    if 'REPORT CHECKLIST' in display_df.columns and not display_df.empty:
        counts = display_df['REPORT CHECKLIST'].value_counts().reset_index()
        counts.columns = ['Jenis', 'Bil']
        fig_bar = px.bar(counts, x='Jenis', y='Bil', title='Kekerapan Laporan', color='Jenis')
        st.plotly_chart(fig_bar, use_container_width=True)

# --- 10. DOWNLOAD DATA ---
csv = display_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download Data Paparan Ini (CSV)",
    data=csv,
    file_name=f"VTMS_Export_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)



