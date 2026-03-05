import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# ── API ANAHTARLARI ───────────────────────────────────────────────────────────
ODDS_API_KEY    = "cdf9790dbd2d52e5d593e5e4b9a76118"          # the-odds-api.com
FOOTBALL_API_KEY = "c09318cad2ff47f92f8468f48dc64f72"  # api-football v3

FOOTBALL_HOST   = "https://v3.football.api-sports.io"
HEADERS_FB      = {
    "x-apisports-key": FOOTBALL_API_KEY
}

st.set_page_config(page_title="Scout v32", layout="wide", page_icon="⚡", initial_sidebar_state="collapsed")

# ── SESSION STATE ─────────────────────────────────────────────────────────────
if 'kupon_havuzu'  not in st.session_state: st.session_state.kupon_havuzu  = []
if 'arsiv'         not in st.session_state: st.session_state.arsiv         = []
if 'stat_cache'    not in st.session_state: st.session_state.stat_cache    = {}   # takım_id → istat
if 'takim_id_cache' not in st.session_state: st.session_state.takim_id_cache = {} # "İsim|lig_id" → takim_id

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

.stat-section { margin-top: 8px; }
.stat-title {
    font-family: 'Rajdhani', sans-serif; font-size: 0.85rem; font-weight: 700;
    color: #3d7eff; letter-spacing: 1px; text-transform: uppercase;
    margin: 8px 0 6px 0; padding-bottom: 4px; border-bottom: 1px solid #252a40;
}
.stat-table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
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
.sv-na   { color: #555d75; font-style: italic; }

.form-row { display: flex; gap: 4px; margin-top: 2px; justify-content: center; }
.f-box {
    width: 22px; height: 22px; border-radius: 5px; text-align: center;
    color: white; font-size: 11px; font-weight: 700;
    display: inline-flex; align-items: center; justify-content: center;
}
.G { background-color: #28a745; } .B { background-color: #555d75; } .M { background-color: #dc3545; }

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
.canlı-badge { background: #3a1e1e; color: #ff4b4b; padding: 2px 8px; border-radius: 10px; font-size: 0.72rem; font-weight: 700; animation: blink 1.2s infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.4} }
</style>
""", unsafe_allow_html=True)

# ── LİG HARİTASI: Odds API key → API-Football league_id & season ──────────────
# Odds API sport key : (api-football league_id, sezon)
LIG_MAP = {
    "soccer_turkey_super_league":          (203, 2024),
    "soccer_epl":                          (39,  2024),
    "soccer_spain_la_liga":                (140, 2024),
    "soccer_germany_bundesliga":           (78,  2024),
    "soccer_italy_serie_a":                (135, 2024),
    "soccer_france_ligue_one":             (61,  2024),
    "soccer_netherlands_eredivisie":       (88,  2024),
    "soccer_portugal_primeira_liga":       (94,  2024),
    "soccer_champions_league":             (2,   2024),
    "soccer_europa_league":                (3,   2024),
    "soccer_usa_mls":                      (253, 2025),
    "soccer_brazil_campeonato":            (71,  2025),
    "soccer_argentina_primera_division":   (128, 2024),
}

FUTBOL_LIGLER    = list(LIG_MAP.keys())
BASKETBOL_LIGLER = ["basketball_nba", "basketball_euroleague"]
KARMA_LIGLER     = list(LIG_MAP.keys())[:6] + BASKETBOL_LIGLER[:1]

SEZON = 2024   # Varsayılan futbol sezonu

# ── API-FOOTBALL YARDIMCI FONKSİYONLARI ──────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def get_standings(league_id: int, season: int) -> dict:
    """
    Lig sıralamasını çek.
    Döner: {takim_id: {"siralama": int, "puan": int, "takim_adi": str}}
    """
    url = f"{FOOTBALL_HOST}/standings"
    r   = requests.get(url, headers=HEADERS_FB,
                       params={"league": league_id, "season": season}, timeout=10)
    sonuc = {}
    if r.status_code != 200:
        return sonuc
    try:
        standings = r.json()["response"][0]["league"]["standings"][0]
        for s in standings:
            tid = s["team"]["id"]
            sonuc[tid] = {
                "siralama":  s["rank"],
                "puan":      s["points"],
                "takim_adi": s["team"]["name"],
                "oynanan":   s["all"]["played"],
                "galibiyet": s["all"]["win"],
                "beraberlik":s["all"]["draw"],
                "maglubiyet":s["all"]["lose"],
                "gol_a":     round(s["all"]["goals"]["for"]     / max(s["all"]["played"],1), 2),
                "gol_y":     round(s["all"]["goals"]["against"] / max(s["all"]["played"],1), 2),
            }
    except Exception:
        pass
    return sonuc

@st.cache_data(ttl=3600, show_spinner=False)
def get_team_id(takim_adi: str, league_id: int, season: int) -> int | None:
    """Takım adından API-Football takım ID'si bul"""
    # Önce standings'ten dene (en hızlı)
    standings = get_standings(league_id, season)
    for tid, info in standings.items():
        if takim_adi.lower() in info["takim_adi"].lower() or \
           info["takim_adi"].lower() in takim_adi.lower():
            return tid
    # Bulamazsa search endpoint'i kullan
    r = requests.get(f"{FOOTBALL_HOST}/teams",
                     headers=HEADERS_FB,
                     params={"name": takim_adi, "league": league_id, "season": season},
                     timeout=8)
    if r.status_code == 200:
        resp = r.json().get("response", [])
        if resp:
            return resp[0]["team"]["id"]
    return None

@st.cache_data(ttl=3600, show_spinner=False)
def get_team_stats(team_id: int, league_id: int, season: int) -> dict:
    """
    Takım istatistiklerini çek:
    gol_a, gol_y, korner_a (ort), sari_a (ort), kirmizi_a (ort)
    """
    url = f"{FOOTBALL_HOST}/teams/statistics"
    r   = requests.get(url, headers=HEADERS_FB,
                       params={"team": team_id, "league": league_id, "season": season},
                       timeout=10)
    bos = {"gol_a": None, "gol_y": None, "korner": None,
           "sari": None, "kirmizi": None}
    if r.status_code != 200:
        return bos
    try:
        d       = r.json()["response"]
        oyun    = d["fixtures"]["played"]["total"] or 1

        # Goller
        gol_a   = round((d["goals"]["for"]["total"]["total"]     or 0) / oyun, 2)
        gol_y   = round((d["goals"]["against"]["total"]["total"] or 0) / oyun, 2)

        # Kartlar
        sari_toplam    = sum((d["cards"]["yellow"].get(str(i), {}) or {}).get("total", 0) or 0 for i in range(0, 120, 15))
        kirmizi_toplam = sum((d["cards"]["red"].get(str(i), {})    or {}).get("total", 0) or 0 for i in range(0, 120, 15))

        return {
            "gol_a":    gol_a,
            "gol_y":    gol_y,
            "korner":   None,   # API-Football ücretsiz planda korner istatistiği yok → None
            "sari":     round(sari_toplam    / oyun, 2),
            "kirmizi":  round(kirmizi_toplam / oyun, 2),
        }
    except Exception:
        return bos

@st.cache_data(ttl=3600, show_spinner=False)
def get_last5_form(team_id: int, league_id: int, season: int) -> list:
    """Son 5 maç formunu çek → ['G','B','M', ...]"""
    url = f"{FOOTBALL_HOST}/fixtures"
    r   = requests.get(url, headers=HEADERS_FB,
                       params={
                           "team":   team_id,
                           "league": league_id,
                           "season": season,
                           "last":   5,
                           "status": "FT",   # sadece biten maçlar
                       }, timeout=10)
    if r.status_code != 200:
        return []
    form = []
    try:
        for fix in r.json()["response"]:
            teams  = fix["teams"]
            goals  = fix["goals"]
            ev_mi  = teams["home"]["id"] == team_id
            gol_a  = goals["home"] if ev_mi else goals["away"]
            gol_y  = goals["away"] if ev_mi else goals["home"]
            if gol_a is None or gol_y is None:
                continue
            if gol_a > gol_y:   form.append("G")
            elif gol_a == gol_y: form.append("B")
            else:                form.append("M")
    except Exception:
        pass
    return form  # en eski → en yeni sıralı

# ── İSTATİSTİK HTML ───────────────────────────────────────────────────────────
def sv(val, esik_iyi, esik_orta, ters=False) -> str:
    if val is None: return "sv-na"
    if ters:
        return "sv-iyi" if val <= esik_iyi else ("sv-orta" if val <= esik_orta else "sv-kotu")
    return "sv-iyi" if val >= esik_iyi else ("sv-orta" if val >= esik_orta else "sv-kotu")

def fmt(val, suffix=""):
    return f"{val}{suffix}" if val is not None else "—"

def form_html(fl: list) -> str:
    if not fl: return "<span style='color:#555d75;font-size:0.75rem;'>Veri yok</span>"
    return "<div class='form-row'>" + \
           "".join(f"<span class='f-box {f}'>{f}</span>" for f in fl) + \
           "</div>"

def istatistik_html(ev_takim: str, dep_takim: str, league_id: int, season: int) -> str:
    # Standings'ten lig verisi
    standings = get_standings(league_id, season)

    # Takım ID'leri bul
    ev_id  = get_team_id(ev_takim,  league_id, season)
    dep_id = get_team_id(dep_takim, league_id, season)

    # Standings'ten temel veriler
    ev_s  = standings.get(ev_id,  {}) if ev_id  else {}
    dep_s = standings.get(dep_id, {}) if dep_id else {}

    # Detaylı istatistikler
    ev_stat  = get_team_stats(ev_id,  league_id, season) if ev_id  else {}
    dep_stat = get_team_stats(dep_id, league_id, season) if dep_id else {}

    # Son 5 maç formu
    ev_form  = get_last5_form(ev_id,  league_id, season) if ev_id  else []
    dep_form = get_last5_form(dep_id, league_id, season) if dep_id else []

    # Değerler — standings'ten gelen gol ortalaması stats'tan yoksa fallback
    ev_gol_a  = ev_s.get("gol_a")  or ev_stat.get("gol_a")
    ev_gol_y  = ev_s.get("gol_y")  or ev_stat.get("gol_y")
    dep_gol_a = dep_s.get("gol_a") or dep_stat.get("gol_a")
    dep_gol_y = dep_s.get("gol_y") or dep_stat.get("gol_y")

    ev_sir  = ev_s.get("siralama")
    dep_sir = dep_s.get("siralama")
    ev_pt   = ev_s.get("puan")
    dep_pt  = dep_s.get("puan")

    # Lig büyüklüğüne göre sıra eşiği (genelde 20 takım → top6/mid14)
    sir_iyi, sir_orta = 6, 14

    return f"""
<div class='stat-section'>
    <div class='stat-title'>📊 Takım Karşılaştırması</div>
    <table class='stat-table'>
        <thead><tr>
            <th>İSTATİSTİK</th>
            <th>🏠 {ev_takim[:16]}</th>
            <th>✈️ {dep_takim[:16]}</th>
        </tr></thead>
        <tbody>
            <tr>
                <td>Lig Sırası</td>
                <td class='{sv(ev_sir,  sir_iyi, sir_orta, ters=True) if ev_sir  else "sv-na"}'>
                    {f"{ev_sir}. ({ev_pt} pt)"   if ev_sir  else "—"}
                </td>
                <td class='{sv(dep_sir, sir_iyi, sir_orta, ters=True) if dep_sir else "sv-na"}'>
                    {f"{dep_sir}. ({dep_pt} pt)" if dep_sir else "—"}
                </td>
            </tr>
            <tr>
                <td>G/B/M (Sezon)</td>
                <td>{f"{ev_s.get('galibiyet','—')}/{ev_s.get('beraberlik','—')}/{ev_s.get('maglubiyet','—')}" if ev_s else "—"}</td>
                <td>{f"{dep_s.get('galibiyet','—')}/{dep_s.get('beraberlik','—')}/{dep_s.get('maglubiyet','—')}" if dep_s else "—"}</td>
            </tr>
            <tr>
                <td>Gol Ort. (Atılan)</td>
                <td class='{sv(ev_gol_a,  1.8, 1.2)}'>{fmt(ev_gol_a)}</td>
                <td class='{sv(dep_gol_a, 1.8, 1.2)}'>{fmt(dep_gol_a)}</td>
            </tr>
            <tr>
                <td>Gol Ort. (Yenilen)</td>
                <td class='{sv(ev_gol_y,  0.9, 1.4, ters=True)}'>{fmt(ev_gol_y)}</td>
                <td class='{sv(dep_gol_y, 0.9, 1.4, ters=True)}'>{fmt(dep_gol_y)}</td>
            </tr>
            <tr>
                <td>Sarı Kart / Maç</td>
                <td class='{sv(ev_stat.get("sari"),  2.2, 1.5, ters=True)}'>{fmt(ev_stat.get("sari"))}</td>
                <td class='{sv(dep_stat.get("sari"), 2.2, 1.5, ters=True)}'>{fmt(dep_stat.get("sari"))}</td>
            </tr>
            <tr>
                <td>Kırmızı Kart / Maç</td>
                <td class='{sv(ev_stat.get("kirmizi"),  0.08, 0.15, ters=True)}'>{fmt(ev_stat.get("kirmizi"))}</td>
                <td class='{sv(dep_stat.get("kirmizi"), 0.08, 0.15, ters=True)}'>{fmt(dep_stat.get("kirmizi"))}</td>
            </tr>
            <tr>
                <td>Son 5 Maç</td>
                <td>{form_html(ev_form)}</td>
                <td>{form_html(dep_form)}</td>
            </tr>
        </tbody>
    </table>
    <div style='font-size:0.7rem;color:#555d75;margin-top:6px;'>
        ✅ Gerçek veri: api-football v3 &nbsp;·&nbsp; 🔄 Cache: 1 saat
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

    prog = st.progress(0, text="⏳ Piyasalar taranıyor...")
    for i, lig in enumerate(lig_listesi):
        prog.progress((i + 1) / len(lig_listesi), text=f"⏳ {lig} taranıyor...")
        url = (f"https://api.the-odds-api.com/v4/sports/{lig}/odds/"
               f"?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h,totals")
        try:
            res = requests.get(url, timeout=8)
            if res.status_code != 200: continue
            for m in res.json():
                dt_tr = datetime.strptime(m['commence_time'], "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=3)
                for bm in m['bookmakers'][:1]:
                    for mkt in bm['markets']:
                        for out in mkt['outcomes']:
                            if alt_l <= out['price'] <= ust_l:
                                firsatlar.append({
                                    "Tarih":   dt_tr.strftime("%d %b"),
                                    "Saat":    dt_tr.strftime("%H:%M"),
                                    "H":       m['home_team'],
                                    "A":       m['away_team'],
                                    "Lig":     m['sport_title'],
                                    "OddsLig": lig,
                                    "Tahmin":  out['name'] if mkt['key'] == "h2h"
                                               else f"{out['name']} {out.get('point','')} G",
                                    "Oran":    out['price'],
                                })
        except Exception:
            continue
    prog.empty()

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
        # Odds ligine karşılık gelen api-football lig ID/sezon
        fb_lig_id, fb_sezon = LIG_MAP.get(r['OddsLig'], (None, SEZON))

        st.markdown(f"""
        <div class='match-card'>
            <div class='match-header'>{r['H']} <span style='color:#555d75'>vs</span> {r['A']}</div>
            <div class='match-meta'>📅 {r['Tarih']} &nbsp;🕐 {r['Saat']} &nbsp;·&nbsp; 🏆 {r['Lig']}</div>
            <span class='badge-oran'>📈 {r['Oran']}</span>
            <span class='badge-tahmin'>🎯 {r['Tahmin']}</span>
        </div>
        """, unsafe_allow_html=True)

        col_exp, col_btn = st.columns([5, 1])
        with col_exp:
            with st.expander("📊 Takım İstatistikleri"):
                if fb_lig_id:
                    with st.spinner("Veriler yükleniyor..."):
                        html = istatistik_html(r['H'], r['A'], fb_lig_id, fb_sezon)
                    st.markdown(html, unsafe_allow_html=True)
                else:
                    st.caption("Bu spor için istatistik verisi mevcut değil.")
        with col_btn:
            st.button("➕", key=f"btn_{i}",
                      on_click=mac_ekle,
                      args=(f"{r['H']}-{r['A']}", r['Tahmin'], r['Oran']),
                      use_container_width=True, help="Kupona ekle")

        st.markdown("<hr style='border-color:#1e2235;margin:4px 0 10px;'>", unsafe_allow_html=True)

# ── BAŞLIK & SEKMELER ─────────────────────────────────────────────────────────
st.title("⚡ Superior Scout v32")
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
