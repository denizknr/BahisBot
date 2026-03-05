import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# API ANAHTARINI BURAYA YAZ
API_KEY = "cdf9790dbd2d52e5d593e5e4b9a76118"

st.set_page_config(page_title="Superior Scout v10", layout="wide", page_icon="📈")

# CSS: Form ve Kart Tasarımı
st.markdown("""
    <style>
    .match-card { background-color: #1e2130; padding: 20px; border-radius: 15px; border-left: 8px solid #4e73df; margin-bottom: 20px; }
    .form-box { display: inline-block; width: 18px; height: 18px; border-radius: 3px; margin-right: 2px; text-align: center; color: white; font-size: 11px; font-weight: bold; line-height: 18px; }
    .G { background-color: #28a745; } .B { background-color: #6c757d; } .M { background-color: #dc3545; }
    .stat-link { background-color: #ff4b4b; color: white !important; padding: 8px 15px; border-radius: 8px; text-decoration: none; font-weight: bold; display: inline-block; margin-top: 10px; }
    .success-text { font-weight: bold; color: #00ff00; }
    </style>
    """, unsafe_allow_html=True)

st.title("📈 Pro Scout v10: Akıllı Analiz ve Form Merkezi")

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
    st.info(f"Aranan Oran Aralığı: {ideal_o*0.9:.2f} - {ideal_o*1.1:.2f}")

def form_html(seri):
    html = "<div style='display:inline-block; margin-left:10px;'>"
    for harf in seri:
        html += f"<span class='form-box {harf}'>{harf}</span>"
    html += "</div>"
    return html

def analiz_motoru(spor_list):
    alt_l, ust_l = ideal_o * 0.9, ideal_o * 1.1
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
                                    # Form simülasyonu (Gerçek veri için ek API gerekir, görselleştirme amaçlıdır)
                                    h_form, a_form = "GGBMG", "MBGGM" 
                                    
                                    tahmin = out['name']
                                    if mkt['key'] == "totals": tahmin = f"{out['name']} {out.get('point', '')} GOL"

                                    firsatlar.append({
                                        "Saat": tr_saat,
                                        "Spor": "⚽" if "soccer" in m['sport_key'] else "🏀",
                                        "Maç": f"{h} {form_html(h_form)} vs {a} {form_html(a_form)}",
                                        "Tahmin": tahmin,
                                        "Oran": out['price'],
                                        "Basari": basari,
                                        "Link": f"https://www.google.com/search?q={h.replace(' ', '+')}+vs+{a.replace(' ', '+')}+sofascore"
                                    })
        
        if len(firsatlar) >= 1:
            df = pd.DataFrame(firsatlar).drop_duplicates(subset=['Maç']).head(mac_sayisi)
            for _, r in df.iterrows():
                st.markdown(f"""
                <div class='match-card'>
                    <div style='display: flex; justify-content: space-between;'>
                        <span>📅 {r['Saat']} | {r['Spor']} {r['Maç']}</span>
                        <span style='color: #00ff00; font-weight: bold; font-size: 1.2em;'>{r['Oran']}</span>
                    </div>
                    <div style='margin-top: 10px;'>
                        <span style='color: #ff4b4b; font-size: 1.1em;'>🎯 Tahmin: {r['Tahmin']}</span> | 
                        <span class='success-text'>Güven: %{r['Basari']}</span>
                    </div>
                    <div style='text-align: right;'>
                        <a href='{r['Link']}' target='_blank' class='stat-link'>📊 Analizi Gör</a>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("Uygun maç bulunamadı. Kriterleri esnetin.")

# Ana Sekmeler
tab1, tab2 = st.tabs(["🔍 Analiz Paneli", "📂 Arşiv"])
with tab1:
    c1, c2, c3 = st.columns(3)
    if c1.button("⚽ FUTBOL"): analiz_motoru(["soccer"])
    if c2.button("🏀 BASKETBOL"): analiz_motoru(["basketball"])
    if c3.button("🔥 KARMA"): analiz_motoru(["soccer", "basketball"])
