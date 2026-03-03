import streamlit as st
import os
import tempfile
import time
import datetime
from pathlib import Path

# Page config
st.set_page_config(
    page_title="VaakSetu | Voice Bridge",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tiro+Devanagari+Sanskrit&family=Space+Mono:wght@400;700&family=Syne:wght@400;600;800&display=swap');

:root {
    --bg: #0a0a0f;
    --panel: #111118;
    --border: #1e1e2e;
    --accent: #e8c547;
    --accent2: #4fc3f7;
    --accent3: #f48fb1;
    --text: #e8e8f0;
    --muted: #5a5a7a;
    --success: #69f0ae;
    --recording: #ff5252;
}

* { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Syne', sans-serif;
}

[data-testid="stAppViewContainer"] {
    background: 
        radial-gradient(ellipse 80% 50% at 20% 10%, rgba(232,197,71,0.06) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 80% 80%, rgba(79,195,247,0.05) 0%, transparent 60%),
        var(--bg) !important;
}

[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] { background: var(--panel) !important; }

/* Hide Streamlit default elements */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* Hero header */
.vaaksetu-header {
    text-align: center;
    padding: 2.5rem 0 1.5rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 2rem;
}
.vaaksetu-header .logo {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 2.8rem;
    letter-spacing: -1px;
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent2) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.vaaksetu-header .tagline {
    font-family: 'Space Mono', monospace;
    font-size: 0.75rem;
    color: var(--muted);
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-top: 0.3rem;
}

/* Cards */
.card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}
.card-title {
    font-size: 0.7rem;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 1rem;
    font-family: 'Space Mono', monospace;
}

/* Language selector */
.stSelectbox > div > div {
    background: var(--panel) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
}
.stSelectbox > div > div:focus-within {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(232,197,71,0.15) !important;
}

/* Buttons */
.stButton > button {
    background: transparent !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.75rem !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    border-radius: 8px !important;
    padding: 0.6rem 1.5rem !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
}
.stButton > button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    box-shadow: 0 0 15px rgba(232,197,71,0.1) !important;
}

/* Primary button */
div[data-testid="column"]:first-child .stButton > button {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
}

/* Transcript box */
.transcript-box {
    background: #0d0d14;
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.5rem;
    min-height: 220px;
    max-height: 340px;
    overflow-y: auto;
    font-family: 'Space Mono', monospace;
    font-size: 0.82rem;
    line-height: 1.8;
    color: var(--text);
    position: relative;
}
.transcript-box::-webkit-scrollbar { width: 4px; }
.transcript-box::-webkit-scrollbar-track { background: transparent; }
.transcript-box::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }

.transcript-line {
    display: flex;
    gap: 1rem;
    padding: 0.3rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.03);
    animation: fadeSlide 0.4s ease;
}
@keyframes fadeSlide {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}
.ts-time {
    color: var(--muted);
    font-size: 0.7rem;
    min-width: 50px;
    padding-top: 2px;
    font-family: 'Space Mono', monospace;
}
.ts-text { flex: 1; }
.ts-original { color: var(--accent2); margin-bottom: 0.15rem; }
.ts-translated { color: var(--text); }
.ts-lang-badge {
    font-size: 0.6rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--muted);
    background: rgba(255,255,255,0.04);
    padding: 1px 5px;
    border-radius: 3px;
    margin-left: 0.5rem;
}

/* Status indicators */
.status-idle    { color: var(--muted); }
.status-recording { color: var(--recording); animation: pulse 1.2s infinite; }
.status-processing { color: var(--accent); }
.status-done    { color: var(--success); }
@keyframes pulse {
    0%,100% { opacity: 1; }
    50%      { opacity: 0.4; }
}

/* Recording indicator dot */
.rec-dot {
    display: inline-block;
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--recording);
    margin-right: 6px;
    animation: pulse 1s infinite;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background: var(--panel) !important;
    border: 1px dashed var(--border) !important;
    border-radius: 10px !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: var(--accent) !important;
}

/* Audio recorder */
[data-testid="stAudioInput"] {
    background: var(--panel) !important;
    border-radius: 10px !important;
    padding: 1rem !important;
}

/* Metrics / stats row */
.stats-row {
    display: flex;
    gap: 1rem;
    margin: 0.8rem 0;
}
.stat-chip {
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.4rem 0.8rem;
    font-family: 'Space Mono', monospace;
    font-size: 0.7rem;
    color: var(--muted);
}
.stat-chip span { color: var(--accent); margin-left: 4px; }

/* Download button */
.download-btn {
    display: inline-block;
    background: linear-gradient(135deg, var(--accent) 0%, #c9a832 100%);
    color: #0a0a0f !important;
    font-family: 'Space Mono', monospace;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    padding: 0.7rem 1.8rem;
    border-radius: 8px;
    border: none;
    cursor: pointer;
    text-decoration: none;
    margin-top: 0.5rem;
    transition: all 0.2s;
}
.download-btn:hover { opacity: 0.9; transform: translateY(-1px); }

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    background: var(--panel) !important;
    border-radius: 8px;
    padding: 4px;
    gap: 4px;
    border: 1px solid var(--border);
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--muted) !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.72rem !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    border-radius: 6px !important;
    padding: 0.5rem 1.2rem !important;
}
.stTabs [aria-selected="true"] {
    background: var(--bg) !important;
    color: var(--accent) !important;
    border: 1px solid var(--border) !important;
}
.stTabs [data-baseweb="tab-panel"] {
    padding-top: 1.2rem !important;
}

/* Empty state */
.empty-state {
    text-align: center;
    padding: 3rem 2rem;
    color: var(--muted);
    font-family: 'Space Mono', monospace;
    font-size: 0.75rem;
    letter-spacing: 1px;
}
.empty-icon { font-size: 2.5rem; margin-bottom: 0.8rem; opacity: 0.4; }

/* Alert / info boxes */
[data-testid="stAlert"] {
    background: rgba(79,195,247,0.05) !important;
    border: 1px solid rgba(79,195,247,0.15) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
}

/* Spinner */
[data-testid="stSpinner"] { color: var(--accent) !important; }

/* Radio buttons */
.stRadio > div { gap: 0.5rem !important; }
.stRadio label { 
    background: var(--panel) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    padding: 0.4rem 0.9rem !important;
    font-size: 0.78rem !important;
    cursor: pointer !important;
    transition: all 0.2s !important;
}
.stRadio label:hover { border-color: var(--accent) !important; }

/* Responsive */
@media (max-width: 768px) {
    .vaaksetu-header .logo { font-size: 2rem; }
}
</style>
""", unsafe_allow_html=True)

# ── Helper: check dependencies ──────────────────────────────────────────────
@st.cache_resource
def load_models():
    """Load Whisper and translation models."""
    try:
        import whisper
        model = whisper.load_model("base")
        return model, None
    except ImportError:
        return None, "whisper_missing"
    except Exception as e:
        return None, str(e)

def get_translator(src_lang="en", tgt_lang="ta"):
    """Load Helsinki-NLP translation model."""
    try:
        from transformers import MarianMTModel, MarianTokenizer
        model_name = f"Helsinki-NLP/opus-mt-{src_lang}-{tgt_lang}"
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        model = MarianMTModel.from_pretrained(model_name)
        return tokenizer, model
    except Exception:
        return None, None

def translate_text(text, tgt_lang_code):
    """Translate English text to target Indian language using Helsinki-NLP models."""
    lang_model_map = {
        "ta": "en-ROMANCE",   # fallback handling below
        "hi": "en-hi",
        "ml": "en-ml",
        "te": "en-te",
        "kn": "en-kn",
    }
    try:
        from transformers import MarianMTModel, MarianTokenizer
        model_name = f"Helsinki-NLP/opus-mt-en-{tgt_lang_code}"
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        model = MarianMTModel.from_pretrained(model_name)
        inputs = tokenizer([text], return_tensors="pt", padding=True, truncation=True, max_length=512)
        translated = model.generate(**inputs)
        result = tokenizer.decode(translated[0], skip_special_tokens=True)
        return result
    except Exception as e:
        return f"[Translation unavailable: {str(e)[:60]}]"

def transcribe_audio(audio_path, whisper_model):
    """Transcribe audio using Whisper."""
    try:
        result = whisper_model.transcribe(audio_path, language="en", verbose=False)
        return result
    except Exception as e:
        return None

def format_timestamp(seconds):
    """Format seconds to MM:SS."""
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"

def build_transcript_content(segments, translated_segments, language_name, show_original):
    """Build text content for download."""
    lines = [f"VaakSetu Transcript — {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
             f"Language: {language_name}",
             "=" * 60, ""]
    for i, (seg, trans) in enumerate(zip(segments, translated_segments)):
        ts = format_timestamp(seg.get("start", 0))
        if show_original:
            lines.append(f"[{ts}] EN: {seg['text'].strip()}")
        lines.append(f"[{ts}] {language_name[:2].upper()}: {trans}")
        lines.append("")
    return "\n".join(lines)

# ── Language Config ──────────────────────────────────────────────────────────
LANGUAGES = {
    "Tamil — தமிழ்":       {"code": "ta", "script": "தமிழ்",    "model": "en-ta"},
    "Hindi — हिन्दी":      {"code": "hi", "script": "हिन्दी",   "model": "en-hi"},
    "Malayalam — മലയാളം":  {"code": "ml", "script": "മലയാളം",  "model": "en-ml"},
    "Telugu — తెలుగు":     {"code": "te", "script": "తెలుగు",   "model": "en-te"},
    "Kannada — ಕನ್ನಡ":    {"code": "kn", "script": "ಕನ್ನಡ",    "model": "en-kn"},
}

# ── Session State ────────────────────────────────────────────────────────────
if "segments" not in st.session_state:
    st.session_state.segments = []
if "translated" not in st.session_state:
    st.session_state.translated = []
if "processing" not in st.session_state:
    st.session_state.processing = False
if "status" not in st.session_state:
    st.session_state.status = "idle"
if "word_count" not in st.session_state:
    st.session_state.word_count = 0
if "duration" not in st.session_state:
    st.session_state.duration = 0

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="vaaksetu-header">
    <div class="logo">🎙 VaakSetu</div>
    <div class="tagline">English → Indian Language Voice Bridge</div>
</div>
""", unsafe_allow_html=True)

# ── Layout: Left config | Right transcript ───────────────────────────────────
col_left, col_right = st.columns([1, 1.5], gap="large")

with col_left:
    # Language selection
    st.markdown('<div class="card-title">01 — Select Target Language</div>', unsafe_allow_html=True)
    selected_lang = st.selectbox(
        "Language",
        list(LANGUAGES.keys()),
        label_visibility="collapsed"
    )
    lang_info = LANGUAGES[selected_lang]

    st.markdown("<br>", unsafe_allow_html=True)

    # Output preferences
    st.markdown('<div class="card-title">02 — Display Options</div>', unsafe_allow_html=True)
    show_original = st.checkbox("Show original English alongside translation", value=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Input mode tabs
    st.markdown('<div class="card-title">03 — Audio Input</div>', unsafe_allow_html=True)
    tab_live, tab_upload = st.tabs(["🎤  Live Mic", "📁  Upload File"])

    with tab_live:
        st.markdown('<p style="font-size:0.75rem;color:#5a5a7a;font-family:\'Space Mono\',monospace;margin-bottom:0.8rem;">Record directly from your microphone</p>', unsafe_allow_html=True)
        
        audio_value = st.audio_input("Record Audio", label_visibility="collapsed")
        
        if audio_value is not None:
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                process_live = st.button("⚡ Transcribe", key="btn_live")
            with col_b2:
                clear_live = st.button("✕ Clear", key="btn_clear_live")
            
            if clear_live:
                st.session_state.segments = []
                st.session_state.translated = []
                st.session_state.status = "idle"
                st.rerun()

            if process_live:
                st.session_state.status = "processing"
                whisper_model, err = load_models()
                if err or whisper_model is None:
                    st.error("⚠ Whisper not installed. Run: `pip install openai-whisper`")
                else:
                    with st.spinner("Transcribing & translating..."):
                        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                            f.write(audio_value.getvalue())
                            tmp_path = f.name
                        result = transcribe_audio(tmp_path, whisper_model)
                        os.unlink(tmp_path)
                        
                        if result and result.get("segments"):
                            segs = result["segments"]
                            translated = []
                            progress = st.progress(0)
                            for i, seg in enumerate(segs):
                                t = translate_text(seg["text"].strip(), lang_info["code"])
                                translated.append(t)
                                progress.progress((i+1)/len(segs))
                            progress.empty()
                            st.session_state.segments = segs
                            st.session_state.translated = translated
                            st.session_state.word_count = sum(len(s["text"].split()) for s in segs)
                            st.session_state.duration = segs[-1].get("end", 0) if segs else 0
                            st.session_state.status = "done"
                            st.rerun()
                        else:
                            st.warning("No speech detected. Please try again.")

    with tab_upload:
        st.markdown('<p style="font-size:0.75rem;color:#5a5a7a;font-family:\'Space Mono\',monospace;margin-bottom:0.8rem;">Upload an audio file (MP3, WAV, M4A, FLAC, OGG)</p>', unsafe_allow_html=True)
        
        uploaded = st.file_uploader(
            "Upload Audio",
            type=["mp3", "wav", "m4a", "flac", "ogg", "webm"],
            label_visibility="collapsed"
        )
        
        if uploaded:
            st.audio(uploaded)
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                process_upload = st.button("⚡ Transcribe", key="btn_upload")
            with col_b2:
                clear_up = st.button("✕ Clear", key="btn_clear_up")
            
            if clear_up:
                st.session_state.segments = []
                st.session_state.translated = []
                st.session_state.status = "idle"
                st.rerun()

            if process_upload:
                st.session_state.status = "processing"
                whisper_model, err = load_models()
                if err or whisper_model is None:
                    st.error("⚠ Whisper not installed. Run: `pip install openai-whisper`")
                else:
                    ext = Path(uploaded.name).suffix
                    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
                        f.write(uploaded.read())
                        tmp_path = f.name
                    
                    with st.spinner(f"Processing `{uploaded.name}`..."):
                        result = transcribe_audio(tmp_path, whisper_model)
                        os.unlink(tmp_path)
                        
                        if result and result.get("segments"):
                            segs = result["segments"]
                            translated = []
                            progress = st.progress(0)
                            for i, seg in enumerate(segs):
                                t = translate_text(seg["text"].strip(), lang_info["code"])
                                translated.append(t)
                                progress.progress((i+1)/len(segs))
                            progress.empty()
                            st.session_state.segments = segs
                            st.session_state.translated = translated
                            st.session_state.word_count = sum(len(s["text"].split()) for s in segs)
                            st.session_state.duration = segs[-1].get("end", 0) if segs else 0
                            st.session_state.status = "done"
                            st.rerun()
                        else:
                            st.warning("No speech detected in uploaded file.")

with col_right:
    # Status bar
    status_map = {
        "idle":       ("○", "status-idle",       "Awaiting input"),
        "processing": ("◉", "status-processing", "Processing audio..."),
        "done":       ("●", "status-done",        "Transcription complete"),
    }
    icon, css_class, label = status_map.get(st.session_state.status, status_map["idle"])

    segs = st.session_state.segments
    trans = st.session_state.translated
    
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.8rem;">
        <span class="card-title" style="margin:0;">Live Transcript</span>
        <span class="{css_class}" style="font-family:'Space Mono',monospace;font-size:0.72rem;">
            {icon} {label}
        </span>
    </div>
    """, unsafe_allow_html=True)

    # Stats
    if segs:
        dur_str = format_timestamp(st.session_state.duration)
        st.markdown(f"""
        <div class="stats-row">
            <div class="stat-chip">Segments<span>{len(segs)}</span></div>
            <div class="stat-chip">Words<span>{st.session_state.word_count}</span></div>
            <div class="stat-chip">Duration<span>{dur_str}</span></div>
            <div class="stat-chip">Language<span>{lang_info['script']}</span></div>
        </div>
        """, unsafe_allow_html=True)

    # Transcript display
    if not segs:
        st.markdown("""
        <div class="transcript-box">
            <div class="empty-state">
                <div class="empty-icon">🎵</div>
                <div>Record or upload English audio<br>to see live transcription here</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        lines_html = ""
        for seg, t in zip(segs, trans):
            ts = format_timestamp(seg.get("start", 0))
            original_html = f'<div class="ts-original">{seg["text"].strip()} <span class="ts-lang-badge">EN</span></div>' if show_original else ""
            lines_html += f"""
            <div class="transcript-line">
                <div class="ts-time">{ts}</div>
                <div class="ts-text">
                    {original_html}
                    <div class="ts-translated">{t} <span class="ts-lang-badge">{lang_info['code'].upper()}</span></div>
                </div>
            </div>"""
        
        st.markdown(f'<div class="transcript-box" id="transcript-scroll">{lines_html}</div>', unsafe_allow_html=True)
        
        # Auto-scroll JS
        st.markdown("""
        <script>
        const box = document.getElementById('transcript-scroll');
        if (box) box.scrollTop = box.scrollHeight;
        </script>
        """, unsafe_allow_html=True)

    # Download section
    if segs and trans:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="card-title">Download Transcript</div>', unsafe_allow_html=True)
        
        d_col1, d_col2 = st.columns(2)
        
        # Plain text download
        txt_content = build_transcript_content(segs, trans, selected_lang.split("—")[0].strip(), show_original)
        with d_col1:
            st.download_button(
                label="⬇ Download .TXT",
                data=txt_content.encode("utf-8"),
                file_name=f"vaaksetu_{lang_info['code']}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True,
                key="dl_txt"
            )
        
        # SRT subtitle format download
        srt_lines = []
        for i, (seg, t) in enumerate(zip(segs, trans), 1):
            start = seg.get("start", 0)
            end = seg.get("end", start + 2)
            def srt_time(s):
                h, rem = divmod(s, 3600)
                m, sec = divmod(rem, 60)
                ms = int((sec % 1) * 1000)
                return f"{int(h):02d}:{int(m):02d}:{int(sec):02d},{ms:03d}"
            srt_lines.append(f"{i}\n{srt_time(start)} --> {srt_time(end)}\n{t}\n")
        srt_content = "\n".join(srt_lines)

        with d_col2:
            st.download_button(
                label="⬇ Download .SRT",
                data=srt_content.encode("utf-8"),
                file_name=f"vaaksetu_{lang_info['code']}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.srt",
                mime="text/plain",
                use_container_width=True,
                key="dl_srt"
            )

# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="border-top:1px solid #1e1e2e;margin-top:2.5rem;padding-top:1rem;text-align:center;">
    <span style="font-family:'Space Mono',monospace;font-size:0.65rem;color:#3a3a5a;letter-spacing:2px;">
        VAAKSETU · POWERED BY OPENAI WHISPER + HELSINKI-NLP · BUILT WITH STREAMLIT
    </span>
</div>
""", unsafe_allow_html=True)
