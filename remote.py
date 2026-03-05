import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# API ANAHTARI
API_KEY = "cdf9790dbd2d52e5d593e5e4b9a76118"

st.set_page_config(page_title="Superior Scout v22", layout="wide", page_icon="🎯")

# Hafıza Yönetimi
if 'kupon_havuzu' not in st.session_state: st.session_state.kupon_havuzu = []
if 'arsiv' not in st.session_state: st.session_state.arsiv = []

# CSS: Temiz Kart ve Kupon Tasarımı
st.markdown("""
    <style>
    .match-card { background-color: #1e2130; padding: 15px; border-radius: 12px; border-left: 6px solid #4e73df; margin-bottom: 12px; }
    .f-box { width: 20px; height: 20px; border-radius: 4px; text-align: center; color: white; font-size: 12px; font-weight: bold; line-height: 20px; display: inline-block; margin-right: 2px; }
    .G { background-color: #28a745; } .B { background-color: #6c757d; } .M { background-color: #dc3545; }
    .sidebar-kupon { background-color: #262a3b; padding: 10px; border-radius: 10px; border: 1px solid #4e73df; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 Pro Scout v22: Odaklı Analiz Terminali")

# SOL PANEL: KUPON OLUŞTURMA VE STRATEJİ
with st.sidebar:
    st.header("⚙️ Arama Modu")
    mod = st.radio("Seçim Yöntemi", ["Finansal Hedef", "Doğrudan Oran"])
    
    tutar = st.number_input("Yatırılacak (TL)", min_value=10, value=100)
    
    if mod == "Finansal Hedef":
        hedef = st.number_input("Hedef Kazanç (TL)", min_value=tutar, value=400)
        mac_say = st.slider("İdeal Maç Sayısı", 1, 8, 3)
        target_o = (hedef / tutar) ** (1/mac_say)
    else:
        target_o = st.number_input("İstediğim Oran (Örn: 1.25)", min_value=1.01, value=1.25)
        mac_say = st.slider("Listelenecek Maç Sayısı", 1, 15, 5)

    # KUPON OLUŞTURMA ALANI
    st.divider()
    st.subheader("📋 Güncel Kuponun")
    if st.session_state.kupon_havuzu:
        t_oran = 1.0
        for idx, m in enumerate(st.session_state.kupon_havuzu):
            c1, c2 = st.columns([4, 1])
            c1.write(f"🔹 {m['Maç']} ({m['Oran']})")
            if c2.button("X", key=f"rm_{idx}"):
                st.session_state.kupon_havuzu.pop(idx)
                st.rerun()
            t_oran *= m['Oran']
        
        st.markdown(f"""
        <div class='sidebar-kupon'>
            <b>Toplam Oran: {t_oran:.2f}</b><br>
            <b>Kazanç: {t_oran * tutar:.2f} TL</b>
        </div><br>
        """, unsafe_allow_html=True)
        
        if st.button("💾 KUPONU KAYDEDİLENLERE EKLE", use_container_width=True):
            st.session_state.arsiv.append({
                "tarih": datetime.now().strftime("%d/%m %H:%M"),
                "maclar": list(st.session_state.kupon_havuzu),
                "oran": t_oran,
                "durum": "Bekliyor"
            })
            st.session_state.kupon_havuzu = []
            st.success("Kaydedilenlere eklendi!")
            st.rerun()
    else:
        st.info("Maç eklediğinizde kupon burada oluşur.")

def form_draw(seri):
    return "".join([f"<span class='f-box {h}'>{h}</span>" for h in seri])

def analiz_motoru(spor_list):
    # v17/18 Hassasiyeti: %85 - %115 tolerans
    alt_l, ust_l = target_o * 0.85, target_o * 1.15
    
    with st.spinner('Bülten taranıyor...'):
        firsatlar = []
        for spor in spor_list:
            # Sadece en kararlı marketler
            url = f"https://api.the-odds-api.com/v4/sports/{spor}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,totals"
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
            df = pd.DataFrame(firsatlar).drop_duplicates(subset=['H', 'A']).head(12)
            for i, r in df.iterrows():
                with st.container():
                    st.markdown(f"""
                    <div class='match-card'>
                        <div style='display: flex; justify-content: space-between;'>
                            <span>📅 {r['Saat']} | {r['Lig']} | <b>{r['H']} vs {r['A']}</b></span>
                            <span style='color: #00ff00; font-weight: bold;'>{r['Oran']}</span>
                        </div>
                        <div style='margin-top: 5px; color: #ff4b4b; font-weight: bold;'>🎯 Tahmin: {r['Tahmin']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        with st.expander("📊 Analiz"):
                            st.write(f"🏠 {r['H']}: {form_draw('GGBMG')} | 🚀 {r['A']}: {form_draw('MBGGM')}")
                            st.caption("Gol Ort: 1.8 | Korner: 5.4 | Kart: 2.1")
                    with c2:
                        if st.button("➕ Ekle", key=f"add_{i}"):
                            st.session_state.kupon_havuzu.append({"Maç": f"{r['H']}-{r['A']}", "Tahmin": r['Tahmin'], "Oran": r['Oran']})
                            st.rerun()
        else:
            st.warning("Kriterlere uygun maç bulunamadı.")

# SEKMELER
tab1, tab2 = st.tabs(["🔍 Analiz", "📂 Kaydedilen Kuponlar"])

with tab1:
    c1, c2, c3 = st.columns(3)
    if c1.button("⚽ FUTBOL"): analiz_motoru(["soccer"])
    if c2.button("🏀 BASKETBOL"): analiz_motoru(["basketball"])
    if c3.button("🔥 KARMA"): analiz_motoru(["soccer", "basketball"])

with tab2:
    for idx, k in enumerate(reversed(st.session_state.arsiv)):
        with st.expander(f"📅 {k['tarih']} | Oran: {k['oran']:.2f} | {k['durum']}"):
            st.table(pd.DataFrame(k['maclar']))
            ca, cb = st.columns(2)
            if ca.button("✅ KAZANDI", key=f"w_{idx}"): k['durum'] = "KAZANDI"; st.rerun()
            if cb.button("❌ KAYBETTİ", key=f"l_{idx}"): k['durum'] = "KAYBETTİ"; st.rerun()
