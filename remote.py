import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

API_KEY = "cdf9790dbd2d52e5d593e5e4b9a76118"

st.set_page_config(page_title="Superior Scout v5", layout="wide")

# Görsel Stil
st.markdown("""
    <style>
    .match-box { background-color: #1e2130; padding: 20px; border-radius: 12px; border-left: 6px solid #ff4b4b; margin-bottom: 15px; box-shadow: 2px 2px 10px rgba(0,0,0,0.3); }
    .stat-btn { background-color: #007bff; color: white !important; padding: 8px 15px; border-radius: 5px; text-decoration: none; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 Kesintisiz Analiz ve Scout Merkezi")

with st.sidebar:
    st.header("📊 Finansal Ayarlar")
    tutar = st.number_input("Yatırılacak (TL)", min_value=10, value=100)
    hedef = st.number_input("Hedef Kazanç (TL)", min_value=tutar, value=600) # Hedefi yüksek tutmak daha çok maç bulur
    mac_sayisi = st.slider("Maç Sayısı", 1, 6, 3)
    st.divider()
    min_o = st.number_input("Min Oran Filtresi", value=1.05)
    v_kaynagi = st.selectbox("İstatistik Sitesi", ["SofaScore", "AiScore"])

def analiz_motoru(spor_list):
    oran_hedefi = hedef / tutar
    ideal_o = oran_hedefi ** (1/mac_sayisi)
    
    # AKILLI TOLERANS: Eğer ideal oran düşükse (banko arıyorsan), üst limiti esnetiyoruz.
    alt_l = max(min_o, ideal_o * 0.8)
    ust_l = max(2.50, ideal_o * 1.5) # Üst limiti esnettik ki bülten boş kalmasın

    with st.spinner('Global marketler taranıyor...'):
        firsatlar = []
        for spor in spor_list:
            # h2h: Maç Sonucu, totals: Alt/Üst, double_chance: Çifte Şans
            url = f"https://api.the-odds-api.com/v4/sports/{spor}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,totals,double_chance&oddsFormat=decimal"
            res = requests.get(url)
            if res.status_code == 200:
                for m in res.json():
                    tr_saat = datetime.strptime(m['commence_time'], "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=3)
                    for bm in m['bookmakers'][:2]:
                        for mkt in bm['markets']:
                            for out in mkt['outcomes']:
                                if alt_l <= out['price'] <= ust_l:
                                    firsatlar.append({
                                        "Saat": tr_saat.strftime("%H:%M"),
                                        "Spor": "⚽" if "soccer" in m['sport_key'] else "🏀",
                                        "Maç": f"{m['home_team']} - {m['away_team']}",
                                        "Tahmin": f"{out['name']} ({out.get('point', '')})" if 'point' in out else out['name'],
                                        "Oran": out['price'],
                                        "Lig": m['sport_title'],
                                        "Link": f"https://www.sofascore.com/search?q={m['home_team']}+vs+[{m['away_team']}]" if v_kaynagi=="SofaScore" else f"https://www.aiscore.com/search/{m['home_team']}+{m['away_team']}"
                                    })
        
        if len(firsatlar) >= mac_sayisi:
            df = pd.DataFrame(firsatlar).drop_duplicates(subset=['Maç']).head(mac_sayisi * 2)
            
            st.success(f"Analiz Tamamlandı! Toplam {len(df)} uygun market bulundu.")
            
            for _, r in df.iterrows():
                st.markdown(f"""
                <div class="match-box">
                    <div style="display: flex; justify-content: space-between;">
                        <span><b>{r['Saat']}</b> | {r['Spor']} {r['Maç']}</span>
                        <span style="color: #00ff00; font-weight: bold;">{r['Oran']}</span>
                    </div>
                    <div style="margin-top: 10px; font-size: 0.9em; color: #bbb;">{r['Lig']}</div>
                    <div style="margin-top: 10px; display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 1.1em; color: #ff4b4b;">Tahmin: {r['Tahmin']}</span>
                        <a href="{r['Link']}" target="_blank" class="stat-btn">📊 {v_kaynagi} İncele</a>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning(f"Aranan aralıkta ({alt_l:.2f} - {ust_l:.2f}) maç bulunamadı. Lütfen 'Hedef Kazanç' miktarını artırın.")

tab1, tab2 = st.tabs(["🔍 Canlı Analiz", "📂 Arşiv"])
with tab1:
    c1, c2, c3 = st.columns(3)
    if c1.button("⚽ SADECE FUTBOL"): analiz_motoru(["soccer"])
    if c2.button("🏀 SADECE BASKETBOL"): analiz_motoru(["basketball"])
    if c3.button("🔥 KARMA ANALİZ"): analiz_motoru(["soccer", "basketball"])
