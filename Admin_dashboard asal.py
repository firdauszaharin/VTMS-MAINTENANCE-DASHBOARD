import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz
import re
import os

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
    .pdf-view-container { border: 2px solid #0984E3; border-radius: 12px; overflow: hidden; margin-top: 10px; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# 3. DATA LINKS (CSV FORMAT)
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
    except Exception as e:
        return pd.DataFrame()

df_raw = load_data(SHEET_REPORT_URL)
df_equip = load_data(SHEET_EQUIP_URL)

# --- REPORT ICON MAPPING ---
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
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    st.divider()
    
    st.markdown("### 🔍 REPORT FILTERS")
    if not df_raw.empty and 'Year' in df_raw.columns:
        year_list = sorted(df_raw['Year'].dropna().unique(), reverse=True)
        sel_year = st.selectbox("📅 Select Year:", ["All Years"] + [int(t) for t in year_list])
    else:
        sel_year = st.selectbox("📅 Select Year:", ["All Years"])
        
    search_report = st.text_input("🔎 Report Type:", placeholder="MET, SERVER...")
    search_staff = st.text_input("👤 Staff Name:")
    
    st.divider()
    folder_url = "https://drive.google.com/drive/folders/1lG9eKZ69hpT6q-aqXpNxyd0HMcXdr3A4rAjUaXLCpDpOPffFzG0XK-MGBLaGHcBMcyqWjyLy"
    st.link_button("📂 Open Drive Folder", folder_url, use_container_width=True)

# 6. MAIN CONTENT
st.title("📊 VTMS LPJ/PTP Management Dashboard")

# DEFINISI TAB
tab1, tab2 = st.tabs(["📝 Maintenance Reports", "⚙️ Equipment Status"])

# --- TAB 1: MAINTENANCE REPORTS ---
with tab1:
    if not df_raw.empty:
        # Filter Data
        df = df_raw.copy()
        if sel_year != "All Years": df = df[df['Year'] == sel_year]
        if search_report: df = df[df['REPORT CHECKLIST'].str.contains(search_report, case=False, na=False)]
        if search_staff: df = df[df['Name'].str.contains(search_staff, case=False, na=False)]
        
        time_col = next((c for c in df.columns if any(x in c.lower() for x in ['timestamp', 'time', 'date', 'tarikh'])), None)
        display_df = df.sort_values(by=time_col, ascending=False).reset_index(drop=True) if time_col else df.reset_index(drop=True)
        
        # Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Reports", len(display_df))
        m2.metric("Approved ✅", len(display_df[display_df['STATUS'] == 'APPROVED']) if 'STATUS' in display_df.columns else 0)
        m3.metric("Rejected ❌", len(display_df[display_df['STATUS'] == 'REJECTED']) if 'STATUS' in display_df.columns else 0)
        m4.metric("Active Staff", display_df['Name'].nunique() if 'Name' in display_df.columns else 0)

        # PERFORMANCE OVERVIEW (REPORT ONLY)
        st.markdown("### 🎯 Maintenance Performance Overview")
        col_p, col_b = st.columns(2)
        with col_p:
            st.plotly_chart(px.pie(display_df, names='STATUS', title='Approval Status Distribution', hole=0.4, 
                                  color_discrete_map={'APPROVED':'#2ecc71', 'REJECTED':'#e74c3c'}), use_container_width=True)
        with col_b:
            st.plotly_chart(px.histogram(display_df, x='REPORT CHECKLIST', color='STATUS', title='Report Frequency by Type',
                                         color_discrete_map={'APPROVED':'#2ecc71', 'REJECTED':'#e74c3c'}), use_container_width=True)

        st.divider()

        # Table & Preview
        st.subheader("📋 Submitted Reports Record")
        if 'REPORT CHECKLIST' in display_df.columns:
            display_df.insert(0, 'ICON', display_df['REPORT CHECKLIST'].map(icon_map).fillna("https://cdn-icons-png.flaticon.com/512/2991/2991108.png"))

        event = st.dataframe(display_df, use_container_width=True, hide_index=True,
                            column_config={
                                "ICON": st.column_config.ImageColumn("Type"), 
                                PDF_COL: st.column_config.LinkColumn("Report File", display_text="OPEN PDF 📄")
                            },
                            on_select="rerun", selection_mode="single-row")

        if len(event.selection.rows) > 0:
            st.session_state.selected_row_idx = event.selection.rows[0]

        if st.session_state.selected_row_idx is not None:
            idx = st.session_state.selected_row_idx
            row = display_df.iloc[idx]
            link = row.get(PDF_COL, "")
            if isinstance(link, str) and "drive.google.com" in link:
                file_id = re.search(r'[-\w]{25,}', link).group()
                st.markdown(f'<div class="pdf-view-container"><iframe src="https://drive.google.com/file/d/{file_id}/preview" width="100%" height="600px"></iframe></div>', unsafe_allow_html=True)
    else:
        st.error("Failed to load Report data.")

# --- TAB 2: EQUIPMENT STATUS ---
with tab2:
    if not df_equip.empty:
        st.subheader("⚙️ Inventory & Equipment Status")
        month_cols = [c for c in df_equip.columns if any(yr in c for yr in ["2025", "2026"])]
        
        c_sel, _ = st.columns([0.4, 0.6])
        with c_sel:
            selected_month = st.selectbox("📅 Select Report Month:", month_cols, index=len(month_cols)-1)
        
        st.divider()

        if selected_month in df_equip.columns:
            # Data Processing
            status_series = df_equip[selected_month].astype(str).str.strip().str.upper()
            df_pie = df_equip.copy()
            df_pie[selected_month] = status_series
            
            # Metrics
            me1, me2, me3 = st.columns(3)
            me1.metric(f"Equipment OK", len(df_equip[status_series == 'OK']))
            me2.metric(f"Faulty ⚠️", len(df_equip[status_series == 'FAULTY']))
            me3.metric(f"Missing ❌", len(df_equip[status_series == 'MISSING']))

            # PERFORMANCE OVERVIEW (EQUIPMENT ONLY)
            st.markdown(f"### 🎯 Equipment Performance Overview ({selected_month})")
            col_left, col_right = st.columns(2)
            with col_left:
                st.plotly_chart(px.pie(df_pie, names=selected_month, title='Condition Overview',
                                      color_discrete_map={'OK':'#2ecc71','FAULTY':'#f1c40f','MISSING':'#e74c3c'}), use_container_width=True)
            with col_right:
                if 'Site' in df_pie.columns:
                    st.plotly_chart(px.histogram(df_pie, x='Site', color=selected_month, barmode='group', title='Status by Location',
                                                color_discrete_map={'OK':'#2ecc71','FAULTY':'#f1c40f','MISSING':'#e74c3c'}), use_container_width=True)
            
            if 'Type' in df_pie.columns:
                st.plotly_chart(px.histogram(df_pie, x='Type', color=selected_month, barmode='group', title='Status by Equipment Category',
                                            color_discrete_map={'OK':'#2ecc71','FAULTY':'#f1c40f','MISSING':'#e74c3c'}), use_container_width=True)
            
            st.divider()

            # Inventory Table
            st.subheader("📦 Inventory Asset List")
            search_eq = st.text_input("🔍 Search Asset (SN, Name, Site):", key="search_eq_tab")
            essential_cols = ["Site", "Type", "Serial No", "IP Address", selected_month]
            df_eq_show = df_equip[[c for c in essential_cols if c in df_equip.columns]].copy()
            
            if search_eq:
                df_eq_show = df_eq_show[df_eq_show.astype(str).apply(lambda x: x.str.contains(search_eq, case=False)).any(axis=1)]

            st.dataframe(df_eq_show.style.map(lambda x: 'background-color: #D4EDDA' if x=='OK' else ('background-color: #F8D7DA' if x=='MISSING' else ('background-color: #FFF3CD' if x=='FAULTY' else '')), subset=[selected_month]), use_container_width=True, hide_index=True)
    else:
        st.error("Failed to load Equipment data.")

