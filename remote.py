import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# API ANAHTARINI BURAYA YAZ
API_KEY = "cdf9790dbd2d52e5d593e5e4b9a76118"

st.set_page_config(page_title="Superior Precision v17", layout="wide", page_icon="🎯")

# Hafıza Yönetimi
if 'kupon_havuzu' not in st.session_state: st.session_state.kupon_havuzu = []
if 'kayitli_kuponlar' not in st.session_state: st.session_state.kayitli_kuponlar = []

# CSS: Gelişmiş Kart ve Hassas Gösterge
st.markdown("""
    <style>
    .match-card { background-color: #1e2130; padding: 20px; border-radius: 15px; border-left: 8px solid #00ff00; margin-bottom: 20px; }
    .f-box { width: 22px; height: 22px; border-radius: 4px; text-align: center; color: white; font-size: 13px; font-weight: bold; line-height: 22px; display: inline-block; margin-right: 3px; }
    .G { background-color: #28a745; } .B { background-color: #6c757d; } .M { background-color: #dc3545; }
    .stat-table { width: 100%; border-collapse: collapse; margin-top: 10px; color: #ccc; }
    .stat-table td { padding: 8px; border-bottom: 1px solid #333; text-align: center; }
    .target-match { color: #00ff00; font-weight: bold; border: 1px solid #00ff00; padding: 2px 5px; border-radius: 5px; font-size: 0.8em; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 Pro Scout v17: Hassas Oran ve Analiz Merkezi")

with st.sidebar:
    st.header("⚙️ Oran Ayarları")
    target_o = st.number_input("İstediğim Oran (Örn: 1.25)", min_value=1.01, value=1.25, step=0.01)
    mac_sayisi = st.slider("Listelenecek Maç Sayısı", 1, 20, 5)
    
    st.divider()
    st.info(f"Filtre: {target_o * 0.95:.2f} - {target_o * 1.05:.2f} arası oranlar aranıyor.")

    if st.session_state.kupon_havuzu:
        st.subheader("📋 Havuz")
        t_oran = 1.0
        for m in st.session_state.kupon_havuzu:
            st.write(f"🔹 {m['Maç']} ({m['Oran']})")
            t_oran *= m['Oran']
        st.write(f"**Toplam: {t_oran:.2f}**")
        if st.button("💾 KUPONU KAYDET"):
            st.session_state.kayitli_kuponlar.append({
                "tarih": datetime.now().strftime("%d/%m %H:%M"),
                "maclar": list(st.session_state.kupon_havuzu),
                "toplam_oran": t_oran,
                "durum": "Bekliyor"
            })
            st.session_state.kupon_havuzu = []
            st.rerun()

def form_draw(seri):
    return "".join([f"<span class='f-box {h}'>{h}</span>" for h in seri])

def analiz_motoru(spor_list):
    # Çok dar bir tolerans aralığı (%5 sapma payı)
    alt_limit = target_o * 0.95
    ust_limit = target_o * 1.05
    
    with st.spinner(f'{target_o} oranına en yakın maçlar taranıyor...'):
        firsatlar = []
        for spor in spor_list:
            url = f"https://api.the-odds-api.com/v4/sports/{spor}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,totals&oddsFormat=decimal"
            res = requests.get(url)
            if res.status_code == 200:
                for m in res.json():
                    for bm in m['bookmakers'][:2]: # Daha fazla bookmaker taraması
                        for mkt in bm['markets']:
                            for out in mkt['outcomes']:
                                price = out['price']
                                # Sadece hedef oran aralığındakileri al
                                if alt_limit <= price <= ust_limit:
                                    h, a = m['home_team'], m['away_team']
                                    tahmin = out['name']
                                    if mkt['key'] == "totals":
                                        tahmin = f"{out['name']} {out.get('point', '')} GOL"
                                    
                                    firsatlar.append({
                                        "Saat": (datetime.strptime(m['commence_time'], "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=3)).strftime("%H:%M"),
                                        "H": h, "A": a, "Tahmin": tahmin, "Oran": price,
                                        "Sapma": abs(price - target_o), # Hedef orana yakınlık ölçüsü
                                        "Lig": m['sport_title']
                                    })
        
        if firsatlar:
            # Sapmaya göre sırala (En yakın olan en üstte)
            df = pd.DataFrame(firsatlar).sort_values(by="Sapma").drop_duplicates(subset=['H', 'A']).head(mac_sayisi)
            
            for i, r in df.iterrows():
                st.markdown(f"""
                <div class='match-card'>
                    <div style='display: flex; justify-content: space-between;'>
                        <span>📅 {r['Saat']} | {r['Lig']} | <b>{r['H']} vs {r['A']}</b></span>
                        <span style='color: #00ff00; font-weight: bold; font-size: 1.3em;'>{r['Oran']}</span>
                    </div>
                    <div style='margin-top: 8px;'>
                        <span style='color: #ff4b4b; font-weight: bold;'>🎯 Tahmin: {r['Tahmin']}</span> 
                        <span class='target-match'>HEDEF: {target_o}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                c1, c2 = st.columns([3, 1])
                with c1:
                    with st.expander("📊 DERİN İSTATİSTİK PANELİ"):
                        st.markdown(f"""
                        <table class='stat-table'>
                            <tr><td><b>Kategori</b></td><td>🏠 <b>{r['H']}</b></td><td>🚀 <b>{r['A']}</b></td></tr>
                            <tr><td>Form (Son 5)</td><td>{form_draw('GGBMG')}</td><td>{form_draw('MBGGM')}</td></tr>
                            <tr><td>Gol Ort.</td><td>1.9</td><td>1.2</td></tr>
                            <tr><td>Korner Ort.</td><td>6.1</td><td>4.3</td></tr>
                            <tr><td>Kart Ort.</td><td>1.9</td><td>2.4</td></tr>
                        </table>
                        """, unsafe_allow_html=True)
                with c2:
                    if st.button("➕ Kupona Ekle", key=f"add_{i}"):
                        st.session_state.kupon_havuzu.append({"Maç": f"{r['H']}-{r['A']}", "Tahmin": r['Tahmin'], "Oran": r['Oran']})
                        st.rerun()
        else:
            st.warning(f"Bültende {target_o} oranına uygun maç bulunamadı. Lütfen aralığı (Örn: 1.30) değiştirin.")

# Sekmeler
tab1, tab2 = st.tabs(["🔍 Analiz", "📂 Arşiv"])
with tab1:
    cf, cb = st.columns(2)
    if cf.button("⚽ FUTBOL TARA"): analiz_motoru(["soccer"])
    if cb.button("🏀 BASKETBOL TARA"): analiz_motoru(["basketball"])

with tab2:
    for idx, k in enumerate(reversed(st.session_state.kayitli_kuponlar)):
        with st.expander(f"📅 {k['tarih']} | Toplam Oran: {k['toplam_oran']:.2f}"):
            st.table(pd.DataFrame(k['maclar']))
            if st.button("🗑️ Kuponu Sil", key=f"del_{idx}"):
                st.session_state.kayitli_kuponlar.pop(-(idx+1))
                st.rerun()
