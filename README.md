# 🎬 VDL (Universal Video Downloader & Uzmovi TV) - V2.0

[https://github.com/drowgone/uzmovi_downloader](https://github.com/drowgone/uzmovi_downloader)

VDL - bu istalgan platformadan (YouTube, Instagram, Facebook, Uzmovi va boshqa 1000 dan ortiq saytlar) videolarni eng yuqori sifatda yuklab olish uchun mo'ljallangan terminal va brauzerga asoslangan kuchli vosita.

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Windows%20%7C%20Termux-green.svg)
![Language](https://img.shields.io/badge/language-Python%203-yellow.svg)

---

## ✨ Asosiy Imkoniyatlar (V2 Yangiliklari)

*   **🌐 Universal Qo'llab-quvvatlash**: YouTube, Instagram, FB, Uzmovi va boshqa deyarli hamma saytlardan video olish.
*   **📦 Avtomatik MP4**: Barcha yuklamalar avtomatik ravishda eng sifatli `.mp4` formatiga jamlanadi (FFmpeg yordamida).
*   **💻 To'liq Cross-Platform**: Linux (Gnome Terminal), Windows (CMD) va Termux tizimlarida bir xil mukammal ishlaydi.
*   **🧩 Chrome Integratsiyasi**: Brauzerda o'ng tugmani bosish orqali yuklashni boshlash (Native messaging host).
*   **📂 Batch Download**: Ko'plab havolalarni `.txt` faylidan o'qib, ketma-ket yuklash.
*   **⚡ Tezkorlik**: Ko'p oqimli (multi-threaded) yuklash va fragmentlarni jamlash.
*   **⏸️ Pauza va Davom ettirish**: Yuklashni xohlagan paytda to'xtatib, keyin davom ettirish (Linuxda).

---

## 🚀 O'rnatish va Ishga tushirish (Eng oson yo'li)

Loyihani o'rnatish va barcha kutubxonalarni sozlash uchun terminalda shunchaki quyidagi buyruqni bering:

```bash
python3 setup_vdl.py
```
Bu buyruq kutubxonalarni o'rnatadi, tizimga integratsiya qiladi va dasturni ishga tushiradi.

---

## 🚀 Manual O'rnatish (Qo'lda)

#### **Linux (Ubuntu/Debian):**
```bash
sudo apt update && sudo apt install python3 python3-pip ffmpeg -y
pip install rich questionary yt-dlp
```

#### **Windows:**
1. [Python](https://www.python.org/) va [FFmpeg](https://ffmpeg.org/download.html) o'rnating.
2. Terminalda:
```bash
pip install rich questionary yt-dlp
```

#### **Termux:**
```bash
pkg update && pkg install python ffmpeg -y
pip install rich questionary yt-dlp
```

---

## 🛠️ Sozlash (Global Buyruq)

Loyihani o'rnatganingizdan so'ng terminalda shunchaki `kino` deb yozish orqali ishga tushirish uchun:
1. `python3 uzmovi_dl.py` ni ishlating.
2. **Settings (Sozlamalar)** menyusiga kiring.
3. **Install** tugmasini bosing.

Bu avtomatik ravishda Linuxda symlink, Windowsda esa `.cmd` wrapper yaratadi.

---

## 🌐 Chrome Kengaytmasini Sozlash

1. Chrome'da `chrome://extensions/` ga kiring.
2. **Developer mode** ni yoqing.
3. **Load unpacked** tugmasini bosing va loyihadagi `vdl_extension` papkasini tanlang.
4. Kengaytma ID sini nusxalang.
5. `vdl_host/com.antigravity.vdl.json` faylini ochib, `PLACEHOLDER_ID` o'rniga ID ni qo'ying.
6. `kino` dasturi sozlamalaridan **Install** ni qayta bosing (Hostni ro'yxatga olish uchun).

---

## 📖 Foydalanish

### Interaktiv Menyuda:
```bash
kino
```

### To'g'ridan-to'g'ri URL orqali:
```bash
kino --url https://www.youtube.com/watch?v=...
```

### Yordam oynasi:
```bash
kino --help
```

---

## ⚠️ Eslatma
Dasturdan faqat shaxsiy maqsadlarda va mualliflik huquqlariga rioya qilgan holda foydalaning.

**Ishlab chiquvchi**: Antigravity AI
