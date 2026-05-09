# =====================================================
# DASHBOARD GWR - V7 (MEMBACA KOORDINAT DARI FILE CSV)
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
    coord_path = "koordinat_wilayah.csv"
    
    # Baca file koefisien GWR
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        st.success(f"✅ Data koefisien berhasil dimuat dari {csv_path}")
        
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
    
    # Baca file koordinat
    if os.path.exists(coord_path):
        df_coord = pd.read_csv(coord_path)
        st.success(f"✅ Data koordinat berhasil dimuat dari {coord_path}")
        
        # Gabungkan data koefisien dengan koordinat
        df = df.merge(df_coord, on='Kabupaten', how='left')
    else:
        st.warning(f"⚠️ File {coord_path} tidak ditemukan. Peta tidak dapat ditampilkan.")
        df['Latitude'] = None
        df['Longitude'] = None
    
    # Isi nilai yang mungkin kosong
    df['Koef_Lebar_Jalan'] = pd.to_numeric(df['Koef_Lebar_Jalan'], errors='coerce').fillna(0.06)
    df['Koef_Jarak'] = pd.to_numeric(df['Koef_Jarak'], errors='coerce').fillna(-0.005)
    df['Local_R2'] = pd.to_numeric(df['Local_R2'], errors='coerce').fillna(0.95)
    
    # Tambah kolom rekomendasi
    def get_rekomendasi(row):
        if row['Koef_Lebar_Jalan'] > 0.064 and abs(row['Koef_Jarak']) > 0.006:
            return '🔴 Prioritas jalan + pusat pertumbuhan'
        elif row['Koef_Lebar_Jalan'] > 0.064:
            return '🟠 Prioritas pelebaran jalan'
        elif abs(row['Koef_Jarak']) > 0.006:
            return '🟡 Prioritas pusat pertumbuhan baru'
        else:
            return '🟢 Pertahankan fasilitas lokal'
    
    df['Rekomendasi'] = df.apply(get_rekomendasi, axis=1)
    
    # Hitung jumlah kabupaten yang memiliki koordinat
    has_coord = df['Latitude'].notna().sum()
    total = len(df)
    st.info(f"📌 {has_coord} dari {total} kabupaten/kota memiliki koordinat untuk ditampilkan di peta.")
    
    return df

df = load_data()

# Filter data yang memiliki koordinat untuk peta
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

if len(filtered_df) > 0:
    top_3_lebar = filtered_df.nlargest(3, 'Koef_Lebar_Jalan')[['Kabupaten', 'Koef_Lebar_Jalan']]
    bottom_3_lebar = filtered_df.nsmallest(3, 'Koef_Lebar_Jalan')[['Kabupaten', 'Koef_Lebar_Jalan']]
    
    st.write("**📈 Wilayah dengan pengaruh lebar jalan TERTINGGI:**")
    for _, row in top_3_lebar.iterrows():
        st.write(f"- {row['Kabupaten']}: {row['Koef_Lebar_Jalan']:.4f}")
    
    st.write("**📉 Wilayah dengan pengaruh lebar jalan TERENDAH:**")
    for _, row in bottom_3_lebar.iterrows():
        st.write(f"- {row['Kabupaten']}: {row['Koef_Lebar_Jalan']:.4f}")
    
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