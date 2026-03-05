import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import random

# API ANAHTARI
API_KEY = "cdf9790dbd2d52e5d593e5e4b9a76118"

st.set_page_config(page_title="Scout v30", layout="wide", page_icon="⚡", initial_sidebar_state="collapsed")

# 1. SESSION STATE
if 'kupon_havuzu' not in st.session_state: st.session_state.kupon_havuzu = []
if 'arsiv' not in st.session_state: st.session_state.arsiv = []

# 2. CALLBACK
def mac_ekle(mac_adi, tahmin, oran):
    st.session_state.kupon_havuzu.append({"Maç": mac_adi, "Tahmin": tahmin, "Oran": oran})
    st.toast(f"✅ {mac_adi} eklendi!")

# 3. CSS - MOBİL OPTİMİZE
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #0d0f1a;
        color: #e0e6ff;
    }

    /* BAŞLIK */
    h1 { font-family: 'Rajdhani', sans-serif !important; font-size: 1.6rem !important; letter-spacing: 2px; color: #ffffff; }

    /* MAÇ KARTI */
    .match-card {
        background: linear-gradient(135deg, #161928 0%, #1a1e30 100%);
        padding: 14px 16px;
        border-radius: 14px;
        border-left: 5px solid #3d7eff;
        margin-bottom: 14px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    }
    .match-header { font-family: 'Rajdhani', sans-serif; font-size: 1.05rem; font-weight: 700; color: #ffffff; margin-bottom: 6px; }
    .match-meta { font-size: 0.78rem; color: #7b88b0; margin-bottom: 8px; }
    .badge-oran { background: #1e3a1e; color: #4cff72; padding: 3px 10px; border-radius: 20px; font-size: 0.82rem; font-weight: 600; margin-right: 8px; }
    .badge-tahmin { background: #2a1e1e; color: #ff6b6b; padding: 3px 10px; border-radius: 20px; font-size: 0.82rem; font-weight: 600; }

    /* TAKIM İSTATİSTİK TABLOSU */
    .stat-section { margin-top: 10px; }
    .stat-title { font-family: 'Rajdhani', sans-serif; font-size: 0.85rem; font-weight: 700; color: #3d7eff; letter-spacing: 1px; text-transform: uppercase; margin: 10px 0 6px 0; padding-bottom: 4px; border-bottom: 1px solid #252a40; }
    .stat-table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
    .stat-table th { color: #7b88b0; font-weight: 500; padding: 5px 4px; text-align: center; font-size: 0.75rem; background: #12141f; }
    .stat-table th:first-child { text-align: left; }
    .stat-table td { padding: 6px 4px; text-align: center; border-bottom: 1px solid #1e2235; }
    .stat-table td:first-child { text-align: left; font-weight: 600; color: #c8d0f0; }
    .stat-table tr:last-child td { border-bottom: none; }
    .stat-val-good { color: #4cff72; font-weight: 600; }
    .stat-val-mid { color: #ffd166; font-weight: 600; }
    .stat-val-bad { color: #ff6b6b; font-weight: 600; }

    /* FORM KUTUCULARI */
    .form-row { display: flex; gap: 4px; margin-top: 4px; }
    .f-box { width: 22px; height: 22px; border-radius: 5px; text-align: center; color: white; font-size: 11px; font-weight: 700; line-height: 22px; display: inline-flex; align-items: center; justify-content: center; }
    .G { background-color: #28a745; } .B { background-color: #555d75; } .M { background-color: #dc3545; }

    /* MOBİL BUTON */
    .stButton>button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.85rem !important;
        border: none !important;
        transition: all 0.2s ease !important;
    }

    /* KUPON SIDEBAR */
    .kupon-item { background: #12141f; padding: 8px 12px; border-radius: 8px; margin-bottom: 6px; border-left: 3px solid #3d7eff; font-size: 0.82rem; }

    /* EXPANDER ÖZELLEŞTIRME */
    .streamlit-expanderHeader { font-size: 0.85rem !important; color: #7b88b0 !important; }

    /* SEKME */
    .stTabs [data-baseweb="tab"] { font-family: 'Rajdhani', sans-serif; font-size: 1rem; font-weight: 600; letter-spacing: 1px; }

    /* TOOLTIP RENK */
    div[data-testid="stToast"] { background: #1e3a1e !important; color: #4cff72 !important; }

    /* GENİŞLİK SINIRI (MOBİL) */
    .block-container { max-width: 100% !important; padding: 1rem 0.8rem !important; }
    </style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# 4. İSTATİSTİK ÜRETICI (Takım Bazlı Mock Data)
# ─────────────────────────────────────────
def takim_istatistik_olustur(takim_adi, ev_mi=True):
    """
    Gerçek API'ye bağlandığında buraya football-data.org veya
    API-Football (rapidapi) verisi beslenebilir.
    Şimdilik seed-based deterministik mock veri üretiyoruz.
    """
    seed = sum(ord(c) for c in takim_adi) + (10 if ev_mi else 0)
    rng = random.Random(seed)

    gol_a = round(rng.uniform(0.8, 2.4), 1)   # Atılan gol/maç
    gol_y = round(rng.uniform(0.5, 1.9), 1)   # Yenen gol/maç
    korner = round(rng.uniform(3.5, 7.2), 1)  # Korner/maç
    sari = round(rng.uniform(1.2, 3.0), 1)    # Sarı kart/maç
    kirmizi = round(rng.uniform(0.0, 0.25), 2) # Kırmızı kart/maç
    siralama = rng.randint(1, 20)              # Lig sırası
    puan = rng.randint(20, 68)
    form_list = rng.choices(["G", "B", "M"], weights=[45, 25, 30], k=5)

    return {
        "gol_a": gol_a,
        "gol_y": gol_y,
        "korner": korner,
        "sari": sari,
        "kirmizi": kirmizi,
        "siralama": siralama,
        "puan": puan,
        "form": form_list
    }

def renk_class(deger, esik_iyi, esik_orta, ters=False):
    """Değere göre renk sınıfı döndür"""
    if ters:
        if deger <= esik_iyi: return "stat-val-good"
        elif deger <= esik_orta: return "stat-val-mid"
        else: return "stat-val-bad"
    else:
        if deger >= esik_iyi: return "stat-val-good"
        elif deger >= esik_orta: return "stat-val-mid"
        else: return "stat-val-bad"

def istatistik_html(ev_takim, dep_takim):
    ev  = takim_istatistik_olustur(ev_takim, ev_mi=True)
    dep = takim_istatistik_olustur(dep_takim, ev_mi=False)

    def form_html(form_list):
        boxes = "".join(f"<span class='f-box {f}'>{f}</span>" for f in form_list)
        return f"<div class='form-row'>{boxes}</div>"

    html = f"""
    <div class='stat-section'>
        <div class='stat-title'>📊 Takım Karşılaştırması</div>
        <table class='stat-table'>
            <thead>
                <tr>
                    <th>İSTATİSTİK</th>
                    <th>🏠 {ev_takim[:12]}</th>
                    <th>✈️ {dep_takim[:12]}</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Lig Sırası</td>
                    <td class='{renk_class(ev["siralama"], 6, 12, ters=True)}'>{ev['siralama']}. ({ev['puan']} pt)</td>
                    <td class='{renk_class(dep["siralama"], 6, 12, ters=True)}'>{dep['siralama']}. ({dep['puan']} pt)</td>
                </tr>
                <tr>
                    <td>Gol Ortalaması (A)</td>
                    <td class='{renk_class(ev["gol_a"], 1.8, 1.2)}'>{ev['gol_a']}</td>
                    <td class='{renk_class(dep["gol_a"], 1.8, 1.2)}'>{dep['gol_a']}</td>
                </tr>
                <tr>
                    <td>Gol Ortalaması (Y)</td>
                    <td class='{renk_class(ev["gol_y"], 0.9, 1.4, ters=True)}'>{ev['gol_y']}</td>
                    <td class='{renk_class(dep["gol_y"], 0.9, 1.4, ters=True)}'>{dep['gol_y']}</td>
                </tr>
                <tr>
                    <td>Korner / Maç</td>
                    <td class='{renk_class(ev["korner"], 6.0, 4.5)}'>{ev['korner']}</td>
                    <td class='{renk_class(dep["korner"], 6.0, 4.5)}'>{dep['korner']}</td>
                </tr>
                <tr>
                    <td>Sarı Kart / Maç</td>
                    <td class='{renk_class(ev["sari"], 2.5, 1.8, ters=True)}'>{ev['sari']}</td>
                    <td class='{renk_class(dep["sari"], 2.5, 1.8, ters=True)}'>{dep['sari']}</td>
                </tr>
                <tr>
                    <td>Kırmızı Kart / Maç</td>
                    <td class='{renk_class(ev["kirmizi"], 0.1, 0.2, ters=True)}'>{ev['kirmizi']}</td>
                    <td class='{renk_class(dep["kirmizi"], 0.1, 0.2, ters=True)}'>{dep['kirmizi']}</td>
                </tr>
                <tr>
                    <td>Son 5 Maç Formu</td>
                    <td>{form_html(ev['form'])}</td>
                    <td>{form_html(dep['form'])}</td>
                </tr>
            </tbody>
        </table>
    </div>
    """
    return html

# ─────────────────────────────────────────
# 5. SOL PANEL
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Ayarlar")
    mod = st.radio("Arama Modu", ["Finansal Hedef", "Doğrudan Oran"], horizontal=True)
    tutar = st.number_input("Tutar (TL)", min_value=10, value=100, step=10)

    if mod == "Finansal Hedef":
        hedef = st.number_input("Hedef Kazanç (TL)", value=400, step=50)
        target_o = (hedef / tutar) ** (1/3)
        st.caption(f"Hedef oran/maç: **{target_o:.2f}**")
    else:
        target_o = st.number_input("Oran Kriteri", value=1.25, step=0.05)

    st.divider()
    st.markdown("### 📋 Kupon Havuzu")

    if st.session_state.kupon_havuzu:
        t_oran = 1.0
        for idx, m in enumerate(st.session_state.kupon_havuzu):
            st.markdown(f"""
            <div class='kupon-item'>
                🔹 <b>{m['Maç']}</b><br>
                <span style='color:#7b88b0;font-size:0.78rem;'>{m['Tahmin']} · Oran: <b style='color:#4cff72;'>{m['Oran']}</b></span>
            </div>
            """, unsafe_allow_html=True)
            t_oran *= m['Oran']

        st.success(f"📊 Toplam: **{t_oran:.2f}x** · Kazanç: **{t_oran * tutar:.0f} TL**")

        col_s, col_t = st.columns(2)
        with col_s:
            if st.button("💾 Kaydet", use_container_width=True, type="primary"):
                st.session_state.arsiv.append({
                    "tarih": datetime.now().strftime("%d/%m %H:%M"),
                    "maclar": list(st.session_state.kupon_havuzu),
                    "oran": t_oran,
                    "durum": "Bekliyor"
                })
                st.session_state.kupon_havuzu = []
                st.rerun()
        with col_t:
            if st.button("🗑️ Temizle", use_container_width=True):
                st.session_state.kupon_havuzu = []
                st.rerun()
    else:
        st.info("Henüz maç eklenmedi.")

# ─────────────────────────────────────────
# 6. ANALİZ MOTORU
# ─────────────────────────────────────────
def analiz_motoru(spor_list):
    alt_l, ust_l = target_o * 0.90, target_o * 1.10

    with st.spinner("⏳ Piyasa taranıyor..."):
        url = (f"https://api.the-odds-api.com/v4/sports/{spor_list[0]}/odds/"
               f"?apiKey={API_KEY}&regions=eu&markets=h2h,totals")
        res = requests.get(url)

    if res.status_code != 200:
        st.error("❌ API hatası! Anahtarı kontrol edin.")
        return

    firsatlar = []
    for m in res.json():
        for bm in m['bookmakers'][:1]:
            for mkt in bm['markets']:
                for out in mkt['outcomes']:
                    if alt_l <= out['price'] <= ust_l:
                        firsatlar.append({
                            "Saat": (datetime.strptime(m['commence_time'], "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=3)).strftime("%H:%M"),
                            "H": m['home_team'],
                            "A": m['away_team'],
                            "Lig": m['sport_title'],
                            "Tahmin": out['name'] if mkt['key'] == "h2h" else f"{out['name']} {out.get('point', '')} G",
                            "Oran": out['price']
                        })

    if not firsatlar:
        st.warning("Bu oran aralığında maç bulunamadı.")
        return

    df = pd.DataFrame(firsatlar).drop_duplicates(subset=['H', 'A']).head(12)
    st.caption(f"**{len(df)} fırsat** bulundu · Oran aralığı: {alt_l:.2f} – {ust_l:.2f}")

    for i, r in df.iterrows():
        # MAÇ KARTI
        st.markdown(f"""
        <div class='match-card'>
            <div class='match-header'>⚽ {r['H']} <span style='color:#555d75'>vs</span> {r['A']}</div>
            <div class='match-meta'>🕐 {r['Saat']} &nbsp;·&nbsp; 🏆 {r['Lig']}</div>
            <span class='badge-oran'>📈 {r['Oran']}</span>
            <span class='badge-tahmin'>🎯 {r['Tahmin']}</span>
        </div>
        """, unsafe_allow_html=True)

        col_exp, col_btn = st.columns([5, 1])
        with col_exp:
            with st.expander("📊 Takım İstatistikleri"):
                stat_html = istatistik_html(r['H'], r['A'])
                st.markdown(stat_html, unsafe_allow_html=True)
                st.caption("🟢 İyi · 🟡 Orta · 🔴 Zayıf performans göstergesi")

        with col_btn:
            st.button(
                "➕",
                key=f"btn_{i}",
                on_click=mac_ekle,
                args=(f"{r['H']}-{r['A']}", r['Tahmin'], r['Oran']),
                use_container_width=True,
                help="Kupona ekle"
            )

        st.markdown("<hr style='border-color:#1e2235;margin:4px 0 10px;'>", unsafe_allow_html=True)

# ─────────────────────────────────────────
# 7. BAŞLIK & SEKMELER
# ─────────────────────────────────────────
st.title("⚡ Superior Scout v30")
st.caption(f"Hedef oran: **{target_o:.2f}** · Tutar: **{tutar} TL**")

tab1, tab2 = st.tabs(["🔍 Analiz", "📂 Arşiv"])

with tab1:
    c1, c2, c3 = st.columns(3)
    run_futbol     = c1.button("⚽ FUTBOL",    use_container_width=True, type="primary")
    run_basketbol  = c2.button("🏀 BASKETBOL", use_container_width=True)
    run_karma      = c3.button("🔥 KARMA",     use_container_width=True)

    if run_futbol:    analiz_motoru(["soccer_turkey_super_league"])
    if run_basketbol: analiz_motoru(["basketball_euroleague"])
    if run_karma:     analiz_motoru(["soccer_turkey_super_league"])

with tab2:
    if st.session_state.arsiv:
        for k in reversed(st.session_state.arsiv):
            durum_renk = "🟢" if k['durum'] == "Kazandı" else "🔴" if k['durum'] == "Kaybetti" else "🟡"
            with st.expander(f"{durum_renk} {k['tarih']} · Oran: {k['oran']:.2f}x"):
                df_arsiv = pd.DataFrame(k['maclar'])
                st.dataframe(df_arsiv, use_container_width=True, hide_index=True)

                col_k, col_b = st.columns(2)
                idx = st.session_state.arsiv.index(k)
                if col_k.button("✅ Kazandı", key=f"kaz_{idx}"):
                    st.session_state.arsiv[idx]['durum'] = "Kazandı"; st.rerun()
                if col_b.button("❌ Kaybetti", key=f"kay_{idx}"):
                    st.session_state.arsiv[idx]['durum'] = "Kaybetti"; st.rerun()
    else:
        st.info("Henüz kaydedilmiş kupon yok.")
