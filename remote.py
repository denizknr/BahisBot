import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# API anahtarını buraya ekle
API_KEY = "cdf9790dbd2d52e5d593e5e4b9a76118"

st.set_page_config(page_title="Superior Mind Betting Bot", layout="wide", page_icon="🎯")

# Kalıcı veri saklama (Session State)
if 'arsiv' not in st.session_state: st.session_state.arsiv = []

# Görsel Stil (CSS)
st.markdown("""
    <style>
    .main { background: #0e1117; }
    .stMetric { background: #1e2130; padding: 20px; border-radius: 15px; border: 1px solid #3e445e; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; background: linear-gradient(45deg, #ff4b4b, #ff7e5f); color: white; font-weight: bold; border: none; }
    .stButton>button:hover { transform: scale(1.02); transition: 0.2s; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏆 Global Analiz & Strateji Merkezi")

# Sol Panel: Gelişmiş Filtreler
with st.sidebar:
    st.header("📊 Finansal Ayarlar")
    tutar = st.number_input("Yatırılacak Tutar (TL)", min_value=10, value=100)
    hedef = st.number_input("Hedeflenen Kazanç (TL)", min_value=tutar, value=450)
    mac_sayisi = st.slider("Maç Sayısı", 1, 6, 3)
    
    st.divider()
    st.header("🎯 Market Tercihleri")
    marketler = st.multiselect("Aktif Marketler", ["h2h", "totals", "double_chance", "spreads"], default=["h2h", "totals"])
    st.info("İpucu: Maç bulamazsa Hedef Kazancı artırarak 1.45+ oranlara odaklanın.")

def analiz_et(spor_keys):
    oran_hedefi = hedef / tutar
    ideal_oran = oran_hedefi ** (1/mac_sayisi)
    
    # Oran Aralığı: Piyasanın en verimli olduğu bölge (1.30 - 2.20)
    alt_l, ust_l = max(1.25, ideal_oran * 0.85), min(2.50, ideal_oran * 1.15)
    
    tum_firsatlar = []
    with st.spinner('Global marketler çapraz sorgulanıyor...'):
        for spor in spor_keys:
            m_str = ",".join(marketler)
            url = f"https://api.the-odds-api.com/v4/sports/{spor}/odds/?apiKey={API_KEY}&regions=eu&markets={m_str}&oddsFormat=decimal"
            res = requests.get(url)
            if res.status_code == 200:
                for match in res.json():
                    for bm in match['bookmakers'][:2]: # En iyi bürolar
                        for mkt in bm['markets']:
                            for out in mkt['outcomes']:
                                if alt_l <= out['price'] <= ust_l:
                                    label = f"{out['name']} ({out.get('point', '')})" if 'point' in out else out['name']
                                    tum_firsatlar.append({
                                        "Spor": "⚽" if "soccer" in match['sport_key'] else "🏀",
                                        "Lig": match['sport_title'],
                                        "Maç": f"{match['home_team']} - {match['away_team']}",
                                        "Market": mkt['key'].replace("_"," ").title(),
                                        "Tahmin": label,
                                        "Oran": out['price']
                                    })
        
        if len(tum_firsatlar) >= mac_sayisi:
            df = pd.DataFrame(tum_firsatlar).drop_duplicates(subset=['Maç']).head(mac_sayisi)
            
            # Üst Metrikler
            c1, c2, c3 = st.columns(3)
            c1.metric("Toplam Oran", f"{df['Oran'].prod():.2f}")
            c2.metric("Olası Kazanç", f"{tutar * df['Oran'].prod():.2f} TL")
            c3.metric("Risk Seviyesi", "Düşük/Orta" if ideal_oran < 1.6 else "Yüksek")
            
            st.subheader("📋 En Uygun Market Seçenekleri")
            st.table(df)
            
            if st.button("📥 Bu Kuponu Takibe Al (Arşivle)"):
                st.session_state.arsiv.append({
                    "tarih": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "detay": df.to_dict('records'),
                    "oran": df['Oran'].prod(),
                    "yatirilan": tutar
                })
                st.toast("Kupon başarıyla arşive eklendi!")
        else:
            st.warning(f"Kriterlerinize uygun ({alt_l:.2f}-{ust_l:.2f}) maç bulunamadı. Lütfen hedefi artırın.")

tab1, tab2 = st.tabs(["🔍 Canlı Analiz", "📂 Kupon Arşivi"])

with tab1:
    col1, col2, col3 = st.columns(3)
    if col1.button("⚽ Sadece Futbol"): analiz_et(["soccer"])
    if col2.button("🏀 Sadece Basketbol"): analiz_et(["basketball"])
    if col3.button("🔥 KARMA TARA"): analiz_et(["soccer", "basketball"])

with tab2:
    if not st.session_state.arsiv: st.info("Henüz kaydedilmiş bir analiz bulunmuyor.")
    else:
        for i, k in enumerate(reversed(st.session_state.arsiv)):
            with st.expander(f"📅 {k['tarih']} | Oran: {k['oran']:.2f}"):
                st.table(pd.DataFrame(k['detay']))
                if st.button(f"🗑️ Kuponu Sil", key=f"del_{i}"):
                    st.session_state.arsiv.pop(-(i+1))
                    st.rerun()
