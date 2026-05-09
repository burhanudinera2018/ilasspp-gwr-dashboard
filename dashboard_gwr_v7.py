# =====================================================
# DASHBOARD ILASPP - GWR + KRIGING
# Proyek ILASPP (ATR/BPN)
# =====================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit.components.v1 import html
import os
import numpy as np

# Konfigurasi halaman
st.set_page_config(
    page_title="Dashboard GWR + Kriging - ILASPP",
    page_icon="🗺️",
    layout="wide"
)

st.title("🗺️ Dashboard Analisis Spasial - Proyek ILASPP")
st.markdown("Integrasi GWR (Geographically Weighted Regression) dan Kriging Interpolation")

# =====================================================
# LOAD DATA
# =====================================================

@st.cache_data
def load_gwr_data():
    csv_path = "koefisien_gwr_ilaspp.csv"
    coord_path = "koordinat_wilayah.csv"
    
    df = pd.read_csv(csv_path)
    df_coord = pd.read_csv(coord_path)
    df = df.merge(df_coord, on='Kabupaten', how='left')
    
    df['Koefisien_Lebar_Jalan'] = pd.to_numeric(df['Koefisien_Lebar_Jalan'], errors='coerce')
    df['Koefisien_Jarak'] = pd.to_numeric(df['Koefisien_Jarak'], errors='coerce')
    
    return df

@st.cache_data
def load_kriging_data():
    csv_path = "kriging_results.csv"
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        return df
    else:
        return None

# Load data
df_gwr = load_gwr_data()
df_kriging = load_kriging_data()

# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.header("🔍 Navigasi")
page = st.sidebar.radio(
    "Pilih Halaman",
    ["📍 GWR Analysis", "🗺️ Kriging Interpolation", "📋 Tabel & Rekomendasi"]
)

# =====================================================
# PAGE 1: GWR ANALYSIS
# =====================================================

if page == "📍 GWR Analysis":
    st.header("📍 Geographically Weighted Regression (GWR)")
    st.markdown("Analisis pengaruh lebar jalan dan jarak ke pusat kota terhadap harga tanah")
    
    # Filter
    selected = st.multiselect("Pilih Kabupaten/Kota", options=df_gwr['Kabupaten'].tolist(), default=df_gwr['Kabupaten'].tolist())
    filtered = df_gwr[df_gwr['Kabupaten'].isin(selected)]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🗺️ Peta Koefisien Lebar Jalan")
        if not filtered['Latitude'].isna().all():
            center_lat = filtered['Latitude'].mean()
            center_lon = filtered['Longitude'].mean()
            m = folium.Map(location=[center_lat, center_lon], zoom_start=7)
            for _, row in filtered.iterrows():
                color = 'darkred' if row['Koefisien_Lebar_Jalan'] > 0.065 else 'orange' if row['Koefisien_Lebar_Jalan'] > 0.060 else 'green'
                popup = f"<b>{row['Kabupaten']}</b><br>Koef. Jalan: {row['Koefisien_Lebar_Jalan']:.4f}<br>Koef. Jarak: {row['Koefisien_Jarak']:.4f}"
                folium.CircleMarker([row['Latitude'], row['Longitude']], radius=8, color=color, fill=True, popup=popup).add_to(m)
            map_html = m._repr_html_()
            html(map_html, height=450, width=500)
    
    with col2:
        st.subheader("📊 Ranking Koefisien Lebar Jalan")
        fig = px.bar(filtered.sort_values('Koefisien_Lebar_Jalan'), x='Koefisien_Lebar_Jalan', y='Kabupaten', orientation='h', color='Koefisien_Lebar_Jalan', color_continuous_scale='Reds')
        fig.update_layout(height=450)
        st.plotly_chart(fig, use_container_width=True)

# =====================================================
# PAGE 2: KRIGING INTERPOLATION (DENGAN FOLIUM HEATMAP)
# =====================================================

elif page == "🗺️ Kriging Interpolation":
    st.header("🗺️ Kriging Interpolation")
    st.markdown("Interpolasi spasial untuk memprediksi harga tanah di lokasi tanpa data sampel")
    
    if df_kriging is not None and len(df_kriging) > 0:
        
        # Informasi statistik
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        with col_stat1:
            st.metric("📊 Titik Grid", f"{len(df_kriging):,}")
        with col_stat2:
            st.metric("📈 Rata-rata Prediksi", f"{df_kriging['prediksi'].mean():.2f}")
        with col_stat3:
            st.metric("📉 Min Prediksi", f"{df_kriging['prediksi'].min():.2f}")
        with col_stat4:
            st.metric("📈 Max Prediksi", f"{df_kriging['prediksi'].max():.2f}")
        
        st.markdown("---")
        
        # Pilihan tampilan
        map_type = st.radio(
            "Pilih Jenis Peta",
            ["🔥 Heatmap Prediksi", "⚠️ Heatmap Ketidakpastian (Variance)", "📍 Scatter Plot Titik Grid"],
            horizontal=True
        )
        
        # Buat peta folium
        center_lat = df_kriging['latitude'].mean()
        center_lon = df_kriging['longitude'].mean()
        m = folium.Map(location=[center_lat, center_lon], zoom_start=7, control_scale=True)
        folium.TileLayer('CartoDB positron', name='Light Map', control=True).add_to(m)
        
        if map_type == "🔥 Heatmap Prediksi":
            # Heatmap untuk prediksi
            from folium.plugins import HeatMap
            heat_data = [[row['latitude'], row['longitude'], row['prediksi']] for _, row in df_kriging.iterrows()]
            HeatMap(heat_data, radius=10, blur=15, max_zoom=10, name='Prediksi Kriging').add_to(m)
            st.info("💡 **Semakin merah/terang = semakin tinggi nilai prediksi harga tanah**")
            
        elif map_type == "⚠️ Heatmap Ketidakpastian (Variance)":
            # Heatmap untuk variance
            from folium.plugins import HeatMap
            heat_data = [[row['latitude'], row['longitude'], row['variance']] for _, row in df_kriging.iterrows()]
            HeatMap(heat_data, radius=10, blur=15, max_zoom=10, name='Variance Kriging', gradient={0.2: 'green', 0.5: 'yellow', 0.8: 'red'}).add_to(m)
            st.info("💡 **Semakin merah/terang = semakin tinggi ketidakpastian prediksi**")
            
        else:
            # Scatter plot dengan lingkaran warna
            for _, row in df_kriging.sample(min(500, len(df_kriging))).iterrows():
                color = 'red' if row['prediksi'] > df_kriging['prediksi'].quantile(0.75) else 'orange' if row['prediksi'] > df_kriging['prediksi'].quantile(0.5) else 'green'
                folium.CircleMarker(
                    location=[row['latitude'], row['longitude']],
                    radius=3,
                    color=color,
                    fill=True,
                    fill_opacity=0.5,
                    popup=f"Prediksi: {row['prediksi']:.2f}"
                ).add_to(m)
            st.info("💡 **Setiap titik mewakili satu titik grid hasil interpolasi Kriging**")
        
        folium.LayerControl().add_to(m)
        map_html = m._repr_html_()
        html(map_html, height=550, width=800)
        
        # Tambahkan interpretasi
        st.markdown("---")
        st.subheader("📖 Interpretasi Hasil Kriging")
        
        if map_type == "🔥 Heatmap Prediksi":
            st.write("""
            - **Area merah/terang** menunjukkan prediksi harga tanah yang **lebih tinggi**
            - **Area biru/hijau** menunjukkan prediksi harga tanah yang **lebih rendah**
            - Pola ini konsisten dengan hasil GWR: daerah dekat Surabaya cenderung lebih merah (harga tinggi)
            """)
        elif map_type == "⚠️ Heatmap Ketidakpastian (Variance)":
            st.write("""
            - **Area merah/terang** menunjukkan **ketidakpastian tinggi** (prediksi kurang bisa diandalkan)
            - **Area hijau/gelap** menunjukkan **prediksi lebih pasti**
            - **Rekomendasi:** Tambahkan titik sampel di area dengan variance tinggi untuk meningkatkan akurasi model
            """)
        
        # Tabel sample hasil
        with st.expander("📋 Lihat Detail Data Kriging (Sample 100 titik)"):
            st.dataframe(df_kriging.head(100), use_container_width=True)
        
    else:
        st.warning("⚠️ File kriging_results.csv tidak ditemukan. Jalankan script export_kriging_results.py terlebih dahulu di environment kriging_env.")
        st.code("""
# Jalankan di terminal:
conda activate kriging_env
cd "/Users/macos/Study_burhanudin_2025/Data Analytics/Portfolio Project/hybrid-dashboard"
python export_kriging_results.py
        """)

# =====================================================
# PAGE 3: TABEL & REKOMENDASI
# =====================================================

else:
    st.header("📋 Tabel Koefisien GWR dan Rekomendasi Kebijakan")
    
    display_df = df_gwr[['Kabupaten', 'Provinsi', 'Koefisien_Lebar_Jalan', 'Koefisien_Jarak']].copy()
    display_df.columns = ['Kabupaten', 'Provinsi', 'Koef. Lebar Jalan', 'Koef. Jarak']
    display_df['Koef. Lebar Jalan'] = display_df['Koef. Lebar Jalan'].round(4)
    display_df['Koef. Jarak'] = display_df['Koef. Jarak'].round(4)
    
    st.dataframe(display_df, use_container_width=True)
    
    # Rekomendasi
    st.subheader("💡 Rekomendasi Kebijakan")
    
    top_jalan = df_gwr.nlargest(3, 'Koefisien_Lebar_Jalan')[['Kabupaten', 'Koefisien_Lebar_Jalan']]
    top_jarak = df_gwr.nsmallest(3, 'Koefisien_Jarak')[['Kabupaten', 'Koefisien_Jarak']]
    
    st.write("**🔴 Prioritas Pelebaran Jalan:**")
    for _, row in top_jalan.iterrows():
        st.write(f"   - {row['Kabupaten']}: {row['Koefisien_Lebar_Jalan']:.4f}")
    
    st.write("**🟡 Prioritas Pusat Pertumbuhan Baru (Paling Tergantung Jarak):**")
    for _, row in top_jarak.iterrows():
        st.write(f"   - {row['Kabupaten']}: {row['Koefisien_Jarak']:.4f}")

# =====================================================
# FOOTER
# =====================================================

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "© 2026 Burhanudin Badiuzaman | Dashboard GWR + Kriging - Proyek ILASPP<br>"
    f"🕒 Terakhir diperbarui: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')} WIB"
    "</div>", 
    unsafe_allow_html=True
)