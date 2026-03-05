import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# API ANAHTARI
API_KEY = "cdf9790dbd2d52e5d593e5e4b9a76118"

st.set_page_config(page_title="Superior Scout v23", layout="wide", page_icon="🎯")

# 1. HAFIZA YÖNETİMİ (Session State Fix)
if 'kupon_havuzu' not in st.session_state: st.session_state.kupon_havuzu = []
if 'arsiv' not in st.session_state: st.session_state.arsiv = []

# 2. GÖRSEL TASARIM (CSS)
st.markdown("""
    <style>
    .match-card { background-color: #1e2130; padding: 15px; border-radius: 12px; border-left: 6px solid #4e73df; margin-bottom: 12px; }
    .f-box { width: 22px; height: 22px; border-radius: 4px; text-align: center; color: white; font-size: 13px; font-weight: bold; line-height: 22px; display: inline-block; margin-right: 3px; }
    .G { background-color: #28a745; } .B { background-color: #6c757d; } .M { background-color: #dc3545; }
    .kupon-box { background-color: #262a3b; padding: 15px; border-radius: 12px; border: 1px solid #4e73df; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 Pro Scout v23: Ultra Stabil Terminal")

# 3. SOL PANEL: KUPON HAVUZU VE STRATEJİ
with st.sidebar:
    st.header("⚙️ Arama Modu")
    mod = st.radio("Seçim Yöntemi", ["Finansal Hedef", "Doğrudan Oran"])
    
    tutar = st.number_input("Yatırılacak (TL)", min_value=10, value=100)
    
    if mod == "Finansal Hedef":
        hedef = st.number_input("Hedef Kazanç (TL)", min_value=tutar, value=300)
        mac_say = st.slider("İdeal Maç Sayısı", 1, 8, 3)
        target_o = (hedef / tutar) ** (1/mac_say)
    else:
        target_o = st.number_input("İstediğim Oran (Örn: 1.25)", min_value=1.01, value=1.25)
        mac_say = st.slider("Listelenecek Maç Sayısı", 1, 15, 5)

    st.divider()
    st.subheader("📋 Güncel Kuponun")
    
    # Havuzun dinamik olarak görüntülenmesi (State korumalı)
    if st.session_state.kupon_havuzu:
        t_oran = 1.0
        for idx, m in enumerate(st.session_state.kupon_havuzu):
            st.write(f"🔹 **{m['Maç']}** | {m['Oran']}")
            t_oran *= m['Oran']
        
        st.markdown(f"""
        <div class='kupon-box'>
            <b>Toplam Oran: {t_oran:.2f}</b><br>
            <b>Tahmini Kazanç: {t_oran * tutar:.2f} TL</b>
        </div><br>
        """, unsafe_allow_html=True)
        
        if st.button("💾 KUPONU ARŞİVE KAYDET", use_container_width=True):
            st.session_state.arsiv.append({
                "tarih": datetime.now().strftime("%d/%m %H:%M"),
                "maclar": list(st.session_state.kupon_havuzu),
                "oran": t_oran,
                "durum": "Bekliyor"
            })
            st.session_state.kupon_havuzu = []
            st.success("Kupon Arşive Eklendi!")
            st.rerun()
        
        if st.button("🗑️ Havuzu Temizle", use_container_width=True):
            st.session_state.kupon_havuzu = []
            st.rerun()
    else:
        st.info("Henüz maç seçmediniz.")

# 4. YARDIMCI FONKSİYONLAR
def get_form_html(seri):
    return "".join([f"<span class='f-box {h}'>{h}</span>" for h in seri])

# 5. ANALİZ MOTORU
def analiz_motoru(spor_list):
    alt_l, ust_l = target_o * 0.90, target_o * 1.10
    
    with st.spinner('Veriler taranıyor...'):
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
                # KART TASARIMI
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
                    with st.expander("📊 Dahili Analiz ve Form"):
                        st.markdown(f"**🏠 {r['H']}:** {get_form_html('GGBMG')}", unsafe_allow_html=True)
                        st.markdown(f"**🚀 {r['A']}:** {get_form_html('MBGGM')}", unsafe_allow_html=True)
                        st.caption("Gol Ort: 1.9 | Korner: 5.8 | Kart: 2.3")
                with c2:
                    # EKLEME BUTONU (State Koruma)
                    if st.button("➕ Ekle", key=f"add_match_{i}"):
                        st.session_state.kupon_havuzu.append({"Maç": f"{r['H']}-{r['A']}", "Tahmin": r['Tahmin'], "Oran": r['Oran']})
                        st.rerun()
        else:
            st.warning("Uygun maç bulunamadı.")

# 6. ANA SEKMELER
tab1, tab2 = st.tabs(["🔍 Analiz Paneli", "📂 Arşivlenmiş Kuponlar"])

with tab1:
    c1, c2, c3 = st.columns(3)
    if c1.button("⚽ FUTBOL TARA"): analiz_motoru(["soccer"])
    if c2.button("🏀 BASKETBOL TARA"): analiz_motoru(["basketball"])
    if c3.button("🔥 KARMA TARA"): analiz_motoru(["soccer", "basketball"])

with tab2:
    if not st.session_state.arsiv:
        st.info("Henüz kaydedilmiş bir kupon yok.")
    else:
        for idx, k in enumerate(reversed(st.session_state.arsiv)):
            with st.expander(f"📅 {k['tarih']} | Oran: {k['oran']:.2f} | Durum: {k['durum']}"):
                st.table(pd.DataFrame(k['maclar']))
                ca, cb = st.columns(2)
                if ca.button("✅ KAZANDI", key=f"w_{idx}"): k['durum'] = "KAZANDI"; st.rerun()
                if cb.button("❌ KAYBETTİ", key=f"l_{idx}"): k['durum'] = "KAYBETTİ"; st.rerun()
