# LinkedIn Learning Video Downloader

Bu program, LinkedIn Learning eğitimlerindeki videoları indirmenize yardımcı olan bir masaüstü uygulamasıdır. Program Python ile yazılmış olup PyQt6 arayüzü kullanmaktadır.

![image](https://github.com/user-attachments/assets/5555cbc0-3a80-4a84-8164-a9525f9ab564)


## Özellikler

- LinkedIn Learning video listesini otomatik çekme
- Bölümlere göre video organizasyonu
- Çoklu video seçimi ve indirme
- Kullanıcı dostu arayüz
- İlerleme durumu gösterimi

## Kurulum

### Hazır Exe Dosyası ile Kurulum

1. Releases bölümünden son sürümü indirin
2. İndirilen exe dosyasını çalıştırın

### Kaynak Koddan Kurulum

1. Repoyu klonlayın
```bash
git clone https://github.com/onder7/linkedin-learning-downloader.git
cd linkedin-learning-downloader
```

2. Sanal ortam oluşturun ve aktive edin
```bash
python -m venv venv
# Windows için
venv\Scripts\activate
# Linux/Mac için
source venv/bin/activate
```

3. Gerekli paketleri yükleyin
```bash
pip install -r requirements.txt
```

4. Programı çalıştırın
```bash
python linkedin_learning_downloader.py
```

## Kullanım

1. LinkedIn hesap bilgilerinizi girin
2. İndirmek istediğiniz kurs URL'sini yapıştırın
3. "Videoları Listele" butonuna tıklayın
4. İndirmek istediğiniz videoları seçin
5. İndirme klasörünü belirleyin
6. "Seçili Videoları İndir" butonuna tıklayın

## Gereksinimler

- Python 3.8+
- PyQt6
- Selenium
- yt-dlp
- webdriver-manager

## Önemli Notlar

- Bu program yalnızca eğitim amaçlı yapılmıştır
- LinkedIn Learning aboneliğiniz olması gerekir
- İndirilen videoların telif haklarına dikkat edin

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

## Katkıda Bulunma

1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/AmazingFeature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add some AmazingFeature'`)
4. Branch'inizi push edin (`git push origin feature/AmazingFeature`)
5. Pull Request oluşturun

## İletişim

GitHub: [kullaniciadi](https://github.com/onder7)
Onder7@gmail.com
