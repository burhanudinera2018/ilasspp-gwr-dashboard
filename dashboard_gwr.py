# =====================================================
# DASHBOARD INTERAKTIF HASIL GWR - PROYEK ILASPP
# =====================================================
# Letakkan file ini di root folder hybrid-dashboard
# Jalankan: streamlit run dashboard_gwr.py
# =====================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
import os

# Konfigurasi halaman
st.set_page_config(
    page_title="Dashboard GWR - ILASPP",
    page_icon="🗺️",
    layout="wide"
)

# Judul
st.title("🗺️ Dashboard Analisis GWR - Proyek ILASPP")
st.markdown("---")

# =====================================================
# LOAD DATA DARI CSV (MEMBACA FILE YANG SUDAH ADA)
# =====================================================

@st.cache_data
def load_data():
    # Cek apakah file CSV ada
    csv_path = "koefisien_gwr_ilaspp.csv"
    
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        st.success(f"✅ Data berhasil dimuat dari {csv_path}")
    else:
        # Fallback data jika file tidak ditemukan
        st.warning(f"⚠️ File {csv_path} tidak ditemukan. Menggunakan data contoh.")
        data = {
            'Kabupaten': ['Kota Kediri', 'Kabupaten Kediri', 'Kota Surabaya', 'Kabupaten Sidoarjo', 
                          'Kota Malang', 'Kabupaten Malang'],
            'Koef_Lebar_Jalan': [0.0641, 0.0641, 0.0579, 0.0612, 0.0623, 0.0605],
            'Koef_Jarak': [-0.00568, -0.00568, -0.00065, -0.00380, -0.00420, -0.00460],
            'Latitude': [-7.8169, -7.7833, -7.2575, -7.4531, -7.9666, -8.1667],
            'Longitude': [112.0168, 112.0833, 112.7521, 112.7167, 112.6326, 112.6667]
        }
        df = pd.DataFrame(data)
    
    # Tambah kolom rekomendasi
    df['Rekomendasi'] = df.apply(lambda row: 
        '🔴 Prioritas jalan + pusat pertumbuhan' if (row['Koef_Lebar_Jalan'] > 0.064 and abs(row['Koef_Jarak']) > 0.006)
        else '🟠 Prioritas pelebaran jalan' if row['Koef_Lebar_Jalan'] > 0.064
        else '🟡 Prioritas pusat pertumbuhan baru' if abs(row['Koef_Jarak']) > 0.006
        else '🟢 Pertahankan fasilitas lokal', axis=1)
    
    return df

df = load_data()

# =====================================================
# SIDEBAR - FILTER
# =====================================================

st.sidebar.header("🔍 Filter Data")
selected_kabupaten = st.sidebar.multiselect(
    "Pilih Kabupaten/Kota",
    options=df['Kabupaten'].tolist(),
    default=df['Kabupaten'].tolist()
)

# Filter data
filtered_df = df[df['Kabupaten'].isin(selected_kabupaten)]

# =====================================================
# METRIC CARDS (Ringkasan Statistik)
# =====================================================

st.subheader("📊 Ringkasan Statistik GWR")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📌 Jumlah Sampel", len(filtered_df))

with col2:
    st.metric("📏 Bandwidth Optimal", "186.22 meter")

with col3:
    st.metric("🎯 R-squared Global", "0.969 (96.9%)")

with col4:
    st.metric("📈 Koef. Lebar Jalan (rata-rata)", 
              f"{filtered_df['Koef_Lebar_Jalan'].mean():.4f}")

st.markdown("---")

# =====================================================
# LAYOUT 2 KOLOM: MAP + BAR CHART
# =====================================================

col_map, col_chart = st.columns(2)

with col_map:
    st.subheader("🗺️ Peta Koefisien Lebar Jalan")
    
    # Hitung pusat peta
    center_lat = filtered_df['Latitude'].mean()
    center_lon = filtered_df['Longitude'].mean()
    
    # Buat peta folium
    m = folium.Map(location=[center_lat, center_lon], zoom_start=8, control_scale=True)
    
    # Tambahkan marker untuk setiap kabupaten
    for idx, row in filtered_df.iterrows():
        # Tentukan warna berdasarkan koefisien
        if row['Koef_Lebar_Jalan'] > 0.064:
            color = 'red'
        elif row['Koef_Lebar_Jalan'] > 0.060:
            color = 'orange'
        else:
            color = 'green'
        
        popup_text = f"""
        <b>{row['Kabupaten']}</b><br>
        <b>Koefisien Lebar Jalan:</b> {row['Koef_Lebar_Jalan']:.4f}<br>
        <b>Koefisien Jarak:</b> {row['Koef_Jarak']:.4f}<br>
        <b>Rekomendasi:</b> {row['Rekomendasi']}
        """
        
        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=row['Koef_Lebar_Jalan'] * 100,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            popup=folium.Popup(popup_text, max_width=300)
        ).add_to(m)
    
    # Tampilkan peta
    st_folium(m, width=500, height=400)

with col_chart:
    st.subheader("📊 Ranking Pengaruh Lebar Jalan")
    
    # Bar chart dengan plotly
    fig = px.bar(filtered_df.sort_values('Koef_Lebar_Jalan', ascending=True),
                 x='Koef_Lebar_Jalan',
                 y='Kabupaten',
                 orientation='h',
                 color='Koef_Lebar_Jalan',
                 color_continuous_scale='Plasma',
                 title='Semakin ke kanan, semakin kuat pengaruh lebar jalan',
                 labels={'Koef_Lebar_Jalan': 'Koefisien', 'Kabupaten': ''})
    
    fig.update_layout(height=500, margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# =====================================================
# TABEL DATA + REKOMENDASI
# =====================================================

st.subheader("📋 Tabel Koefisien GWR dan Rekomendasi Kebijakan")

# Format tabel untuk ditampilkan
display_df = filtered_df[['Kabupaten', 'Koef_Lebar_Jalan', 'Koef_Jarak', 'Rekomendasi']].copy()
display_df.columns = ['Kabupaten', 'Koef. Lebar Jalan', 'Koef. Jarak', 'Rekomendasi Kebijakan']
display_df['Koef. Lebar Jalan'] = display_df['Koef. Lebar Jalan'].round(4)
display_df['Koef. Jarak'] = display_df['Koef. Jarak'].round(4)

st.dataframe(display_df, use_container_width=True)

# =====================================================
# DOWNLOAD BUTTON
# =====================================================

st.markdown("---")
st.subheader("📥 Download Data")

csv = display_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📎 Download Tabel sebagai CSV",
    data=csv,
    file_name="hasil_gwr_ilaspp.csv",
    mime="text/csv"
)

st.caption("📌 Dashboard ini dibuat untuk Proyek ILASPP - Analisis GWR Pengaruh Lebar Jalan dan Jarak terhadap Harga Tanah")