import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# API ANAHTARI
API_KEY = "cdf9790dbd2d52e5d593e5e4b9a76118"

st.set_page_config(page_title="Superior Dynamic Scout", layout="wide", page_icon="⚡")

# 1. SESSION STATE (Veri Deposu)
if 'kupon_havuzu' not in st.session_state: st.session_state.kupon_havuzu = []
if 'arsiv' not in st.session_state: st.session_state.arsiv = []

# 2. CSS (Dinamik Görünüm)
st.markdown("""
    <style>
    .match-card { background-color: #262a3b; padding: 15px; border-radius: 12px; border-left: 6px solid #4e73df; margin-bottom: 10px; }
    .f-box { width: 22px; height: 22px; border-radius: 4px; text-align: center; color: white; font-size: 13px; font-weight: bold; line-height: 22px; display: inline-block; margin-right: 3px; }
    .G { background-color: #28a745; } .B { background-color: #6c757d; } .M { background-color: #dc3545; }
    .stButton>button { width: 100%; border-radius: 8px; transition: 0.3s; }
    .stButton>button:active { transform: scale(0.95); }
    </style>
    """, unsafe_allow_html=True)

# 3. DINAMIK KUPON PANELİ (Fragment Yapısı)
@st.fragment
def kupon_paneli():
    with st.sidebar:
        st.header("📋 Kupon Havuzu")
        if st.session_state.kupon_havuzu:
            t_oran = 1.0
            for idx, m in enumerate(st.session_state.kupon_havuzu):
                col_info, col_del = st.columns([4, 1])
                col_info.markdown(f"**{m['Maç']}**\n<small>{m['Tahmin']} | {m['Oran']}</small>", unsafe_allow_html=True)
                if col_del.button("❌", key=f"rm_{idx}_{datetime.now().microsecond}"):
                    st.session_state.kupon_havuzu.pop(idx)
                    st.rerun()
                t_oran *= m['Oran']
            
            st.divider()
            st.metric("Toplam Oran", f"{t_oran:.2f}")
            if st.button("💾 KUPONU KAYDET", type="primary"):
                st.session_state.arsiv.append({
                    "tarih": datetime.now().strftime("%d/%m %H:%M"),
                    "maclar": list(st.session_state.kupon_havuzu),
                    "oran": t_oran, "durum": "Bekliyor"
                })
                st.session_state.kupon_havuzu = []
                st.success("Kayıt başarılı!")
                st.rerun()
        else:
            st.info("Havuz boş. Maç ekleyin.")

# 4. YARDIMCI GÖRSELLER
def get_form_html(seri):
    return "".join([f"<span class='f-box {h}'>{h}</span>" for h in seri])

# 5. ANALİZ MOTORU
def analiz_motoru(spor_list):
    # Sidebar'daki ayarları oku
    with st.sidebar:
        target_o = st.number_input("Hedef Oran", value=1.25, step=0.01)
    
    alt_l, ust_l = target_o * 0.92, target_o * 1.08
    
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
                df = pd.DataFrame(firsatlar).drop_duplicates(subset=['H', 'A']).head(10)
                for i, r in df.iterrows():
                    with st.container():
                        st.markdown(f"""
                        <div class='match-card'>
                            <b>{r['Saat']} | {r['H']} vs {r['A']}</b><br>
                            <span style='color:#00ff00;'>Oran: {r['Oran']}</span> | <span style='color:#ff4b4b;'>Tahmin: {r['Tahmin']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        c1, c2 = st.columns([4, 1])
                        with c1:
                            with st.expander("📊 Veriler"):
                                st.write(f"Form: {get_form_html('GGBMG')} vs {get_form_html('MBGGM')}", unsafe_allow_html=True)
                        with c2:
                            # State güncelleme butonu (Sayfayı baştan yüklemez)
                            if st.button("➕", key=f"add_{i}"):
                                st.session_state.kupon_havuzu.append({"Maç": f"{r['H']}-{r['A']}", "Tahmin": r['Tahmin'], "Oran": r['Oran']})
                                st.toast(f"{r['H']} havuzda!")
                                # st.rerun() yerine fragment'ın otomatik algılamasını bekleyebiliriz ama 
                                # sidebar'ı anlık güncellemek için st.rerun kullanmak en sağlıklısıdır.
                                st.rerun()

# 6. ANA YAPI
kupon_paneli() # Sidebar fragment çağrısı

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
