import pandas as pd
from geopy.geocoders import Nominatim
import time

# Daftar kabupaten yang perlu dicari koordinatnya
kabupaten_list = [
    "Kota Kediri", "Kabupaten Kediri", "Kota Surabaya"
]

geolocator = Nominatim(user_agent="hybrid_bridge")

hasil = []
for nama in kabupaten_list:
    try:
        location = geolocator.geocode(f"{nama}, Indonesia")
        if location:
            hasil.append({
                'nama': nama,
                'lat': location.latitude,
                'lng': location.longitude
            })
            print(f"✅ {nama}: {location.latitude}, {location.longitude}")
        else:
            print(f"❌ {nama}: tidak ditemukan")
        time.sleep(1)  # Hormati rate limit
    except Exception as e:
        print(f"Error: {e}")

pd.DataFrame(hasil).to_csv("data/koordinat_kabupaten.csv", index=False)
print("\n✅ Koordinat disimpan ke data/koordinat_kabupaten.csv")