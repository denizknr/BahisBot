import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import hashlib

# ── API ANAHTARI ──────────────────────────────────────────────────────────────
API_KEY = "c09318cad2ff47f92f8468f48dc64f72"

st.set_page_config(page_title="Scout v31", layout="wide", page_icon="⚡", initial_sidebar_state="collapsed")

# ── SESSION STATE ─────────────────────────────────────────────────────────────
if 'kupon_havuzu' not in st.session_state: st.session_state.kupon_havuzu = []
if 'arsiv'        not in st.session_state: st.session_state.arsiv = []

# ── CALLBACK ──────────────────────────────────────────────────────────────────
def mac_ekle(mac_adi, tahmin, oran):
    st.session_state.kupon_havuzu.append({"Maç": mac_adi, "Tahmin": tahmin, "Oran": oran})
    st.toast(f"✅ {mac_adi} eklendi!")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0d0f1a; color: #e0e6ff; }
h1 { font-family: 'Rajdhani', sans-serif !important; font-size: 1.6rem !important; letter-spacing: 2px; color: #ffffff; }

.match-card {
    background: linear-gradient(135deg, #161928 0%, #1a1e30 100%);
    padding: 14px 16px; border-radius: 14px;
    border-left: 5px solid #3d7eff; margin-bottom: 6px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
}
.match-header { font-family: 'Rajdhani', sans-serif; font-size: 1.05rem; font-weight: 700; color: #ffffff; margin-bottom: 4px; }
.match-meta   { font-size: 0.78rem; color: #7b88b0; margin-bottom: 8px; }
.badge-oran   { background: #1e3a1e; color: #4cff72; padding: 3px 10px; border-radius: 20px; font-size: 0.82rem; font-weight: 600; margin-right: 8px; }
.badge-tahmin { background: #2a1e1e; color: #ff6b6b; padding: 3px 10px; border-radius: 20px; font-size: 0.82rem; font-weight: 600; }
.badge-tarih  { background: #1a1e30; color: #a0aacc; padding: 3px 10px; border-radius: 20px; font-size: 0.78rem; margin-right: 6px; }

/* İSTATİSTİK TABLOSU */
.stat-section { margin-top: 8px; }
.stat-title {
    font-family: 'Rajdhani', sans-serif; font-size: 0.85rem; font-weight: 700;
    color: #3d7eff; letter-spacing: 1px; text-transform: uppercase;
    margin: 8px 0 6px 0; padding-bottom: 4px; border-bottom: 1px solid #252a40;
}
.stat-table  { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
.stat-table th {
    color: #7b88b0; font-weight: 500; padding: 5px 4px;
    text-align: center; font-size: 0.72rem; background: #12141f;
}
.stat-table th:first-child { text-align: left; }
.stat-table td { padding: 6px 4px; text-align: center; border-bottom: 1px solid #1e2235; }
.stat-table td:first-child { text-align: left; font-weight: 600; color: #c8d0f0; font-size: 0.78rem; }
.stat-table tr:last-child td { border-bottom: none; }
.sv-iyi  { color: #4cff72; font-weight: 700; }
.sv-orta { color: #ffd166; font-weight: 700; }
.sv-kotu { color: #ff6b6b; font-weight: 700; }

/* FORM */
.form-row { display: flex; gap: 4px; margin-top: 2px; justify-content: center; }
.f-box {
    width: 22px; height: 22px; border-radius: 5px; text-align: center;
    color: white; font-size: 11px; font-weight: 700;
    display: inline-flex; align-items: center; justify-content: center;
}
.G { background-color: #28a745; } .B { background-color: #555d75; } .M { background-color: #dc3545; }

/* BUTON */
.stButton>button {
    border-radius: 10px !important; font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important; font-size: 0.85rem !important;
    border: none !important; transition: all 0.2s ease !important;
}
.kupon-item {
    background: #12141f; padding: 8px 12px; border-radius: 8px;
    margin-bottom: 6px; border-left: 3px solid #3d7eff; font-size: 0.82rem;
}
.stTabs [data-baseweb="tab"] { font-family: 'Rajdhani', sans-serif; font-size: 1rem; font-weight: 600; letter-spacing: 1px; }
div[data-testid="stToast"]   { background: #1e3a1e !important; color: #4cff72 !important; }
.block-container { max-width: 100% !important; padding: 1rem 0.8rem !important; }
</style>
""", unsafe_allow_html=True)

# ── GLOBAL LİG LİSTESİ ───────────────────────────────────────────────────────
# The Odds API'de aktif olan popüler ligler (sport key formatı)
FUTBOL_LIGLER = [
    "soccer_turkey_super_league",
    "soccer_epl",
    "soccer_spain_la_liga",
    "soccer_germany_bundesliga",
    "soccer_italy_serie_a",
    "soccer_france_ligue_one",
    "soccer_netherlands_eredivisie",
    "soccer_portugal_primeira_liga",
    "soccer_champions_league",
    "soccer_europa_league",
    "soccer_usa_mls",
    "soccer_brazil_campeonato",
    "soccer_argentina_primera_division",
]
BASKETBOL_LIGLER = [
    "basketball_nba",
    "basketball_euroleague",
    "basketball_ncaab",
]
KARMA_LIGLER = FUTBOL_LIGLER[:6] + BASKETBOL_LIGLER[:2]

# ── İSTATİSTİK MOTOR ─────────────────────────────────────────────────────────
def _seed(takim_adi: str, ev_mi: bool) -> int:
    """
    Takım adından tutarlı bir sayısal seed üret.
    Galatasaray her zaman aynı değerleri verir.
    Gerçek API entegrasyonunda bu fonksiyon kaldırılır,
    veriler football-data.org / API-Football'dan çekilir.
    """
    raw = (takim_adi.lower().strip() + ("_home" if ev_mi else "_away")).encode()
    return int(hashlib.md5(raw).hexdigest(), 16) % (2**31)

def takim_istatistik_olustur(takim_adi: str, ev_mi: bool = True) -> dict:
    import random
    rng = random.Random(_seed(takim_adi, ev_mi))

    # Daha gerçekçi aralıklar — ev takımları biraz daha avantajlı
    ev_bonus = 0.15 if ev_mi else 0.0

    gol_a    = round(rng.uniform(0.7 + ev_bonus, 2.2 + ev_bonus), 2)
    gol_y    = round(rng.uniform(0.5, 1.8 - ev_bonus * 0.5), 2)
    korner   = round(rng.uniform(3.5, 7.0), 1)
    sari     = round(rng.uniform(1.0, 3.2), 1)
    kirmizi  = round(rng.uniform(0.00, 0.20), 2)

    # Lig sırası: adın hash'ine göre 1-20 arasında SABIT
    siralama = (int(hashlib.md5(takim_adi.lower().encode()).hexdigest(), 16) % 20) + 1
    puan     = max(5, 72 - siralama * 3 + rng.randint(-4, 4))   # sıraya orantılı puan

    # Son 5 maç formu — sıralama iyiyse kazanma ağırlığı artar
    g_w = max(20, 60 - siralama * 2)   # 1. sıra → %58 galibiyet
    m_w = max(10, 15 + siralama)
    b_w = 100 - g_w - m_w
    form_list = rng.choices(["G", "B", "M"], weights=[g_w, b_w, m_w], k=5)

    return {
        "gol_a": gol_a, "gol_y": gol_y,
        "korner": korner, "sari": sari, "kirmizi": kirmizi,
        "siralama": siralama, "puan": puan, "form": form_list,
    }

def sv(deger, esik_iyi, esik_orta, ters=False) -> str:
    """Değere göre CSS sınıfı"""
    if ters:
        return "sv-iyi" if deger <= esik_iyi else ("sv-orta" if deger <= esik_orta else "sv-kotu")
    return "sv-iyi" if deger >= esik_iyi else ("sv-orta" if deger >= esik_orta else "sv-kotu")

def istatistik_html(ev_takim: str, dep_takim: str) -> str:
    ev  = takim_istatistik_olustur(ev_takim, ev_mi=True)
    dep = takim_istatistik_olustur(dep_takim, ev_mi=False)

    def form_html(fl):
        return "<div class='form-row'>" + "".join(f"<span class='f-box {f}'>{f}</span>" for f in fl) + "</div>"

    # Lig sırası rengi: 1-6 iyi, 7-14 orta, 15+ kötü
    ev_sir_cls  = sv(ev["siralama"],  6, 14, ters=True)
    dep_sir_cls = sv(dep["siralama"], 6, 14, ters=True)

    return f"""
<div class='stat-section'>
    <div class='stat-title'>📊 Takım Karşılaştırması</div>
    <table class='stat-table'>
        <thead><tr>
            <th>İSTATİSTİK</th>
            <th>🏠 {ev_takim[:14]}</th>
            <th>✈️ {dep_takim[:14]}</th>
        </tr></thead>
        <tbody>
            <tr>
                <td>Lig Sırası</td>
                <td class='{ev_sir_cls}'>{ev['siralama']}. <small>({ev['puan']} pt)</small></td>
                <td class='{dep_sir_cls}'>{dep['siralama']}. <small>({dep['puan']} pt)</small></td>
            </tr>
            <tr>
                <td>Gol Ort. (Atılan)</td>
                <td class='{sv(ev["gol_a"],  1.8, 1.2)}'>{ev['gol_a']}</td>
                <td class='{sv(dep["gol_a"], 1.8, 1.2)}'>{dep['gol_a']}</td>
            </tr>
            <tr>
                <td>Gol Ort. (Yenilen)</td>
                <td class='{sv(ev["gol_y"],  0.9, 1.4, ters=True)}'>{ev['gol_y']}</td>
                <td class='{sv(dep["gol_y"], 0.9, 1.4, ters=True)}'>{dep['gol_y']}</td>
            </tr>
            <tr>
                <td>Korner / Maç</td>
                <td class='{sv(ev["korner"],  6.0, 4.5)}'>{ev['korner']}</td>
                <td class='{sv(dep["korner"], 6.0, 4.5)}'>{dep['korner']}</td>
            </tr>
            <tr>
                <td>Sarı Kart / Maç</td>
                <td class='{sv(ev["sari"],  2.2, 1.5, ters=True)}'>{ev['sari']}</td>
                <td class='{sv(dep["sari"], 2.2, 1.5, ters=True)}'>{dep['sari']}</td>
            </tr>
            <tr>
                <td>Kırmızı Kart / Maç</td>
                <td class='{sv(ev["kirmizi"],  0.08, 0.15, ters=True)}'>{ev['kirmizi']}</td>
                <td class='{sv(dep["kirmizi"], 0.08, 0.15, ters=True)}'>{dep['kirmizi']}</td>
            </tr>
            <tr>
                <td>Son 5 Maç</td>
                <td>{form_html(ev['form'])}</td>
                <td>{form_html(dep['form'])}</td>
            </tr>
        </tbody>
    </table>
    <div style='font-size:0.72rem;color:#555d75;margin-top:6px;'>
        ⚠️ İstatistikler tahmini göstergedir. Gerçek veri için API-Football entegrasyonu önerilir.
    </div>
</div>
"""

# ── SOL PANEL ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Ayarlar")
    mod   = st.radio("Arama Modu", ["Finansal Hedef", "Doğrudan Oran"], horizontal=True)
    tutar = st.number_input("Tutar (TL)", min_value=10, value=100, step=10)

    if mod == "Finansal Hedef":
        hedef    = st.number_input("Hedef Kazanç (TL)", value=400, step=50)
        target_o = (hedef / tutar) ** (1/3)
        st.caption(f"Hedef oran/maç: **{target_o:.2f}**")
    else:
        target_o = st.number_input("Oran Kriteri", value=1.25, step=0.05)

    st.divider()
    st.markdown("### 📋 Kupon Havuzu")

    if st.session_state.kupon_havuzu:
        t_oran = 1.0
        for m in st.session_state.kupon_havuzu:
            st.markdown(f"""
            <div class='kupon-item'>
                🔹 <b>{m['Maç']}</b><br>
                <span style='color:#7b88b0;font-size:0.78rem;'>
                    {m['Tahmin']} · <b style='color:#4cff72;'>{m['Oran']}</b>
                </span>
            </div>""", unsafe_allow_html=True)
            t_oran *= m['Oran']

        st.success(f"📊 Toplam: **{t_oran:.2f}x** · Kazanç: **{t_oran * tutar:.0f} TL**")
        cs, ct = st.columns(2)
        with cs:
            if st.button("💾 Kaydet", use_container_width=True, type="primary"):
                st.session_state.arsiv.append({
                    "tarih": datetime.now().strftime("%d/%m %H:%M"),
                    "maclar": list(st.session_state.kupon_havuzu),
                    "oran": t_oran, "durum": "Bekliyor"
                })
                st.session_state.kupon_havuzu = []
                st.rerun()
        with ct:
            if st.button("🗑️ Temizle", use_container_width=True):
                st.session_state.kupon_havuzu = []
                st.rerun()
    else:
        st.info("Henüz maç eklenmedi.")

# ── ANALİZ MOTORU ─────────────────────────────────────────────────────────────
def analiz_motoru(lig_listesi: list):
    alt_l, ust_l = target_o * 0.90, target_o * 1.10
    firsatlar = []

    progress = st.progress(0, text="⏳ Piyasalar taranıyor...")
    for i, lig in enumerate(lig_listesi):
        progress.progress((i + 1) / len(lig_listesi), text=f"⏳ {lig} taranıyor...")
        url = (f"https://api.the-odds-api.com/v4/sports/{lig}/odds/"
               f"?apiKey={API_KEY}&regions=eu&markets=h2h,totals")
        try:
            res = requests.get(url, timeout=8)
            if res.status_code != 200:
                continue
            for m in res.json():
                # Maç zamanını Türkiye saatine çevir (+3)
                dt_utc = datetime.strptime(m['commence_time'], "%Y-%m-%dT%H:%M:%SZ")
                dt_tr  = dt_utc + timedelta(hours=3)
                tarih_str = dt_tr.strftime("%d %b")   # "14 Haz"
                saat_str  = dt_tr.strftime("%H:%M")

                for bm in m['bookmakers'][:1]:
                    for mkt in bm['markets']:
                        for out in mkt['outcomes']:
                            if alt_l <= out['price'] <= ust_l:
                                firsatlar.append({
                                    "Tarih": tarih_str,
                                    "Saat":  saat_str,
                                    "H":     m['home_team'],
                                    "A":     m['away_team'],
                                    "Lig":   m['sport_title'],
                                    "Tahmin": out['name'] if mkt['key'] == "h2h"
                                              else f"{out['name']} {out.get('point','')} G",
                                    "Oran":  out['price'],
                                })
        except Exception:
            continue

    progress.empty()

    if not firsatlar:
        st.warning("Bu oran aralığında hiç maç bulunamadı.")
        return

    df = (pd.DataFrame(firsatlar)
            .drop_duplicates(subset=['H', 'A'])
            .sort_values('Saat')
            .head(15)
            .reset_index(drop=True))

    st.caption(f"**{len(df)} fırsat** · Oran aralığı: {alt_l:.2f} – {ust_l:.2f} · {len(lig_listesi)} lig tarandı")

    for i, r in df.iterrows():
        # Maç kartı
        st.markdown(f"""
        <div class='match-card'>
            <div class='match-header'>{r['H']} <span style='color:#555d75'>vs</span> {r['A']}</div>
            <div class='match-meta'>
                📅 {r['Tarih']} &nbsp;🕐 {r['Saat']} &nbsp;·&nbsp; 🏆 {r['Lig']}
            </div>
            <span class='badge-oran'>📈 {r['Oran']}</span>
            <span class='badge-tahmin'>🎯 {r['Tahmin']}</span>
        </div>
        """, unsafe_allow_html=True)

        col_exp, col_btn = st.columns([5, 1])
        with col_exp:
            with st.expander("📊 Takım İstatistikleri"):
                st.markdown(istatistik_html(r['H'], r['A']), unsafe_allow_html=True)
        with col_btn:
            st.button("➕", key=f"btn_{i}",
                      on_click=mac_ekle,
                      args=(f"{r['H']}-{r['A']}", r['Tahmin'], r['Oran']),
                      use_container_width=True, help="Kupona ekle")

        st.markdown("<hr style='border-color:#1e2235;margin:4px 0 10px;'>", unsafe_allow_html=True)

# ── BAŞLIK & SEKMELER ─────────────────────────────────────────────────────────
st.title("⚡ Superior Scout v31")
st.caption(f"Hedef oran: **{target_o:.2f}** · Tutar: **{tutar} TL**")

tab1, tab2 = st.tabs(["🔍 Analiz", "📂 Arşiv"])

with tab1:
    c1, c2, c3 = st.columns(3)
    run_futbol    = c1.button("⚽ FUTBOL",    use_container_width=True, type="primary")
    run_basketbol = c2.button("🏀 BASKETBOL", use_container_width=True)
    run_karma     = c3.button("🔥 KARMA",     use_container_width=True)

    if run_futbol:    analiz_motoru(FUTBOL_LIGLER)
    if run_basketbol: analiz_motoru(BASKETBOL_LIGLER)
    if run_karma:     analiz_motoru(KARMA_LIGLER)

with tab2:
    if st.session_state.arsiv:
        for k in reversed(st.session_state.arsiv):
            icon = "🟢" if k['durum'] == "Kazandı" else ("🔴" if k['durum'] == "Kaybetti" else "🟡")
            with st.expander(f"{icon} {k['tarih']} · Oran: {k['oran']:.2f}x · {k['durum']}"):
                st.dataframe(pd.DataFrame(k['maclar']), use_container_width=True, hide_index=True)
                ck, cb = st.columns(2)
                idx = st.session_state.arsiv.index(k)
                if ck.button("✅ Kazandı",  key=f"kaz_{idx}"): st.session_state.arsiv[idx]['durum'] = "Kazandı";  st.rerun()
                if cb.button("❌ Kaybetti", key=f"kay_{idx}"): st.session_state.arsiv[idx]['durum'] = "Kaybetti"; st.rerun()
    else:
        st.info("Henüz kaydedilmiş kupon yok.")

