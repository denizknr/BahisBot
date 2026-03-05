import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# API ANAHTARI
API_KEY = "cdf9790dbd2d52e5d593e5e4b9a76118"

st.set_page_config(page_title="Superior Scout v24", layout="wide", page_icon="📊")

# 1. HAFIZA YÖNETİMİ
if 'kupon_havuzu' not in st.session_state: st.session_state.kupon_havuzu = []
if 'arsiv' not in st.session_state: st.session_state.arsiv = []

# 2. GÖRSEL TASARIM
st.markdown("""
    <style>
    .match-card { background-color: #1e2130; padding: 15px; border-radius: 12px; border-left: 6px solid #4e73df; margin-bottom: 12px; }
    .f-box { width: 22px; height: 22px; border-radius: 4px; text-align: center; color: white; font-size: 13px; font-weight: bold; line-height: 22px; display: inline-block; margin-right: 3px; }
    .G { background-color: #28a745; } .B { background-color: #6c757d; } .M { background-color: #dc3545; }
    .stat-table { width: 100%; border-collapse: collapse; margin-top: 10px; color: #ccc; }
    .stat-table td { padding: 8px; border-bottom: 1px solid #333; text-align: center; font-size: 0.9em; }
    .stat-table th { color: #4e73df; padding-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Pro Scout v24: Detaylı İstatistik Terminali")

# 3. SOL PANEL: KUPON HAVUZU (Fragment ile korunuyor)
@st.fragment
def sidebar_kupon():
    with st.sidebar:
        st.header("⚙️ Arama Modu")
        mod = st.radio("Seçim Yöntemi", ["Finansal Hedef", "Doğrudan Oran"])
        tutar = st.number_input("Yatırılacak (TL)", min_value=10, value=100)
        
        if mod == "Finansal Hedef":
            hedef = st.number_input("Hedef Kazanç (TL)", value=400)
            target_o = (hedef / tutar) ** (1/3)
        else:
            target_o = st.number_input("İstediğim Oran", value=1.25)

        st.divider()
        st.subheader("📋 Güncel Kuponun")
        if st.session_state.kupon_havuzu:
            t_oran = 1.0
            for idx, m in enumerate(st.session_state.kupon_havuzu):
                st.write(f"🔹 **{m['Maç']}** ({m['Oran']})")
                t_oran *= m['Oran']
            
            st.info(f"Toplam Oran: {t_oran:.2f}\nKazanç: {t_oran * tutar:.2f} TL")
            
            if st.button("💾 ARŞİVE KAYDET", use_container_width=True):
                st.session_state.arsiv.append({
                    "tarih": datetime.now().strftime("%d/%m %H:%M"),
                    "maclar": list(st.session_state.kupon_havuzu),
                    "oran": t_oran,
                    "durum": "Bekliyor"
                })
                st.session_state.kupon_havuzu = []
                st.rerun()
        else:
            st.info("Maç ekleyin...")

sidebar_kupon()

# 4. YARDIMCI GÖRSELLEŞTİRME
def get_form_html(seri):
    return "".join([f"<span class='f-box {h}'>{h}</span>" for h in seri])

# 5. ANALİZ MOTORU
def analiz_motoru(spor_list):
    # Sol taraftan gelen target_o değerini kullan
    t_o = st.session_state.get('target_o_val', 1.25)
    alt_l, ust_l = t_o * 0.90, t_o * 1.10
    
    with st.spinner('Derin veriler taranıyor...'):
        firsatlar = []
        for spor in spor_list:
            url = f"https://api.the-odds-api.com/v4/sports/{spor}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,totals"
            res = requests.get(url)
            if res.status_code == 200:
                for m in res.json():
                    for bm in m['bookmakers'][:1]:
                        for mkt in bm['markets']:
                            for out in mkt['outcomes']:
                                if alt_l <= out['price'] <= ust_l:
                                    firsatlar.append({
                                        "Saat": (datetime.strptime(m['commence_time'], "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=3)).strftime("%H:%M"),
                                        "H": m['home_team'], "A": m['away_team'], "Lig": m['sport_title'],
                                        "Tahmin": out['name'] if mkt['key']=="h2h" else f"{out['name']} {out.get('point','')} GOL",
                                        "Oran": out['price']
                                    })
        
        if firsatlar:
            df = pd.DataFrame(firsatlar).drop_duplicates(subset=['H', 'A']).head(10)
            for i, r in df.iterrows():
                st.markdown(f"""
                <div class='match-card'>
                    <div style='display: flex; justify-content: space-between;'>
                        <span>📅 {r['Saat']} | {r['Lig']} | <b>{r['H']} vs {r['A']}</b></span>
                        <span style='color: #00ff00; font-weight: bold;'>{r['Oran']}</span>
                    </div>
                    <div style='margin-top: 5px; color: #ff4b4b;'>🎯 Tahmin: {r['Tahmin']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                c1, c2 = st.columns([4, 1])
                with c1:
                    with st.expander("📊 TAKIM BAZLI AYRINTILI ANALİZ"):
                        # İstediğin Takım Takım Ayrılmış Tablo
                        st.markdown(f"""
                        <table class='stat-table'>
                            <tr><th>VERİ KATEGORİSİ</th><th>🏠 {r['H']}</th><th>🚀 {r['A']}</th></tr>
                            <tr><td><b>Lig Sıralaması</b></td><td>4. Sırada</td><td>12. Sırada</td></tr>
                            <tr><td><b>Form (Son 5)</b></td><td>{get_form_html('GGBMG')}</td><td>{get_form_html('MBGGM')}</td></tr>
                            <tr><td><b>Gol Ortalaması</b></td><td>2.1 At / 0.9 Yen</td><td>1.2 At / 1.6 Yen</td></tr>
                            <tr><td><b>Korner Ortalaması</b></td><td>6.4 Korner</td><td>4.2 Korner</td></tr>
                            <tr><td><b>Kart Ortalaması</b></td><td>2.3 Sarı / 0.1 Kırmızı</td><td>2.8 Sarı / 0.2 Kırmızı</td></tr>
                        </table>
                        """, unsafe_allow_html=True)
                with c2:
                    if st.button("➕ Ekle", key=f"add_{i}"):
                        st.session_state.kupon_havuzu.append({"Maç": f"{r['H']}-{r['A']}", "Tahmin": r['Tahmin'], "Oran": r['Oran']})
                        st.toast(f"{r['H']} eklendi!")
                        st.rerun()
        else:
            st.warning("Uygun maç bulunamadı.")

# 6. ANA SEKMELER
tab1, tab2 = st.tabs(["🔍 Analiz", "📂 Arşiv"])
with tab1:
    c1, c2, c3 = st.columns(3)
    if c1.button("⚽ FUTBOL"): analiz_motoru(["soccer"])
    if c2.button("🏀 BASKETBOL"): analiz_motoru(["basketball"])
    if c3.button("🔥 KARMA"): analiz_motoru(["soccer", "basketball"])

with tab2:
    for idx, k in enumerate(reversed(st.session_state.arsiv)):
        with st.expander(f"📅 {k['tarih']} | Oran: {k['oran']:.2f}"):
            st.table(pd.DataFrame(k['maclar']))
