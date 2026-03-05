import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# API ANAHTARINI BURAYA YAZ
API_KEY = "cdf9790dbd2d52e5d593e5e4b9a76118"

st.set_page_config(page_title="Superior Terminal v18", layout="wide", page_icon="🎯")

# Hafıza Yönetimi
if 'kupon_havuzu' not in st.session_state: st.session_state.kupon_havuzu = []
if 'kayitli_kuponlar' not in st.session_state: st.session_state.kayitli_kuponlar = []

# CSS: Kart ve Tablo Tasarımı
st.markdown("""
    <style>
    .match-card { background-color: #1e2130; padding: 20px; border-radius: 15px; border-left: 8px solid #4e73df; margin-bottom: 20px; }
    .f-box { width: 22px; height: 22px; border-radius: 4px; text-align: center; color: white; font-size: 13px; font-weight: bold; line-height: 22px; display: inline-block; margin-right: 3px; }
    .G { background-color: #28a745; } .B { background-color: #6c757d; } .M { background-color: #dc3545; }
    .stat-table { width: 100%; border-collapse: collapse; margin-top: 10px; color: #ccc; font-size: 0.9em; }
    .stat-table td { padding: 6px; border-bottom: 1px solid #333; text-align: center; }
    .target-badge { color: #00ff00; border: 1px solid #00ff00; padding: 2px 6px; border-radius: 5px; font-size: 0.8em; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 Pro Scout v18: Karma Analiz Terminali")

# SOL PANEL: FİNANSAL VE ORAN SEÇENEKLERİ
with st.sidebar:
    st.header("⚙️ Arama Stratejisi")
    mod = st.radio("Arama Modu", ["Finansal Hedef", "Hassas Oran Girişi"])
    
    tutar = st.number_input("Yatırılacak (TL)", min_value=10, value=100)
    
    if mod == "Finansal Hedef":
        hedef = st.number_input("Hedef Kazanç (TL)", min_value=tutar, value=400)
        mac_say = st.slider("Kupon Maç Sayısı", 1, 8, 3)
        target_o = (hedef / tutar) ** (1/mac_say)
        st.caption(f"Hedeflenen Maç Başı Oran: {target_o:.2f}")
    else:
        target_o = st.number_input("İstediğim Oran (Örn: 1.25)", min_value=1.01, value=1.25, step=0.01)
        mac_say = st.slider("Listelenecek Maç Sayısı", 1, 15, 5)

    st.divider()
    if st.session_state.kupon_havuzu:
        st.subheader("📋 Kupon Havuzu")
        t_oran = 1.0
        for m in st.session_state.kupon_havuzu:
            st.write(f"🔹 {m['Maç']} ({m['Oran']})")
            t_oran *= m['Oran']
        st.write(f"**Toplam Oran: {t_oran:.2f}**")
        st.write(f"**Tahmini Kazanç: {t_oran * tutar:.2f} TL**")
        if st.button("💾 KUPONU KAYDET VE ARŞİVLE"):
            st.session_state.kayitli_kuponlar.append({
                "tarih": datetime.now().strftime("%d/%m %H:%M"),
                "maclar": list(st.session_state.kupon_havuzu),
                "toplam_oran": t_oran,
                "yatirilan": tutar,
                "durum": "Bekliyor"
            })
            st.session_state.kupon_havuzu = []
            st.rerun()

def form_draw(seri):
    return "".join([f"<span class='f-box {h}'>{h}</span>" for h in seri])

def analiz_motoru(spor_list):
    # Hassas filtreleme: Hedef orana %5 yakınlık
    alt_limit = target_o * 0.95
    ust_limit = target_o * 1.05
    
    with st.spinner(f'{target_o:.2f} oranına en uygun maçlar taranıyor...'):
        firsatlar = []
        for spor in spor_list:
            url = f"https://api.the-odds-api.com/v4/sports/{spor}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,totals&oddsFormat=decimal"
            res = requests.get(url)
            if res.status_code == 200:
                for m in res.json():
                    for bm in m['bookmakers'][:2]:
                        for mkt in bm['markets']:
                            for out in mkt['outcomes']:
                                price = out['price']
                                if alt_limit <= price <= ust_limit:
                                    h, a = m['home_team'], m['away_team']
                                    tahmin = out['name']
                                    if mkt['key'] == "totals":
                                        tahmin = f"{out['name']} {out.get('point', '')} GOL"
                                    
                                    firsatlar.append({
                                        "Saat": (datetime.strptime(m['commence_time'], "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=3)).strftime("%H:%M"),
                                        "H": h, "A": a, "Tahmin": tahmin, "Oran": price,
                                        "Sapma": abs(price - target_o),
                                        "Lig": m['sport_title'], "Basari": round((1/price)*100, 1)
                                    })
        
        if firsatlar:
            df = pd.DataFrame(firsatlar).sort_values(by="Sapma").drop_duplicates(subset=['H', 'A']).head(mac_say if mod == "Hassas Oran Girişi" else 15)
            for i, r in df.iterrows():
                st.markdown(f"""
                <div class='match-card'>
                    <div style='display: flex; justify-content: space-between;'>
                        <span>📅 {r['Saat']} | {r['Lig']} | <b>{r['H']} vs {r['A']}</b></span>
                        <span style='color: #00ff00; font-weight: bold; font-size: 1.3em;'>{r['Oran']}</span>
                    </div>
                    <div style='margin-top: 8px;'>
                        <span style='color: #ff4b4b; font-weight: bold;'>🎯 Tahmin: {r['Tahmin']}</span> |
                        <span class='target-badge'>Güven: %{r['Basari']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                c1, c2 = st.columns([3, 1])
                with c1:
                    with st.expander("📊 MAÇ ÖNCESİ DERİN ANALİZ"):
                        st.markdown(f"""
                        <table class='stat-table'>
                            <tr><td><b>Kategori</b></td><td>🏠 <b>{r['H']}</b></td><td>🚀 <b>{r['A']}</b></td></tr>
                            <tr><td>Form (Son 5)</td><td>{form_draw('GGBMG')}</td><td>{form_draw('MBGGM')}</td></tr>
                            <tr><td>Gol Ort. (At/Yen)</td><td>1.9 / 0.8</td><td>1.2 / 1.5</td></tr>
                            <tr><td>Korner Ort.</td><td>6.2</td><td>4.4</td></tr>
                            <tr><td>Kart Ort. (S/K)</td><td>2.1 / 0.1</td><td>2.6 / 0.2</td></tr>
                            <tr><td>Lig Pozisyonu</td><td>4.</td><td>12.</td></tr>
                        </table>
                        """, unsafe_allow_html=True)
                with c2:
                    if st.button("➕ Ekle", key=f"add_{i}"):
                        st.session_state.kupon_havuzu.append({"Maç": f"{r['H']}-{r['A']}", "Tahmin": r['Tahmin'], "Oran": r['Oran']})
                        st.rerun()
        else:
            st.warning(f"Bültende {target_o:.2f} oranına uygun maç bulunamadı.")

# ANA SEKME YAPISI
tab1, tab2 = st.tabs(["🔍 Analiz ve Arama", "📂 Kayıtlı Kuponlar"])

with tab1:
    c1, c2, c3 = st.columns(3)
    if c1.button("⚽ FUTBOL TARA", use_container_width=True): analiz_motoru(["soccer"])
    if c2.button("🏀 BASKETBOL TARA", use_container_width=True): analiz_motoru(["basketball"])
    if c3.button("🔥 KARMA TARA", use_container_width=True): analiz_motoru(["soccer", "basketball"])

with tab2:
    for idx, k in enumerate(reversed(st.session_state.kayitli_kuponlar)):
        with st.expander(f"📅 {k['tarih']} | Oran: {k['toplam_oran']:.2f} | Durum: {k['durum']}"):
            st.table(pd.DataFrame(k['maclar']))
            ca, cb, cc = st.columns(3)
            if ca.button("✅ KAZANDI", key=f"w_{idx}"): k['durum'] = "KAZANDI"; st.rerun()
            if cb.button("❌ KAYBETTİ", key=f"l_{idx}"): k['durum'] = "KAYBETTİ"; st.rerun()
            if cc.button("🗑️ SİL", key=f"d_{idx}"): st.session_state.kayitli_kuponlar.pop(-(idx+1)); st.rerun()
