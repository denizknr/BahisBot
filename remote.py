import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# API ANAHTARINI BURAYA YAZ
API_KEY = "cdf9790dbd2d52e5d593e5e4b9a76118"

st.set_page_config(page_title="Superior Scout v6", layout="wide")

st.markdown("""
    <style>
    .match-card { background-color: #1e2130; padding: 15px; border-radius: 12px; border-left: 6px solid #00ff00; margin-bottom: 10px; }
    .stat-link { background-color: #ff4b4b; color: white !important; padding: 5px 10px; border-radius: 5px; text-decoration: none; font-size: 0.8em; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 Geniş Zamanlı Analiz ve Scout Merkezi")

with st.sidebar:
    st.header("📊 Strateji")
    tutar = st.number_input("Yatırılacak (TL)", min_value=10, value=100)
    hedef = st.number_input("Hedef Kazanç (TL)", min_value=tutar, value=800) # Hedefi yüksek tutmak daha çok maç bulur
    mac_sayisi = st.slider("Maç Sayısı", 1, 10, 4)
    st.divider()
    min_o = st.number_input("Min Oran", value=1.10)
    v_kaynagi = st.selectbox("Kaynak", ["SofaScore", "AiScore"])

def analiz_motoru(spor_list):
    oran_hedefi = hedef / tutar
    ideal_o = oran_hedefi ** (1/mac_sayisi)
    
    # Çok geniş bir tolerans aralığı (Bankodan Sürprize)
    alt_l = max(min_o, ideal_o * 0.75)
    ust_l = max(3.0, ideal_o * 1.5)

    with st.spinner('Tüm dünya bülteni taranıyor (1-3 günlük)...'):
        firsatlar = []
        for spor in spor_list:
            # Not: Ücretsiz API 'upcoming' maçları getirir (genelde 2-3 günlük)
            url = f"https://api.the-odds-api.com/v4/sports/{spor}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,totals&oddsFormat=decimal"
            res = requests.get(url)
            if res.status_code == 200:
                for m in res.json():
                    tr_saat = datetime.strptime(m['commence_time'], "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=3)
                    tarih_str = tr_saat.strftime("%d/%m %H:%M")
                    
                    for bm in m['bookmakers'][:3]: # Daha fazla büro tara
                        for mkt in bm['markets']:
                            for out in mkt['outcomes']:
                                if alt_l <= out['price'] <= ust_l:
                                    firsatlar.append({
                                        "Tarih": tarih_str,
                                        "Spor": "⚽" if "soccer" in m['sport_key'] else "🏀",
                                        "Lig": m['sport_title'],
                                        "Maç": f"{m['home_team']} - {m['away_team']}",
                                        "Tahmin": f"{out['name']} ({out.get('point', '')})" if 'point' in out else out['name'],
                                        "Oran": out['price'],
                                        "Link": f"https://www.sofascore.com/search?q={m['home_team']}+vs+{m['away_team']}"
                                    })
        
        if len(firsatlar) >= mac_sayisi:
            # En yakın oranlıları seçmek için sırala
            df = pd.DataFrame(firsatlar).drop_duplicates(subset=['Maç'])
            df['fark'] = abs(df['Oran'] - ideal_o)
            df = df.sort_values('fark').head(mac_sayisi * 2)
            
            st.success(f"Bülten tarandı: {len(df)} maç kriterlere dahil edildi.")
            
            for _, r in df.iterrows():
                st.markdown(f"""
                <div class="match-card">
                    <div style="display: flex; justify-content: space-between;">
                        <span>📅 {r['Tarih']} | {r['Spor']} <b>{r['Maç']}</b></span>
                        <span style="color: #00ff00; font-weight: bold;">{r['Oran']}</span>
                    </div>
                    <div style="font-size: 0.8em; color: #888; margin-bottom: 5px;">{r['Lig']}</div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: #ff4b4b;">Tahmin: {r['Tahmin']}</span>
                        <a href="{r['Link']}" target="_blank" class="stat-link">📊 {v_kaynagi}</a>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("Bültende uygun maç bulunamadı. Lütfen 'Hedef Kazanç' değerini 1000+ yaparak genişletin.")

tab1, tab2 = st.tabs(["🔍 Analiz", "📂 Arşiv"])
with tab1:
    if st.button("🔥 TÜM BÜLTENİ VE LİGLERİ KARMA TARA"):
        analiz_motoru(["soccer", "basketball"])
