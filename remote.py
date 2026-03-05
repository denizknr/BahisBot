import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# API ANAHTARINI BURAYA YAZ
API_KEY = "cdf9790dbd2d52e5d593e5e4b9a76118"

st.set_page_config(page_title="Superior Terminal v15", layout="wide", page_icon="📊")

# Hafıza Yönetimi
if 'kupon_havuzu' not in st.session_state: st.session_state.kupon_havuzu = []
if 'kayitli_kuponlar' not in st.session_state: st.session_state.kayitli_kuponlar = []

# CSS Tasarımı
st.markdown("""
    <style>
    .match-card { background-color: #1e2130; padding: 15px; border-radius: 12px; border-left: 8px solid #4e73df; margin-bottom: 15px; }
    .metric-card { background-color: #262a3b; padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #444; }
    .f-box { width: 22px; height: 22px; border-radius: 4px; text-align: center; color: white; font-size: 13px; font-weight: bold; line-height: 22px; display: inline-block; margin-right: 3px; }
    .G { background-color: #28a745; } .B { background-color: #6c757d; } .M { background-color: #dc3545; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Pro Scout v15: Portföy ve Analiz Terminali")

# ÜST PANEL: FİNANSAL ÖZET
if st.session_state.kayitli_kuponlar:
    df_perf = pd.DataFrame(st.session_state.kayitli_kuponlar)
    toplam_yatirilan = df_perf['yatirilan'].sum()
    kazananlar = df_perf[df_perf['durum'] == "KAZANDI"]
    toplam_kazanc = (kazananlar['yatirilan'] * kazananlar['toplam_oran']).sum()
    net_kar = toplam_kazanc - toplam_yatirilan
    basari_orani = (len(kazananlar) / len(df_perf)) * 100 if len(df_perf) > 0 else 0
    
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='metric-card'>💰 Toplam Yatırılan<br><span style='font-size:1.5em;'>{toplam_yatirilan:.2f} TL</span></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'>📈 Net Kâr/Zarar<br><span style='font-size:1.5em; color:{'#00ff00' if net_kar >=0 else '#ff4b4b'};'>{net_kar:.2f} TL</span></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card'>🎯 Başarı Oranı<br><span style='font-size:1.5em;'>%{basari_orani:.1f}</span></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='metric-card'>🚀 ROI<br><span style='font-size:1.5em;'>%{(net_kar/toplam_yatirilan*100) if toplam_yatirilan > 0 else 0:.1f}</span></div>", unsafe_allow_html=True)

# YAN PANEL
with st.sidebar:
    st.header("⚙️ Kupon Hazırlığı")
    tutar = st.number_input("Kupon Tutarı (TL)", min_value=10, value=100)
    mod = st.radio("Arama Modu", ["Finansal Hedef", "Doğrudan Oran"])
    ideal_o = (st.number_input("Hedef Kazanç", value=500) / tutar) ** (1/3) if mod == "Finansal Hedef" else st.number_input("Maç Başı Oran", value=1.25)
    
    if st.session_state.kupon_havuzu:
        st.subheader("📋 Havuzdaki Maçlar")
        t_oran = 1.0
        for m in st.session_state.kupon_havuzu:
            st.write(f"🔹 {m['Maç']} ({m['Oran']})")
            t_oran *= m['Oran']
        st.write(f"**Toplam Oran: {t_oran:.2f}**")
        if st.button("💾 KUPONU ARŞİVE EKLE"):
            st.session_state.kayitli_kuponlar.append({
                "tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "maclar": list(st.session_state.kupon_havuzu),
                "toplam_oran": t_oran,
                "yatirilan": tutar,
                "durum": "Bekliyor"
            })
            st.session_state.kupon_havuzu = []
            st.rerun()

# ANA SEKMELER
tab1, tab2, tab3 = st.tabs(["🔍 Analiz Merkezi", "📂 Kupon Arşivi", "📊 Finansal Rapor"])

with tab1:
    col1, col2 = st.columns(2)
    if col1.button("⚽ FUTBOL TARA", use_container_width=True):
        # Analiz motoru v14 ile aynı mantıkta çalışır...
        st.info("Piyasa taranıyor, maçlar listelenecek...")
        # (Buraya v14'teki analiz_motoru fonksiyonu gelecek)

with tab2:
    for idx, k in enumerate(reversed(st.session_state.kayitli_kuponlar)):
        with st.expander(f"📅 {k['tarih']} | Oran: {k['toplam_oran']:.2f} | {k['durum']}"):
            st.table(pd.DataFrame(k['maclar']))
            ca, cb, cc = st.columns(3)
            if ca.button("✅ KAZANDI", key=f"w_{idx}"): k['durum'] = "KAZANDI"; st.rerun()
            if cb.button("❌ KAYBETTİ", key=f"l_{idx}"): k['durum'] = "KAYBETTİ"; st.rerun()
            if cc.button("🗑️ SİL", key=f"d_{idx}"): st.session_state.kayitli_kuponlar.pop(-(idx+1)); st.rerun()

with tab3:
    if st.session_state.kayitli_kuponlar:
        st.subheader("📈 Kümülatif Kazanç Grafiği")
        df_perf['kar'] = df_perf.apply(lambda x: (x['yatirilan'] * x['toplam_oran'] - x['yatirilan']) if x['durum'] == "KAZANDI" else (-x['yatirilan'] if x['durum'] == "KAYBETTİ" else 0), axis=1)
        df_perf['kumulatif'] = df_perf['kar'].cumsum()
        fig = px.line(df_perf, x='tarih', y='kumulatif', title="Zaman İçinde Net Kâr Gelişimi", markers=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Rapor oluşturmak için en az bir kuponu sonuçlandırmalısınız.")
