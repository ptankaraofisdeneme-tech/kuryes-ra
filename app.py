import streamlit as st
from datetime import datetime
import sqlite3
import pandas as pd
import io
from database import veritabanini_kur, yeni_sira_no_uret, DB_NAME

# Veritabanını ilk açılışta otomatik oluşturur
veritabanini_kur()

st.set_page_config(page_title="Ofis Sıra Sistemi", page_icon="🛵", layout="wide")

# CSS ile arayüzü özelleştirme
st.markdown("""
    <style>
    .big-font { font-size:60px !important; font-weight: bold; color: #FF4B4B; text-align: center; }
    .success-text { font-size:20px !important; text-align: center; color: #00CC66; }
    .metric-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; text-align: center; }
    .status-badge { padding: 4px 10px; border-radius: 5px; font-weight: bold; font-size: 14px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- YAN MENÜ (NAVİGASYON) ---
SAYFA_SECIMI = st.sidebar.radio("Ekran Seçiniz:", ["Kurye Giriş Ekranı", "Ofis Yönetim Paneli"])

# ==========================================
# 1. SAYFA: KURYE GİRİŞ EKRANI
# ==========================================
if SAYFA_SECIMI == "Kurye Giriş Ekranı":
    st.title("🛵 Ofis Giriş & Sıra Sistemi")
    st.write("Lütfen aşağıdaki bilgileri doldurarak sıra numaranızı alınız.")

    with st.form("kurye_onay_formu", clear_on_submit=True):
        isim = st.text_input("Adınız Soyadınız:", placeholder="Örn: Ahmet Yılmaz")
        plaka = st.text_input("Plakanız:", placeholder="Örn: 34 ABC 123")
        
        sebep = st.selectbox(
            "Geliş Sebebiniz:",
            ["İş Başlangıcı", "İş Çıkışı", "Hakediş İşlemleri", "Ekipman Alım/Teslim", "Diğer"]
        )
        
        detay = st.text_input("Geliş Sebebi 'Diğer' ise lütfen buraya açıklama yazınız:")

        st.write("Girdiğiniz bilgilerin doğruluğundan eminseniz lütfen aşağıdaki butona basarak onaylayın.")
        submit_button = st.form_submit_button("Sıra Numarası Al 🚀")

    if submit_button:
        if isim.strip() == "" or plaka.strip() == "":
            st.error("⚠️ Lütfen Ad Soyad ve Plaka alanlarını boş bırakmayınız!")
        elif sebep == "Diğer" and detay.strip() == "":
            st.error("⚠️ Lütfen geliş sebebinizi kısaca belirtiniz!")
        else:
            sira_numarasi = yeni_sira_no_uret()
            su_an = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            nihai_sebep = detay.strip() if sebep == "Diğer" else sebep
            
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO kurye_talepleri (sira_no, isim_soyisim, plaka, gelis_sebebi, tarih_saat, durum)
                VALUES (?, ?, ?, ?, ?, 'Bekliyor')
            ''', (sira_numarasi, isim.strip(), plaka.strip().upper(), nihai_sebep, su_an))
            conn.commit()
            conn.close()
            
            st.markdown('<p class="success-text">🎉 Kaydınız alındı! Sıra Numaranız:</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="big-font">{sira_numarasi}</p>', unsafe_allow_html=True)
            st.warning("📢 Lütfen sıranız gelene kadar bekleyiniz, adınızla sesleneceğiz.")

# ==========================================
# 2. SAYFA: OFİS YÖNETİM PANELİ (ŞİFRE KORUMALI)
# ==========================================
else:
    st.title("📊 Ofis Sıra Yönetim Paneli")
    
    girilen_sifre = st.text_input("Yönetici Şifresini Giriniz:", type="password")
    
    if girilen_sifre != "filo123":
        st.error("🔒 Bu alana erişmek için yetkiniz yok. Lütfen doğru şifreyi giriniz.")
    else:
        st.success("🔓 Giriş Başarılı. Yönetim Paneli Aktif.")
        
        if st.button("🔄 Listeyi Yenile"):
            st.rerun()

        bugun = datetime.now().strftime("%Y-%m-%d")
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql_query("SELECT * FROM kurye_talepleri WHERE tarih_saat LIKE ?", conn, params=(f"{bugun}%",))
        conn.close()

        if df.empty:
            st.info("Bugün henüz sıra almış kurye bulunmuyor kanka.")
        else:
            bekleyen_sayisi = len(df[df['durum'] == 'Bekliyor'])
            islemde_sayisi = len(df[df['durum'] == 'İşlemde'])
            tamamlanan_sayisi = len(df[df['durum'] == 'Tamamlandı'])
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"<div class='metric-box'><h3>Toplam Gelen</h3><h2>{len(df)}</h2></div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div class='metric-box' style='color: #FF4B4B;'><h3>Bekleyen</h3><h2>{bekleyen_sayisi}</h2></div>", unsafe_allow_html=True)
            with col3:
                st.markdown(f"<div class='metric-box' style='color: #FFA500;'><h3>İşlemde</h3><h2>{islemde_sayisi}</h2></div>", unsafe_allow_html=True)
            with col4:
                st.markdown(f"<div class='metric-box' style='color: #00CC66;'><h3>Tamamlanan</h3><h2>{tamamlanan_sayisi}</h2></div>", unsafe_allow_html=True)
            
            st.write("---")

            st.subheader("⏳ Güncel Sıra Akışı (Bekleyenler ve İşlemdekiler)")
            aktif_df = df[df['durum'].isin(['Bekliyor', 'İşlemde'])]

            if aktif_df.empty:
                st.success("Harika! Bekleyen veya işlemde olan hiçbir kurye yok. 😎")
            else:
                for index, row in aktif_df.iterrows():
                    col_sira, col_bilgi, col_eylem = st.columns([1, 4, 3])
                    
                    with col_sira:
                        if row['durum'] == 'Bekliyor':
                            st.subheader(f"🛑 {row['sira_no']}")
                            st.markdown('<span class="status-badge" style="background-color: #FF4B4B; color: white;">Bekliyor</span>', unsafe_allow_html=True)
                        else:
                            st.subheader(f"⚡ {row['sira_no']}")
                            personel_adi = row.get('islem_yapan', 'Bilinmeyen') if row.get('islem_yapan') else "Personel"
                            st.markdown(f'<span class="status-badge" style="background-color: #FFA500; color: black;">👨‍💻 {personel_adi} İşlemde</span>', unsafe_allow_html=True)
                    
                    with col_bilgi:
                        st.write(f"**Kurye:** {row['isim_soyisim']} ({row['plaka']})")
                        st.write(f"**Geliş Nedeni:** {row['gelis_sebebi']} | **Saat:** {row['tarih_saat'].split()[1]}")
                    
                    with col_eylem:
                        if row['durum'] == 'Bekliyor':
                            personel_secimi = st.selectbox(
                                "İşlemi Üstlenen:",
                                ["Sabri", "Batuhan", "Eren"],
                                key=f"pers_{row['id']}"
                            )
                            
                            btn_cagir, btn_iptal = st.columns(2)
                            with btn_cagir:
                                if st.button(f"📢 Çağır / İşleme Al", key=f"cagir_{row['id']}", use_container_width=True):
                                    conn = sqlite3.connect(DB_NAME)
                                    cursor = conn.cursor()
                                    # BURAYA GÜVENLİK KORUMASI EKLENDİ KANKA (OperationalError Engellendi)
                                    try:
                                        cursor.execute("UPDATE kurye_talepleri SET durum = 'İşlemde', islem_yapan = ? WHERE id = ?", (personel_secimi, row['id']))
                                    except sqlite3.OperationalError:
                                        cursor.execute("UPDATE kurye_talepleri SET durum = 'İşlemde' WHERE id = ?", (row['id'],))
                                    conn.commit()
                                    conn.close()
                                    st.rerun()
                            with btn_iptal:
                                if st.button(f"❌ İptal Et", key=f"iptal_{row['id']}", use_container_width=True):
                                    conn = sqlite3.connect(DB_NAME)
                                    cursor = conn.cursor()
                                    cursor.execute("UPDATE kurye_talepleri SET durum = 'İptal Edildi' WHERE id = ?", (row['id'],))
                                    conn.commit()
                                    conn.close()
                                    st.rerun()
                        
                        elif row['durum'] == 'İşlemde':
                            st.write(f"👉 Bu işlemle şu an **{row.get('islem_yapan', 'Biri')}** ilgileniyor.")
                            if st.button(f"✓ İşlemi Tamamla", key=f"tamam_{row['id']}", type="primary", use_container_width=True):
                                conn = sqlite3.connect(DB_NAME)
                                cursor = conn.cursor()
                                cursor.execute("UPDATE kurye_talepleri SET durum = 'Tamamlandı' WHERE id = ?", (row['id'],))
                                conn.commit()
                                conn.close()
                                st.success(f"{row['sira_no']} numaralı işlem kapatıldı!")
                                st.rerun()
                                
                    st.write("---")

            # Günlük Geçmiş Tablosu Ekranı
            st.subheader("📋 Günlük Tüm Kayıtlar")
            gosterilecek_sutunlar = ["sira_no", "isim_soyisim", "plaka", "gelis_sebebi", "tarih_saat", "durum"]
            if "islem_yapan" in df.columns:
                gosterilecek_sutunlar.append("islem_yapan")
            st.dataframe(df[gosterilecek_sutunlar], use_container_width=True)
            
            # --- EXCEL RAPORLAMA ---
            st.write("---")
            st.subheader("📥 Günlük Raporu İndir")
            
            if "islem_yapan" in df.columns:
                excel_df = df[["sira_no", "isim_soyisim", "plaka", "gelis_sebebi", "tarih_saat", "durum", "islem_yapan"]].copy()
                excel_df.columns = ["Sıra No", "Ad Soyad", "Plaka", "Geliş Sebebi", "İşlem Tarihi", "Durum", "İşlem Yapan"]
            else:
                excel_df = df[["sira_no", "isim_soyisim", "plaka", "gelis_sebebi", "tarih_saat", "durum"]].copy()
                excel_df.columns = ["Sıra No", "Ad Soyad", "Plaka", "Geliş Sebebi", "İşlem Tarihi", "Durum"]
            
            def turkce_buyuk_harf(metin):
                if not isinstance(metin, str):
                    return metin
                return metin.replace('i', 'İ').replace('ı', 'I').upper()

            def plaka_temizle(plaka):
                if not isinstance(plaka, str):
                    return plaka
                return turkce_buyuk_harf(plaka.replace(" ", ""))

            excel_df["Ad Soyad"] = excel_df["Ad Soyad"].apply(turkce_buyuk_harf)
            excel_df["Plaka"] = excel_df["Plaka"].apply(plaka_temizle)
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                excel_df.to_excel(writer, index=False, sheet_name='Günlük Kurye Raporu')
                workbook = writer.book
                worksheet = writer.sheets['Günlük Kurye Raporu']
                for col in worksheet.columns:
                    max_len = max(len(str(cell.value or '')) for cell in col)
                    col_letter = col[0].column_letter
                    worksheet.column_dimensions[col_letter].width = max(max_len + 4, 12)
            
            excel_data = output.getvalue()
            
            st.download_button(
                label="📊 Profesyonel Excel Raporu İndir (.xlsx)",
                data=excel_data,
                file_name=f"kurye_raporu_{bugun}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # ---- CANLI SİSTEMDE TABLOYA SÜTUN EKLEME BUTONU (SADECE 1 KERE BASILACAK) ----
            st.write("---")
            st.subheader("⚙️ Canlı Sistem Güncelleme")
            if st.button("🛠️ Veritabanına 'İşlem Yapan' Sütununu Tanımla"):
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                try:
                    cursor.execute("ALTER TABLE kurye_talepleri ADD COLUMN islem_yapan TEXT")
                    conn.commit()
                    st.success("Sütun başarıyla eklendi! Artık sisteminiz tamamen güncel kanka.")
                except sqlite3.OperationalError:
                    st.info("Bu sütun zaten veritabanınızda mevcut kanka, işlem yapmaya gerek yok.")
                conn.close()
