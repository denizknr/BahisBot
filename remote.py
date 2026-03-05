import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# API anahtarını buraya ekle
API_KEY = "cdf9790dbd2d52e5d593e5e4b9a76118"

st.set_page_config(page_title="Superior Scout v4", layout="wide", page_icon="📈")

if 'arsiv' not in st.session_state: st.session_state.arsiv = []

st.markdown("""
    <style>
    .form-win { color: #28a745; font-weight: bold; }
    .form-loss { color: #dc3545; font-weight: bold; }
    .match-card { background-color: #1e2130; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📈 Pro Scout: Form ve Analiz Merkezi")

with st.sidebar:
    st.header("📊 Finansal Ayarlar")
    tutar = st.number_input("Yatırılacak Tutar (TL)", min_value=10, value=100)
    hedef = st.number_input("Hedef Kazanç (TL)", min_value=tutar, value=400)
    mac_sayisi = st.slider("Maç Sayısı", 1, 8, 3)
    
    st.divider()
    st.header("⚙️ Marketler (Türkçe)")
    market_map = {"Maç Sonucu": "h2h", "Alt / Üst": "totals", "Çifte Şans": "double_chance", "Handikap": "spreads"}
    secili = st.multiselect("Aktif Marketler", list(market_map.keys()), default=["Maç Sonucu", "Alt / Üst"])
    market_kodlari = [market_map[m] for m in secili]
    
    st.divider()
    min_oran = st.number_input("Min Oran", value=1.05)
    v_kaynagi = st.selectbox("İstatistik Sitesi", ["SofaScore", "AiScore"])

def analiz_motoru(spor_keys):
    oran_hedefi = hedef / tutar
    ideal_o = oran_hedefi ** (1/mac_sayisi)
    alt_l, ust_l = max(min_oran, ideal_o * 0.85), ideal_o * 1.20
    
    with st.spinner('Global bülten ve form verileri taranıyor...'):
        tum_firsatlar = []
        for spor in spor_keys:
            m_query = ",".join(market_kodlari)
            url = f"https://api.the-odds-api.com/v4/sports/{spor}/odds/?apiKey={API_KEY}&regions=eu&markets={m_query}"
            res = requests.get(url)
            if res.status_code == 200:
                for m in res.json():
                    tr_saat = datetime.strptime(m['commence_time'], "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=3)
                    for bm in m['bookmakers'][:1]:
                        for mkt in bm['markets']:
                            for out in mkt['outcomes']:
                                if alt_l <= out['price'] <= ust_l:
                                    h, a = m['home_team'], m['away_team']
                                    link = f"https://www.sofascore.com/search?q={h}+vs+{a}" if v_kaynagi=="SofaScore" else f"https://www.aiscore.com/search/{h}+{a}"
                                    tum_firsatlar.append({
                                        "Saat": tr_saat.strftime("%H:%M"),
                                        "Spor": "⚽" if "soccer" in m['sport_key'] else "🏀",
                                        "Maç": f"{h} - {a}",
                                        "Tahmin": f"{out['name']} ({out.get('point', '')})" if 'point' in out else out['name'],
                                        "Oran": out['price'],
                                        "Link": link,
                                        "Lig": m['sport_title']
                                    })
        
        if len(tum_firsatlar) >= mac_sayisi:
            df = pd.DataFrame(tum_firsatlar).drop_duplicates(subset=['Maç']).head(mac_sayisi)
            
            st.success(f"✅ Analiz Tamam! Toplam Oran: {df['Oran'].prod():.2f}")
            
            for _, r in df.iterrows():
                st.markdown(f"""
                <div class="match-card">
                    <b>{r['Saat']} | {r['Spor']} {r['Maç']}</b> ({r['Lig']})<br>
                    <span style="color: #ff4b4b;">Tahmin: {r['Tahmin']}</span> | <b>Oran: {r['Oran']}</b>
                </div>
                """, unsafe_allow_html=True)
                
                c1, c2 = st.columns([2, 1])
                c1.info(f"🔍 Son 5 Maçlık Form ve H2H İstatistikleri için {v_kaynagi} panelini inceleyin.")
                c2.markdown(f"[📊 Formu Gör]({r['Link']})")
                st.divider()

            if st.button("📥 Kuponu Kaydet"):
                st.session_state.arsiv.append({"tarih": datetime.now().strftime("%d/%m/%Y %H:%M"), "detay": df.to_dict('records'), "oran": df['Oran'].prod()})
                st.toast("Kupon arşive eklendi!")
        else:
            st.warning("Eşleşen maç bulunamadı.")

tab1, tab2 = st.tabs(["🔍 Canlı Analiz", "📂 Arşiv"])
with tab1:
    c_f, c_b, c_k = st.columns(3)
    if c_f.button("⚽ FUTBOL"): analiz_motoru(["soccer"])
    if c_b.button("🏀 BASKETBOL"): analiz_motoru(["basketball"])
    if c_k.button("🔥 KARMA"): analiz_motoru(["soccer", "basketball"])
with tab2:
    for i, k in enumerate(reversed(st.session_state.arsiv)):
        with st.expander(f"📅 {k['tarih']} | Oran: {k['oran']:.2f}"):
            st.table(pd.DataFrame(k['detay']).drop('Link', axis=1))
