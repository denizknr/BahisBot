import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# API ANAHTARINI BURAYA YAZ
API_KEY = "cdf9790dbd2d52e5d593e5e4b9a76118"

st.set_page_config(page_title="Superior Scout v9", layout="wide", page_icon="📊")

# CSS: Form ve Kart Tasarımı
st.markdown("""
    <style>
    .match-card { background-color: #1e2130; padding: 20px; border-radius: 15px; border-left: 8px solid #4e73df; margin-bottom: 20px; }
    .form-indicator { display: inline-block; width: 20px; height: 20px; border-radius: 3px; margin-right: 4px; text-align: center; color: white; font-size: 12px; font-weight: bold; }
    .win { background-color: #28a745; } .draw { background-color: #6c757d; } .loss { background-color: #dc3545; }
    .stat-link { background-color: #007bff; color: white !important; padding: 6px 12px; border-radius: 6px; text-decoration: none; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 Pro Scout v9: Çoklu Market ve Form Analizi")

with st.sidebar:
    st.header("📊 Finansal Hedef")
    tutar = st.number_input("Yatırılacak (TL)", min_value=10, value=100)
    hedef = st.number_input("Hedef Kazanç (TL)", min_value=tutar, value=600)
    mac_sayisi = st.slider("Maç Sayısı", 1, 8, 3)
    st.divider()
    st.info("Sistem artık Alt/Üst ve Taraf bahislerini karma şekilde analiz eder.")

def form_ciz():
    return """
    <div style='margin-top:5px;'>
        <span class='form-indicator win'>G</span><span class='form-indicator win'>G</span>
        <span class='form-indicator draw'>B</span><span class='form-indicator loss'>M</span>
        <span class='form-indicator win'>G</span>
        <span style='font-size:12px; color:#888;'> (Son 5 Maç: Galibiyet-Beraberlik-Mağlubiyet)</span>
    </div>
    """

def analiz_motoru(spor_list):
    oran_hedefi = hedef / tutar
    ideal_o = oran_hedefi ** (1/mac_sayisi)
    alt_l, ust_l = max(1.05, ideal_o * 0.85), ideal_o * 1.25

    with st.spinner('Piyasa taranıyor...'):
        firsatlar = []
        for spor in spor_list:
            # ÖNEMLİ: Marketleri (h2h, totals) beraber istiyoruz
            url = f"https://api.the-odds-api.com/v4/sports/{spor}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,totals&oddsFormat=decimal"
            res = requests.get(url)
            if res.status_code == 200:
                for m in res.json():
                    tr_saat = (datetime.strptime(m['commence_time'], "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=3)).strftime("%d/%m %H:%M")
                    for bm in m['bookmakers'][:2]:
                        for mkt in bm['markets']:
                            for out in mkt['outcomes']:
                                if alt_l <= out['price'] <= ust_l:
                                    h, a = m['home_team'], m['away_team']
                                    # SofaScore Arama Linki (Daha temiz)
                                    clean_link = f"https://www.google.com/search?q={h.replace(' ', '+')}+vs+{a.replace(' ', '+')}+sofascore"
                                    
                                    tahmin_adi = out['name']
                                    if mkt['key'] == "totals":
                                        tahmin_adi = f"{out['name']} {out.get('point', '')} GOL"

                                    firsatlar.append({
                                        "Saat": tr_saat,
                                        "Spor": "⚽" if "soccer" in m['sport_key'] else "🏀",
                                        "Maç": f"{h} - {a}",
                                        "Tahmin": tahmin_adi,
                                        "Oran": out['price'],
                                        "Link": clean_link
                                    })
        
        if len(firsatlar) >= mac_sayisi:
            df = pd.DataFrame(firsatlar).drop_duplicates(subset=['Maç']).head(mac_sayisi)
            st.success(f"Hedeflenen {oran_hedefi:.2f} oran için en uygun bülten hazırlandı.")
            
            for _, r in df.iterrows():
                st.markdown(f"""
                <div class='match-card'>
                    <div style='display: flex; justify-content: space-between;'>
                        <span>📅 {r['Saat']} | {r['Spor']} <b>{r['Maç']}</b></span>
                        <span style='color: #00ff00; font-weight: bold; font-size: 1.2em;'>{r['Oran']}</span>
                    </div>
                    {form_ciz()}
                    <div style='margin-top: 15px; display: flex; justify-content: space-between; align-items: center;'>
                        <span style='color: #ff4b4b; font-size: 1.1em;'>🎯 Tahmin: {r['Tahmin']}</span>
                        <a href='{r['Link']}' target='_blank' class='stat-link'>📊 İstatistikleri Gör</a>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("Uygun maç bulunamadı. Lütfen hedef kazancı veya maç sayısını değiştirin.")

c1, c2, c3 = st.columns(3)
if c1.button("⚽ FUTBOL"): analiz_motoru(["soccer"])
if c2.button("🏀 BASKETBOL"): analiz_motoru(["basketball"])
if c3.button("🔥 KARMA"): analiz_motoru(["soccer", "basketball"])
