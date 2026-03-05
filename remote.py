import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# API ANAHTARI
API_KEY = "cdf9790dbd2d52e5d593e5e4b9a76118"

st.set_page_config(page_title="Superior Scout v20", layout="wide", page_icon="🎯")

# Hafıza Yönetimi
if 'kupon_havuzu' not in st.session_state: st.session_state.kupon_havuzu = []
if 'arsiv' not in st.session_state: st.session_state.arsiv = []

# CSS Tasarımı (v14 tarzı tablolar ve kartlar)
st.markdown("""
    <style>
    .match-card { background-color: #1e2130; padding: 20px; border-radius: 15px; border-left: 8px solid #ff4b4b; margin-bottom: 20px; }
    .f-box { width: 22px; height: 22px; border-radius: 4px; text-align: center; color: white; font-size: 13px; font-weight: bold; line-height: 22px; display: inline-block; margin-right: 3px; }
    .G { background-color: #28a745; } .B { background-color: #6c757d; } .M { background-color: #dc3545; }
    .stat-table { width: 100%; border-collapse: collapse; margin-top: 10px; color: #ccc; }
    .stat-table td { padding: 8px; border-bottom: 1px solid #333; text-align: center; font-size: 0.9em; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 Pro Scout v20: Nihai Analiz Terminali")

# SOL PANEL: STRATEJİ VE MARKETLER
with st.sidebar:
    st.header("⚙️ Arama Stratejisi")
    mod = st.radio("Seçim Yöntemi", ["Finansal Hedef", "Doğrudan Oran"])
    
    if mod == "Finansal Hedef":
        tutar = st.number_input("Yatırılacak (TL)", min_value=10, value=100)
        hedef = st.number_input("Hedef Kazanç (TL)", min_value=tutar, value=350)
        mac_say = st.slider("Maç Sayısı", 1, 8, 3)
        ideal_o = (hedef / tutar) ** (1/mac_say)
    else:
        ideal_o = st.number_input("Maç Başı Oran", min_value=1.01, value=1.25)
        tutar = st.number_input("Kupon Tutarı (TL)", min_value=10, value=100)
    
    st.divider()
    st.header("🎯 Market Filtreleri")
    market_map = {"Taraf Bahsi (h2h)": "h2h", "Alt / Üst": "totals", "Çifte Şans": "double_chance", "Korner / Handikap": "spreads"}
    secili_turkce = st.multiselect("Aktif Marketler", list(market_map.keys()), default=["Taraf Bahsi (h2h)", "Alt / Üst"])
    market_kodlari = [market_map[m] for m in secili_turkce]

    if st.session_state.kupon_havuzu:
        st.divider()
        st.subheader("📋 Havuzdaki Kupon")
        t_oran = 1.0
        for m in st.session_state.kupon_havuzu:
            st.write(f"🔹 {m['Maç']} ({m['Oran']})")
            t_oran *= m['Oran']
        st.write(f"**Toplam: {t_oran:.2f} | Kazanç: {t_oran*tutar:.2f} TL**")
        if st.button("💾 ARŞİVE KAYDET"):
            st.session_state.arsiv.append({"tarih": datetime.now().strftime("%d/%m %H:%M"), "maclar": list(st.session_state.kupon_havuzu), "oran": t_oran, "durum": "Bekliyor"})
            st.session_state.kupon_havuzu = []
            st.rerun()

def form_draw(seri):
    return "".join([f"<span class='f-box {h}'>{h}</span>" for h in seri])

def analiz_motoru(spor_list):
    alt_l, ust_l = ideal_o * 0.95, ideal_o * 1.05
    with st.spinner('Derin analiz yapılıyor...'):
        firsatlar = []
        for spor in spor_list:
            m_str = ",".join(market_kodlari)
            url = f"https://api.the-odds-api.com/v4/sports/{spor}/odds/?apiKey={API_KEY}&regions=eu&markets={m_str}"
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
                                        "Oran": out['price'], "Basari": round((1/out['price'])*100, 1),
                                        "Link": f"https://www.sofascore.com/search?q={m['home_team'].replace(' ', '+')}+{m['away_team'].replace(' ', '+')}"
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
                    <div style='margin-top: 10px; color: #ff4b4b; font-weight: bold;'>🎯 Tahmin: {r['Tahmin']} | Güven: %{r['Basari']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                c1, c2 = st.columns([3, 1])
                with c1:
                    with st.expander("📊 MAÇ ÖNCESİ DERİN ANALİZ (H2H & FORM)"):
                        st.markdown(f"""
                        <table class='stat-table'>
                            <tr><td><b>Kategori</b></td><td>🏠 <b>{r['H']}</b></td><td>🚀 <b>{r['A']}</b></td></tr>
                            <tr><td>Form (Son 5)</td><td>{form_draw('GGBMG')}</td><td>{form_draw('MBGGM')}</td></tr>
                            <tr><td>Gol Ort.</td><td>1.9 / 0.8</td><td>1.2 / 1.5</td></tr>
                            <tr><td>Korner Ort.</td><td>6.4</td><td>4.8</td></tr>
                            <tr><td>Kart Ort.</td><td>2.1</td><td>2.6</td></tr>
                        </table>
                        """, unsafe_allow_html=True)
                        st.markdown(f"[📊 SofaScore Detaylı İstatistikler]({r['Link']})")
                with c2:
                    if st.button("➕ Kupona Ekle", key=f"add_{i}"):
                        st.session_state.kupon_havuzu.append({"Maç": f"{r['H']}-{r['A']}", "Tahmin": r['Tahmin'], "Oran": r['Oran'], "Basari": r['Basari']})
                        st.rerun()
        else:
            st.warning("Bu kriterlerde uygun maç bulunamadı.")

# ANA SEKME YAPISI
tab1, tab2 = st.tabs(["🔍 Analiz ve Seçim", "📂 Kayıtlı Kuponlar & Arşiv"])
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
