# 🎙️ Live Audio Translator

Real-time English speech transcription + translation into Indian languages,
powered by **Claude AI** (LLM) as the translation engine.

## Features
- 🎤 Live microphone capture (any format via PyAudio)
- 🗣️ English STT via Google Speech Recognition (free, CPU)
- 🤖 LLM translation via Claude (Tamil, Hindi, Telugu, Kannada, Malayalam)
- 📜 Scrolling live transcript with colour-coded bilingual display
- 📄 Downloadable PDF transcript
- 📋 Downloadable JSON with full Unicode native-script text

## Setup

### 1. Install system dependencies
```bash
# Ubuntu / Debian
sudo apt-get install -y portaudio19-dev python3-pyaudio

# macOS
brew install portaudio
```

### 2. Install Python packages
```bash
pip install -r requirements.txt
```

### 3. Run
```bash
streamlit run app.py
```

### 4. In the sidebar
- Paste your **Anthropic API key** (get one at console.anthropic.com)
- Choose your **target Indian language**
- Press **▶️ Start Recording**

## GitHub Deployment
Push all files to a GitHub repo. For cloud hosting (CPU-based), deploy to
**Streamlit Community Cloud** (https://streamlit.io/cloud) — free tier, CPU only,
connects directly to your GitHub repo.

## Architecture
```
Microphone
   │
   ▼ (PyAudio – 5-sec chunks)
SpeechRecognition (Google STT, free, CPU)
   │
   ▼ English text
Claude API (Anthropic LLM)  ← Translation engine
   │
   ▼ Native-script translation
Streamlit UI  →  Scrolling transcript
                  PDF / JSON download
```

## Notes
- PDF Indian-script rendering: FPDF uses latin-1 internally; non-latin chars
  appear as '?' in the PDF. Use the **JSON export** to get full native-script text,
  or open the PDF in a modern Unicode-capable viewer.
- The app is **CPU-only** — no GPU required.
- Translation quality is high-accuracy thanks to Claude's multilingual LLM capability.
