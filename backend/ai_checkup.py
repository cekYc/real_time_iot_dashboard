from backend.local_storage import storage_engine
import time

class AICheckupDoctor:
    """
    Akıllı AI Sistem Doktoru & Darboğaz Analizörü:
    Sistemin mevcut kapasitesini, belleğini, arka plan servis yükünü ve harcama alışkanlıklarını
    profesyonel bir bilgisayar uzmanı gibi detaylıca check-up eder ve kişiye özel reçeteler hazırlar.
    """
    def __init__(self):
        pass

    def run_checkup(self, current_snapshot):
        report = {
            "timestamp": time.strftime("%H:%M:%S - %d.%m.%Y"),
            "overall_status": "Mükemmel / Optimizasyona Hazır",
            "grade": "A+",
            "summary_message": "Sistem donanım birimleri genel hatlarıyla uyumlu ve kararlı çalışıyor.",
            "diagnose_items": []
        }

        if not current_snapshot:
            report["summary_message"] = "Veri taraması henüz sürüyor, lütfen 2 saniye sonra tekrar deneyin."
            return report

        sys_info = current_snapshot.get("system_info", {})
        mem = current_snapshot.get("memory", {})
        cpu = current_snapshot.get("cpu", {})
        disk = current_snapshot.get("disk", {})
        thermal = current_snapshot.get("thermal", {})
        procs = current_snapshot.get("processes", {}).get("top_list", [])

        grade_points = 100

        # --- 1. RAM Darboğazı & Kapasite İncelemesi ---
        ram_total_gb = mem.get("total_gb", 16.0)
        ram_used_gb = mem.get("used_gb", 0.0)
        ram_pct = mem.get("percent", 0.0)
        swap_pct = mem.get("swap_percent", 0.0)

        if ram_pct >= 85.0:
            grade_points -= 20
            report["diagnose_items"].append({
                "category": "🧠 Bellek (RAM) Darboğazı",
                "severity": "CRITICAL",
                "icon": "🚨",
                "title": "Fiziksel Bellek Sınırda Çalışıyor",
                "detail": f"Mevcut {ram_total_gb} GB belleğinizin %{ram_pct} kadarı ({ram_used_gb} GB) şu anda dolmuş durumda.",
                "prescription": "Özellikle yeni nesil oyunlarda veya yoğun sekme kullanımında ani takılma (micro-stutter) yaşanabilir. Arka planda açık olan gereksiz başlatıcıları kapatın veya 32 GB RAM yükseltmesi yapmayı planlayın."
            })
        elif ram_pct >= 70.0:
            grade_points -= 8
            report["diagnose_items"].append({
                "category": "🧠 Bellek (RAM) Kapasitesi",
                "severity": "WARNING",
                "icon": "⚠️",
                "title": "Yüksek Bellek Yoğunluğu",
                "detail": f"Sisteminiz olağan masaüstü/tarayıcı kullanımında dahi %{ram_pct} RAM harcıyor.",
                "prescription": "Sanal bellek (Windows Pagefile) kullanımına geçildiğinde sistem reaksiyonları yavaşlar; oyunlara girmeden önce web sekmelerini küçültmeniz FPS'i rahatlatacaktır."
            })
        else:
            report["diagnose_items"].append({
                "category": "🧠 Bellek (RAM) Kapasitesi",
                "severity": "OK",
                "icon": "✅",
                "title": "Bellek Alanı Geniş ve Konforlu",
                "detail": f"Belleğinizin yalnızca %{ram_pct} kadarı kullanımda. Ağır multitasking ve oyunlar için bolca manevra alanı var.",
                "prescription": "Hiçbir müdahaleye gerek yoktur, sistem belleğiniz optimum kondisyonda."
            })

        # --- 2. Arka Plan Uygulamaları & Paralı Servis Yükü ---
        bg_heavy_apps = []
        total_bg_ram = 0.0
        for p in procs:
            p_name = p["name"].lower()
            if any(w in p_name for w in ["chrome", "edge", "zen", "discord", "steam", "epic", "spotify"]):
                bg_heavy_apps.append(p["name"])
                total_bg_ram += p["memory_mb"]

        if total_bg_ram > 1800.0 and len(bg_heavy_apps) >= 3:
            grade_points -= 10
            report["diagnose_items"].append({
                "category": "⚙️ Arka Plan Uygulama Verimliliği",
                "severity": "WARNING",
                "icon": "⚡",
                "title": "Arka Planda Yüksek Hazırlıklı Yazılımlar Var",
                "detail": f"Aynı anda açık duran ({', '.join(bg_heavy_apps[:4])}) gibi uygulamalar toplam {round(total_bg_ram,1)} MB sistem hafızası rezerve ediyor.",
                "prescription": "Oynamadığınız oyun platformlarının sistem tepsinindeki ikancıklarını sağ tıklayıp tam kapatmak %5 ile %8 arası ekstra oyun hızı ve işlemci serinliği sağlayacaktır."
            })

        # --- 3. Sürücü (Disk) Performans ile SSD Yaşam Ömrü ---
        partitions = disk.get("partitions", [])
        for part in partitions:
            if part.get("percent", 0) > 88.0:
                grade_points -= 15
                report["diagnose_items"].append({
                    "category": "💾 SSD & Sürücü Daralmaları",
                    "severity": "CRITICAL",
                    "icon": "🔴",
                    "title": f"Sürücü Kapasitesi Limitinde: {part.get('mountpoint')}",
                    "detail": f"SSD/HDD disklerin %88 üzeri doluluğu flash hücrelerinin yazma hızını (NAND Cache) yarı yarıya düşürür.",
                    "prescription": f"En az 20-30 GB gereksiz veya eski indirme dosyasını silerek diskin nefes almasını ve TRIM hızlarının yükselmesini sağlayın."
                })
                break
        else:
            report["diagnose_items"].append({
                "category": "💾 SSD & Sürücü Daralmaları",
                "severity": "OK",
                "icon": "✅",
                "title": "Sürücü Hızları ve Boş Alan Sağlıklı",
                "detail": "Tüm disk bölümlerinizde önbellek yazma yükünü kaldıracak güvenli boş alan mevcuttur.",
                "prescription": "SSD takılmasız okuma-yazma operasyonlarına devam ediyor."
            })

        # --- 4. Termal Soğutma & Frekans Sağlığı ---
        cpu_temp = thermal.get("cpu_temp_c", 0.0)
        gpu_temp = thermal.get("gpu_temp_c", 0.0)
        max_temp = max(cpu_temp, gpu_temp)

        if max_temp >= 82.0:
            grade_points -= 15
            report["diagnose_items"].append({
                "category": "🔥 Termal Soğutma Verimi",
                "severity": "WARNING",
                "icon": "🌡️",
                "title": f"Yüksek Çalışma Sıcaklığı Saptandı ({max_temp}°C)",
                "detail": "İşlemci veya grafik kartınız uzun süreli yüksek hararet bandında seyrediyor.",
                "prescription": "Kasa fan devirlerini kontrol etmeniz, hava deliklerindeki toz kirliliğini silmeniz veya periyodik termal macun tazeliğini teyit etmeniz tavsiye edilir."
            })
        elif max_temp > 20.0:
            report["diagnose_items"].append({
                "category": "🔥 Termal Soğutma Verimi",
                "severity": "OK",
                "icon": "❄️",
                "title": f"Serin ve Dengeli Çalışma ({max_temp}°C)",
                "detail": "Sistem sıcaklıklarınız donanım koruma limitlerinin çok altında hararet yaratmadan atılıyor.",
                "prescription": "Soğutucu ve fan sistemleriniz gayet güçlü bir performans sergilemekte."
            })

        # --- Final Grade Calculation ---
        if grade_points >= 90:
            report["grade"] = "A+"
            report["overall_status"] = "💪 Mükemmel / Zirve Performans"
            report["summary_message"] = "Yapay zeka doktorumuz sisteminizi muhteşem buldu! Oyunlarda ve iş yaparken %100 tam güç verimi alıyorsunuz."
        elif grade_points >= 75:
            report["grade"] = "B+"
            report["overall_status"] = "✨ Gayet İyi / Küçük İyileştirmeler Açık"
            report["summary_message"] = "Sisteminiz dengeli çalışıyor. Sunulan reçetelerdeki ufak sekmeleri temize çekerek A+ performans seviyesine erişebilirsiniz."
        else:
            report["grade"] = "C"
            report["overall_status"] = "⚠️ Darboğaz İkazı / Bakım Önerilir"
            report["summary_message"] = "Bazı birimlerde aşırı RAM doluluğu veya ısınma kaynaklı potansiyel performans kısalmaları teşhis edildi."

        return report

# Global checkup instance
ai_doctor = AICheckupDoctor()
