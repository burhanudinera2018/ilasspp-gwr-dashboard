# =====================================================
# DASHBOARD GWR - REAL DATA dari R
# Proyek ILASPP
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
# LOAD DATA REAL DARI HASIL R
# =====================================================

@st.cache_data
def load_data():
    csv_path = "koefisien_gwr_ilaspp.csv"
    coord_path = "koordinat_wilayah.csv"
    
    # Baca file koefisien GWR (hasil dari R)
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        st.success(f"✅ Data koefisien GWR (hasil R) berhasil dimuat: {len(df)} kabupaten")
    else:
        st.error(f"❌ File {csv_path} tidak ditemukan!")
        st.stop()
    
    # Baca file koordinat
    if os.path.exists(coord_path):
        df_coord = pd.read_csv(coord_path)
        st.success(f"✅ Data koordinat berhasil dimuat: {len(df_coord)} lokasi")
        
        # Gabungkan data koefisien dengan koordinat
        df = df.merge(df_coord, on='Kabupaten', how='left')
    else:
        st.warning(f"⚠️ File {coord_path} tidak ditemukan. Peta tidak dapat ditampilkan.")
        df['Latitude'] = None
        df['Longitude'] = None
    
    # Bersihkan data
    df['Koefisien_Lebar_Jalan'] = pd.to_numeric(df['Koefisien_Lebar_Jalan'], errors='coerce')
    df['Koefisien_Jarak'] = pd.to_numeric(df['Koefisien_Jarak'], errors='coerce')
    df['Local_R2'] = pd.to_numeric(df['Local_R2'], errors='coerce')
    
    # Tambah kolom rekomendasi kebijakan berdasarkan koefisien asli
    def get_rekomendasi(row):
        k_jalan = row['Koefisien_Lebar_Jalan']
        k_jarak = row['Koefisien_Jarak']
        
        if pd.isna(k_jalan) or pd.isna(k_jarak):
            return '⚪ Data tidak lengkap'
        elif k_jalan > 0.065 and abs(k_jarak) > 0.006:
            return '🔴 Prioritas jalan + pusat pertumbuhan baru'
        elif k_jalan > 0.065:
            return '🟠 Prioritas pelebaran jalan'
        elif abs(k_jarak) > 0.006:
            return '🟡 Prioritas pusat pertumbuhan baru'
        else:
            return '🟢 Pertahankan fasilitas lokal'
    
    df['Rekomendasi'] = df.apply(get_rekomendasi, axis=1)
    
    return df

df = load_data()

# Filter data yang memiliki koordinat untuk peta
df_map = df.dropna(subset=['Latitude', 'Longitude']).copy()

# =====================================================
# SIDEBAR FILTER
# =====================================================

st.sidebar.header("🔍 Filter Data")
st.sidebar.markdown("Pilih kabupaten/kota untuk ditampilkan di peta dan tabel")

selected_kabupaten = st.sidebar.multiselect(
    "Kabupaten/Kota",
    options=df['Kabupaten'].tolist(),
    default=df['Kabupaten'].tolist()
)

filtered_df = df[df['Kabupaten'].isin(selected_kabupaten)]
filtered_map_df = df_map[df_map['Kabupaten'].isin(selected_kabupaten)]

# =====================================================
# METRIC CARDS (Ringkasan Statistik)
# =====================================================

st.subheader("📊 Ringkasan Statistik GWR (Hasil Analisis R)")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📌 Jumlah Sampel", len(filtered_df))

with col2:
    # Average coefficient
    avg_coef = filtered_df['Koefisien_Lebar_Jalan'].mean()
    st.metric("📈 Rata-rata Koef. Lebar Jalan", f"{avg_coef:.4f}")

with col3:
    # Average jarak coefficient
    avg_jarak = filtered_df['Koefisien_Jarak'].mean()
    st.metric("📉 Rata-rata Koef. Jarak", f"{avg_jarak:.4f}")

with col4:
    # Rata-rata Local R2
    avg_r2 = filtered_df['Local_R2'].mean()
    st.metric("🎯 Rata-rata Local R²", f"{avg_r2:.3f}")

st.markdown("---")

# =====================================================
# LAYOUT 2 KOLOM: MAP + BAR CHART
# =====================================================

# =====================================================
# UPDATE LAYOUT: PETA FULL WIDTH, GRAFIK DI BAWAH
# =====================================================

# Baris 1: Peta (full width, not in columns)
st.subheader("🗺️ Peta Koefisien Lebar Jalan")
st.caption("Semakin merah/merah tua = semakin kuat pengaruh lebar jalan | Klik marker untuk detail")

if len(filtered_map_df) == 0:
    st.warning("⚠️ Tidak ada data dengan koordinat untuk ditampilkan di peta.")
else:
    center_lat = filtered_map_df['Latitude'].mean()
    center_lon = filtered_map_df['Longitude'].mean()
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=7, control_scale=True)
    folium.TileLayer('CartoDB positron', name='Light Map', control=True).add_to(m)
    
    for idx, row in filtered_map_df.iterrows():
        if row['Koefisien_Lebar_Jalan'] > 0.065:
            color = 'darkred'
        elif row['Koefisien_Lebar_Jalan'] > 0.062:
            color = 'red'
        elif row['Koefisien_Lebar_Jalan'] > 0.060:
            color = 'orange'
        else:
            color = 'green'
        
        popup_text = f"""
        <b>{row['Kabupaten']}</b><br>
        <b>Koefisien Lebar Jalan:</b> {row['Koefisien_Lebar_Jalan']:.4f}<br>
        <b>Koefisien Jarak:</b> {row['Koefisien_Jarak']:.4f}<br>
        <b>Local R²:</b> {row['Local_R2']:.4f}<br>
        <b>Rekomendasi:</b> {row['Rekomendasi']}
        """
        
        radius = max(5, min(20, row['Koefisien_Lebar_Jalan'] * 100))
        
        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            popup=folium.Popup(popup_text, max_width=300)
        ).add_to(m)
    
    folium.LayerControl().add_to(m)
    map_html = m._repr_html_()
    html(map_html, height=500, width=800)  # Width diperbesar

st.markdown("---")

# Baris 2: Dua grafik dalam satu baris (side by side)
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("📊 Ranking Koefisien Lebar Jalan")
    st.caption("Semakin ke kanan, semakin kuat pengaruh lebar jalan")
    
    fig = px.bar(filtered_df.sort_values('Koefisien_Lebar_Jalan', ascending=True),
                 x='Koefisien_Lebar_Jalan',
                 y='Kabupaten',
                 orientation='h',
                 color='Koefisien_Lebar_Jalan',
                 color_continuous_scale='Reds',
                 labels={'Koefisien_Lebar_Jalan': 'Koefisien', 'Kabupaten': ''})
    
    fig.update_layout(height=max(400, len(filtered_df) * 20), margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig, use_container_width=True)

with col_chart2:
    st.subheader("📉 Ranking Koefisien Jarak")
    st.caption("Semakin ke kiri (negatif besar) = semakin kuat pengaruh jarak")
    
    fig2 = px.bar(filtered_df.sort_values('Koefisien_Jarak', ascending=True),
                  x='Koefisien_Jarak',
                  y='Kabupaten',
                  orientation='h',
                  color='Koefisien_Jarak',
                  color_continuous_scale='Blues_r',
                  labels={'Koefisien_Jarak': 'Koefisien', 'Kabupaten': ''})
    
    fig2.update_layout(height=max(400, len(filtered_df) * 20), margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# =====================================================
# BAR CHART KOEFISIEN JARAK (NEGATIF)
# =====================================================

st.subheader("📈 Ranking Koefisien Jarak (Negatif)")
st.caption("Semakin ke kiri (negatif besar) = semakin kuat pengaruh jarak")

fig2 = px.bar(filtered_df.sort_values('Koefisien_Jarak', ascending=True),
              x='Koefisien_Jarak',
              y='Kabupaten',
              orientation='h',
              color='Koefisien_Jarak',
              color_continuous_scale='Blues_r',
              labels={'Koefisien_Jarak': 'Koefisien (negatif = semakin jauh semakin murah)', 'Kabupaten': ''})

fig2.update_layout(height=max(400, len(filtered_df) * 20), margin=dict(l=0, r=0, t=40, b=0))
st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# =====================================================
# TABEL DATA LENGKAP + REKOMENDASI
# =====================================================

st.subheader("📋 Tabel Koefisien GWR dan Rekomendasi Kebijakan")

display_df = filtered_df[['Kabupaten', 'Provinsi', 'Koefisien_Lebar_Jalan', 
                          'Koefisien_Jarak', 'Local_R2', 'Rekomendasi']].copy()
display_df.columns = ['Kabupaten', 'Provinsi', 'Koef. Lebar Jalan', 
                      'Koef. Jarak', 'Local R²', 'Rekomendasi Kebijakan']
display_df['Koef. Lebar Jalan'] = display_df['Koef. Lebar Jalan'].round(4)
display_df['Koef. Jarak'] = display_df['Koef. Jarak'].round(4)
display_df['Local R²'] = display_df['Local R²'].round(4)

st.dataframe(display_df, use_container_width=True)

# =====================================================
# DOWNLOAD BUTTON
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
# INSIGHT WILAYAH PRIORITAS
# =====================================================

st.markdown("---")
st.subheader("💡 Wilayah Prioritas Intervensi (Berdasarkan Koefisien GWR)")

if len(filtered_df) > 0:
    # Wilayah dengan koefisien lebar jalan tertinggi
    top3_lebar = filtered_df.nlargest(3, 'Koefisien_Lebar_Jalan')[['Kabupaten', 'Koefisien_Lebar_Jalan', 'Rekomendasi']]
    
    st.write("**🔴 Prioritas Pelebaran Jalan (Koefisien Lebar Jalan Tertinggi):**")
    for _, row in top3_lebar.iterrows():
        st.write(f"   - {row['Kabupaten']}: {row['Koefisien_Lebar_Jalan']:.4f}")
    
    # Wilayah dengan koefisien jarak paling negatif
    top3_jarak = filtered_df.nsmallest(3, 'Koefisien_Jarak')[['Kabupaten', 'Koefisien_Jarak', 'Rekomendasi']]
    
    st.write("\n**🟡 Prioritas Pusat Pertumbuhan Baru (Paling Tergantung Jarak):**")
    for _, row in top3_jarak.iterrows():
        st.write(f"   - {row['Kabupaten']}: {row['Koefisien_Jarak']:.4f}")

# =====================================================
# FOOTER RINGKAS (COPYRIGHT + TIMESTAMP)
# =====================================================

st.markdown("---")

# Footer utama
st.markdown(
    """
    <div style="text-align: center; color: #666666; font-size: 13px;">
        <strong>© 2026 Burhanudin Badiuzaman</strong> | Data Analyst & Geospatial Analyst<br>
        Dashboard GWR - Proyek ILASPP (ATR/BPN)
    </div>
    """,
    unsafe_allow_html=True
)

# Timestamp update (tetap ada!)
st.caption(f"🕒 Terakhir diperbarui: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')} WIB")
st.caption("📌 Data: Analisis GWR dengan R dan Python | Visualisasi: Streamlit, Folium, Plotly")