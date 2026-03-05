import streamlit as st
import requests
import pandas as pd

# API anahtarını buraya tırnak içine yaz
API_KEY = "cdf9790dbd2d52e5d593e5e4b9a76118"

st.set_page_config(page_title="Bet Strategy Bot", page_icon="⚽")

st.title("⚽🏀 Global Bahis Strateji Paneli")

# Kullanıcı Arayüzü
with st.sidebar:
    st.header("Kriterler")
    tutar = st.number_input("Yatırılacak Tutar (TL)", value=100)
    hedef = st.number_input("Hedeflenen Kazanç (TL)", value=500)
    mac_sayisi = st.slider("Maç Sayısı", 1, 5, 3)
    
    spor_secimi = st.selectbox("Spor Dalı", 
                               options=["soccer_epl", "basketball_nba"], 
                               format_func=lambda x: "İngiltere Premier Lig" if "soccer" in x else "NBA")

if st.button("Sanal Kupon Oluştur"):
    if API_KEY == "BURAYA_API_ANAHTARINI_YAPISTIR":
        st.error("Lütfen önce The Odds API üzerinden aldığınız anahtarı koda ekleyin!")
    else:
        url = f"https://api.the-odds-api.com/v4/sports/{spor_secimi}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h"
        res = requests.get(url)
        
        if res.status_code == 200:
            data = res.json()
            gereken_oran = hedef / tutar
            ideal_mac_orani = gereken_oran ** (1/mac_sayisi)
            
            st.info(f"Hedeflenen toplam oran: {gereken_oran:.2f} | Maç başı ortalama: {ideal_mac_orani:.2f}")
            
            # Maç eşleştirme algoritması
            secilen_maclar = []
            for m in data:
                home = m['home_team']
                away = m['away_team']
                # İlk büronun (genellikle Bet365 veya Pinnacle) oranlarını al
                try:
                    outcomes = m['bookmakers'][0]['markets'][0]['outcomes']
                    for o in outcomes:
                        if (ideal_mac_orani - 0.3) <= o['price'] <= (ideal_mac_orani + 0.3):
                            secilen_maclar.append({"Maç": f"{home} - {away}", "Tahmin": o['name'], "Oran": o['price']})
                            break # Her maçtan sadece bir tahmin al
                except:
                    continue
                if len(secilen_maclar) == mac_sayisi: break

            if len(secilen_maclar) == mac_sayisi:
                st.success("Kriterlere uygun kupon hazır!")
                st.table(pd.DataFrame(secilen_maclar))
            else:
                st.warning("Bu kriterlerde yeterli maç bulunamadı. Hedef kazancı düşürmeyi deneyin.")
        else:
            st.error("Veri çekilemedi. API anahtarınızı veya limitinizi kontrol edin.")

