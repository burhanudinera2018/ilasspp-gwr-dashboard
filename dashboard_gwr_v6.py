# =====================================================
# DASHBOARD GWR - V6 (DENGAN KOORDINAT LENGKAP)
# SEMUA KABUPATEN/KOTA MEMILIKI KOORDINAT UNTUK PETA
# =====================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit.components.v1 import html
import os

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
    # DATA KOORDINAT LENGKAP (SEMUA WILAYAH YANG MUNGKIN ADA)
    # =====================================================
    
    koordinat = {
        'Kabupaten': [
            # Jawa Timur
            'Kota Kediri', 'Kabupaten Kediri', 'Kota Surabaya', 'Kabupaten Sidoarjo',
            'Kota Malang', 'Kabupaten Malang', 'Kota Blitar', 'Kabupaten Blitar',
            'Kota Probolinggo', 'Kabupaten Probolinggo', 'Kota Pasuruan', 
            'Kabupaten Pasuruan', 'Kota Mojokerto', 'Kabupaten Mojokerto', 
            'Kota Madiun', 'Kabupaten Madiun', 'Kabupaten Jombang', 
            'Kabupaten Nganjuk', 'Kabupaten Tulungagung', 'Kabupaten Trenggalek',
            'Kota Batu', 'Kabupaten Lumajang', 'Kabupaten Jember', 'Kabupaten Banyuwangi',
            'Kabupaten Bondowoso', 'Kabupaten Situbondo', 'Kabupaten Sumenep',
            # Jawa Tengah
            'Kota Semarang', 'Kabupaten Semarang', 'Kota Surakarta', 'Kabupaten Sukoharjo',
            'Kota Magelang', 'Kabupaten Magelang', 'Kota Pekalongan', 'Kabupaten Pekalongan',
            'Kota Tegal', 'Kabupaten Tegal', 'Kota Salatiga', 'Kabupaten Boyolali',
            'Kabupaten Klaten', 'Kabupaten Wonogiri', 'Kabupaten Karanganyar',
            'Kabupaten Sragen', 'Kabupaten Grobogan', 'Kabupaten Demak', 'Kabupaten Kudus',
            'Kabupaten Jepara', 'Kabupaten Pati', 'Kabupaten Rembang', 'Kabupaten Blora',
            # DIY Yogyakarta
            'Kota Yogyakarta', 'Kabupaten Sleman', 'Kabupaten Bantul', 
            'Kabupaten Gunungkidul', 'Kabupaten Kulon Progo',
            # Jawa Barat
            'Kota Bandung', 'Kabupaten Bandung', 'Kota Bekasi', 'Kabupaten Bekasi',
            'Kota Bogor', 'Kabupaten Bogor', 'Kota Depok', 'Kabupaten Depok',
            'Kota Cirebon', 'Kabupaten Cirebon', 'Kota Sukabumi', 'Kabupaten Sukabumi',
            'Kota Tasikmalaya', 'Kabupaten Tasikmalaya', 'Kota Cimahi',
            'Kabupaten Karawang', 'Kabupaten Purwakarta', 'Kabupaten Subang',
            'Kabupaten Indramayu', 'Kabupaten Majalengka', 'Kabupaten Kuningan',
            'Kabupaten Garut', 'Kabupaten Ciamis', 'Kabupaten Pangandaran'
        ],
        'Latitude': [
            # JATIM
            -7.8169, -7.7833, -7.2575, -7.4531, -7.9666, -8.1667, -8.1000, -8.1333,
            -7.7500, -7.7833, -7.6500, -7.7000, -7.4667, -7.5000, -7.6333, -7.6667,
            -7.5500, -7.6000, -8.0667, -8.2333, -7.8667, -8.1333, -8.1667, -8.2167,
            -7.9333, -7.7167, -7.0000,
            # JATENG
            -7.0051, -7.2000, -7.5750, -7.6833, -7.4700, -7.5000, -6.8833, -6.9000,
            -6.8667, -6.8667, -7.3167, -7.5333, -7.7000, -7.8000, -7.6000, -7.4167,
            -7.1167, -6.8833, -6.8000, -6.5833, -6.7500, -6.8667, -7.0000,
            # DIY
            -7.7956, -7.7167, -7.8833, -7.9667, -7.8333,
            # JABAR
            -6.9175, -6.9500, -6.2383, -6.2500, -6.5971, -6.5667, -6.3936, -6.4000,
            -6.7167, -6.7167, -6.9167, -6.9167, -7.3333, -7.3333, -6.8833, -6.3000,
            -6.5500, -6.5667, -6.3167, -6.3333, -7.0000, -6.9833, -7.2167, -7.1000, -7.6833
        ],
        'Longitude': [
            # JATIM
            112.0168, 112.0833, 112.7521, 112.7167, 112.6326, 112.6667, 112.1667,
            112.2000, 113.2167, 113.2500, 112.9500, 112.9833, 112.4833, 112.5167,
            111.5333, 111.5667, 112.2333, 112.0167, 111.9000, 111.7667, 112.5167,
            113.2167, 113.7000, 114.3667, 113.8333, 114.0000, 113.8667,
            # JATENG
            110.4403, 110.3500, 110.8167, 110.8333, 110.2167, 110.2167, 109.6667, 109.6667,
            109.1333, 109.1333, 110.5000, 110.6000, 110.6667, 110.9167, 110.9500, 110.9833,
            110.9667, 110.6167, 110.8333, 110.6667, 110.8333, 111.4167, 111.2833,
            # DIY
            110.3695, 110.3500, 110.3667, 110.3500, 110.1667,
            # JABAR
            107.6191, 107.5500, 107.0000, 107.0000, 106.8060, 106.7333, 106.8167, 106.8000,
            108.5667, 108.5500, 106.9333, 106.9333, 108.2167, 108.2167, 107.5500, 107.3000,
            107.4500, 107.4833, 107.7167, 107.7667, 108.2167, 108.2000, 108.3333, 108.5500, 108.6500
        ]
    }
    
    df_koordinat = pd.DataFrame(koordinat)
    
    # Gabungkan data (hanya kabupaten yang ada di df)
    df = df.merge(df_koordinat, on='Kabupaten', how='left')
    
    # Cek apakah ada kabupaten yang tidak memiliki koordinat
    missing_coords = df[df['Latitude'].isna()]
    if len(missing_coords) > 0:
        st.warning(f"⚠️ {len(missing_coords)} kabupaten tidak memiliki koordinat (tidak akan ditampilkan di peta):")
        st.write(missing_coords['Kabupaten'].tolist())
    
    # Isi nilai yang mungkin kosong
    df['Koef_Lebar_Jalan'] = pd.to_numeric(df['Koef_Lebar_Jalan'], errors='coerce').fillna(0.06)
    df['Koef_Jarak'] = pd.to_numeric(df['Koef_Jarak'], errors='coerce').fillna(-0.005)
    df['Local_R2'] = pd.to_numeric(df['Local_R2'], errors='coerce').fillna(0.95)
    
    # Tambah kolom rekomendasi
    df['Rekomendasi'] = df.apply(lambda row: 
        '🔴 Prioritas jalan + pusat pertumbuhan' if (row['Koef_Lebar_Jalan'] > 0.064 and abs(row['Koef_Jarak']) > 0.006)
        else '🟠 Prioritas pelebaran jalan' if row['Koef_Lebar_Jalan'] > 0.064
        else '🟡 Prioritas pusat pertumbuhan baru' if abs(row['Koef_Jarak']) > 0.006
        else '🟢 Pertahankan fasilitas lokal', axis=1)
    
    return df

df = load_data()

# Filter hanya data yang memiliki koordinat untuk peta
df_map = df.dropna(subset=['Latitude', 'Longitude']).copy()

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
# PETA INTERAKTIF
# =====================================================

st.subheader("🗺️ Peta Koefisien Lebar Jalan")

if len(filtered_map_df) == 0:
    st.warning("⚠️ Tidak ada data dengan koordinat lengkap untuk ditampilkan di peta.")
else:
    center_lat = filtered_map_df['Latitude'].mean()
    center_lon = filtered_map_df['Longitude'].mean()
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=7, control_scale=True)
    
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
        <b>Local R²:</b> {row['Local_R2']:.4f}<br>
        <b>Rekomendasi:</b> {row['Rekomendasi']}
        """
        
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
    
    # Tambahkan tile layer yang lebih bagus
    folium.TileLayer('CartoDB positron', name='Light Map', control=False).add_to(m)
    
    map_html = m._repr_html_()
    html(map_html, height=550, width=800)

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

fig.update_layout(height=max(400, len(filtered_df) * 20), margin=dict(l=0, r=0, t=50, b=0))
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
# INSIGHT OTOMATIS
# =====================================================

st.markdown("---")
st.subheader("💡 Insight Otomatis dari Data")

# Hitung beberapa insight
top_3_lebar = filtered_df.nlargest(3, 'Koef_Lebar_Jalan')[['Kabupaten', 'Koef_Lebar_Jalan']]
bottom_3_lebar = filtered_df.nsmallest(3, 'Koef_Lebar_Jalan')[['Kabupaten', 'Koef_Lebar_Jalan']]

st.write("**📈 Wilayah dengan pengaruh lebar jalan TERTINGGI:**")
for _, row in top_3_lebar.iterrows():
    st.write(f"- {row['Kabupaten']}: {row['Koef_Lebar_Jalan']:.4f}")

st.write("**📉 Wilayah dengan pengaruh lebar jalan TERENDAH:**")
for _, row in bottom_3_lebar.iterrows():
    st.write(f"- {row['Kabupaten']}: {row['Koef_Lebar_Jalan']:.4f}")

# Hitung rekomendasi
rekom_counts = filtered_df['Rekomendasi'].value_counts()
st.write("**📊 Distribusi Rekomendasi Kebijakan:**")
for rec, count in rekom_counts.items():
    st.write(f"- {rec}: {count} kabupaten/kota")

# =====================================================
# FOOTER
# =====================================================

st.markdown("---")
st.caption("📌 Dashboard Proyek ILASPP - Analisis Geographically Weighted Regression (GWR)")
st.caption(f"🕒 Terakhir diperbarui: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")