# DuckTransfer - FTP, SFTP & S3 Masaüstü İstemcisi

CyberDuck ve FileZilla benzeri, masaüstünde çalışan bir FTP, SFTP ve Amazon S3 istemcisi. Tkinter ve ttkbootstrap ile modern, koyu temalı bir arayüz sunar.

## Özellikler

- **FTP Desteği**: Klasik FTP sunucularına bağlanma
- **FTP-SSL**: Explicit AUTH TLS ile güvenli FTP
- **SFTP Desteği**: SSH üzerinden dosya aktarımı (paramiko gerekir)
- **Amazon S3 Desteği**: AWS S3 bucket'larına erişim (Access Key / Secret Key ile)
- **Gizli Dosyalar**: Yerel panelde gizli dosyaları gösterme/gizleme
- **Kayıtlı Bağlantılar**: Bağlantı ayarları `~/.config/ducktransfer/connections.json` dosyasında saklanır
- **Çift Panelli Arayüz**: Sol panel yerel dosyalar, sağ panel uzak sunucu
- **Dosya İşlemleri**: Yükleme, indirme, silme, yeni klasör oluşturma
- **İlerleme Göstergesi**: Yükleme/indirme sırasında ilerleme çubuğu
- **Modern UI**: ttkbootstrap ile koyu tema (darkly)

## Kurulum

```bash
# Sanal ortam oluştur (önerilir)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Bağımlılıkları yükle
pip install -r requirements.txt
```

## Çalıştırma

```bash
python main.py
```

## Kullanım

1. **Yeni Bağlantı** butonuna tıklayın
2. **FTP** veya **Amazon S3** seçin
3. Bağlantı bilgilerini girin:
   - **FTP**: Sunucu, port, kullanıcı adı, şifre
   - **S3**: Access Key, Secret Key, bölge, bucket adı
4. **Bağlan** ile bağlantıyı kurun
5. Sol panelden dosya seçip **Yükle** veya sağ panelden seçip **İndir** ile transfer yapın

## Gereksinimler

- Python 3.10+
- ttkbootstrap
- boto3 (S3 için)

## Kayıtlı Bağlantılar

Bağlantı ayarları **`~/.config/ducktransfer/connections.json`** dosyasında tutulur. "Bağlantıyı kaydet" işaretlendiğinde şifre ve secret key de düz metin olarak bu dosyaya yazılır. Bu dosyayı paylaşmayın veya versiyon kontrolüne eklemeyin.

## Proje Yapısı

```
ducktransfer/
├── main.py              # Ana uygulama
├── requirements.txt
├── .gitignore
├── config/              # Kayıtlı bağlantı yönetimi
│   └── connections.py
├── connectors/          # FTP, SFTP ve S3 bağlayıcıları
│   ├── base.py
│   ├── ftp_connector.py
│   ├── sftp_connector.py
│   └── s3_connector.py
└── ui/                  # Arayüz bileşenleri
    ├── panels.py
    ├── connection_dialog.py
    └── progress_dialog.py
```
