import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone

# ── API ANAHTARLARI ───────────────────────────────────────────────────────────
ODDS_API_KEY     = "cdf9790dbd2d52e5d593e5e4b9a76118"
FOOTBALL_API_KEY = "c09318cad2ff47f92f8468f48dc64f72"
FOOTBALL_HOST    = "https://v3.football.api-sports.io"
HEADERS_FB       = {"x-apisports-key": c09318cad2ff47f92f8468f48dc64f72}

st.set_page_config(page_title="Scout v33", layout="wide", page_icon="⚡", initial_sidebar_state="collapsed")

# ── SESSION STATE ─────────────────────────────────────────────────────────────
for key in ['kupon_havuzu', 'arsiv']:
    if key not in st.session_state:
        st.session_state[key] = []

def mac_ekle(mac_adi, tahmin, oran):
    st.session_state.kupon_havuzu.append({"Maç": mac_adi, "Tahmin": tahmin, "Oran": oran})
    st.toast(f"✅ {mac_adi} eklendi!")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;background-color:#0d0f1a;color:#e0e6ff}
h1{font-family:'Rajdhani',sans-serif!important;font-size:1.6rem!important;letter-spacing:2px;color:#fff}
h3{font-family:'Rajdhani',sans-serif!important;font-size:1.1rem!important;color:#c8d0f0}

/* KART */
.match-card{background:linear-gradient(135deg,#161928,#1a1e30);padding:13px 15px;border-radius:14px;border-left:5px solid #3d7eff;margin-bottom:6px;box-shadow:0 4px 20px rgba(0,0,0,.4)}
.match-header{font-family:'Rajdhani',sans-serif;font-size:1.05rem;font-weight:700;color:#fff;margin-bottom:3px}
.match-meta{font-size:.77rem;color:#7b88b0;margin-bottom:8px}

/* BADGE */
.badge{padding:3px 9px;border-radius:20px;font-size:.8rem;font-weight:600;margin-right:5px;display:inline-block;margin-top:3px}
.b-oran   {background:#1e3a1e;color:#4cff72}
.b-tahmin {background:#2a1e1e;color:#ff6b6b}
.b-market {background:#1e2a3a;color:#64b5ff}
.b-tarih  {background:#1a1a2e;color:#a0aacc}

/* STATİSTİK TABLOSU */
.stat-title{font-family:'Rajdhani',sans-serif;font-size:.85rem;font-weight:700;color:#3d7eff;letter-spacing:1px;text-transform:uppercase;margin:8px 0 5px;padding-bottom:3px;border-bottom:1px solid #252a40}
.stat-table{width:100%;border-collapse:collapse;font-size:.79rem}
.stat-table th{color:#7b88b0;font-weight:500;padding:5px 4px;text-align:center;font-size:.72rem;background:#12141f}
.stat-table th:first-child{text-align:left}
.stat-table td{padding:6px 4px;text-align:center;border-bottom:1px solid #1e2235}
.stat-table td:first-child{text-align:left;font-weight:600;color:#c8d0f0;font-size:.77rem}
.stat-table tr:last-child td{border-bottom:none}
.sv-iyi{color:#4cff72;font-weight:700}.sv-orta{color:#ffd166;font-weight:700}.sv-kotu{color:#ff6b6b;font-weight:700}.sv-na{color:#555d75;font-style:italic}

/* FORM */
.form-row{display:flex;gap:4px;margin-top:2px;justify-content:center}
.f-box{width:22px;height:22px;border-radius:5px;color:#fff;font-size:11px;font-weight:700;display:inline-flex;align-items:center;justify-content:center}
.G{background:#28a745}.B{background:#555d75}.M{background:#dc3545}

/* KUPON */
.kupon-item{background:#12141f;padding:8px 12px;border-radius:8px;margin-bottom:6px;border-left:3px solid #3d7eff;font-size:.82rem}

/* LİG SEÇİCİ */
.lig-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:6px;margin-bottom:12px}

.stButton>button{border-radius:10px!important;font-weight:600!important;font-family:'Inter',sans-serif!important;border:none!important;transition:all .2s!important}
.stTabs [data-baseweb="tab"]{font-family:'Rajdhani',sans-serif;font-size:1rem;font-weight:600;letter-spacing:1px}
.block-container{max-width:100%!important;padding:1rem .8rem!important}
div[data-testid="stToast"]{background:#1e3a1e!important;color:#4cff72!important}
</style>
""", unsafe_allow_html=True)

# ── TÜM LİGLER (The Odds API sport keys) ─────────────────────────────────────
TUM_LIGLER = {
    # ─ Avrupa ─
    "🇹🇷 Türkiye Süper Lig":          "soccer_turkey_super_league",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 İngiltere Premier League":  "soccer_epl",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 İngiltere Championship":    "soccer_england_championship",
    "🇪🇸 İspanya La Liga":             "soccer_spain_la_liga",
    "🇪🇸 İspanya La Liga 2":           "soccer_spain_segunda_division",
    "🇩🇪 Almanya Bundesliga":          "soccer_germany_bundesliga",
    "🇩🇪 Almanya 2. Bundesliga":       "soccer_germany_bundesliga2",
    "🇮🇹 İtalya Serie A":              "soccer_italy_serie_a",
    "🇮🇹 İtalya Serie B":              "soccer_italy_serie_b",
    "🇫🇷 Fransa Ligue 1":              "soccer_france_ligue_one",
    "🇫🇷 Fransa Ligue 2":              "soccer_france_ligue_two",
    "🇳🇱 Hollanda Eredivisie":         "soccer_netherlands_eredivisie",
    "🇵🇹 Portekiz Primeira Liga":      "soccer_portugal_primeira_liga",
    "🇧🇪 Belçika Pro League":          "soccer_belgium_first_div",
    "🇬🇷 Yunanistan Super League":     "soccer_greece_super_league",
    "🇷🇺 Rusya Premier League":        "soccer_russia_premier_league",
    "🇵🇱 Polonya Ekstraklasa":         "soccer_poland_ekstraklasa",
    "🇦🇹 Avusturya Bundesliga":        "soccer_austria_bundesliga",
    "🇨🇭 İsviçre Super League":        "soccer_switzerland_superleague",
    "🇸🇪 İsveç Allsvenskan":           "soccer_sweden_allsvenskan",
    "🇳🇴 Norveç Eliteserien":          "soccer_norway_eliteserien",
    "🇩🇰 Danimarka Superliga":         "soccer_denmark_superliga",
    "🇨🇿 Çekya Fortuna Liga":          "soccer_czech_republic_fortuna_liga",
    "🇭🇷 Hırvatistan HNL":             "soccer_croatia_hnl",
    "🇸🇰 Slovakya Fortuna Liga":       "soccer_slovakia_super_liga",
    "🇷🇴 Romanya Liga 1":              "soccer_romania_1_liga",
    "🇺🇦 Ukrayna Premier Liga":        "soccer_ukraine_premier_league",
    "🇷🇸 Sırbistan Super Liga":        "soccer_serbia_superliga",
    # ─ Avrupa Kupaları ─
    "🏆 UEFA Şampiyonlar Ligi":        "soccer_champions_league",
    "🏆 UEFA Avrupa Ligi":             "soccer_europa_league",
    "🏆 UEFA Konferans Ligi":          "soccer_europa_conference_league",
    # ─ Amerika ─
    "🇺🇸 ABD MLS":                     "soccer_usa_mls",
    "🇧🇷 Brezilya Série A":            "soccer_brazil_campeonato",
    "🇦🇷 Arjantin Primera":            "soccer_argentina_primera_division",
    "🇲🇽 Meksika Liga MX":             "soccer_mexico_ligamx",
    "🇨🇱 Şili Primera":                "soccer_chile_primera_division",
    "🇨🇴 Kolombiya Primera A":         "soccer_colombia_primera_a",
    # ─ Asya / Diğer ─
    "🇯🇵 Japonya J1 League":           "soccer_japan_j_league",
    "🇰🇷 Güney Kore K League 1":       "soccer_korea_kleague1",
    "🇨🇳 Çin Super League":            "soccer_china_superleague",
    "🇦🇺 Avustralya A-League":         "soccer_australia_aleague",
    "🌍 Afrika Uluslar Kupası":        "soccer_africa_cup_of_nations",
}

# The Odds API → api-football league_id + season
LIG_MAP = {
    "soccer_turkey_super_league":           (203, 2024),
    "soccer_epl":                           (39,  2024),
    "soccer_england_championship":          (40,  2024),
    "soccer_spain_la_liga":                 (140, 2024),
    "soccer_spain_segunda_division":        (141, 2024),
    "soccer_germany_bundesliga":            (78,  2024),
    "soccer_germany_bundesliga2":           (79,  2024),
    "soccer_italy_serie_a":                 (135, 2024),
    "soccer_italy_serie_b":                 (136, 2024),
    "soccer_france_ligue_one":              (61,  2024),
    "soccer_france_ligue_two":              (62,  2024),
    "soccer_netherlands_eredivisie":        (88,  2024),
    "soccer_portugal_primeira_liga":        (94,  2024),
    "soccer_belgium_first_div":             (144, 2024),
    "soccer_greece_super_league":           (197, 2024),
    "soccer_russia_premier_league":         (235, 2024),
    "soccer_poland_ekstraklasa":            (106, 2024),
    "soccer_austria_bundesliga":            (218, 2024),
    "soccer_switzerland_superleague":       (207, 2024),
    "soccer_sweden_allsvenskan":            (113, 2025),
    "soccer_norway_eliteserien":            (103, 2025),
    "soccer_denmark_superliga":             (119, 2024),
    "soccer_czech_republic_fortuna_liga":   (345, 2024),
    "soccer_croatia_hnl":                   (210, 2024),
    "soccer_slovakia_super_liga":           (332, 2024),
    "soccer_romania_1_liga":                (283, 2024),
    "soccer_ukraine_premier_league":        (333, 2024),
    "soccer_serbia_superliga":              (286, 2024),
    "soccer_champions_league":              (2,   2024),
    "soccer_europa_league":                 (3,   2024),
    "soccer_europa_conference_league":      (848, 2024),
    "soccer_usa_mls":                       (253, 2025),
    "soccer_brazil_campeonato":             (71,  2025),
    "soccer_argentina_primera_division":    (128, 2024),
    "soccer_mexico_ligamx":                 (262, 2025),
    "soccer_chile_primera_division":        (265, 2024),
    "soccer_colombia_primera_a":            (239, 2024),
    "soccer_japan_j_league":                (98,  2025),
    "soccer_korea_kleague1":                (292, 2025),
    "soccer_china_superleague":             (169, 2025),
    "soccer_australia_aleague":             (188, 2024),
}

# ── API-FOOTBALL FONKSİYONLARI ────────────────────────────────────────────────

def _fb_get(endpoint, params, timeout=10):
    """Tek nokta API çağrısı — hata durumunda (status, json) döner"""
    try:
        r = requests.get(f"{FOOTBALL_HOST}/{endpoint}", headers=HEADERS_FB,
                         params=params, timeout=timeout)
        return r.status_code, r.json()
    except Exception as e:
        return 0, {"errors": str(e)}

@st.cache_data(ttl=3600, show_spinner=False)
def get_standings(league_id, season):
    """
    Lig tablosunu çek. Önce verilen sezonu dene, başarısız olursa
    bir önceki sezonu (season-1) dene — bazı ligler henüz yeni sezonu
    API'ye yüklememiş olabilir.
    """
    out = {}
    for s in [season, season - 1]:
        code, data = _fb_get("standings", {"league": league_id, "season": s})
        if code != 200 or not data.get("response"):
            continue
        try:
            # Bazı ligler grup bazlı gelir → standings bir liste listesi
            # Tüm grupları düzleştir
            all_groups = data["response"][0]["league"]["standings"]
            teams_flat = []
            for group in all_groups:
                if isinstance(group, list):
                    teams_flat.extend(group)
                else:
                    teams_flat.append(group)

            for s_row in teams_flat:
                tid    = s_row["team"]["id"]
                played = s_row["all"]["played"] or 1
                out[tid] = {
                    "siralama":   s_row["rank"],
                    "puan":       s_row["points"],
                    "takim_adi":  s_row["team"]["name"],
                    "galibiyet":  s_row["all"]["win"],
                    "beraberlik": s_row["all"]["draw"],
                    "maglubiyet": s_row["all"]["lose"],
                    "gol_a": round(s_row["all"]["goals"]["for"]     / played, 2),
                    "gol_y": round(s_row["all"]["goals"]["against"] / played, 2),
                    "sezon": s,
                }
            if out:
                return out   # başarılı → döndür
        except Exception:
            continue
    return out

@st.cache_data(ttl=3600, show_spinner=False)
def get_team_id(takim_adi, league_id, season):
    """
    Takım adından API-Football team_id bul.
    1) Standings'te kısmi eşleşme ara
    2) /teams search endpoint'ini dene
    3) Takım adından kelimeleri bölerek tekrar dene
    """
    st_data = get_standings(league_id, season)

    # Normalize et
    def norm(s): return s.lower().replace("fc ", "").replace(" fc","").replace("1. ", "").strip()
    adi_n = norm(takim_adi)

    for tid, info in st_data.items():
        b = norm(info["takim_adi"])
        if adi_n in b or b in adi_n:
            return tid

    # /teams search
    for search_name in [takim_adi, takim_adi.split()[0]]:
        code, data = _fb_get("teams", {"name": search_name, "league": league_id, "season": season})
        if code == 200:
            resp = data.get("response", [])
            if resp:
                return resp[0]["team"]["id"]
    return None

@st.cache_data(ttl=3600, show_spinner=False)
def get_team_stats(team_id, league_id, season):
    bos = {"sari": None, "kirmizi": None}
    for s in [season, season - 1]:
        code, data = _fb_get("teams/statistics",
                             {"team": team_id, "league": league_id, "season": s})
        if code != 200 or not data.get("response"):
            continue
        try:
            d    = data["response"]
            oyun = d["fixtures"]["played"]["total"] or 1
            sari = sum(
                (d["cards"]["yellow"].get(str(i), {}) or {}).get("total", 0) or 0
                for i in range(0, 120, 15)
            )
            kir = sum(
                (d["cards"]["red"].get(str(i), {}) or {}).get("total", 0) or 0
                for i in range(0, 120, 15)
            )
            return {"sari": round(sari / oyun, 2), "kirmizi": round(kir / oyun, 2)}
        except Exception:
            continue
    return bos

@st.cache_data(ttl=3600, show_spinner=False)
def get_last5_form(team_id, league_id, season):
    """
    Son 5 maç formunu çek.
    Önce lig filtreli dene, boş gelirse tüm liglerde dene.
    """
    form = []
    param_sets = [
        {"team": team_id, "league": league_id, "season": season, "last": 5, "status": "FT"},
        {"team": team_id, "last": 5, "status": "FT"},   # lig filtresi olmadan
    ]
    for params in param_sets:
        code, data = _fb_get("fixtures", params)
        if code != 200: continue
        try:
            fixtures = data.get("response", [])
            if not fixtures: continue
            form = []
            for fix in fixtures:
                ev_mi = fix["teams"]["home"]["id"] == team_id
                ga = fix["goals"]["home"] if ev_mi else fix["goals"]["away"]
                gy = fix["goals"]["away"] if ev_mi else fix["goals"]["home"]
                if ga is None or gy is None: continue
                form.append("G" if ga > gy else ("B" if ga == gy else "M"))
            if form: return form
        except Exception:
            continue
    return form

# ── YARDIMCI ─────────────────────────────────────────────────────────────────
def sv(v, iyi, orta, ters=False):
    if v is None: return "sv-na"
    return ("sv-iyi" if v<=iyi else ("sv-orta" if v<=orta else "sv-kotu")) if ters else \
           ("sv-iyi" if v>=iyi else ("sv-orta" if v>=orta else "sv-kotu"))

def fmt(v, suf=""): return f"{v}{suf}" if v is not None else "—"

def form_html(fl):
    if not fl: return "<span style='color:#555d75;font-size:.75rem'>Veri yok</span>"
    return "<div class='form-row'>"+"".join(f"<span class='f-box {f}'>{f}</span>" for f in fl)+"</div>"

def istatistik_html(ev, dep, league_id, season):
    st_data  = get_standings(league_id, season)
    ev_id    = get_team_id(ev,  league_id, season)
    dep_id   = get_team_id(dep, league_id, season)
    ev_s     = st_data.get(ev_id,  {}) if ev_id else {}
    dep_s    = st_data.get(dep_id, {}) if dep_id else {}
    ev_stat  = get_team_stats(ev_id,  league_id, season) if ev_id else {}
    dep_stat = get_team_stats(dep_id, league_id, season) if dep_id else {}
    ev_form  = get_last5_form(ev_id,  league_id, season) if ev_id else []
    dep_form = get_last5_form(dep_id, league_id, season) if dep_id else []

    ev_ga  = ev_s.get("gol_a");  dep_ga  = dep_s.get("gol_a")
    ev_gy  = ev_s.get("gol_y");  dep_gy  = dep_s.get("gol_y")
    ev_sr  = ev_s.get("siralama"); dep_sr = dep_s.get("siralama")

    # Standings verisi gelmediyse hangi sezon denendi göster
    sezon_notu = ""
    if not ev_s and not dep_s:
        sezon_notu = f"<div style='font-size:.72rem;color:#ff9f43;margin-top:6px;'>⚠️ Lig tablosu verisi alınamadı (league_id={league_id}, season={season}). API kotanızı veya lig ID'sini kontrol edin.</div>"

    return f"""
<div class='stat-section'>
  <div class='stat-title'>📊 Takım Karşılaştırması</div>
  <table class='stat-table'>
    <thead><tr><th>İSTATİSTİK</th><th>🏠 {ev[:15]}</th><th>✈️ {dep[:15]}</th></tr></thead>
    <tbody>
      <tr><td>Lig Sırası</td>
        <td class='{sv(ev_sr, 6,14,ters=True)}'>{f"{ev_sr}. ({ev_s.get('puan')} pt)" if ev_sr else "—"}</td>
        <td class='{sv(dep_sr,6,14,ters=True)}'>{f"{dep_sr}. ({dep_s.get('puan')} pt)" if dep_sr else "—"}</td></tr>
      <tr><td>G / B / M</td>
        <td>{f"{ev_s.get('galibiyet','—')}/{ev_s.get('beraberlik','—')}/{ev_s.get('maglubiyet','—')}" if ev_s else "—"}</td>
        <td>{f"{dep_s.get('galibiyet','—')}/{dep_s.get('beraberlik','—')}/{dep_s.get('maglubiyet','—')}" if dep_s else "—"}</td></tr>
      <tr><td>Gol Ort. (A)</td>
        <td class='{sv(ev_ga, 1.8,1.2)}'>{fmt(ev_ga)}</td>
        <td class='{sv(dep_ga,1.8,1.2)}'>{fmt(dep_ga)}</td></tr>
      <tr><td>Gol Ort. (Y)</td>
        <td class='{sv(ev_gy, 0.9,1.4,ters=True)}'>{fmt(ev_gy)}</td>
        <td class='{sv(dep_gy,0.9,1.4,ters=True)}'>{fmt(dep_gy)}</td></tr>
      <tr><td>Sarı Kart/Maç</td>
        <td class='{sv(ev_stat.get("sari"), 2.2,1.5,ters=True)}'>{fmt(ev_stat.get("sari"))}</td>
        <td class='{sv(dep_stat.get("sari"),2.2,1.5,ters=True)}'>{fmt(dep_stat.get("sari"))}</td></tr>
      <tr><td>Kırmızı Kart/Maç</td>
        <td class='{sv(ev_stat.get("kirmizi"), 0.08,0.15,ters=True)}'>{fmt(ev_stat.get("kirmizi"))}</td>
        <td class='{sv(dep_stat.get("kirmizi"),0.08,0.15,ters=True)}'>{fmt(dep_stat.get("kirmizi"))}</td></tr>
      <tr><td>Son 5 Maç</td>
        <td>{form_html(ev_form)}</td>
        <td>{form_html(dep_form)}</td></tr>
    </tbody>
  </table>
  {sezon_notu}
  <div style='font-size:.7rem;color:#555d75;margin-top:4px'>✅ Kaynak: api-football v3 · 🔄 Cache: 1 saat</div>
</div>"""

# ── MARKET ETİKETİ ────────────────────────────────────────────────────────────
def market_etiket(mkt_key, out_name, point=None):
    if mkt_key == "h2h":
        return ("1" if out_name.endswith("(Home)") or out_name == out_name else out_name), "Maç Sonu"
    if mkt_key == "totals":
        yon = "Üst" if out_name == "Over" else "Alt"
        return f"{yon} {point} Gol", "Alt/Üst"
    if mkt_key == "spreads":
        return f"Handikap {point}", "Handikap"
    if "corners" in mkt_key:
        yon = "Üst" if out_name == "Over" else ("Alt" if out_name == "Under" else out_name)
        return f"Korner {yon} {point or ''}".strip(), "Korner"
    if "cards" in mkt_key:
        yon = "Üst" if out_name == "Over" else ("Alt" if out_name == "Under" else out_name)
        return f"Kart {yon} {point or ''}".strip(), "Kart"
    return out_name, mkt_key.replace("_", " ").title()

MARKET_RENK = {
    "Maç Sonu": "#3d7eff",
    "Alt/Üst":  "#ff9f43",
    "Korner":   "#a29bfe",
    "Kart":     "#fd79a8",
    "Handikap": "#00cec9",
}

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
            st.markdown(f"""<div class='kupon-item'>🔹 <b>{m['Maç']}</b><br>
            <span style='color:#7b88b0;font-size:.78rem'>{m['Tahmin']} · <b style='color:#4cff72'>{m['Oran']}</b></span>
            </div>""", unsafe_allow_html=True)
            t_oran *= m['Oran']
        st.success(f"📊 **{t_oran:.2f}x** · **{t_oran*tutar:.0f} TL**")
        cs, ct = st.columns(2)
        with cs:
            if st.button("💾 Kaydet", use_container_width=True, type="primary"):
                st.session_state.arsiv.append({
                    "tarih": datetime.now().strftime("%d/%m %H:%M"),
                    "maclar": list(st.session_state.kupon_havuzu),
                    "oran": t_oran, "durum": "Bekliyor"
                })
                st.session_state.kupon_havuzu = []; st.rerun()
        with ct:
            if st.button("🗑️ Temizle", use_container_width=True):
                st.session_state.kupon_havuzu = []; st.rerun()
    else:
        st.info("Henüz maç eklenmedi.")

# ── BAŞLIK ────────────────────────────────────────────────────────────────────
st.title("⚡ Superior Scout v33")
st.caption(f"Hedef oran: **{target_o:.2f}** · Tutar: **{tutar} TL**")

if ODDS_API_KEY == "SENİN_ODDS_API_ANAHTARIN":
    st.error("⚠️ Odds API anahtarı girilmemiş! Dosyanın 7. satırındaki ODDS_API_KEY değişkenine the-odds-api.com anahtarını gir.")

# ── ANALİZ MOTORU ─────────────────────────────────────────────────────────────
def analiz_motoru(secili_lig_keys: list, gun_aralik: int, secili_marketler: list):
    if not secili_lig_keys:
        st.warning("Lütfen en az bir lig seçin.")
        return

    # Oran aralığı — ±20% (daha geniş, daha fazla maç bulunur)
    alt_l = target_o * 0.80
    ust_l = target_o * 1.20

    # Zaman sınırı (UTC)
    simdi = datetime.now(timezone.utc)
    bitis = simdi + timedelta(days=gun_aralik)

    # The Odds API'de her zaman h2h + totals çek, korner için ayrı istek
    temel_markets   = []
    korner_istendi  = "Korner"   in secili_marketler
    kart_istendi    = "Kart"     in secili_marketler
    mac_sonu_ist    = "Maç Sonu" in secili_marketler
    alt_ust_ist     = "Alt/Üst"  in secili_marketler

    if mac_sonu_ist: temel_markets.append("h2h")
    if alt_ust_ist:  temel_markets.append("totals")
    if not temel_markets: temel_markets = ["h2h", "totals"]   # hiç seçilmezse default

    firsatlar = []
    api_hata  = []
    toplam_mac = 0
    prog = st.progress(0, text="⏳ Piyasalar taranıyor...")

    for i, lig_key in enumerate(secili_lig_keys):
        prog.progress((i+1)/len(secili_lig_keys),
                      text=f"⏳ {lig_key.replace('soccer_','').replace('_',' ').title()} ({i+1}/{len(secili_lig_keys)})")

        # ── 1. Temel market isteği (h2h + totals) ────────────────────────────
        def fetch_market(lig, mkts):
            url = (f"https://api.the-odds-api.com/v4/sports/{lig}/odds/"
                   f"?apiKey={ODDS_API_KEY}&regions=eu"
                   f"&markets={','.join(mkts)}&oddsFormat=decimal")
            try:
                r = requests.get(url, timeout=12)
                if r.status_code == 200:
                    return r.json()
                elif r.status_code == 422:
                    return []   # bu lig bu marketi desteklemiyor
                else:
                    api_hata.append(f"{lig}: HTTP {r.status_code}")
                    return []
            except Exception as e:
                api_hata.append(f"{lig}: {str(e)[:40]}")
                return []

        maclar = fetch_market(lig_key, temel_markets)

        # ── 2. Korner marketi — ayrı istek ───────────────────────────────────
        korner_maclar = []
        if korner_istendi:
            # The Odds API'de korner: "alternate_totals" veya "team_totals"
            for korner_market in ["alternate_totals", "team_totals"]:
                km = fetch_market(lig_key, [korner_market])
                if km:
                    korner_maclar = km
                    break

        for mac_grup, kaynak in [(maclar, "normal"), (korner_maclar, "korner")]:
            for m in mac_grup:
                try:
                    dt_utc = datetime.strptime(
                        m['commence_time'], "%Y-%m-%dT%H:%M:%SZ"
                    ).replace(tzinfo=timezone.utc)
                except Exception:
                    continue

                # Zaman filtresi: sadece gelecekteki ve bitis'ten önce
                if dt_utc < simdi or dt_utc > bitis:
                    continue

                toplam_mac += 1
                dt_tr = dt_utc + timedelta(hours=3)

                for bm in m.get('bookmakers', [])[:3]:
                    for mkt in bm.get('markets', []):
                        mkt_key = mkt['key']

                        for out in mkt.get('outcomes', []):
                            price = out.get('price', 0)
                            if not (alt_l <= price <= ust_l):
                                continue

                            point = out.get('point')
                            tahmin_str, market_label = market_etiket(mkt_key, out['name'], point)

                            # Market filtresi
                            if market_label == "Korner" and not korner_istendi:
                                continue
                            if market_label == "Kart" and not kart_istendi:
                                continue
                            if market_label == "Maç Sonu" and not mac_sonu_ist:
                                continue
                            if market_label == "Alt/Üst" and not alt_ust_ist:
                                continue

                            firsatlar.append({
                                "Tarih":   dt_tr.strftime("%d %b"),
                                "Saat":    dt_tr.strftime("%H:%M"),
                                "dt_sort": dt_utc,
                                "H":       m['home_team'],
                                "A":       m['away_team'],
                                "Lig":     m['sport_title'],
                                "OddsLig": lig_key,
                                "Market":  market_label,
                                "Tahmin":  tahmin_str,
                                "Oran":    price,
                            })

    prog.empty()

    # Debug bilgisi
    if api_hata:
        with st.expander(f"⚠️ {len(api_hata)} API uyarısı"):
            for h in api_hata[:10]: st.caption(h)

    if not firsatlar:
        st.error(f"""❌ Hiç fırsat bulunamadı.
        
**Olası sebepler:**
- Odds API anahtarın `SENİN_ODDS_API_ANAHTARIN` olarak kalmış — gerçek anahtarı gir
- Seçilen {len(secili_lig_keys)} ligde şu an aktif maç yok
- Oran kriteri ({alt_l:.2f}–{ust_l:.2f}) bu liglere uymuyor
- Tarama yapılan {gun_aralik} günde maç programlanmamış

**Deneyebileceklerin:** Oran aralığını genişlet, daha fazla lig seç, 3 gün seç.""")
        st.info(f"📊 Toplam taranan maç sayısı: **{toplam_mac}** (zaman filtresine uyanlar)")
        return

    df = (pd.DataFrame(firsatlar)
            .sort_values("dt_sort")
            .drop_duplicates(subset=["H","A","Market","Tahmin"])   # aynı bahisi tekrar alma
            .reset_index(drop=True))

    # Maç başına grupla — her maç tek kart
    mac_gruplari = {}
    for _, r in df.iterrows():
        key = (r["H"], r["A"])
        if key not in mac_gruplari:
            mac_gruplari[key] = {
                "Tarih":   r["Tarih"],
                "Saat":    r["Saat"],
                "dt_sort": r["dt_sort"],
                "Lig":     r["Lig"],
                "OddsLig": r["OddsLig"],
                "bahisler": []
            }
        mac_gruplari[key]["bahisler"].append({
            "Market": r["Market"],
            "Tahmin": r["Tahmin"],
            "Oran":   r["Oran"],
        })

    # Zamana göre sırala, max 20 maç
    sirali = sorted(mac_gruplari.items(), key=lambda x: x[1]["dt_sort"])[:20]

    gun_label = "Bugün" if gun_aralik == 1 else f"Sonraki {gun_aralik} gün"
    st.success(f"✅ **{len(sirali)} maç** · {gun_label} · Oran: {alt_l:.2f}–{ust_l:.2f} · {len(secili_lig_keys)} lig tarandı")

    for mac_idx, ((ev, dep), mac) in enumerate(sirali):
        bahisler = mac["bahisler"]

        # Bahis badge'leri HTML
        badge_html = ""
        for b in bahisler:
            renk = MARKET_RENK.get(b["Market"], "#3d7eff")
            badge_html += f"""
            <span class='badge b-market' style='border:1px solid {renk}40;color:{renk}'>{b['Market']}</span>
            <span class='badge b-tahmin'>🎯 {b['Tahmin']}</span>
            <span class='badge b-oran'>📈 {b['Oran']}</span>
            &nbsp;
            """

        st.markdown(f"""
        <div class='match-card'>
          <div class='match-header'>{ev} <span style='color:#555d75'>vs</span> {dep}</div>
          <div class='match-meta'>📅 {mac['Tarih']} &nbsp;🕐 {mac['Saat']} &nbsp;·&nbsp; 🏆 {mac['Lig']}</div>
          <div style='margin-top:6px;line-height:2.2'>{badge_html}</div>
        </div>
        """, unsafe_allow_html=True)

        # İstatistik expander + bahis butonları yan yana
        col_exp, col_btns = st.columns([4, 2])

        with col_exp:
            with st.expander("📊 Takım İstatistikleri"):
                fb_lig_id, fb_sezon = LIG_MAP.get(mac["OddsLig"], (None, 2024))
                if fb_lig_id:
                    with st.spinner("Veri yükleniyor..."):
                        st.markdown(istatistik_html(ev, dep, fb_lig_id, fb_sezon), unsafe_allow_html=True)
                else:
                    st.caption("Bu lig için istatistik verisi mevcut değil.")

        with col_btns:
            st.markdown("<div style='padding-top:4px'>", unsafe_allow_html=True)
            for b_idx, b in enumerate(bahisler):
                btn_label = f"➕ {b['Market']} · {b['Oran']}"
                st.button(
                    btn_label,
                    key=f"btn_{mac_idx}_{b_idx}",
                    on_click=mac_ekle,
                    args=(f"{ev}-{dep}", f"{b['Market']}: {b['Tahmin']}", b['Oran']),
                    use_container_width=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<hr style='border-color:#1e2235;margin:3px 0 10px'>", unsafe_allow_html=True)

# ── SEKMELER ──────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["🔍 Analiz", "📂 Arşiv"])

with tab1:

    # ── ZAMAN FİLTRESİ ────────────────────────────────────────────────────────
    st.markdown("### ⏱️ Zaman Aralığı")
    gun_secim = st.radio(
        "", ["Bugün", "Yarın", "2 Gün", "3 Gün"],
        horizontal=True, index=2,   # varsayılan: 2 gün
        key="gun_radio"
    )
    gun_map = {"Bugün": 1, "Yarın": 2, "2 Gün": 2, "3 Gün": 3}
    gun_aralik = gun_map[gun_secim]

    # ── MARKET SEÇİMİ ─────────────────────────────────────────────────────────
    st.markdown("### 🎯 Bahis Türü")
    market_cols = st.columns(4)
    sec_mac_sonu = market_cols[0].checkbox("⚽ Maç Sonu",  value=True)
    sec_alt_ust  = market_cols[1].checkbox("📊 Alt/Üst",   value=True)
    sec_korner   = market_cols[2].checkbox("🚩 Korner",    value=True)
    sec_kart     = market_cols[3].checkbox("🟨 Kart",      value=False)

    secili_marketler = []
    if sec_mac_sonu: secili_marketler.append("Maç Sonu")
    if sec_alt_ust:  secili_marketler.append("Alt/Üst")
    if sec_korner:   secili_marketler.append("Korner")
    if sec_kart:     secili_marketler.append("Kart")
    if not secili_marketler: secili_marketler = ["Maç Sonu"]

    # ── LİG SEÇİCİ ───────────────────────────────────────────────────────────
    st.markdown("### 🏆 Lig Seçimi")

    col_hepsi, col_temizle, _ = st.columns([1, 1, 4])
    if col_hepsi.button("✅ Tümünü Seç",   use_container_width=True):
        for k in TUM_LIGLER: st.session_state[f"lig_{k}"] = True
        st.rerun()
    if col_temizle.button("❌ Temizle", use_container_width=True):
        for k in TUM_LIGLER: st.session_state[f"lig_{k}"] = False
        st.rerun()

    # Liglerini gruplara böl
    GRUPLAR = {
        "🌍 Büyük Avrupa Ligleri": [
            "🇹🇷 Türkiye Süper Lig","🏴󠁧󠁢󠁥󠁮󠁧󠁿 İngiltere Premier League",
            "🇪🇸 İspanya La Liga","🇩🇪 Almanya Bundesliga",
            "🇮🇹 İtalya Serie A","🇫🇷 Fransa Ligue 1",
        ],
        "🥈 2. Ligler": [
            "🏴󠁧󠁢󠁥󠁮󠁧󠁿 İngiltere Championship","🇪🇸 İspanya La Liga 2",
            "🇩🇪 Almanya 2. Bundesliga","🇮🇹 İtalya Serie B","🇫🇷 Fransa Ligue 2",
        ],
        "🏆 Avrupa Kupaları": [
            "🏆 UEFA Şampiyonlar Ligi","🏆 UEFA Avrupa Ligi","🏆 UEFA Konferans Ligi",
        ],
        "🌐 Diğer Avrupa": [
            "🇳🇱 Hollanda Eredivisie","🇵🇹 Portekiz Primeira Liga","🇧🇪 Belçika Pro League",
            "🇬🇷 Yunanistan Super League","🇷🇺 Rusya Premier League","🇵🇱 Polonya Ekstraklasa",
            "🇦🇹 Avusturya Bundesliga","🇨🇭 İsviçre Super League","🇸🇪 İsveç Allsvenskan",
            "🇳🇴 Norveç Eliteserien","🇩🇰 Danimarka Superliga","🇨🇿 Çekya Fortuna Liga",
            "🇭🇷 Hırvatistan HNL","🇸🇰 Slovakya Fortuna Liga","🇷🇴 Romanya Liga 1",
            "🇺🇦 Ukrayna Premier Liga","🇷🇸 Sırbistan Super Liga",
        ],
        "🌎 Amerika": [
            "🇺🇸 ABD MLS","🇧🇷 Brezilya Série A","🇦🇷 Arjantin Primera",
            "🇲🇽 Meksika Liga MX","🇨🇱 Şili Primera","🇨🇴 Kolombiya Primera A",
        ],
        "🌏 Asya / Diğer": [
            "🇯🇵 Japonya J1 League","🇰🇷 Güney Kore K League 1","🇨🇳 Çin Super League",
            "🇦🇺 Avustralya A-League","🌍 Afrika Uluslar Kupası",
        ],
    }

    secili_lig_keys = []
    for grup_adi, lig_adlari in GRUPLAR.items():
        with st.expander(grup_adi, expanded=(grup_adi == "🌍 Büyük Avrupa Ligleri")):
            cols = st.columns(2)
            for j, lig_adi in enumerate(lig_adlari):
                lig_key = TUM_LIGLER[lig_adi]
                state_key = f"lig_{lig_adi}"
                varsayilan = grup_adi == "🌍 Büyük Avrupa Ligleri"
                checked = st.session_state.get(state_key, varsayilan)
                if cols[j % 2].checkbox(lig_adi, value=checked, key=state_key):
                    secili_lig_keys.append(lig_key)

    st.markdown(f"**{len(secili_lig_keys)}** lig seçili")
    st.divider()

    # ── TARA BUTONU ───────────────────────────────────────────────────────────
    if st.button("🔍 FIRSAT TAR", use_container_width=True, type="primary"):
        analiz_motoru(secili_lig_keys, gun_aralik, secili_marketler)

with tab2:
    if st.session_state.arsiv:
        for k in reversed(st.session_state.arsiv):
            icon = "🟢" if k['durum']=="Kazandı" else ("🔴" if k['durum']=="Kaybetti" else "🟡")
            with st.expander(f"{icon} {k['tarih']} · {k['oran']:.2f}x · {k['durum']}"):
                st.dataframe(pd.DataFrame(k['maclar']), use_container_width=True, hide_index=True)
                ck, cb = st.columns(2)
                idx = st.session_state.arsiv.index(k)
                if ck.button("✅ Kazandı",  key=f"kaz_{idx}"): st.session_state.arsiv[idx]['durum']="Kazandı";  st.rerun()
                if cb.button("❌ Kaybetti", key=f"kay_{idx}"): st.session_state.arsiv[idx]['durum']="Kaybetti"; st.rerun()
    else:
        st.info("Henüz kaydedilmiş kupon yok.")
