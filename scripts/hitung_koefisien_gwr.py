"""
SCRIPT GWR (Geographically Weighted Regression)
Untuk menghitung koefisien jarak dan lebar jalan per kabupaten/kota
Metode: GWR dengan adaptive bandwidth
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# 1. CEK KETERSEDIAAN LIBRARY
# ============================================================
try:
    from libpysal.weights import Kernel, distance
    from mgwr.gwr import GWR
    from mgwr.sel_bw import Sel_BW
    LIB_AVAILABLE = True
    print("✅ Library GWR tersedia (libpysal, mgwr)")
except ImportError as e:
    LIB_AVAILABLE = False
    print("⚠️ Library GWR tidak tersedia. Install dengan:")
    print("   pip install libpysal mgwr")
    print("   atau")
    print("   conda install -c conda-forge libpysal mgwr")

# ============================================================
# 2. FUNGSI ALTERNATIF (Jika GWR tidak tersedia)
# ============================================================
def hitung_dengan_regresi_biasa(df):
    """
    Alternatif jika GWR tidak bisa diinstall.
    Menggunakan regresi linear biasa + dummy regional.
    """
    print("\n📊 Menggunakan metode alternatif: Regresi Linear dengan Dummy Regional")
    
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import OneHotEncoder
    
    # Ekstrak fitur
    X = df[['X_jarak', 'X_lebar_jalan']].values
    
    # Tambahkan dummy provinsi/regional
    if 'provinsi' in df.columns:
        encoder = OneHotEncoder(sparse_output=False)
        prov_dummies = encoder.fit_transform(df[['provinsi']])
        X = np.hstack([X, prov_dummies])
    
    # Tambahkan interaksi (jarak * lebar_jalan)
    interaksi = (df['X_jarak'] * df['X_lebar_jalan']).values.reshape(-1, 1)
    X = np.hstack([X, interaksi])
    
    # Regresi
    model = LinearRegression()
    model.fit(X, df['Y'])
    
    # Koefisien global
    koef_jarak = model.coef_[0]
    koef_lebar = model.coef_[1]
    
    # Semua wilayah mendapat koefisien yang sama (homogen)
    hasil = pd.DataFrame({
        'nama_kabupaten': df['nama_kabupaten'],
        'koefisien_jarak': koef_jarak,
        'koefisien_lebar_jalan': koef_lebar,
        'p_value_jarak': 0.05,  # estimasi
        'p_value_lebar_jalan': 0.05,
        'metode': 'regresi_linear'
    })
    
    return hasil

def hitung_dengan_gwr(df, coords):
    """
    Hitung koefisien dengan GWR (Geographically Weighted Regression)
    """
    print("\n📊 Menjalankan GWR (Geographically Weighted Regression)...")
    
    y = df['Y'].values.reshape(-1, 1)
    X = df[['X_jarak', 'X_lebar_jalan']].values
    
    # Tentukan bandwidth optimal
    print("   - Menghitung bandwidth optimal...")
    try:
        # Gunakan Golden Section Search
        bw_selector = Sel_BW(coords, y, X, fixed=False, multi=True)
        bw = bw_selector.search()
        print(f"   - Bandwidth optimal: {bw:.2f}")
    except:
        # Fallback: gunakan 50% dari total data sebagai bandwidth
        bw = len(df) * 0.5
        print(f"   - Bandwidth fallback: {bw:.0f}")
    
    # Jalankan GWR
    print("   - Menjalankan regresi GWR...")
    gwr_model = GWR(coords, y, X, bw, fixed=False, kernel='gaussian')
    gwr_results = gwr_model.fit()
    
    # Ekstrak hasil
    hasil = pd.DataFrame({
        'nama_kabupaten': df['nama_kabupaten'],
        'koefisien_jarak': gwr_results.params[:, 1],
        'koefisien_lebar_jalan': gwr_results.params[:, 2],
        'p_value_jarak': gwr_results.p_values[:, 1],
        'p_value_lebar_jalan': gwr_results.p_values[:, 2],
        'r_squared_local': gwr_results.localR2,
        'metode': 'gwr'
    })
    
    return hasil

def tentukan_dominasi(row, alternatif=False):
    """
    Tentukan dominasi berdasarkan p-value dan nilai koefisien
    """
    if alternatif:
        # Untuk metode alternatif (tanpa p-value yang valid)
        if row['koefisien_jarak'] > row['koefisien_lebar_jalan'] * 1.2:
            return "jarak"
        elif row['koefisien_lebar_jalan'] > row['koefisien_jarak'] * 1.2:
            return "lebar_jalan"
        else:
            return "seimbang"
    
    # Metode standar dengan p-value
    signif_jarak = row['p_value_jarak'] < 0.05
    signif_lebar = row['p_value_lebar_jalan'] < 0.05
    
    if not signif_jarak and not signif_lebar:
        return "seimbang"  # tidak signifikan, default seimbang
    elif signif_jarak and not signif_lebar:
        return "jarak"
    elif not signif_jarak and signif_lebar:
        return "lebar_jalan"
    else:
        # Keduanya signifikan, bandingkan nilai absolut koefisien
        if abs(row['koefisien_jarak']) > abs(row['koefisien_lebar_jalan']):
            return "jarak"
        else:
            return "lebar_jalan"

# ============================================================
# 3. FUNGSI UTAMA
# ============================================================
def hitung_koefisien_dari_data_mentah(file_path_data="data/data_mentah_spasial.csv", 
                                       file_path_output="data/sample_coefficients.csv"):
    """
    Fungsi utama untuk menghitung koefisien dari data mentah
    """
    print("="*60)
    print("🌉 HYBRID BRIDGE - PERHITUNGAN KOEFISIEN SPASIAL")
    print("="*60)
    
    # Baca data mentah
    print(f"\n📂 Membaca data mentah dari: {file_path_data}")
    try:
        df = pd.read_csv(file_path_data)
        print(f"   ✅ Data loaded: {len(df)} kabupaten/kota")
    except FileNotFoundError:
        print(f"   ❌ File tidak ditemukan: {file_path_data}")
        print("\n📌 Contoh format file yang dibutuhkan:")
        print(df_example.to_string())
        return False
    
    # Validasi kolom yang diperlukan
    required_cols = ['nama_kabupaten', 'Y', 'X_jarak', 'X_lebar_jalan', 'lat', 'lng']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"   ❌ Kolom yang hilang: {missing_cols}")
        return False
    
    print(f"   ✅ Semua kolom required tersedia")
    
    # Siapkan koordinat
    coords = df[['lng', 'lat']].values
    
    # Hitung koefisien dengan metode yang tersedia
    if LIB_AVAILABLE:
        hasil = hitung_dengan_gwr(df, coords)
        alternatif = False
    else:
        print("\n⚠️ GWR tidak tersedia, menggunakan metode alternatif...")
        hasil = hitung_dengan_regresi_biasa(df)
        alternatif = True
    
    # Tentukan dominasi
    print("\n🎯 Menentukan dominasi per wilayah...")
    hasil['dominasi'] = hasil.apply(lambda row: tentukan_dominasi(row, alternatif), axis=1)
    
    # Statistik hasil
    print(f"\n📊 Distribusi Dominasi:")
    print(hasil['dominasi'].value_counts())
    
    # Siapkan output untuk dashboard
    output = hasil[['nama_kabupaten', 'koefisien_jarak', 'koefisien_lebar_jalan', 'dominasi']]
    
    # Bulatkan koefisien
    output['koefisien_jarak'] = output['koefisien_jarak'].round(4)
    output['koefisien_lebar_jalan'] = output['koefisien_lebar_jalan'].round(4)
    
    # Simpan ke CSV
    output.to_csv(file_path_output, index=False)
    print(f"\n✅ Koefisien disimpan ke: {file_path_output}")
    
    # Tampilkan contoh hasil
    print("\n📋 Contoh hasil (5 kabupaten pertama):")
    print(output.head().to_string(index=False))
    
    return True

# ============================================================
# 4. CONTOH DATA MENTAH (Template)
# ============================================================
df_example = pd.DataFrame({
    'nama_kabupaten': ['Kota Kediri', 'Kabupaten Kediri', 'Kota Surabaya', 'Kota Malang'],
    'provinsi': ['Jawa Timur', 'Jawa Timur', 'Jawa Timur', 'Jawa Timur'],
    'Y': [3500000, 2800000, 5500000, 4000000],
    'X_jarak': [25, 35, 0, 20],
    'X_lebar_jalan': [8.5, 6.2, 12.3, 7.5],
    'lat': [-7.8169, -7.7833, -7.2575, -7.9666],
    'lng': [112.0168, 112.0833, 112.7521, 112.6326]
})

# ============================================================
# 5. EKSEKUSI (JIKA DIJALANKAN LANGSUNG)
# ============================================================
if __name__ == "__main__":
    import sys
    
    print("\n" + "="*60)
    print("🚀 HYBRID BRIDGE - KOEFISIEN SPASIAL CALCULATOR")
    print("="*60)
    
    # Cek apakah file data mentah ada
    import os
    if os.path.exists("data/data_mentah_spasial.csv"):
        print("\n📁 Data mentah ditemukan. Memulai perhitungan...")
        hitung_koefisien_dari_data_mentah()
    else:
        print("\n⚠️ File data/data_mentah_spasial.csv belum ada.")
        print("\n📌 Template file yang dibutuhkan:")
        print(df_example.to_string())
        print("\n🔧 Silakan buat file 'data/data_mentah_spasial.csv' dengan format di atas.")
        print("   Atau jalankan script ini setelah file tersedia.")
    
    print("\n" + "="*60)
    print("💡 Tips: Untuk menginstall library GWR:")
    print("   pip install libpysal mgwr")
    print("="*60)
