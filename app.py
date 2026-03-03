import streamlit as st
import anthropic
import os
import tempfile
from datetime import datetime
from pathlib import Path

# ── PAGE SETUP ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Lecture Interpreter",
    page_icon="🎙️",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── STYLING ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background-color: #0f172a !important;
    color: #f1f5f9 !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stSidebar"]  { background-color: #1e293b !important; }
[data-testid="stHeader"]   { background: transparent !important; }
h1,h2,h3                   { color: #f1f5f9 !important; }

.big-title   { font-size:2rem; font-weight:700; color:#38bdf8; margin-bottom:4px; }
.subtitle    { color:#94a3b8; font-size:.95rem; margin-bottom:20px; }
.lang-label  { color:#94a3b8; font-size:.78rem; text-transform:uppercase;
               letter-spacing:.08em; font-weight:600; margin-bottom:5px; }
.lang-from   { background:#166534; color:#4ade80; border:1px solid #15803d;
               border-radius:8px; padding:8px 18px; font-weight:700; font-size:1rem; }
.arrow-txt   { font-size:1.6rem; color:#38bdf8; font-weight:700; }

/* Panels */
.panel-en {
    background:#1e293b; border:1px solid #334155; border-left:4px solid #4ade80;
    border-radius:10px; padding:14px 18px; margin-bottom:14px;
}
.panel-tr {
    background:#0c1a3a; border:1px solid #1e40af; border-left:4px solid #38bdf8;
    border-radius:10px; padding:14px 18px; margin-bottom:14px;
}
.panel-head { font-size:.72rem; text-transform:uppercase; letter-spacing:.08em;
              font-weight:700; margin-bottom:8px; }
.panel-head.en { color:#4ade80; }
.panel-head.tr { color:#38bdf8; }
.seg-time  { font-size:.68rem; color:#64748b; font-family:monospace; margin-bottom:4px; }
.seg-en    { font-size:1rem; color:#e2e8f0; line-height:1.65; }
.seg-tr    { font-size:1.05rem; color:#93c5fd; line-height:1.75; }

/* Status */
.ok-badge  { display:inline-flex; align-items:center; gap:6px;
             background:#14532d; color:#4ade80; border:1px solid #166534;
             border-radius:20px; padding:4px 12px; font-size:.78rem; font-weight:600; }
.err-badge { display:inline-flex; align-items:center; gap:6px;
             background:#451a03; color:#fb923c; border:1px solid #7c2d12;
             border-radius:20px; padding:4px 12px; font-size:.78rem; font-weight:600; }
.dot { width:8px; height:8px; background:#4ade80; border-radius:50%;
       display:inline-block; animation:blink 1.2s ease-in-out infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }

/* Audio progress */
.audio-step {
    background:#1e293b; border:1px solid #334155; border-radius:10px;
    padding:14px 18px; margin-bottom:10px;
}
.step-num {
    display:inline-flex; align-items:center; justify-content:center;
    width:26px; height:26px; border-radius:50%; background:#1d4ed8;
    color:#fff; font-size:.8rem; font-weight:700; margin-right:10px;
}
.step-label { font-size:.95rem; font-weight:600; color:#e2e8f0; }
.step-done  { color:#4ade80; }
.step-wait  { color:#64748b; }

/* Widget overrides */
div[data-testid="stTextArea"] textarea {
    background:#1e293b !important; color:#f1f5f9 !important;
    border:1px solid #334155 !important; border-radius:8px !important; font-size:1rem !important;
}
div[data-testid="stSelectbox"]>div>div {
    background:#1e293b !important; color:#f1f5f9 !important; border:1px solid #334155 !important;
}
div[data-testid="stButton"]>button {
    font-family:'Inter',sans-serif !important; font-weight:700 !important;
    font-size:1rem !important; border-radius:8px !important; padding:10px 20px !important;
}
div[data-testid="stButton"]>button[kind="primary"] {
    background:linear-gradient(135deg,#1d4ed8,#0369a1) !important;
    color:white !important; border:none !important;
}
div[data-testid="stTextInput"] input {
    background:#1e293b !important; color:#f1f5f9 !important; border:1px solid #334155 !important;
}
.stTabs [data-baseweb="tab-list"] { background:#1e293b !important; border-radius:8px !important; padding:4px !important; }
.stTabs [data-baseweb="tab"]      { color:#94a3b8 !important; font-weight:600 !important; }
.stTabs [aria-selected="true"]    { background:#0f172a !important; color:#38bdf8 !important; border-radius:6px !important; }
div[data-testid="stFileUploader"] {
    background:#1e293b !important; border:2px dashed #334155 !important; border-radius:10px !important;
}
</style>
""", unsafe_allow_html=True)

# ── LANGUAGE MAP ──────────────────────────────────────────────────────────────
LANGUAGES = {
    "Tamil":     "தமிழ்",
    "Hindi":     "हिंदी",
    "Telugu":    "తెలుగు",
    "Kannada":   "ಕನ್ನಡ",
    "Malayalam": "മലയാളം",
    "Marathi":   "मराठी",
    "Bengali":   "বাংলা",
}
LANG_LIST = list(LANGUAGES.keys())

# ── SESSION STATE ─────────────────────────────────────────────────────────────
for k, v in {
    "segments":    [],
    "target_lang": "Tamil",
    "api_key":     "",
    "qna_answer":  "",
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── HELPERS ───────────────────────────────────────────────────────────────────
def get_api_key():
    return st.session_state.api_key or os.environ.get("ANTHROPIC_API_KEY", "")


def transcribe_audio(file_bytes: bytes, suffix: str) -> tuple[str, str | None]:
    """
    Transcribe audio using OpenAI Whisper (CPU, runs locally on server).
    Returns (transcript_text, error_or_None).
    """
    try:
        import whisper
    except ImportError:
        return "", "whisper_not_installed"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        model = whisper.load_model("base")   # ~150 MB, CPU-friendly
        result = model.transcribe(tmp_path, language="en")
        transcript = result["text"].strip()
        return transcript, None
    except Exception as e:
        return "", str(e)
    finally:
        try:
            os.unlink(tmp_path)
        except:
            pass


def do_translate(english_text: str, target_lang: str) -> tuple[str, str | None]:
    """Translate English → target_lang using Claude. Returns (translation, error)."""
    key = get_api_key()
    if not key:
        return "", "NO_KEY"
    try:
        client = anthropic.Anthropic(api_key=key)
        native = LANGUAGES[target_lang]
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=(
                f"You are an expert academic translator. "
                f"Translate the English text the user provides into {target_lang} ({native}). "
                f"Return ONLY the translated text — no explanation, no English, no extra lines."
            ),
            messages=[{"role": "user", "content": english_text}],
        )
        return resp.content[0].text.strip(), None
    except anthropic.AuthenticationError:
        return "", "BAD_KEY"
    except Exception as e:
        return "", str(e)


def do_qna(question: str, context: str, answer_lang: str) -> str:
    key = get_api_key()
    if not key:
        return "No API key set."
    try:
        client = anthropic.Anthropic(api_key=key)
        native = LANGUAGES.get(answer_lang, answer_lang)
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            system=(
                f"You are a helpful teaching assistant. "
                f"Answer the student's question based on the lecture transcript. "
                f"Respond in {answer_lang} ({native}). Be clear and concise."
            ),
            messages=[{"role": "user", "content":
                f"Lecture transcript:\n{context}\n\nStudent question: {question}"}],
        )
        return resp.content[0].text.strip()
    except Exception as e:
        return f"Error: {e}"


def add_segment(english: str, translation: str, lang: str):
    st.session_state.segments.append({
        "ts":          datetime.now().strftime("%H:%M:%S"),
        "english":     english,
        "translation": translation,
        "lang":        lang,
        "native":      LANGUAGES[lang],
    })


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔑 Anthropic API Key")
    st.markdown("Get yours free at [console.anthropic.com](https://console.anthropic.com)")
    key_val = st.text_input("Key", type="password",
        value=st.session_state.api_key, placeholder="sk-ant-api03-...",
        label_visibility="collapsed")
    if key_val != st.session_state.api_key:
        st.session_state.api_key = key_val

    if get_api_key():
        st.markdown('<div class="ok-badge"><span class="dot"></span> Key active</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="err-badge">⚠️ Enter API key above</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📊 Stats")
    st.metric("Segments", len(st.session_state.segments))
    st.metric("Words processed", sum(len(s["english"].split()) for s in st.session_state.segments))
    st.markdown("---")
    if st.button("🗑️ Clear all", use_container_width=True):
        st.session_state.segments   = []
        st.session_state.qna_answer = ""
        st.rerun()


# ── MAIN UI ───────────────────────────────────────────────────────────────────
st.markdown('<div class="big-title">🎙️ Guest Lecture Interpreter</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Upload audio or type English text → instant translation to your language</div>', unsafe_allow_html=True)

# ── LANGUAGE SELECTOR ─────────────────────────────────────────────────────────
st.markdown("### 🌐 Your Language")
c1, c2, c3 = st.columns([3, 1, 4])
with c1:
    st.markdown('<div class="lang-label">Lecture language</div>', unsafe_allow_html=True)
    st.markdown('<div class="lang-from">🇬🇧 English</div>', unsafe_allow_html=True)
with c2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="arrow-txt" style="text-align:center">→</div>', unsafe_allow_html=True)
with c3:
    st.markdown('<div class="lang-label">Translate to</div>', unsafe_allow_html=True)
    sel = st.selectbox("lang", LANG_LIST,
        index=LANG_LIST.index(st.session_state.target_lang),
        format_func=lambda l: f"{l}  —  {LANGUAGES[l]}",
        label_visibility="collapsed", key="lang_sel")
    if sel != st.session_state.target_lang:
        st.session_state.target_lang = sel
        st.rerun()

target_lang   = st.session_state.target_lang
target_native = LANGUAGES[target_lang]
st.info(f"✅  **English  →  {target_lang} ({target_native})**   ·   Change the dropdown above to switch.")
st.markdown("---")

# ── TABS ──────────────────────────────────────────────────────────────────────
tab_audio, tab_text, tab_qna = st.tabs(["🎵  Upload Audio", "✍️  Type / Paste Text", "❓  Ask About Lecture"])


# ═══════════════════════════════════════════════════════════════════════════════
#  TAB 1 — AUDIO UPLOAD
# ═══════════════════════════════════════════════════════════════════════════════
with tab_audio:
    st.markdown(f"**Upload a recorded lecture audio file. It will be transcribed to English text, then translated to {target_lang}.**")

    # How-it-works steps
    st.markdown("""
    <div class="audio-step">
      <span class="step-num">1</span><span class="step-label">Upload your audio file (.mp3 / .wav / .m4a / .ogg / .flac)</span>
    </div>
    <div class="audio-step">
      <span class="step-num">2</span><span class="step-label">Click <b>Transcribe &amp; Translate</b></span>
    </div>
    <div class="audio-step">
      <span class="step-num">3</span><span class="step-label">See English transcript + translation side by side below</span>
    </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Upload audio",
        type=["mp3", "wav", "m4a", "ogg", "flac", "webm"],
        label_visibility="collapsed",
        key="audio_uploader",
    )

    if uploaded:
        # Show player
        st.audio(uploaded, format=f"audio/{uploaded.name.split('.')[-1]}")
        st.markdown(f"**File:** `{uploaded.name}`  ·  **Size:** {uploaded.size / 1024:.1f} KB")

        if not get_api_key():
            st.error("⚠️ Enter your Anthropic API key in the sidebar before processing.")
        else:
            if st.button("🚀  Transcribe & Translate", type="primary", use_container_width=True, key="audio_btn"):
                audio_bytes = uploaded.read()
                suffix = "." + uploaded.name.split(".")[-1].lower()

                # ── STEP 1: Transcribe ────────────────────────────────────────
                with st.status("🔊 Step 1 — Transcribing audio with Whisper…", expanded=True) as status:
                    st.write("Loading Whisper model (first run downloads ~150 MB)…")
                    transcript, err = transcribe_audio(audio_bytes, suffix)

                    if err == "whisper_not_installed":
                        status.update(label="⚠️ Whisper not available", state="error")
                        st.error(
                            "The `openai-whisper` package is not installed on this server.\n\n"
                            "**To fix:** Add `openai-whisper` and `ffmpeg-python` to `requirements.txt` "
                            "and redeploy, OR use the **Type / Paste Text** tab to manually enter the lecture text."
                        )
                        st.stop()
                    elif err:
                        status.update(label="❌ Transcription failed", state="error")
                        st.error(f"Whisper error: {err}")
                        st.stop()
                    elif not transcript:
                        status.update(label="⚠️ No speech detected", state="error")
                        st.warning("No speech was detected in the audio. Please check the file.")
                        st.stop()
                    else:
                        status.update(label="✅ Transcription complete!", state="complete")
                        st.success(f"Transcribed {len(transcript.split())} words.")

                # Show transcript so user can review / edit
                st.markdown("#### 📝 Transcribed English Text")
                st.markdown("> *(You can review this — it will be translated below)*")
                edited_transcript = st.text_area(
                    "Transcript (editable)",
                    value=transcript,
                    height=160,
                    key="audio_transcript_edit",
                    label_visibility="collapsed",
                )

                # ── STEP 2: Split into ~200-word chunks & translate ───────────
                with st.status(f"🌐 Step 2 — Translating to {target_lang}…", expanded=True) as status2:
                    words = edited_transcript.split()
                    chunk_size = 200
                    chunks = [
                        " ".join(words[i : i + chunk_size])
                        for i in range(0, len(words), chunk_size)
                    ]
                    total = len(chunks)
                    prog = st.progress(0)
                    all_ok = True

                    for idx, chunk in enumerate(chunks):
                        chunk = chunk.strip()
                        if not chunk:
                            continue
                        st.write(f"Translating chunk {idx + 1}/{total}…")
                        translation, terr = do_translate(chunk, target_lang)
                        if terr:
                            status2.update(label=f"❌ Translation error on chunk {idx+1}", state="error")
                            st.error(f"Error: {terr}")
                            all_ok = False
                            break
                        add_segment(chunk, translation, target_lang)
                        prog.progress((idx + 1) / total)

                    if all_ok:
                        status2.update(label=f"✅ Translated {total} chunk(s) to {target_lang}!", state="complete")

                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
#  TAB 2 — TYPE / PASTE TEXT
# ═══════════════════════════════════════════════════════════════════════════════
with tab_text:
    st.markdown("**Type or paste the English lecture text, then click Translate.**")

    text_in = st.text_area(
        "English text",
        height=150,
        placeholder="Paste or type English lecture content here…\n\nExample: Today we study the fundamentals of machine learning. A model learns patterns from data.",
        label_visibility="collapsed",
        key="text_input_main",
    )

    if not get_api_key():
        st.error("⚠️ Enter your Anthropic API key in the sidebar.")

    if st.button(f"🌐  Translate  →  {target_lang} ({target_native})",
                 type="primary", use_container_width=True, key="text_btn"):
        t = text_in.strip()
        if not t:
            st.warning("Please enter some English text first.")
        elif not get_api_key():
            st.error("Enter API key in the sidebar.")
        else:
            with st.spinner(f"Translating to {target_lang}…"):
                tr, err = do_translate(t, target_lang)
            if err == "NO_KEY":
                st.error("No API key — open the sidebar.")
            elif err == "BAD_KEY":
                st.error("Invalid API key — check at console.anthropic.com")
            elif err:
                st.error(f"Error: {err}")
            else:
                add_segment(t, tr, target_lang)
                st.success(f"✅ Translated to {target_lang}!")
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
#  TAB 3 — Q&A
# ═══════════════════════════════════════════════════════════════════════════════
with tab_qna:
    if not st.session_state.segments:
        st.info("📭 No lecture content yet. Upload audio or paste text first.")
    else:
        ctx = " ".join(s["english"] for s in st.session_state.segments)
        st.markdown(f"Ask anything about the lecture. Answer comes in **{target_lang} ({target_native})**.")
        q = st.text_input("Question", placeholder="e.g. What is the main topic of this lecture?",
                          label_visibility="collapsed", key="qna_input")
        if st.button("💬 Get Answer", type="primary", use_container_width=True, key="qna_btn"):
            if q.strip():
                with st.spinner("Thinking…"):
                    st.session_state.qna_answer = do_qna(q.strip(), ctx, target_lang)
        if st.session_state.qna_answer:
            st.markdown(f"""
            <div style="background:#0c1a3a;border-left:4px solid #38bdf8;border-radius:0 8px 8px 0;
                        padding:14px 18px;margin-top:12px;font-size:1rem;line-height:1.7;color:#93c5fd;">
              {st.session_state.qna_answer}
            </div>""", unsafe_allow_html=True)

st.markdown("---")

# ── LIVE TRANSCRIPT + TRANSLATION ─────────────────────────────────────────────
st.markdown(f"### 📜 Transcript  &  {target_lang} Translation")

if not st.session_state.segments:
    st.markdown("""
    <div style="text-align:center;padding:40px 20px;background:#1e293b;
                border-radius:12px;color:#64748b;">
      <div style="font-size:2.5rem;margin-bottom:8px;">🎙️</div>
      <div style="font-size:1rem;font-weight:600;color:#94a3b8;">No segments yet</div>
      <div style="font-size:.85rem;margin-top:6px;">
        Upload an audio file or paste English text above to get started
      </div>
    </div>""", unsafe_allow_html=True)
else:
    for seg in reversed(st.session_state.segments):
        col_l, col_r = st.columns(2, gap="medium")
        with col_l:
            st.markdown(f"""
            <div class="panel-en">
              <div class="panel-head en">🇬🇧 English</div>
              <div class="seg-time">{seg['ts']}</div>
              <div class="seg-en">{seg['english']}</div>
            </div>""", unsafe_allow_html=True)
        with col_r:
            st.markdown(f"""
            <div class="panel-tr">
              <div class="panel-head tr">🇮🇳 {seg['lang']} ({seg['native']})</div>
              <div class="seg-time">{seg['ts']}</div>
              <div class="seg-tr">{seg['translation']}</div>
            </div>""", unsafe_allow_html=True)

    # ── DOWNLOAD ──────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### ⬇️ Download")
    d1, d2 = st.columns(2)
    with d1:
        en_out = "\n\n".join(f"[{s['ts']}]\n{s['english']}" for s in st.session_state.segments)
        st.download_button("📄 English Transcript (.txt)", en_out,
            file_name=f"transcript_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain", use_container_width=True)
    with d2:
        tr_out = "\n\n".join(f"[{s['ts']}] {s['lang']}\n{s['translation']}" for s in st.session_state.segments)
        st.download_button(f"📄 {target_lang} Translation (.txt)", tr_out,
            file_name=f"{target_lang}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain", use_container_width=True)

st.markdown("""
<div style="text-align:center;color:#334155;font-size:.8rem;padding:16px 0;">
  Deploy on Streamlit Cloud · Share URL with students · Each picks their own language 📱
</div>""", unsafe_allow_html=True)
