import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# API anahtarını buraya ekle
API_KEY = "cdf9790dbd2d52e5d593e5e4b9a76118"

st.set_page_config(page_title="Superior Betting & Archive", layout="wide")

# Kayıtlı kuponlar için bellek yönetimi
if 'arsiv' not in st.session_state:
    st.session_state.arsiv = []

# Görsel Stil
st.markdown("""
    <style>
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3e445e; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; font-weight: bold; }
    .save-button>button { background-color: #28a745 !important; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏆 Global Analiz ve Kupon Arşivi")

# Sol Panel
with st.sidebar:
    st.header("📊 Strateji")
    tutar = st.number_input("Yatırılacak Tutar (TL)", min_value=10, value=100)
    hedef = st.number_input("Hedef Kazanç (TL)", min_value=tutar, value=500)
    mac_sayisi = st.slider("Maç Sayısı", 1, 10, 3)
    marketler = st.multiselect("Marketler", ["h2h", "totals", "spreads"], default=["h2h", "totals"])

tab_analiz, tab_arsiv = st.tabs(["🔍 Canlı Analiz", "📂 Kayıtlı Kuponlarım"])

def analiz_motoru(spor_group):
    oran_hedefi = hedef / tutar
    mac_basi_ideal = oran_hedefi ** (1/mac_sayisi)
    
    with st.spinner('Global marketler taranıyor...'):
        # Aktif ligleri çek
        lig_res = requests.get(f"https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}")
        if lig_res.status_code != 200: return st.error("API Hatası!")
        
        ligler = [l['key'] for l in lig_res.json() if l['group'] == spor_group][:10]
        tum_secenekler = []
        
        for lig in ligler:
            m_str = ",".join(marketler)
            o_url = f"https://api.the-odds-api.com/v4/sports/{lig}/odds/?apiKey={API_KEY}&regions=eu&markets={m_str}"
            o_res = requests.get(o_url)
            if o_res.status_code == 200:
                for match in o_res.json():
                    for bm in match['bookmakers'][:1]:
                        for mkt in bm['markets']:
                            for out in mkt['outcomes']:
                                if (mac_basi_ideal * 0.85) <= out['price'] <= (mac_basi_ideal * 1.15):
                                    label = f"{out['name']} ({out.get('point', '')})" if 'point' in out else out['name']
                                    tum_secenekler.append({
                                        "Maç": f"{match['home_team']} - {match['away_team']}",
                                        "Tahmin": label,
                                        "Oran": out['price'],
                                        "Market": mkt['key'].upper()
                                    })
        
        if len(tum_secenekler) >= mac_sayisi:
            df = pd.DataFrame(tum_secenekler).drop_duplicates(subset=['Maç']).head(mac_sayisi)
            st.table(df)
            toplam_oran = df['Oran'].prod()
            st.success(f"Kupon Hazır! Toplam Oran: {toplam_oran:.2f} | Tahmini Kazanç: {tutar * toplam_oran:.2f} TL")
            
            # Kaydetme Butonu
            if st.button("📥 Bu Kuponu Arşive Kaydet", key="save_btn"):
                yeni_kayit = {
                    "tarih": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "detay": df.to_dict('records'),
                    "toplam_oran": toplam_oran,
                    "yatirilan": tutar
                }
                st.session_state.arsiv.append(yeni_kayit)
                st.toast("Kupon başarıyla kaydedildi!")
        else:
            st.warning("Uygun maç bulunamadı.")

with tab_analiz:
    c1, c2 = st.columns(2)
    if c1.button("⚽ Futbol Tara"): analiz_motoru("soccer")
    if c2.button("🏀 Basketbol Tara"): analiz_motoru("basketball")

with tab_arsiv:
    if not st.session_state.arsiv:
        st.info("Henüz kaydedilmiş bir kupon bulunmuyor.")
    else:
        for i, k in enumerate(reversed(st.session_state.arsiv)):
            with st.expander(f"📅 {k['tarih']} - Oran: {k['toplam_oran']:.2f} - {k['yatirilan']} TL"):
                st.table(pd.DataFrame(k['detay']))
                if st.button(f"Kuponu Sil", key=f"del_{i}"):
                    st.session_state.arsiv.pop(-(i+1))
                    st.rerun()
