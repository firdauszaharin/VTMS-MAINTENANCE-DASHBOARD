import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz 
import os
import re

# --------------------------------------------------
# 1. PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="VTMS Maintenance Dashboard",
    layout="wide",
    page_icon="📡"
)

# --------------------------------------------------
# 2. CUSTOM MODERN CSS
# --------------------------------------------------
st.markdown("""
<style>
.main {
    background-color: #f4f6f9;
}

h1 {
    font-family: 'Segoe UI', sans-serif;
    font-weight: 600;
}

.kpi-card {
    background: white;
    padding: 22px;
    border-radius: 14px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.06);
    text-align: center;
}

.kpi-title {
    font-size: 14px;
    color: #6b7280;
    margin-bottom: 5px;
}

.kpi-value {
    font-size: 30px;
    font-weight: 600;
    color: #111827;
}

section[data-testid="stSidebar"] {
    background-color: #111827;
}

section[data-testid="stSidebar"] * {
    color: white !important;
}

.block-container {
    padding-top: 1.5rem;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# 3. MALAYSIA TIMEZONE
# --------------------------------------------------
msia_tz = pytz.timezone('Asia/Kuala_Lumpur')
waktu_msia = datetime.now(msia_tz)

# --------------------------------------------------
# 4. LOAD DATA
# --------------------------------------------------
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSEHHkyeSHjGBSi3wp-T5eE0vCZtgZ2mpWmUktMZiUHqfvb9Aow1r8OK_ZTq9wCQrxg62xTUX2DpgS_/pub?gid=296214979&single=true&output=csv"
PDF_COL = "UPLOAD REPORT"

@st.cache_data(ttl=60)
def load_data(url):
    try:
        data = pd.read_csv(url)
        data.columns = data.columns.str.strip()
        data['Timestamp'] = pd.to_datetime(data['Timestamp'])
        data['Tahun'] = data['Timestamp'].dt.year
        return data
    except Exception as e:
        st.error(f"Gagal memuatkan data: {e}")
        return pd.DataFrame()

df_raw = load_data(SHEET_URL)

if df_raw.empty:
    st.warning("⚠️ Data tidak tersedia.")
    st.stop()

# --------------------------------------------------
# 5. SIDEBAR
# --------------------------------------------------
with st.sidebar:
    st.markdown("## 🛡️ VTMS ADMIN")
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)

    st.divider()
    st.markdown("### 📂 AKSES FAIL")
    folder_url = "https://drive.google.com/drive/folders/1lG9eKZ69hpT6q-aqXpNxyd0HMcXdr3A4rAjUaXLCpDpOPffFzG0XK-MGBLaGHcBMcyqWjyLy?usp=drive_link"
    st.link_button("📁 Folder Laporan (Drive)", folder_url, use_container_width=True)

    st.divider()
    st.markdown("### 🔍 TAPISAN DATA")

    tahun_list = sorted(df_raw['Tahun'].dropna().unique(), reverse=True)
    sel_tahun = st.selectbox("📅 Pilih Tahun:", ["Semua Tahun"] + [int(t) for t in tahun_list])

    search_report = st.text_input("🔎 Cari Jenis Report:")
    search_staff = st.text_input("👤 Cari Nama Staff:")

    st.divider()
    csv_export = df_raw.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download All Data (CSV)", csv_export, "VTMS_Data_Full.csv")

# --------------------------------------------------
# 6. FILTER LOGIC
# --------------------------------------------------
df = df_raw.copy()

if sel_tahun != "Semua Tahun":
    df = df[df['Tahun'] == sel_tahun]

if search_report:
    df = df[df['REPORT CHECKLIST'].str.contains(search_report, case=False, na=False)]

if search_staff:
    df = df[df['Name'].str.contains(search_staff, case=False, na=False)]

display_df = df.sort_values(by="Timestamp", ascending=False).reset_index(drop=True)

# --------------------------------------------------
# 7. HEADER
# --------------------------------------------------
st.markdown(f"""
<h1>VTMS Maintenance & Report Dashboard</h1>
<p style='color:gray;'>
Real-Time Monitoring | Data Tahun: <b>{sel_tahun}</b> | 
Masa Sistem: <b>{waktu_msia.strftime('%d/%m/%Y %H:%M')}</b>
</p>
""", unsafe_allow_html=True)

st.divider()

# --------------------------------------------------
# 8. KPI CARDS
# --------------------------------------------------
total_laporan = len(display_df)
approved = len(display_df[display_df['STATUS'] == 'APPROVED']) if 'STATUS' in display_df.columns else 0
rejected = len(display_df[display_df['STATUS'] == 'REJECTED']) if 'STATUS' in display_df.columns else 0
total_staff = display_df['Name'].nunique() if 'Name' in display_df.columns else 0

c1, c2, c3, c4 = st.columns(4)

cards = [
    ("Jumlah Laporan", total_laporan, "#2563eb"),
    ("Approved", approved, "#16a34a"),
    ("Rejected", rejected, "#dc2626"),
    ("Jumlah Staff", total_staff, "#7c3aed")
]

for col, (title, value, color) in zip([c1, c2, c3, c4], cards):
    with col:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value" style="color:{color};">{value}</div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# --------------------------------------------------
# 9. TABLE
# --------------------------------------------------
st.subheader("📋 Rekod Laporan")

column_config = {}
if PDF_COL in display_df.columns:
    column_config[PDF_COL] = st.column_config.LinkColumn("Fail Report", display_text="BUKA PDF 📄")

st.dataframe(
    display_df,
    use_container_width=True,
    height=400,
    column_config=column_config,
    hide_index=True
)

# --------------------------------------------------
# 10. CHARTS
# --------------------------------------------------
st.divider()
col1, col2 = st.columns(2)

with col1:
    if 'STATUS' in display_df.columns and not display_df.empty:
        fig_pie = px.pie(
            display_df,
            names='STATUS',
            hole=0.5,
            color_discrete_sequence=['#2563eb', '#16a34a', '#dc2626']
        )
        fig_pie.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Segoe UI")
        )
        st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    if 'REPORT CHECKLIST' in display_df.columns and not display_df.empty:
        counts = display_df['REPORT CHECKLIST'].value_counts().reset_index()
        counts.columns = ['Jenis', 'Bil']
        fig_bar = px.bar(
            counts,
            x='Jenis',
            y='Bil',
            text='Bil',
            color='Jenis'
        )
        fig_bar.update_layout(
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Segoe UI")
        )
        st.plotly_chart(fig_bar, use_container_width=True)

# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.markdown("""
<hr>
<p style='text-align:center;color:gray;font-size:12px;'>
VTMS Monitoring System © 2026 | EDM Engineering
</p>
""", unsafe_allow_html=True)
