import streamlit as st
import requests
import pandas as pd

# API anahtarını buraya ekle
API_KEY = "cdf9790dbd2d52e5d593e5e4b9a76118"

st.set_page_config(page_title="Superior Multi-Market Analiz", layout="wide")

# Görsel Stil Geliştirmeleri
st.markdown("""
    <style>
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3e445e; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #ff4b4b; color: white; font-weight: bold; }
    th { background-color: #262730 !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🌍 Global Çoklu Market Analiz Sistemi")

# Sol Panel: Finansal ve Teknik Ayarlar
with st.sidebar:
    st.header("📊 Strateji Ayarları")
    tutar = st.number_input("Yatırılacak Tutar (TL)", min_value=10, value=100)
    hedef = st.number_input("Hedeflenen Kazanç (TL)", min_value=tutar, value=500)
    mac_sayisi = st.slider("Kupon Maç Sayısı", 1, 10, 3)
    
    st.divider()
    marketler = st.multiselect("Aktif Marketler", 
                              ["h2h", "totals", "spreads"], 
                              default=["h2h", "totals"])
    st.caption("h2h: Taraf | totals: Alt/Üst | spreads: Handikap")

# Dinamik Lig Listesi
spor_dallari = {
    "Futbol": "soccer",
    "Basketbol": "basketball"
}

tab_f, tab_b = st.tabs(["⚽ Futbol (Tüm Ligler)", "🏀 Basketbol (Tüm Ligler)"])

def bulten_tara(spor_key):
    # Tüm aktif ligleri çek
    with st.spinner('Global ligler ve marketler analiz ediliyor...'):
        # 1. Önce o spor dalındaki tüm aktif ligleri al
        lig_url = f"https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}"
        lig_res = requests.get(lig_url)
        
        if lig_res.status_code != 200:
            st.error("API Bağlantı Hatası!")
            return

        aktif_ligler = [l['key'] for l in lig_res.json() if l['group'] == spor_key]
        
        # 2. Oran hesaplamaları
        oran_hedefi = hedef / tutar
        mac_basi_ideal = oran_hedefi ** (1/mac_sayisi)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Toplam Çarpan Hedefi", f"{oran_hedefi:.2f}x")
        c2.metric("Maç Başı Gereken Oran", f"{mac_basi_ideal:.2f}")
        c3.metric("Taranan Lig Sayısı", len(aktif_ligler))

        tum_secenekler = []
        market_str = ",".join(marketler)

        # 3. Her ligi tara (Ücretsiz planda limit dolmaması için ilk 15 aktif lig)
        for lig in aktif_ligler[:15]:
            odds_url = f"https://api.the-odds-api.com/v4/sports/{lig}/odds/?apiKey={API_KEY}&regions=eu&markets={market_str}&oddsFormat=decimal"
            o_res = requests.get(odds_url)
            if o_res.status_code == 200:
                data = o_res.json()
                for match in data:
                    home = match['home_team']
                    away = match['away_team']
                    league_name = match['sport_title']
                    
                    for bookmaker in match['bookmakers']:
                        for market in bookmaker['markets']:
                            for outcome in market['outcomes']:
                                # Filtreleme: İdeal orana %20 tolerans ile yaklaş
                                if (mac_basi_ideal * 0.85) <= outcome['price'] <= (mac_basi_ideal * 1.15):
                                    label = outcome['name']
                                    if 'point' in outcome: # Alt/Üst veya Handikap ise baremi ekle
                                        label = f"{outcome['name']} ({outcome['point']})"
                                    
                                    tum_secenekler.append({
                                        "Lig": league_name,
                                        "Maç": f"{home} - {away}",
                                        "Market": market['key'].upper(),
                                        "Tahmin": label,
                                        "Oran": outcome['price']
                                    })

        # 4. Sonuçları Göster
        if len(tum_secenekler) >= mac_sayisi:
            st.subheader("📋 Kriterlerinize Uygun En İyi Seçenekler")
            df = pd.DataFrame(tum_secenekler).drop_duplicates(subset=['Maç']) # Aynı maçı tekrar etme
            st.dataframe(df.head(mac_sayisi * 2), use_container_width=True)
            
            # Örnek Kupon Oluştur
            kupon = df.sample(min(mac_sayisi, len(df)))
            st.success(f"✅ Örnek Kupon Hazır! Toplam Oran: {kupon['Oran'].prod():.2f}")
            st.table(kupon)
        else:
            st.warning("Eşleşen sonuç bulunamadı. Lütfen oran hedefini veya market seçeneklerini esnetin.")

with tab_f:
    if st.button("🔥 Tüm Futbol Dünyasını Tara"):
        bulten_tara("soccer")

with tab_b:
    if st.button("🔥 Tüm Basketbol Dünyasını Tara"):
        bulten_tara("basketball")
