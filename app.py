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
            
            # Veritabanına kaydet (Hatalı text_saat kısmı temizlendi kanka)
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

    # Bugünün tarihini al ve bugünkü verileri çek (Güvenli ve hatasız sorgu)
    bugun = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM kurye_talepleri WHERE tarih_saat LIKE ?", conn, params=(f"{bugun}%",))
    conn.close()

    if df.empty:
        st.info("Bugün henüz sıra almış kurye bulunmuyor kanka.")
    else:
        # Üst Özet İstatistik Kutuları
        bekleyen_sayisi = len(df[df['durum'] == 'Bekliyor'])
        tamamlanan_sayisi = len(df[df['durum'] == 'Tamamlandı'])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"<div class='metric-box'><h3>Toplam Gelen</h3><h2>{len(df)}</h2></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='metric-box' style='color: #FF4B4B;'><h3>Bekleyen Sıra</h3><h2>{bekleyen_sayisi}</h2></div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div class='metric-box' style='color: #00CC66;'><h3>Tamamlanan</h3><h2>{tamamlanan_sayisi}</h2></div>", unsafe_allow_html=True)
        
        st.write("---")

        # Sıra Yönetim Alanı
        st.subheader("⏳ Bekleyen Talepler ve İşlem Yapma")
        bekleyen_df = df[df['durum'] == 'Bekliyor']

        if bekleyen_df.empty:
            st.success("Harika! Bekleyen hiçbir kurye yok. 😎")
        else:
            # Bekleyen kuryeleri butonlarla listele
            for index, row in bekleyen_df.iterrows():
                col_sira, col_bilgi, col_buton = st.columns([1, 4, 2])
                
                with col_sira:
                    st.subheader(f"🛑 {row['sira_no']}")
                
                with col_bilgi:
                    st.write(f"**Kurye:** {row['isim_soyisim']} ({row['plaka']})")
                    st.write(f"**Geliş Nedeni:** {row['gelis_sebebi']} | **Saat:** {row['tarih_saat'].split()[1]}")
                
                with col_buton:
                    # Durumu "Tamamlandı" olarak güncelleme butonu
                    if st.button(f"✓ Tamamla", key=f"btn_{row['id']}"):
                        conn = sqlite3.connect(DB_NAME)
                        cursor = conn.cursor()
                        cursor.execute("UPDATE kurye_talepleri SET durum = 'Tamamlandı' WHERE id = ?", (row['id'],))
                        conn.commit()
                        conn.close()
                        st.success(f"{row['sira_no']} numaralı işlem tamamlandı!")
                        st.rerun()
                st.write("---")

        # Günlük Geçmiş Tablosu Ekranı
        st.subheader("📋 Günlük Tüm Kayıtlar")
        st.dataframe(df[["sira_no", "isim_soyisim", "plaka", "gelis_sebebi", "tarih_saat", "durum"]], use_container_width=True)
        
        # --- TÜRKÇE KARAKTER VE SÜTUN SORUNU DÜZELTİLMİŞ EXCEL RAPORLAMA ---
        st.write("---")
        st.subheader("📥 Günlük Raporu İndir")
        
        # Excel için veriyi kopyalayıp başlıkları düzenliyoruz
        excel_df = df[["sira_no", "isim_soyisim", "plaka", "gelis_sebebi", "tarih_saat", "durum"]].copy()
        excel_df.columns = ["Sıra No", "Ad Soyad", "Plaka", "Geliş Sebebi", "İşlem Tarihi", "Durum"]
        
        # Arka planda gerçek bir Excel (.xlsx) dosyası oluşturma işlemi
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            excel_df.to_excel(writer, index=False, sheet_name='Günlük Kurye Raporu')
            
            # Sütun genişliklerini içeriğe göre otomatik olarak genişletiyoruz
            workbook = writer.book
            worksheet = writer.sheets['Günlük Kurye Raporu']
            
            for col in worksheet.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                col_letter = col[0].column_letter
                worksheet.column_dimensions[col_letter].width = max(max_len + 4, 12)
        
        excel_data = output.getvalue()
        
        # İndirme Butonu
        st.download_button(
            label="📊 Profesyonel Excel Raporu İndir (.xlsx)",
            data=excel_data,
            file_name=f"kurye_raporu_{bugun}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
