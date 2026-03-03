import streamlit as st
import anthropic
import speech_recognition as sr
import threading
import queue
import time
import io
import wave
import json
from datetime import datetime
from fpdf import FPDF
import pyaudio

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Live Audio Translator",
    page_icon="🎙️",
    layout="wide"
)

# ── Styling ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif}

.hdr{
  background:linear-gradient(135deg,#667eea,#764ba2);
  padding:2rem;border-radius:16px;text-align:center;
  color:white;margin-bottom:1.5rem;
  box-shadow:0 8px 32px rgba(102,126,234,.3)
}
.hdr h1{font-size:2.4rem;margin:0;font-weight:700}
.hdr p{margin:.4rem 0 0;opacity:.9;font-size:1.05rem}

.tbox{
  background:#0f0f1a;border:1px solid #2d2d4e;border-radius:12px;
  padding:1.5rem;min-height:320px;max-height:420px;
  overflow-y:auto;line-height:1.9;color:#e8e8f0
}
.en{
  color:#7dd3fc;padding:.35rem .8rem;
  border-left:3px solid #3b82f6;
  background:rgba(59,130,246,.07);
  border-radius:0 6px 6px 0;margin-bottom:.3rem
}
.tr{
  color:#86efac;padding:.35rem .8rem;
  border-left:3px solid #22c55e;
  background:rgba(34,197,94,.07);
  border-radius:0 6px 6px 0;
  margin-bottom:.9rem;font-size:1.1rem
}
.rec{
  display:inline-flex;align-items:center;gap:8px;
  background:rgba(239,68,68,.15);border:1px solid rgba(239,68,68,.4);
  color:#f87171;padding:.45rem 1.2rem;border-radius:50px;
  font-weight:600;animation:pulse 1.5s infinite
}
.idle{
  display:inline-flex;align-items:center;gap:8px;
  background:rgba(100,116,139,.15);border:1px solid rgba(100,116,139,.3);
  color:#94a3b8;padding:.45rem 1.2rem;border-radius:50px;font-weight:600
}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.55}}
.ts{color:#6b7280;font-size:.74rem;margin-right:6px}
.badge{
  display:inline-block;
  background:linear-gradient(135deg,#667eea,#764ba2);
  color:white;padding:.25rem .9rem;border-radius:50px;
  font-weight:600;font-size:.9rem
}
</style>
""", unsafe_allow_html=True)

# ── Language Config ─────────────────────────────────────────────────────────────
LANGUAGES = {
    "Tamil (தமிழ்)":       "Tamil",
    "Hindi (हिंदी)":        "Hindi",
    "Telugu (తెలుగు)":      "Telugu",
    "Kannada (ಕನ್ನಡ)":     "Kannada",
    "Malayalam (മലയാളം)":  "Malayalam",
}

HINTS = {
    "Tamil":     "Use Tamil Unicode script (e.g. வணக்கம்).",
    "Hindi":     "Use Devanagari script (e.g. नमस्ते).",
    "Telugu":    "Use Telugu Unicode script (e.g. నమస్కారం).",
    "Kannada":   "Use Kannada Unicode script (e.g. ನಮಸ್ಕಾರ).",
    "Malayalam": "Use Malayalam Unicode script (e.g. നമസ്കാരം).",
}

# ── Session State ───────────────────────────────────────────────────────────────
def init():
    defaults = dict(
        recording=False,
        transcripts=[],
        audio_q=queue.Queue(),
        rec_thread=None,
        stop_ev=None,
        words=0, segs=0,
        api_key="",
    )
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init()

# ── Claude Translation ──────────────────────────────────────────────────────────
def translate(text: str, lang: str, api_key: str) -> str:
    """Use Claude (LLM) to translate English → target Indian language."""
    client = anthropic.Anthropic(api_key=api_key)
    prompt = (
        f"You are a professional translator specializing in Indian languages.\n"
        f"Translate the following English text to {lang}.\n"
        f"{HINTS.get(lang, '')}\n"
        f"Return ONLY the translated text in native script — "
        f"no explanations, no romanization.\n\n"
        f"English: {text}"
    )
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()

# ── Audio Recording Thread ──────────────────────────────────────────────────────
def record_loop(q: queue.Queue, stop: threading.Event):
    """Background thread: captures mic audio in 5-second chunks."""
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    CHUNK_SECS = 5

    p = pyaudio.PyAudio()
    try:
        stream = p.open(
            format=FORMAT, channels=CHANNELS, rate=RATE,
            input=True, frames_per_buffer=CHUNK
        )
        while not stop.is_set():
            frames = []
            for _ in range(int(RATE / CHUNK * CHUNK_SECS)):
                if stop.is_set():
                    break
                frames.append(stream.read(CHUNK, exception_on_overflow=False))
            if frames:
                q.put(frames)
        stream.stop_stream()
        stream.close()
    except Exception as e:
        q.put({"error": str(e)})
    finally:
        p.terminate()

# ── Speech-to-Text ──────────────────────────────────────────────────────────────
def stt(frames: list, rate: int = 16000) -> str | None:
    """Google Speech Recognition (free, CPU-based) — English only."""
    recognizer = sr.Recognizer()
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(b"".join(frames))
    buf.seek(0)
    with sr.AudioFile(buf) as source:
        audio = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio)
    except Exception:
        return None

# ── PDF Export ──────────────────────────────────────────────────────────────────
def make_pdf(transcripts: list, lang: str, incl_en: bool) -> bytes:
    pdf = FPDF()
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(80, 60, 160)
    pdf.cell(0, 12, "Live Audio Transcript & Translation", ln=True, align="C")

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(
        0, 7,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  |  Language: {lang}",
        ln=True, align="C"
    )
    pdf.ln(4)
    pdf.set_draw_color(180, 160, 220)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    for i, e in enumerate(transcripts, 1):
        # Segment header
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(160, 130, 200)
        pdf.cell(0, 6, f"Segment {i}  [{e.get('ts', '')}]", ln=True)

        if incl_en:
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(40, 100, 180)
            pdf.cell(0, 6, "English:", ln=True)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(30, 30, 30)
            pdf.multi_cell(0, 6, e.get("en", ""))
            pdf.ln(2)

        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(30, 140, 70)
        pdf.cell(0, 6, f"{lang} Translation:", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(30, 30, 30)
        # FPDF requires latin-1; non-latin chars shown as '?'
        raw = e.get("translated", "")
        safe = raw.encode("latin-1", errors="replace").decode("latin-1")
        pdf.multi_cell(0, 6, safe)
        pdf.ln(4)

        pdf.set_draw_color(220, 215, 235)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)

    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.multi_cell(
        0, 5,
        "NOTE: Indian script characters require a Unicode-capable PDF viewer. "
        "Use the JSON export to preserve full native-script text."
    )
    return pdf.output(dest="S").encode("latin-1")

# ═══════════════════════ UI ═══════════════════════════════════════════════════════

st.markdown(
    '<div class="hdr">'
    '<h1>🎙️ Live Audio Translator</h1>'
    '<p>Real-time English speech → Indian Language Translation &nbsp;|&nbsp; Powered by Claude AI</p>'
    '</div>',
    unsafe_allow_html=True,
)

# ── Sidebar ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    st.markdown("---")

    key_in = st.text_input(
        "🔑 Anthropic API Key",
        type="password",
        value=st.session_state.api_key,
        placeholder="sk-ant-...",
    )
    if key_in:
        st.session_state.api_key = key_in

    st.markdown("---")
    st.markdown("### 🌐 Target Language")
    lbl  = st.selectbox("Translate to:", list(LANGUAGES.keys()))
    lang = LANGUAGES[lbl]
    st.markdown(f'<span class="badge">→ {lang}</span>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📄 PDF Options")
    incl_en = st.checkbox("Include English transcription", value=True)
    incl_tr = st.checkbox("Include translation", value=True)

    st.markdown("---")
    st.markdown("### 📊 Session Stats")
    c1, c2 = st.columns(2)
    c1.metric("Segments", st.session_state.segs)
    c2.metric("Words",    st.session_state.words)

    st.markdown("---")
    if st.button("🗑️ Clear All"):
        st.session_state.transcripts = []
        st.session_state.segs = 0
        st.session_state.words = 0
        st.rerun()

# ── Main Columns ─────────────────────────────────────────────────────────────────
L, R = st.columns([2, 1])

with L:
    st.markdown("### 📜 Live Transcript & Translation")

    if st.session_state.recording:
        st.markdown('<div class="rec">🔴 &nbsp;Recording &amp; Translating…</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<div class="idle">⚪ &nbsp;Idle — press Start to begin</div>',
                    unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Scrolling transcript
    html = '<div class="tbox">'
    if not st.session_state.transcripts:
        html += '<span style="color:#4b5563;font-style:italic">Transcript will appear here as you speak…</span>'
    else:
        for e in st.session_state.transcripts:
            ts = e.get("ts", "")
            if incl_en:
                html += f'<div class="en"><span class="ts">{ts}</span>🇬🇧 {e["en"]}</div>'
            if incl_tr:
                html += f'<div class="tr">🌐 {e["translated"]}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

with R:
    st.markdown("### 🎛️ Controls")
    st.markdown("<br>", unsafe_allow_html=True)

    api_ok = bool(st.session_state.api_key)
    if not api_ok:
        st.warning("⚠️ Enter your Anthropic API key in the sidebar.")

    if not st.session_state.recording:
        if st.button("▶️ Start Recording", disabled=not api_ok, use_container_width=True):
            st.session_state.recording = True
            st.session_state.stop_ev  = threading.Event()
            st.rerun()
    else:
        if st.button("⏹️ Stop Recording", use_container_width=True):
            st.session_state.recording = False
            if st.session_state.stop_ev:
                st.session_state.stop_ev.set()
            st.rerun()

    st.markdown("---")
    st.markdown("### 📥 Download")

    if st.session_state.transcripts:
        pdf_bytes = make_pdf(st.session_state.transcripts, lang, incl_en)
        st.download_button(
            "📄 Download PDF",
            data=pdf_bytes,
            file_name=f"transcript_{lang.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
        json_bytes = json.dumps(
            st.session_state.transcripts, ensure_ascii=False, indent=2
        ).encode("utf-8")
        st.download_button(
            "📋 Download JSON (full Unicode)",
            data=json_bytes,
            file_name=f"transcript_{lang.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True,
        )
    else:
        st.info("Start recording to enable downloads.")

    st.markdown("---")
    st.markdown("""
**How it works**
1. 🎤 Mic captures 5-sec audio chunks
2. 🗣️ Google STT → English text (free, CPU)
3. 🤖 Claude LLM translates to your language
4. 📜 Scrolling transcript updates live
5. 📄 Download as PDF or JSON anytime
    """)

# ── Recording Polling Loop ───────────────────────────────────────────────────────
if st.session_state.recording:
    # Start background thread if needed
    if (
        st.session_state.rec_thread is None
        or not st.session_state.rec_thread.is_alive()
    ):
        t = threading.Thread(
            target=record_loop,
            args=(st.session_state.audio_q, st.session_state.stop_ev),
            daemon=True,
        )
        t.start()
        st.session_state.rec_thread = t

    # Process one queued audio chunk per Streamlit rerun
    try:
        frames = st.session_state.audio_q.get_nowait()
        if isinstance(frames, dict) and "error" in frames:
            st.error(f"Microphone error: {frames['error']}")
            st.session_state.recording = False
        else:
            en_text = stt(frames)
            if en_text:
                with st.spinner(f"Translating to {lang}…"):
                    translated = translate(en_text, lang, st.session_state.api_key)
                st.session_state.transcripts.append({
                    "en":         en_text,
                    "translated": translated,
                    "ts":         datetime.now().strftime("%H:%M:%S"),
                })
                st.session_state.segs  += 1
                st.session_state.words += len(en_text.split())
    except queue.Empty:
        pass

    time.sleep(0.4)
    st.rerun()
```

---

### `requirements.txt`
```
streamlit>=1.35.0
anthropic>=0.28.0
SpeechRecognition>=3.10.0
pyaudio>=0.2.14
fpdf2>=2.7.9
