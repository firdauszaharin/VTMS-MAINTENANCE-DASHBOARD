import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz
import re
import os
from streamlit_plotly_events import plotly_events # WAJIB INSTALL: pip install streamlit-plotly-events

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

# 2. MODERN CSS
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #2D3436; }
    [data-testid="stMetric"] { 
        background: #F8F9FA; padding: 15px; border-radius: 12px; 
        border-top: 4px solid #0984E3; box-shadow: 0 2px 10px rgba(0,0,0,0.05); 
    }
    .alert-box {
        background-color: #FFF5F5; border-left: 5px solid #FF4B4B;
        padding: 15px; border-radius: 8px; margin-bottom: 20px;
    }
    .pdf-view-container { border: 2px solid #0984E3; border-radius: 12px; overflow: hidden; margin-top: 10px; }
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
        return data
    except Exception as e:
        return pd.DataFrame()

df_raw = load_data(SHEET_REPORT_URL)
df_equip = load_data(SHEET_EQUIP_URL)

# 5. SIDEBAR
with st.sidebar:
    st.markdown("## 🛡️ VTMS ADMIN")
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    st.divider()
    st.markdown(f"🕒 **Last Sync:** {waktu_msia.strftime('%H:%M:%S')}")
    st.divider()
    st.link_button("📂 Open Drive Folder", "https://drive.google.com/drive/folders/1lG9eKZ69hpT6q-aqXpNxyd0HMcXdr3A4jUaXLCpDpOPffFzG0XK-MGBLaGHcBMcyqWjyLy", use_container_width=True)

# 6. EXECUTIVE SUMMARY
st.title("📊 VTMS LPJ/PTP Management Dashboard")

# 7. MAIN CONTENT TABS
tab1, tab2 = st.tabs(["📝 Maintenance Reports", "⚙️ Equipment Status"])

# --- TAB 1 (REPORTS) - KEKALKAN LOGIK ASAL ---
with tab1:
    st.info("Sila rujuk kod sebelum ini untuk bahagian Laporan.")

# --- TAB 2: EQUIPMENT STATUS (DENGAN INTERACTIVE FILTER) ---
with tab2:
    if not df_equip.empty:
        month_cols = [c for c in df_equip.columns if any(yr in c for yr in ["2025", "2026"])]
        c_sel, _ = st.columns([0.4, 0.6])
        with c_sel:
            selected_month = st.selectbox("📅 Select Report Month:", month_cols, index=len(month_cols)-1)
        
        st.divider()

        if selected_month in df_equip.columns:
            # Pre-processing
            df_pie = df_equip.copy()
            df_pie[selected_month] = df_pie[selected_month].astype(str).str.strip().str.upper()
            
            st.markdown(f"### 🎯 Performance Overview ({selected_month})")
            st.caption("💡 Tip: Klik pada mana-mana bar di dalam graf untuk tapis jadual Inventory.")

            # ROW 1: Pie & Site Histogram
            col_a, col_b = st.columns(2)
            with col_a:
                fig_pie = px.pie(df_pie, names=selected_month, title='Condition Overview',
                                 color_discrete_map={'OK':'#2ecc71','FAULTY':'#f1c40f','MISSING':'#e74c3c'})
                st.plotly_chart(fig_pie, use_container_width=True)

            with col_b:
                fig_site = px.histogram(df_pie, x='Site', color=selected_month, barmode='group', 
                                       title='Status by Location (Click Bar to Filter)',
                                       color_discrete_map={'OK':'#2ecc71','FAULTY':'#f1c40f','MISSING':'#e74c3c'})
                # Capture Click on Site
                click_site = plotly_events(fig_site, click_event=True, key="click_site")

            # ROW 2: Type Histogram
            st.markdown("---")
            fig_type = px.histogram(df_pie, x='Type', color=selected_month, barmode='group', 
                                   title='Status by Equipment Category (Click Bar to Filter)',
                                   color_discrete_map={'OK':'#2ecc71','FAULTY':'#f1c40f','MISSING':'#e74c3c'})
            # Capture Click on Type
            click_type = plotly_events(fig_type, click_event=True, key="click_type")

            # --- LOGIK TAPISAN (FILTER) ---
            filtered_df = df_equip.copy()
            active_filter = None

            if click_site:
                active_filter = click_site[0]['x']
                filtered_df = filtered_df[filtered_df['Site'] == active_filter]
                st.success(f"Filtering by Site: **{active_filter}**")
            
            elif click_type:
                active_filter = click_type[0]['x']
                filtered_df = filtered_df[filtered_df['Type'] == active_filter]
                st.success(f"Filtering by Category: **{active_filter}**")

            if active_filter:
                if st.button("Reset Filter 🔄"):
                    st.rerun()

            st.divider()

            # --- JADUAL INVENTORY ---
            st.subheader("📦 Inventory Asset List")
            search_eq = st.text_input("🔍 Search Manual (SN, Name, IP):", key="search_eq_tab")
            
            essential_cols = ["Site", "Type", "Serial No", "IP Address", selected_month]
            df_eq_show = filtered_df[[c for c in essential_cols if c in filtered_df.columns]].copy()
            
            if search_eq:
                df_eq_show = df_eq_show[df_eq_show.astype(str).apply(lambda x: x.str.contains(search_eq, case=False)).any(axis=1)]

            st.dataframe(df_eq_show.style.map(
                lambda x: 'background-color: #D4EDDA' if x=='OK' else (
                          'background-color: #F8D7DA' if x=='MISSING' else (
                          'background-color: #FFF3CD' if x=='FAULTY' else '')), 
                subset=[selected_month]), use_container_width=True, hide_index=True)
