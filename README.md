# 🎙 VaakSetu — English to Indian Language Voice Bridge

A Streamlit app that transcribes English audio (live mic or uploaded files) and translates it in real time into **Tamil, Hindi, Malayalam, Telugu, or Kannada** with scrolling timestamped output. Transcripts are downloadable as `.TXT` or `.SRT` subtitle files.

---

## Features

- 🎤 **Live microphone recording** via browser
- 📁 **File upload** — MP3, WAV, M4A, FLAC, OGG, WEBM
- 🔤 **5 Indian languages** — Tamil · Hindi · Malayalam · Telugu · Kannada
- 📜 **Scrolling timestamped transcript** with optional bilingual display
- ⬇ **Download** as plain text (`.txt`) or subtitle (`.srt`) format
- 🌑 Dark, minimal UI with no distractions

---

## Tech Stack

| Component | Library |
|-----------|---------|
| Speech-to-text | [OpenAI Whisper](https://github.com/openai/whisper) (`base` model) |
| Translation | [Helsinki-NLP MarianMT](https://huggingface.co/Helsinki-NLP) |
| UI | [Streamlit](https://streamlit.io) |

---

## Local Setup

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/vaaksetu.git
cd vaaksetu
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

> **ffmpeg** is also required for audio processing:
> - macOS: `brew install ffmpeg`
> - Ubuntu/Debian: `sudo apt install ffmpeg`
> - Windows: [Download from ffmpeg.org](https://ffmpeg.org/download.html)

### 3. Run the app

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Deploy on Streamlit Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Select this repo → set `app.py` as the main file
5. Click **Deploy**

> ⚠️ First load downloads the Whisper `base` model (~145 MB) and MarianMT models for the selected language. Subsequent loads use the cache.

### Streamlit Cloud `packages.txt`

Create a file `packages.txt` in the repo root (already included) to auto-install ffmpeg:

```
ffmpeg
```

---

## Translation Models Used

| Language | Helsinki-NLP Model |
|----------|--------------------|
| Tamil    | `opus-mt-en-ta`    |
| Hindi    | `opus-mt-en-hi`    |
| Malayalam | `opus-mt-en-ml`   |
| Telugu   | `opus-mt-en-te`    |
| Kannada  | `opus-mt-en-kn`    |

---

## Project Structure

```
vaaksetu/
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── packages.txt            # System packages (ffmpeg)
├── .streamlit/
│   └── config.toml         # Streamlit theme & server config
└── README.md
```

---

## License

MIT — free to use, modify, and distribute.
