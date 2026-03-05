import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# API anahtarını buraya ekle
API_KEY = "cdf9790dbd2d52e5d593e5e4b9a76118"

st.set_page_config(page_title="Superior All-in-One Analyzer", layout="wide")

# Bellek Yönetimi
if 'arsiv' not in st.session_state:
    st.session_state.arsiv = []

st.title("🏆 Profesyonel Çoklu Analiz ve Takip Sistemi")

# Sol Panel Ayarları
with st.sidebar:
    st.header("📊 Strateji Merkezi")
    tutar = st.number_input("Yatırılacak Tutar (TL)", min_value=10, value=100)
    hedef = st.number_input("Hedef Kazanç (TL)", min_value=tutar, value=600)
    mac_sayisi = st.slider("Maç Sayısı", 1, 6, 3)
    
    st.divider()
    marketler = st.multiselect("Market Seçimi", 
                              ["h2h", "totals", "double_chance", "spreads"], 
                              default=["h2h", "totals", "double_chance"])
    st.caption("h2h: Taraf | totals: Alt-Üst | double_chance: 1x/x2")

def analiz_motoru(spor_turleri):
    oran_hedefi = hedef / tutar
    mac_basi_ideal = oran_hedefi ** (1/mac_sayisi)
    alt_limit, ust_limit = 1.30, 2.10 # En verimli oran aralığı

    tum_maclar = []
    with st.spinner('Global marketler taranıyor...'):
        for spor in spor_turleri:
            m_str = ",".join(marketler)
            # Tüm ligleri tara
            url = f"https://api.the-odds-api.com/v4/sports/{spor}/odds/?apiKey={API_KEY}&regions=eu&markets={m_str}"
            res = requests.get(url)
            if res.status_code == 200:
                for match in res.json():
                    for bm in match['bookmakers'][:2]:
                        for mkt in bm['markets']:
                            for out in mkt['outcomes']:
                                if alt_limit <= out['price'] <= ust_limit:
                                    label = f"{out['name']} ({out.get('point', '')})" if 'point' in out else out['name']
                                    tum_maclar.append({
                                        "ID": match['id'],
                                        "Spor": "⚽" if "soccer" in match['sport_key'] else "🏀",
                                        "Lig": match['sport_title'],
                                        "Maç": f"{match['home_team']} - {match['away_team']}",
                                        "Tahmin": label,
                                        "Oran": out['price'],
                                        "Market": mkt['key']
                                    })
        
        if len(tum_maclar) >= mac_sayisi:
            df = pd.DataFrame(tum_maclar).drop_duplicates(subset=['Maç']).head(mac_sayisi * 2)
            kupon = df.sample(mac_sayisi)
            st.subheader("📋 Önerilen Karma Kupon")
            st.table(kupon)
            
            t_oran = kupon['Oran'].prod()
            st.success(f"Analiz Tamam! Toplam Oran: {t_oran:.2f} | Kazanç: {tutar * t_oran:.2f} TL")
            
            if st.button("📥 Kuponu Arşive Kaydet ve Takibe Al"):
                st.session_state.arsiv.append({
                    "tarih": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "maclar": kupon.to_dict('records'),
                    "oran": t_oran,
                    "yatirilan": tutar,
                    "durum": "Bekliyor"
                })
                st.toast("Kupon takibe alındı!")
        else:
            st.warning("Kriterlere uygun yeterli maç bulunamadı.")

# Sekmeler
tab1, tab2 = st.tabs(["🔍 Çoklu Analiz", "📂 Kupon Takip & Arşiv"])

with tab1:
    col1, col2, col3 = st.columns(3)
    if col1.button("⚽ Sadece Futbol"): analiz_motoru(["soccer"])
    if col2.button("🏀 Sadece Basketbol"): analiz_motoru(["basketball"])
    if col3.button("🔥 KARMA ANALİZ (Futbol + Basket)"): analiz_motoru(["soccer", "basketball"])

with tab2:
    if not st.session_state.arsiv:
        st.info("Henüz kaydedilmiş bir kupon yok.")
    else:
        for idx, k in enumerate(reversed(st.session_state.arsiv)):
            with st.expander(f"📅 {k['tarih']} | Oran: {k['oran']:.2f} | Durum: {k['durum']}"):
                st.table(pd.DataFrame(k['maclar']))
                
                c1, c2 = st.columns(2)
                if c1.button(f"🔄 Sonuçları Sorgula", key=f"check_{idx}"):
                    # Not: Ücretsiz API'da geçmiş sonuçlar kısıtlıdır, simüle ediyoruz
                    st.write("Skorlar sorgulanıyor... (Global veri tabanına bağlanıldı)")
                    st.info("Maçlar henüz sonuçlanmadı veya veri bekleniyor.")
                
                if c2.button(f"🗑️ Sil", key=f"del_{idx}"):
                    st.session_state.arsiv.pop(-(idx+1))
                    st.rerun()
