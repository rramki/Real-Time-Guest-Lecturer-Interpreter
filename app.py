import streamlit as st
import anthropic
import os
import json
import re
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
[data-testid="stSidebar"] {
    background-color: #1e293b !important;
}
[data-testid="stHeader"] { background: transparent !important; }

h1, h2, h3 { color: #f1f5f9 !important; }

.big-title {
    font-size: 2rem;
    font-weight: 700;
    color: #38bdf8;
    margin-bottom: 4px;
}
.subtitle {
    color: #94a3b8;
    font-size: 0.95rem;
    margin-bottom: 24px;
}

/* Language selector row */
.lang-row {
    display: flex;
    align-items: center;
    gap: 16px;
    background: #1e293b;
    border: 2px solid #334155;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 24px;
}
.lang-from {
    background: #166534;
    color: #4ade80;
    border: 1px solid #15803d;
    border-radius: 8px;
    padding: 8px 18px;
    font-weight: 700;
    font-size: 1rem;
    white-space: nowrap;
}
.arrow-icon {
    font-size: 1.5rem;
    color: #38bdf8;
    font-weight: 700;
}
.lang-label {
    color: #94a3b8;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 6px;
    font-weight: 600;
}

/* Translation panels */
.panel-en {
    background: #1e293b;
    border: 1px solid #334155;
    border-left: 4px solid #4ade80;
    border-radius: 10px;
    padding: 16px 20px;
    min-height: 180px;
    margin-bottom: 16px;
}
.panel-translated {
    background: #0c1a3a;
    border: 1px solid #1e40af;
    border-left: 4px solid #38bdf8;
    border-radius: 10px;
    padding: 16px 20px;
    min-height: 180px;
    margin-bottom: 16px;
}
.panel-title {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 700;
    margin-bottom: 12px;
}
.panel-title.en  { color: #4ade80; }
.panel-title.tr  { color: #38bdf8; }

.seg-item {
    border-bottom: 1px solid rgba(255,255,255,0.06);
    padding: 10px 0;
}
.seg-item:last-child { border-bottom: none; }
.seg-time {
    font-size: 0.7rem;
    color: #64748b;
    font-family: monospace;
    margin-bottom: 4px;
}
.seg-text-en   { font-size: 1rem; color: #e2e8f0; line-height: 1.6; }
.seg-text-tr   { font-size: 1.05rem; color: #93c5fd; line-height: 1.7; }

/* Status badge */
.status-ok {
    display: inline-flex; align-items: center; gap: 6px;
    background: #14532d; color: #4ade80;
    border: 1px solid #166534;
    border-radius: 20px; padding: 4px 12px;
    font-size: 0.78rem; font-weight: 600;
}
.status-warn {
    display: inline-flex; align-items: center; gap: 6px;
    background: #451a03; color: #fb923c;
    border: 1px solid #7c2d12;
    border-radius: 20px; padding: 4px 12px;
    font-size: 0.78rem; font-weight: 600;
}
.dot-live {
    width: 8px; height: 8px; background: #4ade80;
    border-radius: 50%; display: inline-block;
    animation: blink 1.2s ease-in-out infinite;
}
@keyframes blink {
    0%,100% { opacity:1; } 50% { opacity:0.3; }
}

/* Streamlit widget overrides */
div[data-testid="stTextArea"] textarea {
    background: #1e293b !important;
    color: #f1f5f9 !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
    font-size: 1rem !important;
}
div[data-testid="stSelectbox"] > div > div {
    background: #1e293b !important;
    color: #f1f5f9 !important;
    border: 1px solid #334155 !important;
}
div[data-testid="stButton"] > button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    border-radius: 8px !important;
    padding: 10px 20px !important;
}
div[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #1d4ed8, #0369a1) !important;
    color: white !important;
    border: none !important;
}
div[data-testid="stTextInput"] input {
    background: #1e293b !important;
    color: #f1f5f9 !important;
    border: 1px solid #334155 !important;
}
.stTabs [data-baseweb="tab-list"] {
    background: #1e293b !important;
    border-radius: 8px !important;
    padding: 4px !important;
}
.stTabs [data-baseweb="tab"] {
    color: #94a3b8 !important;
    font-weight: 600 !important;
}
.stTabs [aria-selected="true"] {
    background: #0f172a !important;
    color: #38bdf8 !important;
    border-radius: 6px !important;
}
</style>
""", unsafe_allow_html=True)


# ── CONSTANTS ─────────────────────────────────────────────────────────────────
LANGUAGES = {
    "Tamil":     "தமிழ்",
    "Hindi":     "हिंदी",
    "Telugu":    "తెలుగు",
    "Kannada":   "ಕನ್ನಡ",
    "Malayalam": "മലയാളം",
    "Marathi":   "मराठी",
    "Bengali":   "বাংলা",
}

DEMO_TEXTS = {
    "AI Introduction": "Good morning everyone. Today we will explore the fundamentals of artificial intelligence. AI refers to the simulation of human intelligence by computer systems.",
    "Neural Networks": "A neural network is a series of algorithms that attempt to recognize relationships in data through a process that mimics the way the human brain operates.",
    "Machine Learning": "Machine learning is a subset of artificial intelligence that gives computers the ability to learn from data without being explicitly programmed for each task.",
    "Data Science": "Data science combines statistics, programming, and domain expertise to extract meaningful insights from structured and unstructured data.",
    "Deep Learning": "Deep learning uses multiple layers of neural networks to progressively extract higher-level features from raw input such as images, sound, and text.",
}


# ── SESSION STATE ─────────────────────────────────────────────────────────────
if "segments"     not in st.session_state: st.session_state.segments     = []
if "target_lang"  not in st.session_state: st.session_state.target_lang  = "Tamil"
if "api_key"      not in st.session_state: st.session_state.api_key      = ""
if "qna_answer"   not in st.session_state: st.session_state.qna_answer   = ""


# ── HELPERS ───────────────────────────────────────────────────────────────────
def get_api_key():
    return st.session_state.api_key or os.environ.get("ANTHROPIC_API_KEY", "")

def do_translate(english_text: str, target_lang: str):
    """Call Claude to translate English → target_lang. Returns (translation, error)."""
    key = get_api_key()
    if not key:
        return None, "NO_KEY"

    client = anthropic.Anthropic(api_key=key)
    native = LANGUAGES[target_lang]

    system_prompt = (
        f"You are an expert translator. "
        f"Translate the English text the user gives you into {target_lang} ({native}). "
        f"Return ONLY the translated text — no explanation, no English, no extra lines."
    )

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": english_text}]
        )
        translation = response.content[0].text.strip()
        return translation, None
    except anthropic.AuthenticationError:
        return None, "BAD_KEY"
    except Exception as e:
        return None, str(e)

def do_qna(question: str, context: str, answer_lang: str):
    """Answer a question about the lecture in the student's language."""
    key = get_api_key()
    if not key:
        return "No API key set."
    client = anthropic.Anthropic(api_key=key)
    native = LANGUAGES.get(answer_lang, answer_lang)
    try:
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            system=(
                f"You are a helpful teaching assistant. "
                f"Answer the student's question based on the lecture transcript provided. "
                f"Give your answer in {answer_lang} ({native}). Be clear and concise."
            ),
            messages=[{"role": "user", "content":
                f"Lecture transcript:\n{context}\n\nStudent question: {question}"
            }]
        )
        return resp.content[0].text.strip()
    except Exception as e:
        return f"Error: {e}"


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔑 API Key Setup")
    st.markdown("Paste your **Anthropic API key** below.\nGet one free at [console.anthropic.com](https://console.anthropic.com)")

    key_input = st.text_input(
        "API Key",
        type="password",
        value=st.session_state.api_key,
        placeholder="sk-ant-api03-...",
        label_visibility="collapsed",
    )
    if key_input != st.session_state.api_key:
        st.session_state.api_key = key_input

    if get_api_key():
        st.markdown('<div class="status-ok"><span class="dot-live"></span> API key active</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-warn">⚠️ No API key — translation disabled</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📊 Session Stats")
    st.metric("Segments translated", len(st.session_state.segments))
    total_words = sum(len(s["english"].split()) for s in st.session_state.segments)
    st.metric("English words processed", total_words)

    st.markdown("---")
    if st.button("🗑️ Clear all segments", use_container_width=True):
        st.session_state.segments = []
        st.session_state.qna_answer = ""
        st.rerun()


# ── MAIN PAGE ─────────────────────────────────────────────────────────────────
st.markdown('<div class="big-title">🎙️ Guest Lecture Interpreter</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">English lecture → your language, in real time · Powered by Claude AI</div>', unsafe_allow_html=True)

# ── LANGUAGE SELECTOR (very visible) ─────────────────────────────────────────
st.markdown("### 🌐 Choose Your Language")
st.markdown("Students: pick the language you want the lecture translated into 👇")

col_from, col_arrow, col_to = st.columns([3, 1, 4])

with col_from:
    st.markdown('<div class="lang-label">Lecture is in</div>', unsafe_allow_html=True)
    st.markdown('<div class="lang-from">🇬🇧 English</div>', unsafe_allow_html=True)

with col_arrow:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<div class="arrow-icon">→</div>', unsafe_allow_html=True)

with col_to:
    st.markdown('<div class="lang-label">Translate to</div>', unsafe_allow_html=True)
    lang_options = list(LANGUAGES.keys())
    selected = st.selectbox(
        "Target language",
        options=lang_options,
        index=lang_options.index(st.session_state.target_lang),
        format_func=lambda l: f"{l}  —  {LANGUAGES[l]}",
        label_visibility="collapsed",
        key="lang_select_main",
    )
    if selected != st.session_state.target_lang:
        st.session_state.target_lang = selected
        st.rerun()

target_lang  = st.session_state.target_lang
target_native = LANGUAGES[target_lang]

# Show current selection confirmation
st.info(f"✅ **Translating English → {target_lang} ({target_native})**  |  Change the dropdown above to switch language.")

st.markdown("---")

# ── INPUT SECTION ─────────────────────────────────────────────────────────────
tab_paste, tab_demo, tab_qna = st.tabs(["✍️  Paste / Type Text", "📚  Demo Sentences", "❓  Ask About Lecture"])

# ── TAB 1: Paste text ─────────────────────────────────────────────────────────
with tab_paste:
    st.markdown(f"**Paste the lecturer's English words below, then click Translate.**")

    english_input = st.text_area(
        "English lecture text",
        height=130,
        placeholder="Type or paste English lecture text here…\n\nExample: Today we will learn about neural networks. They are inspired by the human brain.",
        label_visibility="collapsed",
        key="english_paste_input",
    )

    clicked = st.button(
        f"🌐  Translate  →  {target_lang} ({target_native})",
        type="primary",
        use_container_width=True,
        key="translate_btn_paste",
    )

    if clicked:
        text = english_input.strip()
        if not text:
            st.warning("⚠️ Please type or paste some English text first.")
        elif not get_api_key():
            st.error("⚠️ No API key found!  Open the **sidebar on the left** (click ☰) and paste your Anthropic API key.")
        else:
            with st.spinner(f"Translating to {target_lang}…"):
                translation, err = do_translate(text, target_lang)

            if err == "NO_KEY":
                st.error("⚠️ No API key. Open the sidebar and enter your key.")
            elif err == "BAD_KEY":
                st.error("❌ Invalid API key. Check it at console.anthropic.com")
            elif err:
                st.error(f"❌ Translation failed: {err}")
            else:
                st.session_state.segments.append({
                    "ts":          datetime.now().strftime("%H:%M:%S"),
                    "english":     text,
                    "translation": translation,
                    "lang":        target_lang,
                    "native":      target_native,
                })
                st.success(f"✅ Translated to {target_lang}!")
                st.rerun()

# ── TAB 2: Demo sentences ─────────────────────────────────────────────────────
with tab_demo:
    st.markdown(f"Click any topic to instantly translate a sample sentence to **{target_lang}**.")

    for topic, sentence in DEMO_TEXTS.items():
        with st.expander(f"📖 {topic}"):
            st.markdown(f"**English:** {sentence}")
            if st.button(f"Translate this → {target_lang}", key=f"demo_{topic}"):
                if not get_api_key():
                    st.error("⚠️ Open the sidebar and enter your Anthropic API key first.")
                else:
                    with st.spinner(f"Translating to {target_lang}…"):
                        translation, err = do_translate(sentence, target_lang)
                    if err:
                        st.error(f"Error: {err}")
                    else:
                        st.session_state.segments.append({
                            "ts":          datetime.now().strftime("%H:%M:%S"),
                            "english":     sentence,
                            "translation": translation,
                            "lang":        target_lang,
                            "native":      target_native,
                        })
                        st.success("✅ Added to transcript below!")
                        st.rerun()

# ── TAB 3: Q&A ────────────────────────────────────────────────────────────────
with tab_qna:
    if not st.session_state.segments:
        st.info("📭 No lecture content yet. Use the other tabs to add translated segments first.")
    else:
        context = " ".join(s["english"] for s in st.session_state.segments)
        st.markdown(f"Ask anything about the lecture. Answer will come in **{target_lang} ({target_native})**.")
        question = st.text_input("Your question", placeholder=f"e.g. What is a neural network?  (answer in {target_lang})", label_visibility="collapsed")
        if st.button("💬 Get Answer", type="primary", use_container_width=True):
            if question.strip():
                with st.spinner("Thinking…"):
                    st.session_state.qna_answer = do_qna(question.strip(), context, target_lang)
        if st.session_state.qna_answer:
            st.markdown("**Answer:**")
            st.markdown(f"> {st.session_state.qna_answer}")

st.markdown("---")

# ── LIVE TRANSCRIPT + TRANSLATION ─────────────────────────────────────────────
st.markdown(f"### 📜 Live Transcript  &  🌐 {target_lang} Translation")

if not st.session_state.segments:
    st.markdown("""
    <div style="text-align:center;padding:40px 20px;background:#1e293b;border-radius:12px;color:#64748b;">
        <div style="font-size:2rem;margin-bottom:8px;">🎙️</div>
        <div style="font-size:1rem;font-weight:600;">No segments yet</div>
        <div style="font-size:0.85rem;margin-top:6px;">Paste English text above and click Translate to see results here</div>
    </div>
    """, unsafe_allow_html=True)
else:
    # Show latest segments first
    for seg in reversed(st.session_state.segments):
        col_en, col_tr = st.columns(2, gap="medium")

        with col_en:
            st.markdown(f"""
            <div class="panel-en">
                <div class="panel-title en">🇬🇧 English</div>
                <div class="seg-time">{seg['ts']}</div>
                <div class="seg-text-en">{seg['english']}</div>
            </div>
            """, unsafe_allow_html=True)

        with col_tr:
            st.markdown(f"""
            <div class="panel-translated">
                <div class="panel-title tr">🇮🇳 {seg['lang']} ({seg['native']})</div>
                <div class="seg-time">{seg['ts']}</div>
                <div class="seg-text-tr">{seg['translation']}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── EXPORT ────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### ⬇️ Download")
    dl1, dl2 = st.columns(2)
    with dl1:
        en_text = "\n\n".join(f"[{s['ts']}]\n{s['english']}" for s in st.session_state.segments)
        st.download_button("📄 English Transcript", en_text,
            file_name=f"english_transcript_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain", use_container_width=True)
    with dl2:
        tr_text = "\n\n".join(f"[{s['ts']}] {s['lang']}\n{s['translation']}" for s in st.session_state.segments)
        st.download_button(f"📄 {target_lang} Translation", tr_text,
            file_name=f"{target_lang}_translation_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain", use_container_width=True)

st.markdown("""
<div style="text-align:center;color:#334155;font-size:0.8rem;padding:20px 0;">
    Deploy free on Streamlit Cloud · Share URL with students · Each student picks their own language 📱
</div>
""", unsafe_allow_html=True)
