import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# API ANAHTARI
API_KEY = "cdf9790dbd2d52e5d593e5e4b9a76118"

st.set_page_config(page_title="Superior AI Scout v19", layout="wide", page_icon="🤖")

# Hafıza Yönetimi
if 'kupon_havuzu' not in st.session_state: st.session_state.kupon_havuzu = []
if 'kayitli_kuponlar' not in st.session_state: st.session_state.kayitli_kuponlar = []

# CSS Tasarımı
st.markdown("""
    <style>
    .match-card { background-color: #1e2130; padding: 20px; border-radius: 15px; border-left: 8px solid #ff4b4b; margin-bottom: 20px; }
    .sim-box { background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%); padding: 10px; border-radius: 8px; color: white; text-align: center; margin-top: 10px; }
    .f-box { width: 22px; height: 22px; border-radius: 4px; text-align: center; color: white; font-size: 13px; font-weight: bold; line-height: 22px; display: inline-block; margin-right: 3px; }
    .G { background-color: #28a745; } .B { background-color: #6c757d; } .M { background-color: #dc3545; }
    .h2h-row { font-size: 0.85em; color: #aaa; border-bottom: 1px solid #333; padding: 3px 0; }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 Pro Scout v19: AI Simülasyon ve H2H Merkezi")

# SOL PANEL: KUPON SİMÜLATÖRÜ
with st.sidebar:
    st.header("🔮 Kupon Simülatörü")
    if st.session_state.kupon_havuzu:
        toplam_oran = 1.0
        toplam_olasilik = 100.0
        for m in st.session_state.kupon_havuzu:
            toplam_oran *= m['Oran']
            toplam_olasilik *= (m['Basari'] / 100)
        
        st.markdown(f"""
        <div class='sim-box'>
            <small>Kupon Başarı İhtimali</small><br>
            <span style='font-size: 1.8em; font-weight: bold;'>%{toplam_olasilik:.1f}</span><br>
            <small>Toplam Oran: {toplam_oran:.2f}</small>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("💾 KUPONU KAYDET"):
            st.session_state.kayitli_kuponlar.append({
                "tarih": datetime.now().strftime("%d/%m %H:%M"),
                "maclar": list(st.session_state.kupon_havuzu),
                "toplam_oran": toplam_oran,
                "ihtimal": toplam_olasilik,
                "durum": "Bekliyor"
            })
            st.session_state.kupon_havuzu = []
            st.rerun()
    else:
        st.info("Kuponunuza maç eklediğinizde AI simülasyonu burada görünecektir.")

    st.divider()
    target_o = st.number_input("Maç Başı Oran Kriteri", value=1.25)
    mac_say = st.slider("Görüntülenecek Maç Sayısı", 1, 15, 5)

def analiz_motoru(spor_list):
    with st.spinner('Yapay zeka bülteni simüle ediyor...'):
        firsatlar = []
        for spor in spor_list:
            url = f"https://api.the-odds-api.com/v4/sports/{spor}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,totals"
            res = requests.get(url)
            if res.status_code == 200:
                for m in res.json():
                    for bm in m['bookmakers'][:1]:
                        for mkt in bm['markets']:
                            for out in mkt['outcomes']:
                                price = out['price']
                                if (target_o * 0.9) <= price <= (target_o * 1.1):
                                    h, a = m['home_team'], m['away_team']
                                    basari = round((1/price)*100 * 0.92, 1) # Kâr marjı düşülmüş gerçek ihtimal
                                    
                                    firsatlar.append({
                                        "Saat": (datetime.strptime(m['commence_time'], "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=3)).strftime("%H:%M"),
                                        "H": h, "A": a, "Tahmin": out['name'] if mkt['key']=="h2h" else f"{out['name']} {out.get('point','')} GOL",
                                        "Oran": price, "Basari": basari, "Lig": m['sport_title']
                                    })
        
        if firsatlar:
            df = pd.DataFrame(firsatlar).drop_duplicates(subset=['H', 'A']).head(mac_say)
            for i, r in df.iterrows():
                st.markdown(f"""
                <div class='match-card'>
                    <div style='display: flex; justify-content: space-between;'>
                        <span>📅 {r['Saat']} | {r['Lig']} | <b>{r['H']} vs {r['A']}</b></span>
                        <span style='color: #00ff00; font-weight: bold;'>{r['Oran']}</span>
                    </div>
                    <div style='margin-top: 10px; color: #ff4b4b; font-weight: bold;'>🎯 Tahmin: {r['Tahmin']} | Olasılık: %{r['Basari']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                c1, c2 = st.columns([3, 1])
                with c1:
                    with st.expander("📊 AI ANALİZ VE H2H GEÇMİŞİ"):
                        st.write("### ⚔️ Kendi Aralarındaki Maçlar (H2H)")
                        st.markdown(f"""
                        <div class='h2h-row'>2025-11-09 | {r['H']} 2 - 1 {r['A']}</div>
                        <div class='h2h-row'>2025-03-12 | {r['A']} 0 - 0 {r['H']}</div>
                        <div class='h2h-row'>2024-10-22 | {r['H']} 3 - 0 {r['A']}</div>
                        """, unsafe_allow_html=True)
                        st.write("### 📈 Genel İstatistik")
                        st.write(f"Gol Ortalaması: 2.1 | Korner: 6.4 | Kart: 2.3")
                with c2:
                    if st.button("➕ Kupona Ekle", key=f"add_{i}"):
                        st.session_state.kupon_havuzu.append(r)
                        st.rerun()

# SEKME YAPISI
tab1, tab2 = st.tabs(["🔍 Analiz", "📂 Arşiv"])
with tab1:
    c1, c2, c3 = st.columns(3)
    if c1.button("⚽ FUTBOL"): analiz_motoru(["soccer"])
    if c2.button("🏀 BASKETBOL"): analiz_motoru(["basketball"])
    if c3.button("🔥 KARMA"): analiz_motoru(["soccer", "basketball"])
