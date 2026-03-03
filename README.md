# 🎙️ Guest Lecture Interpreter

Real-time multilingual lecture transcription and translation for students — powered by Claude AI (Anthropic).

## Features

- 🌐 **8 Indian Languages**: English, Tamil, Hindi, Telugu, Kannada, Malayalam, Marathi, Bengali
- 🤖 **AI-Powered**: Uses Claude claude-opus-4-5 for transcription + translation
- 📱 **Mobile-Friendly**: Students access via browser on any device
- 💬 **Q&A Mode**: Ask questions about the lecture content
- ⬇️ **Export**: Download full transcript and translation as .txt
- 🔄 **Scrolling Live Feed**: Latest segments shown first with timestamps

## Architecture

```
[Audio/Text Input]
       ↓
[Streamlit Web App]
       ↓
[Anthropic Claude API]
  · Transcription
  · Language Detection
  · Translation
       ↓
[Scrolling Text UI for Students]
```

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/lecture-interpreter.git
cd lecture-interpreter
pip install -r requirements.txt
```

### 2. Set API Key

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

Or enter it directly in the app sidebar.

### 3. Run Locally

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

### 4. Deploy on Streamlit Cloud (Free)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo → Deploy
4. Add `ANTHROPIC_API_KEY` in **Secrets** settings
5. Share the URL with your students 📱

## Usage

### For the Lecturer/Operator:
1. Open the app on a laptop/desktop
2. Enter Anthropic API key (sidebar)
3. Select lecturer's language and target translation language
4. **Option A**: Upload a recorded audio file (.wav/.mp3)
5. **Option B**: Paste spoken text and click Translate
6. Segments appear in real-time in both panes

### For Students:
1. Open the shared URL on their mobile browser
2. See live scrolling transcript (left) and translation (right)
3. Use the Q&A tab to ask questions about the lecture

## Languages Supported

| Language  | Code | Script |
|-----------|------|--------|
| English   | en   | Latin  |
| Tamil     | ta   | தமிழ்  |
| Hindi     | hi   | देवनागरी |
| Telugu    | te   | తెలుగు |
| Kannada   | kn   | ಕನ್ನಡ |
| Malayalam | ml   | മലയാളം |
| Marathi   | mr   | मराठी |
| Bengali   | bn   | বাংলা |

## Streamlit Cloud Secrets

In `Settings → Secrets`, add:

```toml
ANTHROPIC_API_KEY = "sk-ant-..."
```

## Tech Stack

- **Frontend/Backend**: [Streamlit](https://streamlit.io) (Python)
- **AI Model**: Anthropic Claude claude-opus-4-5
- **Audio Processing**: PyAudio / wave
- **Deployment**: Streamlit Community Cloud (free)

## Notes on Live Audio

Browser-based microphone capture requires HTTPS + server-side WebSocket support. For **fully live** streaming:
- Deploy on a server (e.g., Railway, Render, EC2)
- Use the `pyaudio` component for server-side mic capture
- Or use the text input mode for near-real-time operation

## License

MIT — Free for educational use.
