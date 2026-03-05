import streamlit as st
import requests
import pandas as pd

# API anahtarını buraya ekle
API_KEY = "cdf9790dbd2d52e5d593e5e4b9a76118"

st.set_page_config(page_title="Pro Bahis Analiz", layout="wide")

# Görsel Stil (CSS)
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 Global Strateji ve Analiz Paneli")

# Sol Panel: Kriterler
with st.sidebar:
    st.header("📊 Finansal Parametreler")
    tutar = st.number_input("Yatırılacak Tutar (TL)", min_value=10, value=100)
    hedef = st.number_input("Hedeflenen Kazanç (TL)", min_value=tutar, value=500)
    mac_sayisi = st.slider("Kupon Maç Sayısı", 1, 5, 3)
    
    st.divider()
    st.info("Sistem, global market verilerini kullanarak hedef kazancınıza en uygun 'Value' oranları seçer.")

# Ana Ekran: Spor Dalları Ayrımı
tab_futbol, tab_basketbol = st.tabs(["⚽ Futbol (Global)", "🏀 Basketbol (NBA/Euro)"])

def veri_cek_ve_listele(spor_key):
    url = f"https://api.the-odds-api.com/v4/sports/{spor_key}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h"
    res = requests.get(url)
    
    if res.status_code == 200:
        data = res.json()
        toplam_oran_hedefi = hedef / tutar
        ortalama_oran = toplam_oran_hedefi ** (1/mac_sayisi)
        
        # Üst Metrikler
        c1, c2, c3 = st.columns(3)
        c1.metric("Hedef Çarpan", f"{toplam_oran_hedefi:.2f}x")
        c2.metric("Maç Başı Oran", f"{ortalama_oran:.2f}")
        c3.metric("Maç Havuzu", len(data))

        secilenler = []
        for m in data:
            try:
                outcomes = m['bookmakers'][0]['markets'][0]['outcomes']
                for o in outcomes:
                    if (ortalama_oran - 0.25) <= o['price'] <= (ortalama_oran + 0.25):
                        secilenler.append({
                            "Maç": f"{m['home_team']} v {m['away_team']}",
                            "Tahmin": o['name'],
                            "Oran": o['price'],
                            "Büro": m['bookmakers'][0]['title']
                        })
                        break
            except: continue
            if len(secilenler) == mac_sayisi: break

        if len(secilenler) >= mac_sayisi:
            st.subheader("📋 Önerilen Strateji Tablosu")
            df = pd.DataFrame(secilenler)
            st.table(df)
            st.success(f"Kupon tamamlandı! Toplam Oran: {df['Oran'].prod():.2f}")
        else:
            st.warning("Bu kriterlere uygun yeterli maç bulunamadı. Lütfen hedef kazancı veya maç sayısını esnetin.")
    else:
        st.error("API Veri Hatası! Anahtarınızı veya limitinizi kontrol edin.")

with tab_futbol:
    st.write("### Premier League ve Avrupa Ligleri Analizi")
    if st.button("Futbol Analizini Başlat"):
        veri_cek_ve_listele("soccer_epl") # EPL varsayılan, artırılabilir

with tab_basketbol:
    st.write("### NBA ve Global Basketbol Analizi")
    if st.button("Basketbol Analizini Başlat"):
        veri_cek_ve_listele("basketball_nba")
