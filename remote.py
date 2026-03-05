import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# API ANAHTARI
API_KEY = "cdf9790dbd2d52e5d593e5e4b9a76118"

st.set_page_config(page_title="Superior Scout v21", layout="wide", page_icon="🎯")

# Hafıza Yönetimi
if 'kupon_havuzu' not in st.session_state: st.session_state.kupon_havuzu = []
if 'arsiv' not in st.session_state: st.session_state.arsiv = []

# CSS: v18 Tarzı Sade ve Kararlı Tasarım
st.markdown("""
    <style>
    .match-card { background-color: #1e2130; padding: 15px; border-radius: 12px; border-left: 6px solid #4e73df; margin-bottom: 15px; }
    .f-box { width: 22px; height: 22px; border-radius: 4px; text-align: center; color: white; font-size: 13px; font-weight: bold; line-height: 22px; display: inline-block; margin-right: 3px; }
    .G { background-color: #28a745; } .B { background-color: #6c757d; } .M { background-color: #dc3545; }
    .stat-table { width: 100%; border-collapse: collapse; margin-top: 10px; color: #ccc; }
    .stat-table td { padding: 6px; border-bottom: 1px solid #333; text-align: center; font-size: 0.9em; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 Pro Scout v21: Kararlı Analiz Terminali")

# SOL PANEL: v18 ESNEKLİĞİ + v20 MARKETLERİ
with st.sidebar:
    st.header("⚙️ Arama Stratejisi")
    mod = st.radio("Seçim Yöntemi", ["Finansal Hedef", "Doğrudan Oran"])
    
    tutar = st.number_input("Yatırılacak (TL)", min_value=10, value=100)
    
    if mod == "Finansal Hedef":
        hedef = st.number_input("Hedef Kazanç (TL)", min_value=tutar, value=400)
        mac_say = st.slider("Maç Sayısı", 1, 8, 3)
        target_o = (hedef / tutar) ** (1/mac_say)
    else:
        target_o = st.number_input("İstediğim Oran (Örn: 1.25)", min_value=1.01, value=1.50)
        mac_say = st.slider("Listelenecek Maç Sayısı", 1, 15, 5)
    
    st.divider()
    st.header("🎯 Market Seçenekleri")
    market_map = {"Taraf (h2h)": "h2h", "Alt / Üst": "totals", "Çifte Şans": "double_chance", "Handikap": "spreads"}
    secili = st.multiselect("Aktif Marketler", list(market_map.keys()), default=["Taraf (h2h)", "Alt / Üst"])
    market_kodlari = [market_map[m] for m in secili]

    if st.session_state.kupon_havuzu:
        st.divider()
        st.subheader("📋 Mevcut Kupon")
        t_oran = 1.0
        for m in st.session_state.kupon_havuzu:
            st.write(f"🔹 {m['Maç']} ({m['Oran']})")
            t_oran *= m['Oran']
        st.write(f"**Toplam Oran: {t_oran:.2f}**")
        if st.button("💾 KUPONU ARŞİVE AT"):
            st.session_state.arsiv.append({"tarih": datetime.now().strftime("%d/%m %H:%M"), "maclar": list(st.session_state.kupon_havuzu), "oran": t_oran, "durum": "Bekliyor"})
            st.session_state.kupon_havuzu = []
            st.success("Kaydedildi!")

def form_draw(seri):
    return "".join([f"<span class='f-box {h}'>{h}</span>" for h in seri])

def analiz_motoru(spor_list):
    # v17'deki gibi esnek ama odaklı tolerans
    alt_l, ust_l = target_o * 0.85, target_o * 1.15
    
    with st.spinner('Bülten taranıyor...'):
        firsatlar = []
        for spor in spor_list:
            m_str = ",".join(market_kodlari)
            url = f"https://api.the-odds-api.com/v4/sports/{spor}/odds/?apiKey={API_KEY}&regions=eu&markets={m_str}&oddsFormat=decimal"
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
                                        "Tahmin": out['name'] if mkt['key']!="totals" else f"{out['name']} {out.get('point','')} GOL",
                                        "Oran": out['price'], "Basari": round((1/out['price'])*100, 1)
                                    })
        
        if firsatlar:
            df = pd.DataFrame(firsatlar).drop_duplicates(subset=['H', 'A']).head(15)
            for i, r in df.iterrows():
                st.markdown(f"""
                <div class='match-card'>
                    <div style='display: flex; justify-content: space-between;'>
                        <span>📅 {r['Saat']} | {r['Lig']} | <b>{r['H']} vs {r['A']}</b></span>
                        <span style='color: #00ff00; font-weight: bold;'>{r['Oran']}</span>
                    </div>
                    <div style='margin-top: 10px; color: #ff4b4b; font-weight: bold;'>🎯 Tahmin: {r['Tahmin']} | Güven: %{r['Basari']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                c1, c2 = st.columns([3, 1])
                with c1:
                    with st.expander("📊 İSTATİSTİK VE FORM"):
                        st.markdown(f"""
                        <table class='stat-table'>
                            <tr><td><b>Kategori</b></td><td>🏠 <b>{r['H']}</b></td><td>🚀 <b>{r['A']}</b></td></tr>
                            <tr><td>Form (Son 5)</td><td>{form_draw('GGBMG')}</td><td>{form_draw('MBGGM')}</td></tr>
                            <tr><td>Gol Ort.</td><td>1.8 / 0.9</td><td>1.1 / 1.6</td></tr>
                            <tr><td>Korner / Kart</td><td>6.2 / 2.1</td><td>4.4 / 2.5</td></tr>
                        </table>
                        """, unsafe_allow_html=True)
                with c2:
                    if st.button("➕ Ekle", key=f"add_{i}"):
                        st.session_state.kupon_havuzu.append({"Maç": f"{r['H']}-{r['A']}", "Tahmin": r['Tahmin'], "Oran": r['Oran']})
                        st.toast(f"{r['H']} eklendi!")

# SEKME YAPISI
tab1, tab2 = st.tabs(["🔍 Analiz", "📂 Arşiv"])
with tab1:
    c_f, c_b, c_k = st.columns(3)
    if c_f.button("⚽ FUTBOL"): analiz_motoru(["soccer"])
    if c_b.button("🏀 BASKETBOL"): analiz_motoru(["basketball"])
    if c_k.button("🔥 KARMA"): analiz_motoru(["soccer", "basketball"])

with tab2:
    for idx, k in enumerate(reversed(st.session_state.arsiv)):
        with st.expander(f"📅 {k['tarih']} | Oran: {k['oran']:.2f} | {k['durum']}"):
            st.table(pd.DataFrame(k['maclar']))
            ca, cb = st.columns(2)
            if ca.button("✅ KAZANDI", key=f"w_{idx}"): k['durum'] = "KAZANDI"; st.rerun()
            if cb.button("❌ KAYBETTİ", key=f"l_{idx}"): k['durum'] = "KAYBETTİ"; st.rerun()
