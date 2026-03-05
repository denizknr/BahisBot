import streamlit as st
import requests
import pandas as pd

# API anahtarını buraya ekle
API_KEY = "cdf9790dbd2d52e5d593e5e4b9a76118"

st.set_page_config(page_title="Superior Stable Analyzer", layout="wide")

st.title("🚀 Kesin Sonuç Odaklı Analiz Sistemi")

with st.sidebar:
    st.header("📊 Strateji")
    tutar = st.number_input("Yatırılacak Tutar (TL)", min_value=10, value=100)
    hedef = st.number_input("Hedef Kazanç (TL)", min_value=tutar, value=350)
    mac_sayisi = st.slider("Maç Sayısı", 1, 5, 2)
    
    st.divider()
    st.warning("Not: Maç bulamazsa Hedef Kazancı artırın veya Maç Sayısını düşürün.")

def stabil_analiz(spor_key):
    # Hesaplama: Toleransı geniş tutuyoruz (1.20 - 2.50 arası her şeyi tara)
    oran_hedefi = hedef / tutar
    mac_basi_ideal = oran_hedefi ** (1/mac_sayisi)
    
    with st.spinner('Global bülten taranıyor...'):
        # EN GARANTİ: Sadece h2h (Taraf) ve totals (Alt/Üst) tara
        url = f"https://api.the-odds-api.com/v4/sports/{spor_key}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,totals&oddsFormat=decimal"
        res = requests.get(url)
        
        if res.status_code == 200:
            data = res.json()
            if not data:
                st.error("Bu ligde/sporda şu an aktif maç yok.")
                return

            secilenler = []
            for match in data:
                try:
                    # En popüler büroyu seç (Genelde listenin başındaki)
                    outcomes = match['bookmakers'][0]['markets'][0]['outcomes']
                    for out in outcomes:
                        # Geniş tolerans aralığı
                        if (mac_basi_ideal * 0.7) <= out['price'] <= (mac_basi_ideal * 1.3):
                            label = f"{out['name']} ({out.get('point', '')})" if 'point' in out else out['name']
                            secilenler.append({
                                "Lig": match['sport_title'],
                                "Maç": f"{match['home_team']} - {match['away_team']}",
                                "Tahmin": label,
                                "Oran": out['price']
                            })
                            break
                    if len(secilenler) >= mac_sayisi: break
                except: continue

            if len(secilenler) >= mac_sayisi:
                df = pd.DataFrame(secilenler).head(mac_sayisi)
                st.table(df)
                st.success(f"Kupon Tamam! Toplam Oran: {df['Oran'].prod():.2f}")
            else:
                st.warning(f"Kriterlere uygun maç bulunamadı. Gereken oran: {mac_basi_ideal:.2f}")
        else:
            st.error("API Hatası! Anahtarınızı kontrol edin.")

col1, col2 = st.columns(2)
if col1.button("⚽ Futbol Dünyasını Tara"): stabil_analiz("soccer")
if col2.button("🏀 Basketbol Dünyasını Tara"): stabil_analiz("basketball")
