import warnings
import streamlit as st
import anthropic
import os
import tempfile
from datetime import datetime

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
h1, h2, h3                 { color: #f1f5f9 !important; }

.big-title  { font-size: 2rem; font-weight: 700; color: #38bdf8; margin-bottom: 4px; }
.subtitle   { color: #94a3b8; font-size: .95rem; margin-bottom: 20px; }
.lang-label { color: #94a3b8; font-size: .78rem; text-transform: uppercase;
              letter-spacing: .08em; font-weight: 600; margin-bottom: 5px; }
.lang-from  { background: #166534; color: #4ade80; border: 1px solid #15803d;
              border-radius: 8px; padding: 8px 18px; font-weight: 700; font-size: 1rem; display:inline-block; }
.arrow-txt  { font-size: 1.6rem; color: #38bdf8; font-weight: 700; }

.panel-en {
    background: #1e293b; border: 1px solid #334155; border-left: 4px solid #4ade80;
    border-radius: 10px; padding: 14px 18px; margin-bottom: 14px;
}
.panel-tr {
    background: #0c1a3a; border: 1px solid #1e40af; border-left: 4px solid #38bdf8;
    border-radius: 10px; padding: 14px 18px; margin-bottom: 14px;
}
.panel-head     { font-size: .72rem; text-transform: uppercase; letter-spacing: .08em;
                  font-weight: 700; margin-bottom: 8px; }
.panel-head.en  { color: #4ade80; }
.panel-head.tr  { color: #38bdf8; }
.seg-time  { font-size: .68rem; color: #64748b; font-family: monospace; margin-bottom: 4px; }
.seg-en    { font-size: 1rem;   color: #e2e8f0; line-height: 1.65; }
.seg-tr    { font-size: 1.05rem; color: #93c5fd; line-height: 1.75; }

.ok-badge  { display: inline-flex; align-items: center; gap: 6px;
             background: #14532d; color: #4ade80; border: 1px solid #166534;
             border-radius: 20px; padding: 4px 12px; font-size: .78rem; font-weight: 600; }
.err-badge { display: inline-flex; align-items: center; gap: 6px;
             background: #451a03; color: #fb923c; border: 1px solid #7c2d12;
             border-radius: 20px; padding: 4px 12px; font-size: .78rem; font-weight: 600; }
.dot { width: 8px; height: 8px; background: #4ade80; border-radius: 50%;
       display: inline-block; animation: blink 1.2s ease-in-out infinite; }
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: .3; } }

.audio-step  { background: #1e293b; border: 1px solid #334155; border-radius: 10px;
               padding: 12px 16px; margin-bottom: 8px; }
.step-num    { display: inline-flex; align-items: center; justify-content: center;
               width: 24px; height: 24px; border-radius: 50%; background: #1d4ed8;
               color: #fff; font-size: .78rem; font-weight: 700; margin-right: 8px; }
.step-label  { font-size: .93rem; font-weight: 600; color: #e2e8f0; }

div[data-testid="stTextArea"] textarea {
    background: #1e293b !important; color: #f1f5f9 !important;
    border: 1px solid #334155 !important; border-radius: 8px !important; font-size: 1rem !important;
}
div[data-testid="stSelectbox"] > div > div {
    background: #1e293b !important; color: #f1f5f9 !important; border: 1px solid #334155 !important;
}
div[data-testid="stButton"] > button {
    font-family: 'Inter', sans-serif !important; font-weight: 700 !important;
    font-size: 1rem !important; border-radius: 8px !important; padding: 10px 20px !important;
}
div[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #1d4ed8, #0369a1) !important;
    color: white !important; border: none !important;
}
div[data-testid="stTextInput"] input {
    background: #1e293b !important; color: #f1f5f9 !important; border: 1px solid #334155 !important;
}
.stTabs [data-baseweb="tab-list"] { background: #1e293b !important; border-radius: 8px !important; padding: 4px !important; }
.stTabs [data-baseweb="tab"]      { color: #94a3b8 !important; font-weight: 600 !important; }
.stTabs [aria-selected="true"]    { background: #0f172a !important; color: #38bdf8 !important; border-radius: 6px !important; }
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
for _k, _v in {
    "segments":    [],
    "target_lang": "Tamil",
    "api_key":     "",
    "qna_answer":  "",
}.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ── HELPERS ───────────────────────────────────────────────────────────────────
def get_api_key():
    return st.session_state.api_key or os.environ.get("ANTHROPIC_API_KEY", "")


def transcribe_audio(file_bytes, suffix):
    """
    Transcribe audio using OpenAI Whisper (CPU).
    Returns (transcript_text, error_string_or_None).
    """
    try:
        import whisper
    except ImportError:
        return "", "whisper_not_installed"

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        model = whisper.load_model("base")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = model.transcribe(tmp_path, language="en", fp16=False)

        transcript = result["text"].strip()
        return transcript, None

    except Exception as exc:
        return "", str(exc)

    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


def do_translate(english_text, target_lang):
    """
    Translate English text → target_lang using Claude.
    Returns (translation_string, error_string_or_None).
    """
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
                "You are an expert academic translator. "
                "Translate the English text the user provides into "
                + target_lang + " (" + native + "). "
                "Return ONLY the translated text — no explanation, no English, no extra lines."
            ),
            messages=[{"role": "user", "content": english_text}],
        )
        return resp.content[0].text.strip(), None
    except anthropic.AuthenticationError:
        return "", "BAD_KEY"
    except Exception as exc:
        return "", str(exc)


def do_qna(question, context, answer_lang):
    """Answer a question about the lecture in the student's chosen language."""
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
                "You are a helpful teaching assistant. "
                "Answer the student's question based on the lecture transcript. "
                "Respond in " + answer_lang + " (" + native + "). Be clear and concise."
            ),
            messages=[{"role": "user", "content":
                "Lecture transcript:\n" + context + "\n\nStudent question: " + question}],
        )
        return resp.content[0].text.strip()
    except Exception as exc:
        return "Error: " + str(exc)


def add_segment(english, translation, lang):
    st.session_state.segments.append({
        "ts":          datetime.now().strftime("%H:%M:%S"),
        "english":     english,
        "translation": translation,
        "lang":        lang,
        "native":      LANGUAGES[lang],
    })


# ══════════════════════════════════════════════════════════════════════════════
#  UI
# ══════════════════════════════════════════════════════════════════════════════

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔑 Anthropic API Key")
    st.markdown("Get yours free at [console.anthropic.com](https://console.anthropic.com)")
    key_val = st.text_input(
        "Key",
        type="password",
        value=st.session_state.api_key,
        placeholder="sk-ant-api03-...",
        label_visibility="collapsed",
    )
    if key_val != st.session_state.api_key:
        st.session_state.api_key = key_val

    if get_api_key():
        st.markdown('<div class="ok-badge"><span class="dot"></span> Key active</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="err-badge">⚠️ Enter API key above</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📊 Stats")
    st.metric("Segments", len(st.session_state.segments))
    total_words = sum(len(s["english"].split()) for s in st.session_state.segments)
    st.metric("Words processed", total_words)
    st.markdown("---")
    if st.button("🗑️ Clear all", use_container_width=True):
        st.session_state.segments   = []
        st.session_state.qna_answer = ""
        st.rerun()


# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown('<div class="big-title">🎙️ Guest Lecture Interpreter</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Upload lecture audio or type English text → instant translation to your language</div>', unsafe_allow_html=True)


# ── LANGUAGE SELECTOR ─────────────────────────────────────────────────────────
st.markdown("### 🌐 Your Language")
c1, c2, c3 = st.columns([3, 1, 4])
with c1:
    st.markdown('<div class="lang-label">Lecture is in</div>', unsafe_allow_html=True)
    st.markdown('<div class="lang-from">🇬🇧 English</div>', unsafe_allow_html=True)
with c2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="arrow-txt" style="text-align:center">→</div>', unsafe_allow_html=True)
with c3:
    st.markdown('<div class="lang-label">Translate to</div>', unsafe_allow_html=True)
    sel = st.selectbox(
        "lang",
        LANG_LIST,
        index=LANG_LIST.index(st.session_state.target_lang),
        format_func=lambda l: l + "  —  " + LANGUAGES[l],
        label_visibility="collapsed",
        key="lang_sel",
    )
    if sel != st.session_state.target_lang:
        st.session_state.target_lang = sel
        st.rerun()

target_lang   = st.session_state.target_lang
target_native = LANGUAGES[target_lang]

st.info("✅  English  →  **" + target_lang + " (" + target_native + ")**   ·   Change the dropdown above to switch language.")
st.markdown("---")


# ── TABS ──────────────────────────────────────────────────────────────────────
tab_audio, tab_text, tab_qna = st.tabs(["🎵  Upload Audio", "✍️  Type / Paste Text", "❓  Ask About Lecture"])


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 1 — AUDIO UPLOAD
# ══════════════════════════════════════════════════════════════════════════════
with tab_audio:
    st.markdown("**Upload a recorded lecture audio file — it will be transcribed to English, then translated to " + target_lang + ".**")

    st.markdown("""
    <div class="audio-step"><span class="step-num">1</span>
      <span class="step-label">Upload audio (.mp3 / .wav / .m4a / .ogg / .flac)</span></div>
    <div class="audio-step"><span class="step-num">2</span>
      <span class="step-label">Click <b>Transcribe &amp; Translate</b></span></div>
    <div class="audio-step"><span class="step-num">3</span>
      <span class="step-label">English transcript + translation appear side by side below</span></div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Upload audio",
        type=["mp3", "wav", "m4a", "ogg", "flac", "webm"],
        label_visibility="collapsed",
        key="audio_uploader",
    )

    if uploaded is not None:
        ext = uploaded.name.rsplit(".", 1)[-1].lower()
        st.audio(uploaded, format="audio/" + ext)
        st.markdown("**File:** `" + uploaded.name + "`  ·  **Size:** " + str(round(uploaded.size / 1024, 1)) + " KB")

        if not get_api_key():
            st.error("⚠️ Enter your Anthropic API key in the sidebar before processing.")
        else:
            if st.button("🚀  Transcribe & Translate", type="primary", use_container_width=True, key="audio_btn"):
                audio_bytes = uploaded.read()
                file_suffix = "." + ext

                # ── STEP 1: Whisper transcription ─────────────────────────────
                with st.status("🔊  Step 1 — Transcribing audio with Whisper…", expanded=True) as status1:
                    st.write("Loading Whisper model (first run may take ~30 s to download ~150 MB)…")
                    transcript, err = transcribe_audio(audio_bytes, file_suffix)

                    if err == "whisper_not_installed":
                        status1.update(label="⚠️ Whisper not installed", state="error")
                        st.error(
                            "The `openai-whisper` package is not installed.\n\n"
                            "Make sure `requirements.txt` contains `openai-whisper` and `packages.txt` contains `ffmpeg`, then redeploy."
                        )
                        st.stop()
                    elif err:
                        status1.update(label="❌ Transcription failed", state="error")
                        st.error("Whisper error: " + err)
                        st.stop()
                    elif not transcript:
                        status1.update(label="⚠️ No speech detected", state="error")
                        st.warning("No speech was detected. Please check the audio file.")
                        st.stop()
                    else:
                        status1.update(label="✅ Transcription complete — " + str(len(transcript.split())) + " words", state="complete")

                # Allow editing before translation
                st.markdown("#### 📝 Transcribed English Text")
                st.caption("Review and edit if needed before translating:")
                edited = st.text_area(
                    "Transcript",
                    value=transcript,
                    height=160,
                    key="audio_transcript_edit",
                    label_visibility="collapsed",
                )

                # ── STEP 2: Translate in chunks ────────────────────────────────
                with st.status("🌐  Step 2 — Translating to " + target_lang + "…", expanded=True) as status2:
                    words      = edited.split()
                    chunk_size = 200
                    chunks     = [" ".join(words[i: i + chunk_size]) for i in range(0, len(words), chunk_size)]
                    total      = len(chunks)
                    prog       = st.progress(0)
                    all_ok     = True

                    for idx, chunk in enumerate(chunks):
                        chunk = chunk.strip()
                        if not chunk:
                            continue
                        st.write("Translating chunk " + str(idx + 1) + " / " + str(total) + "…")
                        translation, terr = do_translate(chunk, target_lang)
                        if terr:
                            status2.update(label="❌ Translation error on chunk " + str(idx + 1), state="error")
                            st.error("Error: " + terr)
                            all_ok = False
                            break
                        add_segment(chunk, translation, target_lang)
                        prog.progress((idx + 1) / total)

                    if all_ok:
                        status2.update(
                            label="✅ Translated " + str(total) + " chunk(s) to " + target_lang + "!",
                            state="complete",
                        )

                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 2 — TYPE / PASTE TEXT
# ══════════════════════════════════════════════════════════════════════════════
with tab_text:
    st.markdown("**Type or paste English lecture text, then click Translate.**")

    text_in = st.text_area(
        "English text",
        height=150,
        placeholder="Paste or type English lecture content here…\n\nExample: Today we study machine learning. A model learns patterns from large amounts of data.",
        label_visibility="collapsed",
        key="text_input_main",
    )

    if not get_api_key():
        st.error("⚠️ Enter your Anthropic API key in the sidebar.")

    if st.button(
        "🌐  Translate  →  " + target_lang + " (" + target_native + ")",
        type="primary",
        use_container_width=True,
        key="text_btn",
    ):
        t = text_in.strip()
        if not t:
            st.warning("Please enter some English text first.")
        elif not get_api_key():
            st.error("Enter API key in the sidebar.")
        else:
            with st.spinner("Translating to " + target_lang + "…"):
                tr, err = do_translate(t, target_lang)
            if err == "NO_KEY":
                st.error("No API key — open the sidebar.")
            elif err == "BAD_KEY":
                st.error("Invalid API key — check at console.anthropic.com")
            elif err:
                st.error("Error: " + err)
            else:
                add_segment(t, tr, target_lang)
                st.success("✅ Translated to " + target_lang + "!")
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 3 — Q&A
# ══════════════════════════════════════════════════════════════════════════════
with tab_qna:
    if not st.session_state.segments:
        st.info("📭 No lecture content yet. Upload audio or paste text first.")
    else:
        ctx = " ".join(s["english"] for s in st.session_state.segments)
        st.markdown("Ask anything about the lecture. Answer comes in **" + target_lang + " (" + target_native + ")**.")
        q = st.text_input(
            "Question",
            placeholder="e.g. What is the main topic of this lecture?",
            label_visibility="collapsed",
            key="qna_input",
        )
        if st.button("💬 Get Answer", type="primary", use_container_width=True, key="qna_btn"):
            if q.strip():
                with st.spinner("Thinking…"):
                    st.session_state.qna_answer = do_qna(q.strip(), ctx, target_lang)
        if st.session_state.qna_answer:
            st.markdown(
                '<div style="background:#0c1a3a;border-left:4px solid #38bdf8;border-radius:0 8px 8px 0;'
                'padding:14px 18px;margin-top:12px;font-size:1rem;line-height:1.7;color:#93c5fd;">'
                + st.session_state.qna_answer + "</div>",
                unsafe_allow_html=True,
            )


# ── LIVE RESULTS ──────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📜 Transcript  &  " + target_lang + " Translation")

if not st.session_state.segments:
    st.markdown("""
    <div style="text-align:center;padding:40px 20px;background:#1e293b;border-radius:12px;color:#64748b;">
      <div style="font-size:2.5rem;margin-bottom:8px;">🎙️</div>
      <div style="font-size:1rem;font-weight:600;color:#94a3b8;">No segments yet</div>
      <div style="font-size:.85rem;margin-top:6px;">Upload audio or paste English text above to get started</div>
    </div>""", unsafe_allow_html=True)
else:
    for seg in reversed(st.session_state.segments):
        col_l, col_r = st.columns(2, gap="medium")
        with col_l:
            st.markdown(
                '<div class="panel-en">'
                '<div class="panel-head en">🇬🇧 English</div>'
                '<div class="seg-time">' + seg["ts"] + '</div>'
                '<div class="seg-en">'  + seg["english"]     + '</div>'
                '</div>',
                unsafe_allow_html=True,
            )
        with col_r:
            st.markdown(
                '<div class="panel-tr">'
                '<div class="panel-head tr">🇮🇳 ' + seg["lang"] + ' (' + seg["native"] + ')</div>'
                '<div class="seg-time">' + seg["ts"] + '</div>'
                '<div class="seg-tr">'  + seg["translation"] + '</div>'
                '</div>',
                unsafe_allow_html=True,
            )

    # ── DOWNLOAD ──────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### ⬇️ Download")
    d1, d2 = st.columns(2)
    ts_now = datetime.now().strftime("%Y%m%d_%H%M")
    with d1:
        en_out = "\n\n".join("[" + s["ts"] + "]\n" + s["english"] for s in st.session_state.segments)
        st.download_button(
            "📄 English Transcript (.txt)", en_out,
            file_name="transcript_" + ts_now + ".txt",
            mime="text/plain", use_container_width=True,
        )
    with d2:
        tr_out = "\n\n".join("[" + s["ts"] + "] " + s["lang"] + "\n" + s["translation"] for s in st.session_state.segments)
        st.download_button(
            "📄 " + target_lang + " Translation (.txt)", tr_out,
            file_name=target_lang + "_translation_" + ts_now + ".txt",
            mime="text/plain", use_container_width=True,
        )

st.markdown(
    '<div style="text-align:center;color:#334155;font-size:.8rem;padding:16px 0;">'
    "Deploy on Streamlit Cloud · Share URL with students · Each picks their own language 📱"
    "</div>",
    unsafe_allow_html=True,
)
