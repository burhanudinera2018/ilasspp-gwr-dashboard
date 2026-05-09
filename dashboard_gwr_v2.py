# =====================================================
# DASHBOARD GWR - TANPA streamlit_folium
# =====================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit.components.v1 import html
import os

st.set_page_config(page_title="Dashboard GWR - ILASPP", page_icon="🗺️", layout="wide")

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
    else:
        st.warning(f"⚠️ File {csv_path} tidak ditemukan. Menggunakan data contoh.")
        data = {
            'Kabupaten': ['Kota Kediri', 'Kabupaten Kediri', 'Kota Surabaya', 'Kabupaten Sidoarjo', 
                          'Kota Malang', 'Kabupaten Malang', 'Kota Blitar', 'Kabupaten Blitar',
                          'Kota Probolinggo', 'Kabupaten Probolinggo', 'Kota Pasuruan', 
                          'Kabupaten Pasuruan', 'Kota Mojokerto', 'Kabupaten Mojokerto', 
                          'Kota Madiun', 'Kabupaten Madiun', 'Kabupaten Jombang', 
                          'Kabupaten Nganjuk', 'Kabupaten Tulungagung', 'Kabupaten Trenggalek'],
            'Koef_Lebar_Jalan': [0.0641, 0.0641, 0.0579, 0.0612, 0.0623, 0.0605, 0.0630, 0.0625,
                                  0.0608, 0.0615, 0.0585, 0.0592, 0.0620, 0.0618, 0.0635, 0.0630,
                                  0.0622, 0.0619, 0.0628, 0.0624],
            'Koef_Jarak': [-0.00568, -0.00568, -0.00065, -0.00380, -0.00420, -0.00460, -0.00500,
                           -0.00520, -0.00400, -0.00430, -0.00250, -0.00280, -0.00480, -0.00500,
                           -0.00550, -0.00560, -0.00530, -0.00510, -0.00540, -0.00555],
            'Latitude': [-7.8169, -7.7833, -7.2575, -7.4531, -7.9666, -8.1667, -8.1000, -8.1333,
                         -7.7500, -7.7833, -7.6500, -7.7000, -7.4667, -7.5000, -7.6333, -7.6667,
                         -7.5500, -7.6000, -8.0667, -8.2333],
            'Longitude': [112.0168, 112.0833, 112.7521, 112.7167, 112.6326, 112.6667, 112.1667,
                          112.2000, 113.2167, 113.2500, 112.9500, 112.9833, 112.4833, 112.5167,
                          111.5333, 111.5667, 112.2333, 112.0167, 111.9000, 111.7667]
        }
        df = pd.DataFrame(data)
    
    df['Rekomendasi'] = df.apply(lambda row: 
        '🔴 Prioritas jalan + pusat pertumbuhan' if (row['Koef_Lebar_Jalan'] > 0.064 and abs(row['Koef_Jarak']) > 0.006)
        else '🟠 Prioritas pelebaran jalan' if row['Koef_Lebar_Jalan'] > 0.064
        else '🟡 Prioritas pusat pertumbuhan baru' if abs(row['Koef_Jarak']) > 0.006
        else '🟢 Pertahankan fasilitas lokal', axis=1)
    
    return df

df = load_data()

# Sidebar filter
st.sidebar.header("🔍 Filter Data")
selected_kabupaten = st.sidebar.multiselect(
    "Pilih Kabupaten/Kota",
    options=df['Kabupaten'].tolist(),
    default=df['Kabupaten'].tolist()
)

filtered_df = df[df['Kabupaten'].isin(selected_kabupaten)]

# Metric Cards
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

# Peta dengan folium (tanpa st_folium)
st.subheader("🗺️ Peta Koefisien Lebar Jalan")

center_lat = filtered_df['Latitude'].mean()
center_lon = filtered_df['Longitude'].mean()

m = folium.Map(location=[center_lat, center_lon], zoom_start=8, control_scale=True)

for idx, row in filtered_df.iterrows():
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

# Simpan peta ke HTML dan tampilkan di Streamlit
map_html = m._repr_html_()
html(map_html, height=500, width=700)

st.markdown("---")

# Bar Chart
st.subheader("📊 Ranking Pengaruh Lebar Jalan")
fig = px.bar(filtered_df.sort_values('Koef_Lebar_Jalan', ascending=True),
             x='Koef_Lebar_Jalan',
             y='Kabupaten',
             orientation='h',
             color='Koef_Lebar_Jalan',
             color_continuous_scale='Plasma',
             labels={'Koef_Lebar_Jalan': 'Koefisien', 'Kabupaten': ''})
fig.update_layout(height=500, margin=dict(l=0, r=0, t=40, b=0))
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Tabel
st.subheader("📋 Tabel Koefisien GWR dan Rekomendasi Kebijakan")
display_df = filtered_df[['Kabupaten', 'Koef_Lebar_Jalan', 'Koef_Jarak', 'Rekomendasi']].copy()
display_df.columns = ['Kabupaten', 'Koef. Lebar Jalan', 'Koef. Jarak', 'Rekomendasi Kebijakan']
display_df['Koef. Lebar Jalan'] = display_df['Koef. Lebar Jalan'].round(4)
display_df['Koef. Jarak'] = display_df['Koef. Jarak'].round(4)
st.dataframe(display_df, use_container_width=True)

# Download
st.markdown("---")
csv = display_df.to_csv(index=False).encode('utf-8')
st.download_button("📎 Download Tabel sebagai CSV", csv, "hasil_gwr_ilaspp.csv", "text/csv")

st.caption("📌 Dashboard Proyek ILASPP - Analisis GWR")