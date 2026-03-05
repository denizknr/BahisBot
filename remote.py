import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# API ANAHTARINI BURAYA YAZ
API_KEY = "cdf9790dbd2d52e5d593e5e4b9a76118"

st.set_page_config(page_title="Superior Scout v11", layout="wide", page_icon="📈")

# CSS: Gelişmiş Kart ve Form Tasarımı
st.markdown("""
    <style>
    .match-card { background-color: #1e2130; padding: 20px; border-radius: 15px; border-left: 8px solid #4e73df; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    .form-container { display: flex; gap: 3px; margin-left: 10px; }
    .f-box { width: 20px; height: 20px; border-radius: 4px; text-align: center; color: white; font-size: 12px; font-weight: bold; line-height: 20px; }
    .G { background-color: #28a745; } .B { background-color: #6c757d; } .M { background-color: #dc3545; }
    .success-badge { background-color: #00ff00; color: #000; padding: 2px 8px; border-radius: 10px; font-weight: bold; font-size: 0.8em; }
    .stat-btn { background-color: #ff4b4b; color: white !important; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: bold; display: inline-block; }
    </style>
    """, unsafe_allow_html=True)

st.title("📈 Pro Scout v11: Nihai Analiz Merkezi")

with st.sidebar:
    st.header("⚙️ Arama Modu")
    mod = st.radio("Seçim Yöntemi", ["Finansal Hedef", "Doğrudan Oran"])
    
    if mod == "Finansal Hedef":
        tutar = st.number_input("Yatırılacak (TL)", min_value=10, value=100)
        hedef = st.number_input("Hedef Kazanç (TL)", min_value=tutar, value=300)
        mac_sayisi = st.slider("Maç Sayısı", 1, 8, 3)
        ideal_o = (hedef / tutar) ** (1/mac_sayisi)
    else:
        ideal_o = st.number_input("İstediğim Maç Başı Oran", min_value=1.01, value=1.20, step=0.01)
        mac_sayisi = st.slider("Listelenecek Maç Sayısı", 1, 15, 5)
    
    st.divider()
    st.info(f"Hedeflenen Oran: {ideal_o:.2f}")

def generate_form(seri):
    return "".join([f"<span class='f-box {h}'>{h}</span>" for h in seri])

def analiz_motoru(spor_list):
    alt_l, ust_l = ideal_o * 0.85, ideal_o * 1.25 # Genişletilmiş aralık
    with st.spinner('Piyasa taranıyor...'):
        firsatlar = []
        for spor in spor_list:
            url = f"https://api.the-odds-api.com/v4/sports/{spor}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,totals&oddsFormat=decimal"
            res = requests.get(url)
            if res.status_code == 200:
                for m in res.json():
                    tr_saat = (datetime.strptime(m['commence_time'], "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=3)).strftime("%d/%m %H:%M")
                    for bm in m['bookmakers'][:1]:
                        for mkt in bm['markets']:
                            for out in mkt['outcomes']:
                                if alt_l <= out['price'] <= ust_l:
                                    h, a = m['home_team'], m['away_team']
                                    basari = round((1/out['price']) * 100, 1)
                                    # Form simülasyonu
                                    h_f, a_f = generate_form("GGBMG"), generate_form("MBGGM")
                                    
                                    tahmin = out['name']
                                    if mkt['key'] == "totals": tahmin = f"{out['name']} {out.get('point', '')} GOL"

                                    firsatlar.append({
                                        "Saat": tr_saat,
                                        "Spor": "⚽" if "soccer" in m['sport_key'] else "🏀",
                                        "H": h, "A": a, "HF": h_f, "AF": a_f,
                                        "Tahmin": tahmin,
                                        "Oran": out['price'],
                                        "Basari": basari,
                                        "Link": f"https://www.sofascore.com/search?q={h.replace(' ', '+')}+{a.replace(' ', '+')}"
                                    })
        
        if firsatlar:
            df = pd.DataFrame(firsatlar).drop_duplicates(subset=['H', 'A']).head(mac_sayisi)
            for _, r in df.iterrows():
                st.markdown(f"""
                <div class='match-card'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div style='font-size: 1.1em;'>
                            📅 {r['Saat']} | {r['Spor']} <b>{r['H']}</b> {r['HF']} <span style='color:#666;'>vs</span> <b>{r['A']}</b> {r['AF']}
                        </div>
                        <div style='color: #00ff00; font-weight: bold; font-size: 1.3em;'>{r['Oran']}</div>
                    </div>
                    <div style='margin-top: 15px; display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <span style='color: #ff4b4b; font-size: 1.1em; font-weight: bold;'>🎯 Tahmin: {r['Tahmin']}</span>
                            <span class='success-badge'>%{r['Basari']} Güven</span>
                        </div>
                        <a href='{r['Link']}' target='_blank' class='stat-btn'>📊 SofaScore Verileri</a>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("Uygun maç bulunamadı. Lütfen kriterleri esnetin.")

tab1, tab2 = st.tabs(["🔍 Canlı Analiz", "📂 Arşiv"])
with tab1:
    c1, c2, c3 = st.columns(3)
    if c1.button("⚽ FUTBOL"): analiz_motoru(["soccer"])
    if c2.button("🏀 BASKETBOL"): analiz_motoru(["basketball"])
    if c3.button("🔥 KARMA"): analiz_motoru(["soccer", "basketball"])
