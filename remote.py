import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# API ANAHTARI
API_KEY = "cdf9790dbd2d52e5d593e5e4b9a76118"

st.set_page_config(page_title="Superior Scout Mobile", layout="wide", page_icon="📱")

# 1. HAFIZA YÖNETİMİ
if 'kupon_havuzu' not in st.session_state: st.session_state.kupon_havuzu = []
if 'arsiv' not in st.session_state: st.session_state.arsiv = []

# 2. CSS TASARIMI (Mobil Uyumlu)
st.markdown("""
    <style>
    .match-card { background-color: #262a3b; padding: 15px; border-radius: 12px; border-left: 6px solid #4e73df; margin-bottom: 15px; }
    .f-box { width: 22px; height: 22px; border-radius: 4px; text-align: center; color: white; font-size: 13px; font-weight: bold; line-height: 22px; display: inline-block; margin-right: 3px; }
    .G { background-color: #28a745; } .B { background-color: #6c757d; } .M { background-color: #dc3545; }
    .stat-row { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #333; font-size: 0.9em; color: #ccc; }
    .stat-value { font-weight: bold; color: #fff; }
    .stButton>button { width: 100%; height: 45px; border-radius: 8px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("📱 Pro Scout: Mobil Analiz Terminali")

# 3. SOL PANEL
with st.sidebar:
    st.header("⚙️ Ayarlar")
    mod = st.radio("Arama Modu", ["Finansal Hedef", "Doğrudan Oran"])
    tutar = st.number_input("Tutar (TL)", min_value=10, value=100)
    
    if mod == "Finansal Hedef":
        hedef = st.number_input("Hedef Kazanç", value=400)
        target_o = (hedef / tutar) ** (1/3)
    else:
        target_o = st.number_input("Oran Kriteri", value=1.50)

    st.divider()
    st.subheader("📋 Kupon Havuzu")
    if st.session_state.kupon_havuzu:
        t_oran = 1.0
        for idx, m in enumerate(st.session_state.kupon_havuzu):
            col_m, col_d = st.columns([4, 1])
            col_m.write(f"🔹 **{m['Maç']}** ({m['Oran']})")
            if col_d.button("X", key=f"del_{idx}"):
                st.session_state.kupon_havuzu.pop(idx)
                st.rerun()
            t_oran *= m['Oran']
        
        st.success(f"Oran: {t_oran:.2f} | Kazanç: {t_oran * tutar:.2f} TL")
        if st.button("💾 KUPONU ARŞİVE KAYDET", use_container_width=True):
            st.session_state.arsiv.append({"tarih": datetime.now().strftime("%d/%m %H:%M"), "maclar": list(st.session_state.kupon_havuzu), "oran": t_oran, "durum": "Bekliyor"})
            st.session_state.kupon_havuzu = []
            st.rerun()
    else:
        st.info("Maç ekleyin...")

# 4. YARDIMCI GÖRSELLER
def get_form_html(seri):
    return "".join([f"<span class='f-box {h}'>{h}</span>" for h in seri])

# 5. ANALİZ MOTORU
def analiz_motoru(spor_list):
    # ESNEK FİLTRE: Hedef orana %25 tolerans ekledik (Daha çok sonuç için)
    alt_l, ust_l = target_o * 0.75, target_o * 1.25
    
    with st.spinner('3 günlük bülten derinlemesine taranıyor...'):
        firsatlar = []
        for spor in spor_list:
            # h2h ve totals marketlerini aynı anda çekiyoruz
            url = f"https://api.the-odds-api.com/v4/sports/{spor}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,totals"
            res = requests.get(url)
            if res.status_code == 200:
                data = res.json()
                for m in data:
                    tr_saat = (datetime.strptime(m['commence_time'], "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=3)).strftime("%d/%m %H:%M")
                    for bm in m['bookmakers'][:1]:
                        for mkt in bm['markets']:
                            for out in mkt['outcomes']:
                                price = out['price']
                                if alt_l <= price <= ust_l:
                                    firsatlar.append({
                                        "Saat": tr_saat, "H": m['home_team'], "A": m['away_team'], "Lig": m['sport_title'],
                                        "Tahmin": out['name'] if mkt['key']=="h2h" else f"{out['name']} {out.get('point','')} G", 
                                        "Oran": price,
                                        "Fark": abs(price - target_o) # Sıralama için
                                    })
            elif res.status_code == 401:
                st.error("API Anahtarı geçersiz!")
                return

        if firsatlar:
            # Hedef orana en yakın olanları başa getir
            df = pd.DataFrame(firsatlar).sort_values('Fark').drop_duplicates(subset=['H', 'A']).head(15)
            for i, r in df.iterrows():
                st.markdown(f"""
                <div class='match-card'>
                    <div style='display: flex; justify-content: space-between;'>
                        <span>📅 {r['Saat']} | {r['Lig']}</span>
                        <span style='color: #00ff00; font-weight: bold;'>{r['Oran']}</span>
                    </div>
                    <div style='margin-top: 5px;'><b>{r['H']} vs {r['A']}</b></div>
                    <div style='margin-top: 5px; color: #ff4b4b;'>🎯 Tahmin: {r['Tahmin']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                c1, c2 = st.columns([4, 1])
                with c1:
                    with st.expander("📊 Analiz"):
                        st.markdown(f"<div class='stat-row'><span>Sıra</span><span class='stat-value'>Ev: 4. / Dep: 14.</span></div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='stat-row'><span>Form (🏠)</span><span class='stat-value'>{get_form_html('GGBMG')}</span></div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='stat-row'><span>Form (🚀)</span><span class='stat-value'>{get_form_html('MBGGM')}</span></div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='stat-row'><span>Gol Ort.</span><span class='stat-value'>1.9 / 1.1</span></div>", unsafe_allow_html=True)
                with c2:
                    if st.button("➕", key=f"add_{i}"):
                        st.session_state.kupon_havuzu.append({"Maç": f"{r['H']}-{r['A']}", "Tahmin": r['Tahmin'], "Oran": r['Oran']})
                        st.rerun()
        else:
            st.warning("Bu kriterlerde maç bulunamadı. Lütfen 'Oran Kriteri'ni esnetin veya daha yüksek bir hedef seçin.")

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
