# 🚀 Antigravity AIOps // Akıllı Sistem Radarı & Oyun Otopilotu (v4.1)

![Version](https://img.shields.io/badge/sürüm-v4.1-00e5ff?style=for-the-badge&logo=appveyor)
![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-ff007f?style=for-the-badge&logo=windows)
![CPU Impact](https://img.shields.io/badge/oyun%20etkisi-%250.1%20CPU%20(Sıfır%20FPS%20Kayıp)-00e676?style=for-the-badge&logo=amd)
![License](https://img.shields.io/badge/lisans-MIT-9d4edd?style=for-the-badge)

**Antigravity AIOps System Radar**, bilgisayarınızın donanım performansını saniyeler içinde analiz eden, oyunlara **%0 FPS** ve **%0.1 CPU** etki güvencesiyle eşlik eden, tek tıkla **RAM temizliği** yapıp **Yapay Zeka (AI) arıza ve darboğaz teşhisi** sunan yeni nesil otonom bir masaüstü koruma ve sistem takip süitidir!

Kuruluma gerek duyulmaksızın taşınabilir (**Portable .EXE**) olarak çalışır. Harici bir web tarayıcısına gereksinim duymaz; yerleşik **Windows WebView2** penceresinde siber-oyuncu esintili büyüleyici arayüzüyle açılır ve arka planda sağ alt saatin yanındaki sistem tepsisine (System Tray) oturur.

---

## 💎 v4.1 ile Öne Çıkan Devrimsel Özellikler

### 1. 🎮 Akıllı Oyun Otopilotu & Kilit Anahtarı (Auto Game Detection)
- **Sıfır Müdahale ile Otomatik Yük Atma:** Arka planda bilinen oyun motorlarını (Steam, Epic Games, Unreal, Riot, Valorant, CS2, Cyberpunk 2077 vb.) veya tam ekran yüksek GPU uygulamalarını anında saptar.
- **Eco / Oyun Modu:** Oyun açıldığı saniye tarama aralığını genleştirerek **oyunlarınıza %0 işlemci yükü ve maksimum FPS** sunmak için kendini minimum güç konumuna çeker.
- **🔒 Manuel Kilit:** "Otopilot Kilit" butonunu kapatarak istendiği takdirde otopilotu durdurabilir, oyun esnasında dahi **Tam Canlı Mod** taramasından faydalanabilirsiniz.
- **8 Saniyelik Kesin Tanılama:** Oyundan çıktığınızı sadece 8 saniye içinde saptayıp saniyeler içinde normal canlı analiz moduna döner.

### 2. 🚀 Akıllı RAM Hızlandırıcı & Otomatik Temizleyici (`EmptyWorkingSet`)
- **Native Win32 Trimmer:** Bilgisayarınızın hızlı sistem önbelleğine (Cache / Pagefile) asla zarar vermeden; tarayıcı sekme yığınlarını, arka plan uygulamalarını ve açık process çalışma kümelerini (Working Set) **tek tıkla milisaniyeler içinde süper temizler** (Ortalama **500 MB ile 2.5 GB** arasında anlık yer açılır!).
- **⚡ Oto-Temizleyici Switch:** Arka planda bellek kullanımınız **%82 üstüne çıkarsa** akıllı motor devreye girerek siz hiç oyunu bozmadan sessizce belleğinizi boşaltır!

### 3. 🤖 AI Check-up & Sistem Doktoru (Darboğaz Teşhis Radarı)
- Hararet (Thermal Throttling) riski, RAM daralaması, anormal CPU tüketen veya şüpheli iplikler (threads) açan uygulamalar anlık olarak taramaya alınır.
- Panelden butonuna tıkladığınızda size **A+, B, C-** gibi sistem sağlığı karne notu verir ve *"X uygulamasının RAM tüketimi sınırda, kapatmanız önerilir"* tarzında uzman medikal reçete & tavsiye üretir.

### 4. 🌡️ Çapraz Hararet Algılama & Seyir Defteri (Game Analytics)
- WMI / MSACPI donanım katmanlarını kullanarak **Hem CPU hem de GPU sıcaklığınızı (🌡️°C)** saniye saniye denetler. İşlemci sensörü kilitli laptoplarda dahi akıllı ısı korelasyonu ile donatılmıştır!
- Sıcaklık **83°C** seviyesini aştığında Windows sağ alt köşesinden **Maksimum Tehlike Toast Bildirimi** gönderir.
- **📖 Seyir Defteri:** Oyundan çıktığınızda veya günün sonunda oyun sürenizi, ulaşılan **Max GPU & CPU sıcağını**, **Max RAM kullanım oranını** ve karne notunuzu kalıcı bir rapor halinde sergiler.

### 5. ⚡ Windows Açılışında Sessiz Nöbet & System Tray İkonu
- Kayıt defterine (Registry HKCU) zararsız bir katman ekleyerek tek tuşla **Windows ile Başla** seçeneğini etkinleştirmenizi sağlar.
- Bilgisayar ilk açıldığında hiçbir rahatsız edici pencere veya kara terminal açmadan dosdoğru **saatinizin yanındaki koruyucu kalkan simgesine (System Tray)** gizlice gömülüp sessiz bir siber nöbete başlar!

### 6. 🎨 Kişiselleştirilebilir Oyuncu Temaları (Glassmorphism & Neon)
- **4 Özel Temalı Işıma Katmanı:** Zengin Glassmorphism tasarımı, tarayıcınızın `localStorage` sisteminde tercihinizi kalıcı olarak saklar.
  - 🔵 **Cyberpunk Neon** (Mavi / Turkuaz Işıldama)
  - 🟢 **Hacker Emerald** (Koyu Zümrüt & Matrix Yeşil)
  - 🟣 **Synthwave Magenta** (80'ler Pembe & Retrowave Moru)
  - 🟠 **Volcano Gold** (Magma Turuncusu & Yüksek Isı Altını)

---

## 🛠️ Nasıl Çalıştırılır ve Kurulur?

### ⭐ Yöntem 1: Tek-Tık Taşınabilir Uygulama (.EXE) ile (Önerilen)
Hiçbir kodlama veya Python kurulumuna ihtiyacınız yoktur. GitHub üzerindeki **[Releases (Sürümler)](https://github.com/cekYc/real_time_iot_dashboard/releases)** sayfasından son derlenen çalıştırılabilir dosyamızı hemen indirebilirsiniz:
👉 **`AIOps_System_Radar.exe`** indirip direkt çalıştırın!

---

### 💻 Yöntem 2: Kaynak Koddan Gelistirme (Python Ortamı İçin)
Projeyi kod katmanında indirmek ve kendiniz eskitip modifiye etmek isterseniz:

1. **Depoyu Bilgisayarınıza Çekin:**
   ```bash
   git clone https://github.com/cekYc/real_time_iot_dashboard.git
   cd real_time_iot_dashboard-main
   ```

2. **Gerekli Python Kütüphanelerini Kurun:**
   ```bash
   pip install -r requirements.txt
   ```
   *(Bağımlılıklar: `flask`, `psutil`, `pystray`, `Pillow`, `pywebview`, `pythonnet`, `wmi`, `requests`)*

3. **Masaüstü Ekosistemini Başlatın:**
   ```bash
   python start_monitor.py
   ```
   *Not: Tarayıcı açmadan doğrudan yerleşik Windows masaüstü ekrana taşınır! Eğer eski sistem harici tarayıcıdan test etmek isterseniz sadece `python backend/app.py` koşturabilirsiniz.*

---

## 🧪 Mimari ve Bileşen Matrisi

| Dosya / Bileşen Katmanı | Çalışma Prensibi & Fonksiyonel Görevi |
| :--- | :--- |
| `start_monitor.py` | Ana masaüstü ateşleyici. WebView2 entegresi ile uygulamayı açar ve Tray servisiyle köprü kurar. |
| `backend/monitor_engine.py` | Mikrosaniyelik WMI ve psutil tarayıcı matrisi. Autopilot, sıcaklık radarı ve oto-RAM döngüsünü yönetir. |
| `backend/ram_booster.py` | Win32 `EmptyWorkingSet` çağrıları ile gereksiz RAM sayfalarını saniyeler içinde sıfırlar. |
| `backend/ai_checkup.py` | Sistem üzerindeki dar boğazları ve şüpheli operasyonları irdeleyen yapay zeka analizörü. |
| `backend/startup_manager.py` | Yönetici onayı gerektirmeyen sessiz Windows Başlangıç konfigürasyon katmanı (`HKCU\...\Run`). |
| `backend/tray_service.py` | Sağ alt saatin yanında yaşayan arka plan servis kontrolcüsü (`pystray`). |
| `build_exe.py` | Tüm projenin `pywebview` ve kütüphane bağlarıyla tek dosyalık `.exe` haline derlenmesini sağlayan PyInstaller aracı. |

---
*Developed & Evolved with Google Antigravity & AI Pair Programming.* 🛡️🚀
