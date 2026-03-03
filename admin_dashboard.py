import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz
import re
import os

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="VTMS Executive Dashboard",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# =========================
# TIMEZONE
# =========================
msia_tz = pytz.timezone('Asia/Kuala_Lumpur')
waktu_msia = datetime.now(msia_tz)

# =========================
# MODERN PREMIUM CSS
# =========================
st.markdown("""
<style>

html, body, [class*="css"]  {
    font-family: 'Segoe UI', sans-serif;
}

.stApp {
    background: linear-gradient(to bottom right, #f4f6f9, #ffffff);
}

.main-title {
    font-size: 34px;
    font-weight: 700;
    background: linear-gradient(90deg, #0984E3, #6C5CE7);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 10px;
}

.subtitle {
    color: #636e72;
    font-size: 15px;
    margin-bottom: 25px;
}

[data-testid="stMetric"] {
    background: white;
    padding: 18px;
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    transition: 0.3s ease;
}

[data-testid="stMetric"]:hover {
    transform: translateY(-5px);
    box-shadow: 0 6px 25px rgba(0,0,0,0.12);
}

.section-card {
    background: white;
    padding: 25px;
    border-radius: 20px;
    box-shadow: 0 4px 25px rgba(0,0,0,0.05);
    margin-bottom: 25px;
}

.alert-modern {
    background: linear-gradient(90deg, #ff7675, #d63031);
    color: white;
    padding: 18px;
    border-radius: 15px;
    font-weight: 500;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

</style>
""", unsafe_allow_html=True)

# =========================
# DATA SOURCE
# =========================
SHEET_REPORT_URL = "YOUR_REPORT_CSV_LINK"
SHEET_EQUIP_URL = "YOUR_EQUIPMENT_CSV_LINK"
PDF_COL = "UPLOAD REPORT"

@st.cache_data(ttl=60)
def load_data(url):
    try:
        df = pd.read_csv(url, on_bad_lines='skip')
        df.columns = df.columns.str.strip()
        time_col = next((c for c in df.columns if 'time' in c.lower() or 'date' in c.lower()), None)
        if time_col:
            df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
            df['Year'] = df[time_col].dt.year
        return df
    except:
        return pd.DataFrame()

df_raw = load_data(SHEET_REPORT_URL)
df_equip = load_data(SHEET_EQUIP_URL)

# =========================
# HEADER
# =========================
st.markdown('<div class="main-title">📊 VTMS LPJ/PTP Executive Dashboard</div>', unsafe_allow_html=True)
st.markdown(f'<div class="subtitle">Real-Time Monitoring • Last Sync: {waktu_msia.strftime("%d %B %Y | %H:%M:%S")}</div>', unsafe_allow_html=True)

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.header("🛡️ VTMS Control Panel")
    st.markdown("---")
    
    year_filter = "All"
    if not df_raw.empty and "Year" in df_raw.columns:
        years = sorted(df_raw["Year"].dropna().unique(), reverse=True)
        year_filter = st.selectbox("📅 Filter Year", ["All"] + list(years))
    
    search_report = st.text_input("🔎 Search Report")
    search_staff = st.text_input("👤 Search Staff")
    
    st.markdown("---")
    st.markdown("### System Access")
    st.link_button("📂 Open Google Drive", "YOUR_DRIVE_LINK", use_container_width=True)

# =========================
# ALERT SECTION
# =========================
if not df_equip.empty:
    latest_col = df_equip.columns[-1]
    status_series = df_equip[latest_col].astype(str).str.upper()
    faulty_count = len(df_equip[status_series.isin(["FAULTY", "MISSING"])])
    
    if faulty_count > 0:
        st.markdown(f"""
        <div class="alert-modern">
        ⚠️ {faulty_count} Equipment Issues Detected ({latest_col}) – Immediate Action Required
        </div>
        """, unsafe_allow_html=True)

# =========================
# TABS
# =========================
tab1, tab2 = st.tabs(["📝 Maintenance Reports", "⚙️ Equipment Status"])

# ===================================================
# TAB 1 – REPORTS
# ===================================================
with tab1:
    if not df_raw.empty:
        df = df_raw.copy()
        
        if year_filter != "All":
            df = df[df["Year"] == year_filter]
        if search_report:
            df = df[df["REPORT CHECKLIST"].str.contains(search_report, case=False, na=False)]
        if search_staff:
            df = df[df["Name"].str.contains(search_staff, case=False, na=False)]
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Reports", len(df))
        col2.metric("Approved", len(df[df["STATUS"]=="APPROVED"]))
        col3.metric("Rejected", len(df[df["STATUS"]=="REJECTED"]))
        col4.metric("Pending", len(df[~df["STATUS"].isin(["APPROVED","REJECTED"])]))
        
        st.markdown("### 📈 Performance Overview")
        
        c1, c2 = st.columns(2)
        
        with c1:
            fig1 = px.pie(df, names="STATUS", hole=0.55,
                          color_discrete_map={
                              "APPROVED":"#00b894",
                              "REJECTED":"#d63031"
                          })
            fig1.update_layout(template="plotly_white")
            st.plotly_chart(fig1, use_container_width=True)
        
        with c2:
            fig2 = px.histogram(df, x="REPORT CHECKLIST", color="STATUS",
                                color_discrete_map={
                                    "APPROVED":"#00b894",
                                    "REJECTED":"#d63031"
                                })
            fig2.update_layout(template="plotly_white")
            st.plotly_chart(fig2, use_container_width=True)
        
        st.markdown("### 📋 Reports Record")
        st.dataframe(df, use_container_width=True)

# ===================================================
# TAB 2 – EQUIPMENT
# ===================================================
with tab2:
    if not df_equip.empty:
        
        month_cols = df_equip.columns[-6:]
        selected_month = st.selectbox("📅 Select Month", month_cols, index=len(month_cols)-1)
        
        status_series = df_equip[selected_month].astype(str).str.upper()
        
        m1, m2, m3 = st.columns(3)
        m1.metric("OK", len(df_equip[status_series=="OK"]))
        m2.metric("FAULTY", len(df_equip[status_series=="FAULTY"]))
        m3.metric("MISSING", len(df_equip[status_series=="MISSING"]))
        
        st.markdown("### ⚙️ Equipment Performance Overview")
        
        c1, c2 = st.columns(2)
        
        with c1:
            fig3 = px.pie(df_equip, names=selected_month, hole=0.6,
                          color_discrete_map={
                              "OK":"#00b894",
                              "FAULTY":"#fdcb6e",
                              "MISSING":"#d63031"
                          })
            fig3.update_layout(template="plotly_white")
            st.plotly_chart(fig3, use_container_width=True)
        
        with c2:
            if "Site" in df_equip.columns:
                fig4 = px.histogram(df_equip, x="Site", color=selected_month,
                                    barmode="group",
                                    color_discrete_map={
                                        "OK":"#00b894",
                                        "FAULTY":"#fdcb6e",
                                        "MISSING":"#d63031"
                                    })
                fig4.update_layout(template="plotly_white")
                st.plotly_chart(fig4, use_container_width=True)
        
        st.markdown("### 📦 Equipment Asset List")
        st.dataframe(df_equip, use_container_width=True)
