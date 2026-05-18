import sqlite3
from datetime import datetime

DB_NAME = "ofis_sira_sistemi.db"


def veritabanini_kur():
    """Sistemin çalışması için gerekli SQLite tablosunu oluşturur."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS kurye_talepleri
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       sira_no
                       TEXT
                       NOT
                       NULL,
                       isim_soyisim
                       TEXT
                       NOT
                       NULL,
                       plaka
                       TEXT
                       NOT
                       NULL,
                       gelis_sebebi
                       TEXT
                       NOT
                       NULL,
                       tarih_saat
                       TEXT
                       NOT
                       NULL,
                       durum
                       TEXT
                       DEFAULT
                       'Bekliyor'
                   )
                   ''')
    conn.commit()
    conn.close()


def yeni_sira_no_uret():
    """Bugün gelen toplam kurye sayısına göre düz sıra numarası üretir (001, 002...)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    bugun = datetime.now().strftime("%Y-%m-%d")

    # Bugün açılmış toplam kayıt sayısını bul
    cursor.execute('''
                   SELECT COUNT(*)
                   FROM kurye_talepleri
                   WHERE tarih_saat LIKE ?
                   ''', (f"{bugun}%",))

    bugunku_siralar = cursor.fetchone()[0]
    conn.close()

    yeni_sira = bugunku_siralar + 1
    return f"{yeni_sira:03d}"  # 1 -> "001", 12 -> "012" yapar