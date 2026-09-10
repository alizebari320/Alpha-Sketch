<div align="center">

# Alpha-Sketch 🎨

**Upload one image → get an AI-narrated sketch video. No prompts, no typing.**

[English](#english) · [العربية](#العربية) · [کوردیی سۆرانی](#کوردیی-سۆرانی) · [کوردیی بادینی](#کوردیی-بادینی)

FastAPI · OpenCV · Gemini Vision · edge-tts · PIL + ffmpeg — **100% local rendering**

</div>

---

<a name="english"></a>

## 🇬🇧 English

**Alpha-Sketch** turns any photo into a short video: it converts the image into 4
sketch styles (pencil, color pencil, cartoon, blueprint), writes a narration
script about what it *sees* in the image, records a voiceover, and renders
karaoke-captioned videos ready for Reels/TikTok (9:16) and YouTube (16:9).

### ✨ Features
- 🖼️ **Image-only input** — drop a photo, that's all. No prompts.
- ✏️ **4 sketch styles** — pencil, color pencil, cartoon, blueprint (pure OpenCV, no GPU)
- 🧠 **AI scriptwriter** — Gemini *looks at your image* and writes the narration; offline fallback included
- 🔊 **Neural voiceover** — edge-tts voices with word-level timing
- 🎤 **Karaoke captions** — the spoken word lights up in neon pink
- 🌐 **3 languages** — English, Arabic (voice + RTL captions), Kurdish Sorani (RTL captions)
- 📱 **Dual format** — 9:16 and 16:9 MP4s in one run
- 💻 **Local-first** — everything renders on your machine

### 🚀 Quick start
```bash
pip install -r requirements.txt
uvicorn app.main:app --port 8901
# open http://localhost:8901 and drop an image
```

Optional — enable Gemini scripts (free key: https://aistudio.google.com/apikey):
```bash
export GEMINI_API_KEY=your_key    # or put it in .gemini_key
```

### 🔌 API
| Endpoint | What it does |
|---|---|
| `POST /api/generate` | multipart: `image`, `lang` (`en`/`ar`/`ku`) → `job_id` |
| `GET /api/status/{id}` | progress %, stage, title, scenes |
| `GET /api/video/{id}/{vertical\|landscape}` | rendered MP4 |
| `GET /api/sketch/{id}/{style}` | still sketch preview |

### 📁 Layout
```
app/
  main.py      FastAPI server, background jobs
  pipeline.py  end-to-end orchestration
  sketch.py    OpenCV sketch styles
  script.py    Gemini vision script + offline fallback
  tts.py       edge-tts voiceover + word timings
  render.py    PIL frame renderer + ffmpeg pipe
static/
  index.html   upload UI, progress, preview, downloads
```

---

<a name="العربية"></a>

## 🇸🇦 العربية

**Alpha-Sketch** يحوّل أي صورة إلى فيديو قصير: يحوّل الصورة إلى ٤ أنماط رسم
تخطيطي (قلم رصاص، ألوان، كرتون، مخطط هندسي)، يكتب نصًا للتعليق الصوتي عمّا
يراه في الصورة فعلًا، يسجّل الصوت، وينتج فيديوهات بترجمة كاريوكي جاهزة
لإنستغرام وتيك توك (9:16) ويوتيوب (16:9).

### ✨ المزايا
- 🖼️ **الإدخال صورة فقط** — أسقط صورتك، هذا كل شيء. بلا كتابة.
- ✏️ **٤ أنماط رسم** — قلم رصاص، ألوان، كرتون، مخطط هندسي (OpenCV بلا كرت شاشة)
- 🧠 **كاتب سيناريو ذكي** — Gemini ينظر إلى صورتك ويكتب التعليق؛ مع وضع احتياطي يعمل بدون إنترنت
- 🔊 **صوت عصبي** — أصوات edge-tts بتوقيت دقيق لكل كلمة
- 🎤 **ترجمة كاريوكي** — الكلمة المنطوقة تتوهّج بالوردي
- 🌐 **اللغات** — العربية (صوت + ترجمة من اليمين)، الإنجليزية، الكردية
- 📱 **صيغتان** — 9:16 و 16:9 في تشغيل واحد
- 💻 **محليّ بالكامل** — كل شيء يُنتج على جهازك

### 🚀 التشغيل
```bash
pip install -r requirements.txt
uvicorn app.main:app --port 8901
# افتح http://localhost:8901 وأسقط صورتك
```

---

<a name="کوردیی-سۆرانی"></a>

## 🇹🇯 کوردیی سۆرانی

**Alpha-Sketch** هەر وێنەیەک دەکات بە ڤیدیۆیەکی کورت: وێنەکە دەگۆڕێت بۆ
چوار شێوازی خەتکاری (خەتکار، خەتکاری ڕەنگاوڕەنگ، کارتۆن، پلانی ئەندازیاری)،
نووسینێک دەنووسرێت دەربارەی ئەوەی AI بەرچاوی دەکەوێت لە وێنەکە، دەنگ تۆمار
دەکرێت، و ڤیدیۆکان لەگەڵ ژێرنووسی کاریۆکی ئامادە دەبن بۆ ئینستاگرام و
تیکتۆک (9:16) و یوتیوب (16:9).

### ✨ تایبەتمەندییەکان
- 🖼️ **تەنها وێنە** — وێنەیەک فڕێ بدە، ئەوە هەموویەتی. بەبێ نووسین.
- ✏️ **چوار شێوازی خەتکاری** — خەتکار، ڕەنگاوڕەنگ، کارتۆن، بلوپرینت (بە OpenCV، بەبێ GPU)
- 🧠 **نووسەری سیناریۆی AI** — Gemini سەیری وێنەکە دەکات و نووسینەکە دەنووسێت؛ فۆلباکی ئۆفلاین هەیە
- 🔊 **دەنگی نیۆڕاڵ** — دەنگەکانی edge-tts بە کاتی وردی هەموو ووشەیەک
- 🎤 **ژێرنووسی کاریۆکی** — ووشەی خوێندراوە بە پەمەیی دەدرەوشێتەوە
- 🌐 **زمانەکان** — سۆرانی (ژێرنووسی RTL)، عەرەبی (دەنگ + RTL)، ئینگلیزی
- 📱 **دوو فۆرمات** — 9:16 و 16:9 لە یەک جاردا
- 💻 **١٠٠٪ ناوخۆیی** — هەموو شتێک لەسەر کۆمپیوتەرەکەت دروست دەکرێت

### 🚀 دەستپێکردن
```bash
pip install -r requirements.txt
uvicorn app.main:app --port 8901
# http://localhost:8901 بکەرەوە و وێنەیەک فڕێ بدە
```

---

<a name="کوردیی-بادینی"></a>

## 🇹🇯 کوردیی بادینی

**Alpha-Sketch** هەر وێنەیەک دگۆڕێت بۆ ڤیدیۆیەکی کورت: وێنەکە دبنێت
چوار شێوازی هەڵکێشان (خەتکاری، خەتکاری رەنگاوڕەنگ، کارتۆن، پلانی
ئەندازیاری)، نڤیسینێک دنڤیسریت سەرباری ئەوەی AI دبینێت لە وێنەکێ، دەنگ
تۆمار دکەت، و ڤیدیۆکان ب ژێرنڤیسا کاریۆکی ئاماده‌ دبن بۆ ئینستاگرام و
تیکتۆک (9:16) و یوتیوب (16:9).

### ✨ تایبەتمەندییەن
- 🖼️ **تەنها وێنە** — وێنەیەک باڕکە، ئەڤە هەموویە. بێ نڤیسین.
- ✏️ **چوار شێوازێ هەڵکێشانێ** — خەتکار، رەنگاوڕەنگ، کارتۆن، بلوپرینت (OpenCV، بێ GPU)
- 🧠 **نڤیسەری سیناریۆیێ AI** — Gemini سەیری وێنەکێ دکەت و نڤیسینێ دنڤیسێت؛ فۆلباکی ئۆفلاین هەیە
- 🔊 **دەنگێ نێۆڕاڵ** — دەنگێن edge-tts ب کاتێ وری هەر وشەیەکێ
- 🎤 **ژێرنڤیسا کاریۆکی** — وشەیا خێندراوی ب پەمەیی ڕۆن دبێت
- 🌐 **زمانێن** — بادینی و سۆرانی (ژێرنڤیسا RTL)، عەرەبی (دەنگ + RTL)، ئینگلیزی
- 📱 **دوو فۆرمات** — 9:16 و 16:9 ل یەک کارێ
- 💻 **١٠٠٪ ناوخۆیی** — هەر شتێ ل سەر کۆمپیوتەرا تێ دروست دکریت

### 🚀 دەستپێک
```bash
pip install -r requirements.txt
uvicorn app.main:app --port 8901
# http://localhost:8901 ڤەکە و وێنەیەک باڕکە
```

---

<div align="center">

**Made by [alizebari320](https://github.com/alizebari320)** · MIT License

</div>
