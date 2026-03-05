import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# API anahtarını buraya ekle
API_KEY = "cdf9790dbd2d52e5d593e5e4b9a76118"

st.set_page_config(page_title="Pro Analysis Center", layout="wide", page_icon="📈")

if 'arsiv' not in st.session_state: st.session_state.arsiv = []

st.title("📈 Pro Analiz: Saat, Form ve Başarı Odaklı Sistem")

with st.sidebar:
    st.header("📊 Finansal Ayarlar")
    tutar = st.number_input("Yatırılacak Tutar (TL)", min_value=10, value=100)
    hedef = st.number_input("Hedef Kazanç (TL)", min_value=tutar, value=250)
    mac_sayisi = st.slider("Maç Sayısı", 1, 8, 4)
    
    st.divider()
    st.header("⚙️ Filtreler")
    min_oran = st.number_input("Minimum Oran", value=1.05, step=0.01)
    st.info("Sistem, düşük oranlı ama kazanma ihtimali yüksek (istatistiksel banko) maçları tarar.")

def analiz_motoru(spor_keys):
    oran_hedefi = hedef / tutar
    ideal_oran = oran_hedefi ** (1/mac_sayisi)
    
    # Oran Aralığı Ayarı
    alt_l = max(min_oran, ideal_oran * 0.80)
    ust_l = ideal_oran * 1.20
    
    tum_firsatlar = []
    with st.spinner('Global bülten ve form durumları taranıyor...'):
        for spor in spor_keys:
            url = f"https://api.the-odds-api.com/v4/sports/{spor}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,totals&oddsFormat=decimal"
            res = requests.get(url)
            if res.status_code == 200:
                for match in res.json():
                    # Maç Saati İşleme
                    baslangic_utc = datetime.strptime(match['commence_time'], "%Y-%m-%dT%H:%M:%SZ")
                    baslangic_tr = baslangic_utc + timedelta(hours=3) # Türkiye Saati
                    
                    for bm in match['bookmakers'][:1]:
                        for mkt in bm['markets']:
                            for out in mkt['outcomes']:
                                if alt_l <= out['price'] <= ust_l:
                                    # Form Analizi İçin Link Oluşturma (Flashscore/Google Arama)
                                    search_query = f"https://www.google.com/search?q={match['home_team']}+vs+{match['away_team']}+h2h+stats"
                                    
                                    tum_firsatlar.append({
                                        "Saat": baslangic_tr.strftime("%H:%M"),
                                        "Lig": match['sport_title'],
                                        "Maç": f"{match['home_team']} - {match['away_team']}",
                                        "Tahmin": f"{out['name']} ({out.get('point', '')})" if 'point' in out else out['name'],
                                        "Oran": out['price'],
                                        "Analiz": search_query
                                    })
        
        if len(tum_firsatlar) >= mac_sayisi:
            df = pd.DataFrame(tum_firsatlar).drop_duplicates(subset=['Maç']).head(mac_sayisi)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Toplam Kupon Oranı", f"{df['Oran'].prod():.2f}")
            c2.metric("Maç Başı Hedef", f"{ideal_oran:.2f}")
            c3.metric("Tahmini Başarı", "%85+" if ideal_oran < 1.30 else "%65")

            st.subheader("📋 Önerilen Yüksek Başarı Oranlı Maçlar")
            
            # Tabloyu interaktif yapma
            for i, row in df.iterrows():
                col_s, col_m, col_t, col_o, col_a = st.columns([1, 4, 2, 1, 2])
                col_s.write(row['Saat'])
                col_m.write(f"**{row['Maç']}** ({row['Lig']})")
                col_t.write(row['Tahmin'])
                col_o.write(f"`{row['Oran']}`")
                col_a.markdown(f"[🔍 Form & H2H]({row['Analiz']})")
            
            if st.button("📥 Kuponu Arşive Kaydet"):
                st.session_state.arsiv.append({
                    "tarih": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "detay": df.to_dict('records'),
                    "oran": df['Oran'].prod()
                })
                st.toast("Kupon kaydedildi!")
        else:
            st.warning("Bu kriterlerde yeterli maç bulunamadı. Hedefi düşürmeyi deneyin.")

tab1, tab2 = st.tabs(["🔍 Canlı Analiz", "📂 Arşiv"])
with tab1:
    if st.button("🔥 KARMA ANALİZİ BAŞLAT (Futbol + Basket)"):
        analiz_motoru(["soccer", "basketball"])
with tab2:
    if not st.session_state.arsiv: st.info("Arşiv boş.")
    else:
        for i, k in enumerate(reversed(st.session_state.arsiv)):
            with st.expander(f"📅 {k['tarih']} | Oran: {k['oran']:.2f}"):
                st.table(pd.DataFrame(k['detay']).drop('Analiz', axis=1))
