import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# API ANAHTARI
API_KEY = "cdf9790dbd2d52e5d593e5e4b9a76118"

st.set_page_config(page_title="Superior Scout v29", layout="wide", page_icon="⚡")

# 1. SESSION STATE (Hafıza Yönetimi)
if 'kupon_havuzu' not in st.session_state: st.session_state.kupon_havuzu = []
if 'arsiv' not in st.session_state: st.session_state.arsiv = []

# 2. CALLBACK FONKSİYONLARI (Dinamik Ekleme İçin)
def mac_ekle(mac_adi, tahmin, oran):
    # Bu fonksiyon sayfa yenilenmeden önce veriyi hafızaya atar
    st.session_state.kupon_havuzu.append({
        "Maç": mac_adi,
        "Tahmin": tahmin,
                "Oran": oran
    })
    st.toast(f"✅ {mac_adi} eklendi!")

# 3. GÖRSEL AYARLAR (CSS)
st.markdown("""
    <style>
    .match-card { background-color: #1e2130; padding: 15px; border-radius: 12px; border-left: 6px solid #4e73df; margin-bottom: 12px; }
    .f-box { width: 22px; height: 22px; border-radius: 4px; text-align: center; color: white; font-size: 13px; font-weight: bold; line-height: 22px; display: inline-block; margin-right: 3px; }
    .G { background-color: #28a745; } .B { background-color: #6c757d; } .M { background-color: #dc3545; }
    .stat-row { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid #333; font-size: 0.85em; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ Pro Scout v29: Dinamik Mobil Analiz")

# 4. SOL PANEL (Daima Güncel)
with st.sidebar:
    st.header("⚙️ Ayarlar & Kupon")
    mod = st.radio("Arama Modu", ["Finansal Hedef", "Doğrudan Oran"])
    tutar = st.number_input("Tutar (TL)", min_value=10, value=100)
    
    if mod == "Finansal Hedef":
        hedef = st.number_input("Hedef Kazanç", value=400)
        target_o = (hedef / tutar) ** (1/3)
    else:
        target_o = st.number_input("Oran Kriteri", value=1.25)

    st.divider()
    st.subheader("📋 Kupon Havuzu")
    if st.session_state.kupon_havuzu:
        t_oran = 1.0
        for idx, m in enumerate(st.session_state.kupon_havuzu):
            st.write(f"🔹 **{m['Maç']}** ({m['Oran']})")
            t_oran *= m['Oran']
        
        st.success(f"Oran: {t_oran:.2f} | Kazanç: {t_oran * tutar:.2f} TL")
        
        if st.button("💾 KUPONU KAYDET", use_container_width=True):
            st.session_state.arsiv.append({"tarih": datetime.now().strftime("%d/%m %H:%M"), "maclar": list(st.session_state.kupon_havuzu), "oran": t_oran, "durum": "Bekliyor"})
            st.session_state.kupon_havuzu = []
            st.rerun()
    else:
        st.info("Maç ekleyin...")

# 5. ANALİZ MOTORU
def analiz_motoru(spor_list):
    alt_l, ust_l = target_o * 0.90, target_o * 1.10
    with st.spinner('Piyasa taranıyor...'):
        url = f"https://api.the-odds-api.com/v4/sports/{spor_list[0]}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,totals"
        res = requests.get(url)
        if res.status_code == 200:
            firsatlar = []
            for m in res.json():
                for bm in m['bookmakers'][:1]:
                    for mkt in bm['markets']:
                        for out in mkt['outcomes']:
                            if alt_l <= out['price'] <= ust_l:
                                firsatlar.append({
                                    "Saat": (datetime.strptime(m['commence_time'], "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=3)).strftime("%H:%M"),
                                    "H": m['home_team'], "A": m['away_team'], "Lig": m['sport_title'],
                                    "Tahmin": out['name'] if mkt['key']=="h2h" else f"{out['name']} {out.get('point','')} G",
                                    "Oran": out['price']
                                })
            
            if firsatlar:
                df = pd.DataFrame(firsatlar).drop_duplicates(subset=['H', 'A']).head(12)
                for i, r in df.iterrows():
                    st.markdown(f"""
                    <div class='match-card'>
                        <b>{r['Saat']} | {r['H']} vs {r['A']}</b><br>
                        <span style='color:#00ff00;'>Oran: {r['Oran']}</span> | <span style='color:#ff4b4b;'>Tahmin: {r['Tahmin']}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        with st.expander("📊 Veriler"):
                            st.markdown(f"<div class='stat-row'><span>Sıralama</span><span>Ev: 4. / Dep: 14.</span></div>", unsafe_allow_html=True)
                            st.markdown(f"<div class='stat-row'><span>Gol Ort.</span><span>Ev: 1.9 / Dep: 1.2</span></div>", unsafe_allow_html=True)
                    with c2:
                        # ON_CLICK CALLBACK: Sayfayı sıfırlamadan veriyi ekler
                        st.button("➕", key=f"btn_{i}", on_click=mac_ekle, args=(f"{r['H']}-{r['A']}", r['Tahmin'], r['Oran']))
        else:
            st.error("API hatası! Anahtarı kontrol edin.")

# 6. SEKMELER
t1, t2 = st.tabs(["🔍 Analiz", "📂 Arşiv"])
with t1:
    c1, c2, c3 = st.columns(3)
    if c1.button("⚽ FUTBOL"): analiz_motoru(["soccer"])
    if c2.button("🏀 BASKETBOL"): analiz_motoru(["basketball"])
    if c3.button("🔥 KARMA"): analiz_motoru(["soccer", "basketball"])

with t2:
    if st.session_state.arsiv:
        for k in reversed(st.session_state.arsiv):
            with st.expander(f"📅 {k['tarih']} | Oran: {k['oran']:.2f}"):
                st.table(pd.DataFrame(k['maclar']))
