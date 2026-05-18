import streamlit as st
from datetime import datetime
import sqlite3
import pandas as pd
import io
from database import veritabanini_kur, yeni_sira_no_uret, DB_NAME

# Veritabanını ilk açılışta otomatik oluşturur
veritabanini_kur()

st.set_page_config(page_title="Ofis Sıra Sistemi", page_icon="🛵", layout="wide")

# CSS ile arayüzü özelleştirelim (Büyük sıra numarası ve özet kutuları için)
st.markdown("""
    <style>
    .big-font { font-size:60px !important; font-weight: bold; color: #FF4B4B; text-align: center; }
    .success-text { font-size:20px !important; text-align: center; color: #00CC66; }
    .metric-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- YAN MENÜ (NAVİGASYON) ---
SAYFA_SECIMI = st.sidebar.radio("Ekran Seçiniz:", ["Kurye Giriş Ekranı", "Ofis Yönetim Paneli"])

# ==========================================
# 1. SAYFA: KURYE GİRİŞ EKRANI (QR Okutunca Açılan Ekran)
# ==========================================
if SAYFA_SECIMI == "Kurye Giriş Ekranı":
    st.title("🛵 Ofis Giriş & Sıra Sistemi")
    st.write("Lütfen aşağıdaki bilgileri doldurarak sıra numaranızı alınız.")

    with st.form("kurye_giris_formu", clear_on_submit=True):
        isim = st.text_input("Adınız Soyadınız:", placeholder="Örn: Ahmet Yılmaz")
        plaka = st.text_input("Plakanız:", placeholder="Örn: 34 ABC 123")
        
        sebep = st.selectbox(
            "Geliş Sebebiniz:",
            ["İş Başlangıcı", "İş Çıkışı", "Hakediş İşlemleri", "Ekipman Alım/Teslim", "Diğer"]
        )
        
        detay = ""
        if sebep == "Diğer":
            detay = st.text_input("Lütfen geliş sebebinizi kısaca yazın:")

        submit_button = st.form_submit_button("Sıra Numarası Al")

    if submit_button:
        if isim.strip() == "" or plaka.strip() == "":
            st.error("⚠️ Lütfen Ad Soyad ve Plaka alanlarını boş bırakmayınız!")
        else:
            # Düz sıra numarasını üret (001, 002...)
            sira_numarasi = yeni_sira_no_uret()
            su_an = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            nihai_sebep = detay if sebep == "Diğer" else sebep
            
            # Veritabanına kaydet
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO kurye_talepleri (sira_no, isim_soyisim, plaka, gelis_sebebi, tarih_saat)
                VALUES (?, ?, ?, ?, ?)
            ''', (sira_numarasi, isim.strip(), plaka.strip().upper(), nihai_sebep, su_an))
            conn.commit()
            conn.close()
            
            # Kuryeye ekranında numarasını göster
            st.markdown('<p class="success-text">🎉 Kaydınız alındı! Sıra Numaranız:</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="big-font">{sira_numarasi}</p>', unsafe_allow_html=True)
            st.info("💡 Lütfen içerideki ekrandan sıranızı takip ediniz.")

# ==========================================
# 2. SAYFA: OFİS YÖNETİM PANELİ (İçerideki Personelin Göreceği Ekran)
# ==========================================
else:
    st.title("📊 Ofis Sıra Yönetim Paneli")
    
    # Sayfayı manuel yenilemek için buton
    if st.button("🔄 Listeyi Yenile"):
        st.rerun()

    # Bugünün tarihini al ve bugünkü verileri çek
    bugun = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query(f"SELECT * FROM kurye_talepleri WHERE tarih_saat LIKE '{bugun}%
