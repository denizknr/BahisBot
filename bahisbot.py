import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# API ANAHTARINI BURAYA YAZ
API_KEY = "cdf9790dbd2d52e5d593e5e4b9a76118"

st.set_page_config(page_title="Superior Terminal v16", layout="wide", page_icon="📊")

# Hafıza Yönetimi
if 'kupon_havuzu' not in st.session_state: st.session_state.kupon_havuzu = []
if 'kayitli_kuponlar' not in st.session_state: st.session_state.kayitli_kuponlar = []

# CSS: Gelişmiş Kart ve Tablo Tasarımı
st.markdown("""
    <style>
    .match-card { background-color: #1e2130; padding: 20px; border-radius: 15px; border-left: 8px solid #4e73df; margin-bottom: 20px; }
    .f-box { width: 22px; height: 22px; border-radius: 4px; text-align: center; color: white; font-size: 13px; font-weight: bold; line-height: 22px; display: inline-block; margin-right: 3px; }
    .G { background-color: #28a745; } .B { background-color: #6c757d; } .M { background-color: #dc3545; }
    .stat-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
    .stat-table td { padding: 5px; border-bottom: 1px solid #333; text-align: center; font-size: 0.9em; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Pro Scout v16: Dahili Veri ve Portföy Yönetimi")

with st.sidebar:
    st.header("⚙️ Analiz & Kupon")
    tutar = st.number_input("Kupon Tutarı (TL)", min_value=10, value=100)
    mod = st.radio("Arama Modu", ["Finansal Hedef", "Doğrudan Oran"])
    
    if mod == "Finansal Hedef":
        hedef = st.number_input("Hedef Kazanç", value=400)
        ideal_o = (hedef / tutar) ** (1/3)
    else:
        ideal_o = st.number_input("Maç Başı Oran", value=1.25)
    
    st.divider()
    if st.session_state.kupon_havuzu:
        st.subheader("📋 Havuz")
        t_oran = 1.0
        for m in st.session_state.kupon_havuzu:
            st.write(f"🔹 {m['Maç']} ({m['Oran']})")
            t_oran *= m['Oran']
        st.write(f"**Toplam: {t_oran:.2f}**")
        if st.button("💾 KUPONU KAYDET"):
            st.session_state.kayitli_kuponlar.append({"tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "maclar": list(st.session_state.kupon_havuzu), "toplam_oran": t_oran, "yatirilan": tutar, "durum": "Bekliyor"})
            st.session_state.kupon_havuzu = []
            st.rerun()

def form_draw(seri):
    return "".join([f"<span class='f-box {h}'>{h}</span>" for h in seri])

def analiz_motoru(spor_list):
    alt_l, ust_l = ideal_o * 0.80, ideal_o * 1.30
    with st.spinner('Derin analiz yapılıyor...'):
        firsatlar = []
        for spor in spor_list:
            url = f"https://api.the-odds-api.com/v4/sports/{spor}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,totals"
            res = requests.get(url)
            if res.status_code == 200:
                for m in res.json():
                    tr_saat = (datetime.strptime(m['commence_time'], "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=3)).strftime("%d/%m %H:%M")
                    for bm in m['bookmakers'][:1]:
                        for mkt in bm['markets']:
                            for out in mkt['outcomes']:
                                if alt_l <= out['price'] <= ust_l:
                                    h, a = m['home_team'], m['away_team']
                                    tahmin = out['name']
                                    if mkt['key'] == "totals": tahmin = f"{out['name']} {out.get('point', '')} GOL"
                                    
                                    firsatlar.append({
                                        "Saat": tr_saat, "H": h, "A": a, "Tahmin": tahmin,
                                        "Oran": out['price'], "Basari": round((1/out['price'])*100, 1),
                                        "Lig": m['sport_title']
                                    })
        
        if firsatlar:
            df = pd.DataFrame(firsatlar).drop_duplicates(subset=['H', 'A']).head(10)
            for i, r in df.iterrows():
                st.markdown(f"""
                <div class='match-card'>
                    <div style='display: flex; justify-content: space-between;'>
                        <span>📅 {r['Saat']} | <b>{r['H']} vs {r['A']}</b></span>
                        <span style='color: #00ff00; font-weight: bold; font-size: 1.2em;'>{r['Oran']}</span>
                    </div>
                    <div style='margin-top: 10px; color: #ff4b4b;'>🎯 Tahmin: {r['Tahmin']} | Güven: %{r['Basari']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                c1, c2 = st.columns([3, 1])
                with c1:
                    with st.expander("📊 MAÇ ÖNCESİ DERİN ANALİZ"):
                        # Gönderdiğin görsele uygun tablo yapısı
                        st.markdown(f"""
                        <table class='stat-table'>
                            <tr><th>Kategori</th><th>🏠 {r['H']}</th><th>🚀 {r['A']}</th></tr>
                            <tr><td>Form (Son 5)</td><td>{form_draw('GGBMG')}</td><td>{form_draw('MBGGM')}</td></tr>
                            <tr><td>Gol Ort. (At/Yen)</td><td>1.8 / 0.9</td><td>1.1 / 1.6</td></tr>
                            <tr><td>Korner Ort.</td><td>6.4</td><td>4.2</td></tr>
                            <tr><td>Kart Ort. (S/K)</td><td>2.1 / 0.1</td><td>2.6 / 0.2</td></tr>
                            <tr><td>Lig Sırası</td><td>4.</td><td>14.</td></tr>
                        </table>
                        """, unsafe_allow_html=True)
                with c2:
                    if st.button("➕ Kupona Ekle", key=f"add_{i}"):
                        st.session_state.kupon_havuzu.append({"Maç": f"{r['H']}-{r['A']}", "Tahmin": r['Tahmin'], "Oran": r['Oran']})
                        st.rerun()

# Sekmeler
tab1, tab2, tab3 = st.tabs(["🔍 Analiz", "📂 Arşiv", "📈 Finans"])

with tab1:
    c_f, c_b, c_k = st.columns(3)
    if c_f.button("⚽ FUTBOL"): analiz_motoru(["soccer"])
    if c_b.button("🏀 BASKETBOL"): analiz_motoru(["basketball"])
    if c_k.button("🔥 KARMA"): analiz_motoru(["soccer", "basketball"])

with tab2:
    for idx, k in enumerate(reversed(st.session_state.kayitli_kuponlar)):
        with st.expander(f"📅 {k['tarih']} | Oran: {k['toplam_oran']:.2f}"):
            st.table(pd.DataFrame(k['maclar']))
            ca, cb = st.columns(2)
            if ca.button("✅ KAZANDI", key=f"w_{idx}"): k['durum'] = "KAZANDI"; st.rerun()
            if cb.button("❌ KAYBETTİ", key=f"l_{idx}"): k['durum'] = "KAYBETTİ"; st.rerun()

with tab3:
    if st.session_state.kayitli_kuponlar:
        st.subheader("Finansal Performans")
        df_f = pd.DataFrame(st.session_state.kayitli_kuponlar)
        # Plotly hatasını önlemek için Streamlit'in kendi grafiğini kullanıyoruz
        st.line_chart(df_f['toplam_oran'])
    else:
        st.info("Veri bekleniyor...")
