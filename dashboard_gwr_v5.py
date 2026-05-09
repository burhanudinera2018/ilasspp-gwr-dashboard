# =====================================================
# DASHBOARD GWR - DENGAN HANDLING DATA KOSONG
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
    page_title="Dashboard GWR - ILASPP",
    page_icon="🗺️",
    layout="wide"
)

st.title("🗺️ Dashboard Analisis GWR - Proyek ILASPP")
st.markdown("---")

# =====================================================
# LOAD DATA
# =====================================================

@st.cache_data
def load_data():
    csv_path = "koefisien_gwr_ilaspp.csv"
    
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        st.success(f"✅ Data berhasil dimuat dari {csv_path}")
        
        # Rename kolom
        df = df.rename(columns={
            'Kabupaten': 'Kabupaten',
            'Koefisien_Lebar_Jalan': 'Koef_Lebar_Jalan',
            'Koefisien_Jarak': 'Koef_Jarak',
            'Local_R2': 'Local_R2'
        })
    else:
        st.error(f"❌ File {csv_path} tidak ditemukan!")
        st.stop()
    
    # =====================================================
    # DATA KOORDINAT LENGKAP (SEMUA KABUPATEN DARI CSV)
    # =====================================================
    
    koordinat = {
        'Kabupaten': [
            'Kota Kediri', 'Kabupaten Kediri', 'Kota Surabaya', 'Kabupaten Sidoarjo',
            'Kota Malang', 'Kabupaten Malang', 'Kota Blitar', 'Kabupaten Blitar',
            'Kota Probolinggo', 'Kabupaten Probolinggo', 'Kota Pasuruan', 
            'Kabupaten Pasuruan', 'Kota Mojokerto', 'Kabupaten Mojokerto', 
            'Kota Madiun', 'Kabupaten Madiun', 'Kabupaten Jombang', 
            'Kabupaten Nganjuk', 'Kabupaten Tulungagung', 'Kabupaten Trenggalek'
        ],
        'Latitude': [
            -7.8169, -7.7833, -7.2575, -7.4531, -7.9666, -8.1667, -8.1000, -8.1333,
            -7.7500, -7.7833, -7.6500, -7.7000, -7.4667, -7.5000, -7.6333, -7.6667,
            -7.5500, -7.6000, -8.0667, -8.2333
        ],
        'Longitude': [
            112.0168, 112.0833, 112.7521, 112.7167, 112.6326, 112.6667, 112.1667,
            112.2000, 113.2167, 113.2500, 112.9500, 112.9833, 112.4833, 112.5167,
            111.5333, 111.5667, 112.2333, 112.0167, 111.9000, 111.7667
        ]
    }
    df_koordinat = pd.DataFrame(koordinat)
    
    # Gabungkan data
    df = df.merge(df_koordinat, on='Kabupaten', how='left')
    
    # Cek data yang tidak memiliki koordinat
    missing_coords = df[df['Latitude'].isna()]
    if len(missing_coords) > 0:
        st.warning(f"⚠️ {len(missing_coords)} kabupaten tidak memiliki koordinat dan akan dikeluarkan dari peta")
        st.write("Kabupaten yang tidak memiliki koordinat:", missing_coords['Kabupaten'].tolist())
    
    # Hapus baris dengan koordinat kosong untuk peta
    df_map = df.dropna(subset=['Latitude', 'Longitude']).copy()
    
    # Isi nilai yang mungkin kosong di kolom lain
    df['Koef_Lebar_Jalan'] = pd.to_numeric(df['Koef_Lebar_Jalan'], errors='coerce').fillna(0.06)
    df['Koef_Jarak'] = pd.to_numeric(df['Koef_Jarak'], errors='coerce').fillna(-0.005)
    df['Local_R2'] = pd.to_numeric(df['Local_R2'], errors='coerce').fillna(0.95)
    
    df_map['Koef_Lebar_Jalan'] = pd.to_numeric(df_map['Koef_Lebar_Jalan'], errors='coerce').fillna(0.06)
    df_map['Koef_Jarak'] = pd.to_numeric(df_map['Koef_Jarak'], errors='coerce').fillna(-0.005)
    
    # Tambah kolom rekomendasi
    df['Rekomendasi'] = df.apply(lambda row: 
        '🔴 Prioritas jalan + pusat pertumbuhan' if (row['Koef_Lebar_Jalan'] > 0.064 and abs(row['Koef_Jarak']) > 0.006)
        else '🟠 Prioritas pelebaran jalan' if row['Koef_Lebar_Jalan'] > 0.064
        else '🟡 Prioritas pusat pertumbuhan baru' if abs(row['Koef_Jarak']) > 0.006
        else '🟢 Pertahankan fasilitas lokal', axis=1)
    
    df_map['Rekomendasi'] = df_map.apply(lambda row: 
        '🔴 Prioritas jalan + pusat pertumbuhan' if (row['Koef_Lebar_Jalan'] > 0.064 and abs(row['Koef_Jarak']) > 0.006)
        else '🟠 Prioritas pelebaran jalan' if row['Koef_Lebar_Jalan'] > 0.064
        else '🟡 Prioritas pusat pertumbuhan baru' if abs(row['Koef_Jarak']) > 0.006
        else '🟢 Pertahankan fasilitas lokal', axis=1)
    
    return df, df_map

df, df_map = load_data()

# =====================================================
# SIDEBAR FILTER
# =====================================================

st.sidebar.header("🔍 Filter Data")
selected_kabupaten = st.sidebar.multiselect(
    "Pilih Kabupaten/Kota",
    options=df['Kabupaten'].tolist(),
    default=df['Kabupaten'].tolist()
)

filtered_df = df[df['Kabupaten'].isin(selected_kabupaten)]
filtered_map_df = df_map[df_map['Kabupaten'].isin(selected_kabupaten)]

# =====================================================
# METRIC CARDS
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
    st.metric("📈 Rata-rata Koef. Lebar Jalan", f"{filtered_df['Koef_Lebar_Jalan'].mean():.4f}")

st.markdown("---")

# =====================================================
# PETA INTERAKTIF (HANYA JIKA ADA DATA)
# =====================================================

st.subheader("🗺️ Peta Koefisien Lebar Jalan")

if len(filtered_map_df) == 0:
    st.warning("⚠️ Tidak ada data dengan koordinat lengkap untuk ditampilkan di peta.")
else:
    center_lat = filtered_map_df['Latitude'].mean()
    center_lon = filtered_map_df['Longitude'].mean()
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=8, control_scale=True)
    
    for idx, row in filtered_map_df.iterrows():
        # Tentukan warna
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
        
        # Radius minimal 5, maksimal 20
        radius = max(5, min(20, row['Koef_Lebar_Jalan'] * 100))
        
        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            popup=folium.Popup(popup_text, max_width=300)
        ).add_to(m)
    
    map_html = m._repr_html_()
    html(map_html, height=500, width=700)

st.markdown("---")

# =====================================================
# BAR CHART
# =====================================================

st.subheader("📊 Ranking Pengaruh Lebar Jalan per Kabupaten")

fig = px.bar(filtered_df.sort_values('Koef_Lebar_Jalan', ascending=True),
             x='Koef_Lebar_Jalan',
             y='Kabupaten',
             orientation='h',
             color='Koef_Lebar_Jalan',
             color_continuous_scale='Plasma',
             title='Semakin ke kanan, semakin kuat pengaruh lebar jalan terhadap harga tanah',
             labels={'Koef_Lebar_Jalan': 'Koefisien Regresi', 'Kabupaten': ''})

fig.update_layout(height=500, margin=dict(l=0, r=0, t=50, b=0))
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# =====================================================
# TABEL DATA
# =====================================================

st.subheader("📋 Tabel Koefisien GWR dan Rekomendasi Kebijakan")

display_df = filtered_df[['Kabupaten', 'Koef_Lebar_Jalan', 'Koef_Jarak', 'Local_R2', 'Rekomendasi']].copy()
display_df.columns = ['Kabupaten', 'Koef. Lebar Jalan', 'Koef. Jarak', 'Local R²', 'Rekomendasi Kebijakan']
display_df['Koef. Lebar Jalan'] = display_df['Koef. Lebar Jalan'].round(4)
display_df['Koef. Jarak'] = display_df['Koef. Jarak'].round(4)
display_df['Local R²'] = display_df['Local R²'].round(4)

st.dataframe(display_df, use_container_width=True)

# =====================================================
# DOWNLOAD
# =====================================================

st.markdown("---")
st.subheader("📥 Download Data")

csv_data = display_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📎 Download Tabel sebagai CSV",
    data=csv_data,
    file_name="hasil_gwr_ilaspp.csv",
    mime="text/csv"
)

# =====================================================
# FOOTER
# =====================================================

st.markdown("---")
st.caption("📌 Dashboard Proyek ILASPP - Analisis Geographically Weighted Regression (GWR)")
st.caption(f"🕒 Terakhir diperbarui: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")