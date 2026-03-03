import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_plotly_events import plotly_events # Perlu install ini

# ... (Kekalkan kod loading data anda di sini) ...

with tab2:
    if not df_equip.empty:
        # ... (Kekalkan kod metrik & selectbox bulan) ...

        if selected_month in df_equip.columns:
            df_pie = df_equip.copy()
            df_pie[selected_month] = df_pie[selected_month].astype(str).str.strip().str.upper()

            st.markdown(f"### 🎯 Equipment Performance Overview ({selected_month})")
            st.info("💡 Tip: Klik pada bar di dalam graf 'Status by Location' untuk tapis jadual di bawah.")
            
            col_left, col_right = st.columns(2)
            
            with col_left:
                fig_pie = px.pie(df_pie, names=selected_month, title='Condition Overview',
                                 color_discrete_map={'OK':'#2ecc71','FAULTY':'#f1c40f','MISSING':'#e74c3c'})
                st.plotly_chart(fig_pie, use_container_width=True)

            with col_right:
                # Kita gunakan plotly_events untuk menangkap klik
                fig_site = px.histogram(df_pie, x='Site', color=selected_month, barmode='group', 
                                       title='Status by Location (Click to Filter)',
                                       color_discrete_map={'OK':'#2ecc71','FAULTY':'#f1c40f','MISSING':'#e74c3c'})
                
                # Ini akan mengembalikan data klik
                selected_point = plotly_events(fig_site, click_event=True, hover_event=False)

            # --- LOGIK TAPISAN (FILTER) ---
            search_site_click = ""
            if selected_point:
                # Mengambil nama Site daripada titik yang diklik
                search_site_click = selected_point[0]['x']
                st.success(f"Filtering by Site: **{search_site_click}**")
                if st.button("Clear Filter ❌"):
                    st.rerun()

            st.divider()

            # --- JADUAL INVENTORY ---
            st.subheader("📦 Inventory Asset List")
            
            # Gabungkan carian teks manual DAN klik pada graf
            search_eq = st.text_input("🔍 Search Asset (SN, Name, Site):", key="search_eq_tab")
            
            essential_cols = ["Site", "Type", "Serial No", "IP Address", selected_month]
            df_eq_show = df_equip[[c for c in essential_cols if c in df_equip.columns]].copy()
            
            # Tapis berdasarkan Klik Graf
            if search_site_click:
                df_eq_show = df_eq_show[df_eq_show['Site'] == search_site_click]
            
            # Tapis berdasarkan Carian Teks
            if search_eq:
                df_eq_show = df_eq_show[df_eq_show.astype(str).apply(lambda x: x.str.contains(search_eq, case=False)).any(axis=1)]

            st.dataframe(df_eq_show.style.map(
                lambda x: 'background-color: #D4EDDA' if x=='OK' else (
                          'background-color: #F8D7DA' if x=='MISSING' else (
                          'background-color: #FFF3CD' if x=='FAULTY' else '')), 
                subset=[selected_month]), use_container_width=True, hide_index=True)
