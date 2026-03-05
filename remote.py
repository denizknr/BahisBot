import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# API ANAHTARINI BURAYA YAZ
API_KEY = "cdf9790dbd2d52e5d593e5e4b9a76118"

st.set_page_config(page_title="Superior Scout v8", layout="wide", page_icon="📈")

# Görsel İyileştirmeler
st.markdown("""
    <style>
    .match-card { background-color: #1e2130; padding: 20px; border-radius: 15px; border-left: 8px solid #4e73df; margin-bottom: 20px; }
    .success-bar-bg { background-color: #333; border-radius: 6px; width: 100%; height: 12px; margin-top: 8px; }
    .success-bar-fill { height: 12px; border-radius: 6px; transition: width 0.5s ease-in-out; }
    .stat-link { background-color: #ff4b4b; color: white !important; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-weight: bold; display: inline-block; margin-top: 10px; }
    .stat-link-alt { background-color: #2b2d42; color: #8d99ae !important; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-size: 0.9em; margin-left: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📈 Pro Scout v8: Gelişmiş İstatistik ve Başarı Analizi")

with st.sidebar:
    st.header("📊 Analiz Ayarları")
    tutar = st.number_input("Yatırılacak (TL)", min_value=10, value=100)
    hedef = st.number_input("Hedef Kazanç (TL)", min_value=tutar, value=500)
    mac_sayisi = st.slider("Maç Sayısı", 1, 10, 3)
    st.divider()
    min_o = st.number_input("Min Oran", value=1.05, step=0.01)

def basari_rengi(yuzde):
    if yuzde > 75: return "#28a745"
    if yuzde > 55: return "#ffc107"
    return "#dc3545"

def analiz_motoru(spor_list, baslik):
    oran_hedefi = hedef / tutar
    ideal_o = oran_hedefi ** (1/mac_sayisi)
    alt_l, ust_l = max(min_o, ideal_o * 0.75), ideal_o * 1.5

    with st.spinner(f'{baslik} bülteni derinlemesine taranıyor...'):
        firsatlar = []
        for spor in spor_list:
            url = f"https://api.the-odds-api.com/v4/sports/{spor}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,totals&oddsFormat=decimal"
            res = requests.get(url)
            if res.status_code == 200:
                for m in res.json():
                    tr_saat = datetime.strptime(m['commence_time'], "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=3)
                    for bm in m['bookmakers'][:2]:
                        for mkt in bm['markets']:
                            for out in mkt['outcomes']:
                                if alt_l <= out['price'] <= ust_l:
                                    prob = (1 / out['price']) * 100
                                    h, a = m['home_team'], m['away_team']
                                    # SofaScore ve AiScore Linklerini Temizleme
                                    sofa_l = f"https://www.sofascore.com/search?q={h.replace(' ', '+')}+{a.replace(' ', '+')}"
                                    ai_l = f"https://www.aiscore.com/search/{h.replace(' ', '+')}+{a.replace(' ', '+')}"
                                    
                                    firsatlar.append({
                                        "Saat": tr_saat.strftime("%d/%m %H:%M"),
                                        "Spor": "⚽" if "soccer" in m['sport_key'] else "🏀",
                                        "Maç": f"{h} - {a}",
                                        "Tahmin": f"{out['name']} ({out.get('point', '')})" if 'point' in out else out['name'],
                                        "Oran": out['price'],
                                        "Başarı": round(prob, 1),
                                        "Sofa": sofa_l,
                                        "Ai": ai_l
                                    })
        
        if len(firsatlar) >= mac_sayisi:
            df = pd.DataFrame(firsatlar).drop_duplicates(subset=['Maç'])
            df = df.sort_values(by="Başarı", ascending=False).head(mac_sayisi * 2)
            
            st.subheader(f"✅ {baslik} Market Analizi")
            
            for _, r in df.iterrows():
                b_renk = basari_rengi(r['Başarı'])
                st.markdown(f"""
                <div class="match-card">
                    <div style="display: flex; justify-content: space-between;">
                        <span><b>{r['Saat']}</b> | {r['Spor']} <b>{r['Maç']}</b></span>
                        <span style="font-size: 1.3em; font-weight: bold; color: {b_renk};">{r['Oran']}</span>
                    </div>
                    <div style="margin: 10px 0; color: #ff4b4b; font-size: 1.1em;">Tahmin: {r['Tahmin']}</div>
                    <div style="width: 100%;">
                        <span style="font-size: 0.85em; color: #bbb;">Güven Endeksi: %{r['Başarı']}</span>
                        <div class="success-bar-bg"><div class="success-bar-fill" style="width: {r['Başarı']}%; background-color: {b_renk};"></div></div>
                    </div>
                    <div style="margin-top: 15px;">
                        <a href="{r['Sofa']}" target="_blank" class="stat-link">📊 SofaScore Form</a>
                        <a href="{r['Ai']}" target="_blank" class="stat-link-alt">🔍 AiScore Alternatif</a>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("Bu kriterlerde uygun maç bulunamadı. Lütfen 'Hedef Kazanç' miktarını artırın.")

# Arayüz Butonları
st.write("### 🏟️ Analiz Başlat")
c1, c2, c3 = st.columns(3)
if c1.button("⚽ FUTBOL TARA", use_container_width=True): analiz_motoru(["soccer"], "Futbol")
if c2.button("🏀 BASKETBOL TARA", use_container_width=True): analiz_motoru(["basketball"], "Basketbol")
if c3.button("🔥 KARMA ANALİZ", use_container_width=True): analiz_motoru(["soccer", "basketball"], "Karma")
