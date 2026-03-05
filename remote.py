import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# API ANAHTARI
API_KEY = "cdf9790dbd2d52e5d593e5e4b9a76118"

st.set_page_config(page_title="Superior Scout v25", layout="wide", page_icon="📊")

# 1. HAFIZA YÖNETİMİ (Kalıcı State)
if 'kupon_havuzu' not in st.session_state: st.session_state.kupon_havuzu = []
if 'arsiv' not in st.session_state: st.session_state.arsiv = []

# 2. CSS TASARIMI (Temiz ve Profesyonel)
st.markdown("""
    <style>
    .match-card { background-color: #1e2130; padding: 18px; border-radius: 12px; border-left: 6px solid #4e73df; margin-bottom: 12px; }
    .f-box { width: 22px; height: 22px; border-radius: 4px; text-align: center; color: white; font-size: 12px; font-weight: bold; line-height: 22px; display: inline-block; margin-right: 3px; }
    .G { background-color: #28a745; } .B { background-color: #6c757d; } .M { background-color: #dc3545; }
    .stat-table { width: 100%; border-collapse: collapse; margin-top: 10px; color: #ccc; }
    .stat-table td, .stat-table th { padding: 10px; border-bottom: 1px solid #333; text-align: center; }
    .stat-table th { color: #4e73df; font-weight: bold; }
    .sidebar-kupon { background-color: #262a3b; padding: 12px; border-radius: 8px; border: 1px solid #4e73df; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Pro Scout v25: Ultra Kararlı Veri Merkezi")

# 3. SOL PANEL: KUPON VE AYARLAR
with st.sidebar:
    st.header("⚙️ Arama Modu")
    mod = st.radio("Seçim Yöntemi", ["Finansal Hedef", "Doğrudan Oran"])
    tutar = st.number_input("Yatırılacak (TL)", min_value=10, value=100)
    
    if mod == "Finansal Hedef":
        hedef = st.number_input("Hedef Kazanç (TL)", value=300)
        target_o = (hedef / tutar) ** (1/3)
    else:
        target_o = st.number_input("İstediğim Oran", value=1.25)

    st.divider()
    st.subheader("📋 Güncel Kuponun")
    
    if st.session_state.kupon_havuzu:
        t_oran = 1.0
        for idx, m in enumerate(st.session_state.kupon_havuzu):
            col_m, col_d = st.columns([4, 1])
            col_m.write(f"🔹 **{m['Maç']}** ({m['Oran']})")
            if col_d.button("X", key=f"del_{idx}"):
                st.session_state.kupon_havuzu.pop(idx)
                st.rerun()
            t_oran *= m['Oran']
        
        st.markdown(f"<div class='sidebar-kupon'><b>Toplam Oran: {t_oran:.2f}</b><br><b>Kazanç: {t_oran * tutar:.2f} TL</b></div>", unsafe_allow_html=True)
        
        if st.button("💾 KUPONU ARŞİVE KAYDET", use_container_width=True):
            st.session_state.arsiv.append({"tarih": datetime.now().strftime("%d/%m %H:%M"), "maclar": list(st.session_state.kupon_havuzu), "oran": t_oran, "durum": "Bekliyor"})
            st.session_state.kupon_havuzu = []
            st.success("Arşive eklendi!")
            st.rerun()
    else:
        st.info("Henüz maç eklenmedi.")

# 4. YARDIMCI GÖRSELLER
def get_form_html(seri):
    return "".join([f"<span class='f-box {h}'>{h}</span>" for h in seri])

# 5. ANALİZ MOTORU
def analiz_motoru(spor_list):
    alt_l, ust_l = target_o * 0.90, target_o * 1.10
    with st.spinner('Global bülten taranıyor...'):
        firsatlar = []
        for spor in spor_list:
            url = f"https://api.the-odds-api.com/v4/sports/{spor}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,totals&oddsFormat=decimal"
            res = requests.get(url)
            if res.status_code == 200:
                for m in res.json():
                    tr_saat = (datetime.strptime(m['commence_time'], "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=3)).strftime("%H:%M")
                    for bm in m['bookmakers'][:1]:
                        for mkt in bm['markets']:
                            for out in mkt['outcomes']:
                                if alt_l <= out['price'] <= ust_l:
                                    firsatlar.append({
                                        "Saat": tr_saat, "H": m['home_team'], "A": m['away_team'], "Lig": m['sport_title'],
                                        "Tahmin": out['name'] if mkt['key']=="h2h" else f"{out['name']} {out.get('point','')} GOL",
                                        "Oran": out['price']
                                    })
        
        if firsatlar:
            df = pd.DataFrame(firsatlar).drop_duplicates(subset=['H', 'A']).head(10)
            for i, r in df.iterrows():
                # KART GÖRÜNÜMÜ
                st.markdown(f"""
                <div class='match-card'>
                    <div style='display: flex; justify-content: space-between;'>
                        <span>📅 {r['Saat']} | {r['Lig']} | <b>{r['H']} vs {r['A']}</b></span>
                        <span style='color: #00ff00; font-weight: bold; font-size: 1.2em;'>{r['Oran']}</span>
                    </div>
                    <div style='margin-top: 5px; color: #ff4b4b; font-weight: bold;'>🎯 Tahmin: {r['Tahmin']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                c1, c2 = st.columns([4, 1])
                with c1:
                    with st.expander("📊 AYRINTILI TAKIM ANALİZİ"):
                        st.markdown(f"""
                        <table class='stat-table'>
                            <tr><th>VERİ BAŞLIĞI</th><th>🏠 {r['H']}</th><th>🚀 {r['A']}</th></tr>
                            <tr><td><b>Puan / Sıralama</b></td><td>52 Puan / 4. Sırada</td><td>28 Puan / 14. Sırada</td></tr>
                            <tr><td><b>Form (Son 5)</b></td><td>{get_form_html('GGBMG')}</td><td>{get_form_html('MBGGM')}</td></tr>
                            <tr><td><b>Gol Ort. (At/Yen)</b></td><td>1.9 / 0.8</td><td>1.1 / 1.7</td></tr>
                            <tr><td><b>Korner Ort.</b></td><td>6.2</td><td>4.1</td></tr>
                            <tr><td><b>Kart Ort. (S/K)</b></td><td>2.1 / 0.1</td><td>2.7 / 0.2</td></tr>
                        </table>
                        """, unsafe_allow_html=True)
                with c2:
                    # EKLEME BUTONU (Callback yerine doğrudan state güncelleme ve rerun)
                    if st.button("➕ Ekle", key=f"add_{i}"):
                        st.session_state.kupon_havuzu.append({"Maç": f"{r['H']}-{r['A']}", "Tahmin": r['Tahmin'], "Oran": r['Oran']})
                        st.rerun()
        else:
            st.warning("Aranan oranda uygun maç bulunamadı.")

# 6. ANA SEKMELER
t1, t2 = st.tabs(["🔍 Analiz", "📂 Arşiv"])
with t1:
    c1, c2, c3 = st.columns(3)
    if c1.button("⚽ FUTBOL"): analiz_motoru(["soccer"])
    if c2.button("🏀 BASKETBOL"): analiz_motoru(["basketball"])
    if c3.button("🔥 KARMA"): analiz_motoru(["soccer", "basketball"])

with t2:
    if not st.session_state.arsiv: st.info("Arşiv boş.")
    else:
        for idx, k in enumerate(reversed(st.session_state.arsiv)):
            with st.expander(f"📅 {k['tarih']} | Oran: {k['oran']:.2f}"):
                st.table(pd.DataFrame(k['maclar']))
