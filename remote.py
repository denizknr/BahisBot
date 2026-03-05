import streamlit as st
import requests
import pandas as pd

# API anahtarını buraya ekle
API_KEY = "cdf9790dbd2d52e5d593e5e4b9a76118"

st.set_page_config(page_title="Global Multi-Market Analiz", layout="wide")

# Görsel Stil
st.markdown("""
    <style>
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3e445e; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #ff4b4b; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🌍 Global Bahis ve Market Analiz Sistemi")

# Sol Panel: Finansal ve Teknik Ayarlar
with st.sidebar:
    st.header("📊 Strateji Ayarları")
    tutar = st.number_input("Yatırılacak Tutar (TL)", min_value=10, value=100)
    hedef = st.number_input("Hedeflenen Kazanç (TL)", min_value=tutar, value=400)
    mac_sayisi = st.slider("Maç Sayısı", 1, 5, 3)
    
    st.divider()
    market_tipi = st.multiselect("Market Seçenekleri", ["h2h", "totals"], default=["h2h", "totals"])
    st.caption("h2h: Taraf Bahsi | totals: Alt/Üst")

# Spor ve Lig Veritabanı
ligler = {
    "Futbol": [
        {"name": "Tüm Dünyadan Karışık", "key": "soccer"},
        {"name": "İngiltere Premier Lig", "key": "soccer_epl"},
        {"name": "Şampiyonlar Ligi", "key": "soccer_uefa_champs_league"},
        {"name": "Türkiye Süper Lig", "key": "soccer_turkey_super_league"},
        {"name": "İspanya La Liga", "key": "soccer_spain_la_liga"},
        {"name": "Almanya Bundesliga", "key": "soccer_germany_bundesliga"}
    ],
    "Basketbol": [
        {"name": "NBA", "key": "basketball_nba"},
        {"name": "EuroLeague", "key": "basketball_euroleague"},
        {"name": "İspanya ACB", "key": "basketball_spain_acb"},
        {"name": "Fransa LNB", "key": "basketball_france_lnb"}
    ]
}

tab_f, tab_b = st.tabs(["⚽ Futbol Dünyası", "🏀 Basketbol Dünyası"])

def analiz_et(spor_key):
    markets = ",".join(market_tipi)
    url = f"https://api.the-odds-api.com/v4/sports/{spor_key}/odds/?apiKey={API_KEY}&regions=eu&markets={markets}&oddsFormat=decimal"
    
    with st.spinner('Global marketler taranıyor...'):
        res = requests.get(url)
        if res.status_code == 200:
            data = res.json()
            if not data:
                st.warning("Seçilen ligde şu an aktif maç bulunamadı.")
                return

            oran_hedefi = hedef / tutar
            mac_basi_oran = oran_hedefi ** (1/mac_sayisi)
            
            c1, c2 = st.columns(2)
            c1.metric("Toplam Çarpan Hedefi", f"{oran_hedefi:.2f}x")
            c2.metric("Gereken Ortalama Oran", f"{mac_basi_oran:.2f}")

            oneriler = []
            for m in data:
                try:
                    for bookmaker in m['bookmakers']:
                        for market in bookmaker['markets']:
                            for outcome in market['outcomes']:
                                # Oran filtreleme
                                if (mac_basi_oran - 0.3) <= outcome['price'] <= (mac_basi_oran + 0.3):
                                    label = outcome['name']
                                    # Alt/Üst ise baremi de ekle
                                    if 'point' in outcome:
                                        label = f"{outcome['name']} {outcome['point']}"
                                    
                                    oneriler.append({
                                        "Maç": f"{m['home_team']} vs {m['away_team']}",
                                        "Market": market['key'].upper(),
                                        "Tahmin": label,
                                        "Oran": outcome['price'],
                                        "Lig": m['sport_title']
                                    })
                                    break
                            if len(oneriler) >= mac_sayisi: break
                        if len(oneriler) >= mac_sayisi: break
                except: continue
                if len(oneriler) >= mac_sayisi: break

            if len(oneriler) >= mac_sayisi:
                st.table(pd.DataFrame(oneriler))
                st.success(f"Analiz Tamamlandı. Toplam Kupon Oranı: {pd.DataFrame(oneriler)['Oran'].prod():.2f}")
            else:
                st.error("Kriterlere uygun yeterli market bulunamadı.")
        else:
            st.error(f"Hata: {res.status_code}. API limitinizi veya anahtarınızı kontrol edin.")

with tab_f:
    secili_lig_f = st.selectbox("Lig Seçin (Futbol)", [l['name'] for l in ligler['Futbol']])
    f_key = [l['key'] for l in ligler['Futbol'] if l['name'] == secili_lig_f][0]
    if st.button("Futbol Marketlerini Tara"):
        analiz_et(f_key)

with tab_b:
    secili_lig_b = st.selectbox("Lig Seçin (Basketbol)", [l['name'] for l in ligler['Basketbol']])
    b_key = [l['key'] for l in ligler['Basketbol'] if l['name'] == secili_lig_b][0]
    if st.button("Basketbol Marketlerini Tara"):
        analiz_et(b_key)

