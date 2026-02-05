# DuckTransfer

CyberDuck ve FileZilla tarzında, masaüstünde çalışan bir dosya transfer aracı. FTP, SFTP ve Amazon S3 ile konuşabiliyor. Tkinter ile yazıldı, ttkbootstrap sayesinde de koyu temalı düzgün bir arayüzü var.

## Ne yapıyor?

Sol tarafta bilgisayarınızdaki dosyalar, sağ tarafta uzak sunucu. Dosya seçip yükle/indir butonlarıyla transfer ediyorsun. Klasik çift panelli dosya yöneticisi mantığı.

**Desteklenen protokoller:**
- FTP (klasik)
- FTP-SSL (şifreli)
- SFTP (SSH üzerinden – paramiko kurulu olmalı)
- Amazon S3

**Diğer özellikler:**
- Gizli dosyaları gösterme seçeneği (yerel panelde)
- Bağlantıları kaydedip sonra tek tıkla yükleme
- Yeni klasör oluşturma, dosya silme
- Yükleme/indirme sırasında ilerleme çubuğu

## Kurulum

```bash
python -m venv .venv
source .venv/bin/activate   # Windows'ta: .venv\Scripts\activate

pip install -r requirements.txt
```

## Çalıştırma

```bash
python main.py
```

## Nasıl kullanılır?

1. **Yeni Bağlantı** ile FTP, SFTP veya S3 bilgilerini gir
2. Bağlan
3. Sol panelden dosya seç → **Yükle**, sağ panelden seç → **İndir**

Kayıtlı bağlantılar varsa listeden seçip **Yükle** ile formu doldurup bağlanabilirsin. İstersen "Bağlantıyı kaydet" ile ayarları saklayabilirsin.

## Kayıtlı bağlantılar nereye gidiyor?

`~/.config/ducktransfer/connections.json` dosyasına yazılıyor. Şifre ve secret key de düz metin olarak burada duruyor – bu dosyayı kimseyle paylaşma ve Git'e ekleme.

## Proje yapısı

```
├── main.py           # Ana uygulama
├── config/           # Bağlantı kaydetme/yükleme
├── connectors/       # FTP, SFTP, S3 bağlayıcıları
└── ui/               # Arayüz (paneller, dialoglar)
```

## Gereksinimler

- Python 3.10+
- ttkbootstrap, boto3 (S3 için)
- SFTP için: paramiko
