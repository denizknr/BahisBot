import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# API anahtarını buraya ekle
API_KEY = "cdf9790dbd2d52e5d593e5e4b9a76118"

st.set_page_config(page_title="Superior Strategy Bot", layout="wide")

if 'arsiv' not in st.session_state:
    st.session_state.arsiv = []

st.title("🏆 Optimize Edilmiş Market Analiz Sistemi")

with st.sidebar:
    st.header("📊 Strateji")
    tutar = st.number_input("Yatırılacak Tutar (TL)", min_value=10, value=100)
    # En uygun oranlar için hedefi otomatik optimize ediyoruz
    hedef = st.number_input("Hedef Kazanç (TL)", min_value=tutar, value=450)
    mac_sayisi = st.slider("Maç Sayısı", 1, 5, 3)
    
    st.divider()
    st.info("Sistem şu an 1.35-1.90 aralığındaki 'Popüler Market' verilerine öncelik veriyor.")

def analiz_motoru(spor_group):
    # Hesaplama: Hedeflenen kazanç için gereken minimum çarpan
    oran_hedefi = hedef / tutar
    mac_basi_ideal = oran_hedefi ** (1/mac_sayisi)
    
    # Tolerans aralığını 'En Çok Tercih Edilen' oranlara göre esnetiyoruz (1.30 - 1.95)
    alt_limit = max(1.30, mac_basi_ideal * 0.90)
    ust_limit = min(2.00, mac_basi_ideal * 1.10)

    with st.spinner('Popüler global marketler analiz ediliyor...'):
        lig_res = requests.get(f"https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}")
        if lig_res.status_code != 200: return st.error("API Bağlantı Hatası!")
        
        # En popüler 15 ligi tara
        ligler = [l['key'] for l in lig_res.json() if l['group'] == spor_group][:15]
        tum_secenekler = []
        
        for lig in ligler:
            # Hem Taraf hem Alt/Üst marketlerini tara
            o_url = f"https://api.the-odds-api.com/v4/sports/{lig}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,totals&oddsFormat=decimal"
            o_res = requests.get(o_url)
            if o_res.status_code == 200:
                for match in o_res.json():
                    for bm in match['bookmakers'][:2]: # En popüler 2 büroyu tara (Bet365/Pinnacle)
                        for mkt in bm['markets']:
                            for out in mkt['outcomes']:
                                if alt_limit <= out['price'] <= ust_limit:
                                    label = f"{out['name']} ({out.get('point', '')})" if 'point' in out else out['name']
                                    tum_secenekler.append({
                                        "Lig": match['sport_title'],
                                        "Maç": f"{match['home_team']} - {match['away_team']}",
                                        "Tahmin": label,
                                        "Oran": out['price'],
                                        "Market": "Alt/Üst" if mkt['key'] == "totals" else "Maç Sonucu"
                                    })
        
        if len(tum_secenekler) >= mac_sayisi:
            # En uygunları seçmek için listeyi maça göre tekilleştir ve en yüksek oranlıları başa al
            df = pd.DataFrame(tum_secenekler).drop_duplicates(subset=['Maç']).sort_values(by="Oran", ascending=False)
            onerilen_kupon = df.head(mac_sayisi)
            
            st.subheader("📋 En Uygun Market Seçenekleri")
            st.table(onerilen_kupon)
            
            toplam_oran = onerilen_kupon['Oran'].prod()
            st.success(f"✅ Analiz Tamamlandı! Toplam Oran: {toplam_oran:.2f} | Beklenen Kazanç: {tutar * toplam_oran:.2f} TL")
            
            if st.button("📥 Kuponu Arşive Kaydet"):
                st.session_state.arsiv.append({
                    "tarih": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "detay": onerilen_kupon.to_dict('records'),
                    "toplam_oran": toplam_oran,
                    "yatirilan": tutar
                })
                st.toast("Kupon başarıyla kaydedildi!")
        else:
            st.warning(f"Aranan oran aralığında ({alt_limit:.2f} - {ust_limit:.2f}) yeterli maç bulunamadı. Lütfen hedef kazancı değiştirin.")

tab1, tab2 = st.tabs(["🔍 Analiz", "📂 Arşiv"])
with tab1:
    c1, c2 = st.columns(2)
    if c1.button("⚽ Futbol"): analiz_motoru("soccer")
    if c2.button("🏀 Basketbol"): analiz_motoru("basketball")
with tab2:
    if not st.session_state.arsiv: st.info("Arşiv boş.")
    else:
        for i, k in enumerate(reversed(st.session_state.arsiv)):
            with st.expander(f"📅 {k['tarih']} - Oran: {k['toplam_oran']:.2f}"):
                st.table(pd.DataFrame(k['detay']))
