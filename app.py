import streamlit as st
import anthropic
import speech_recognition as sr
import queue
import json
import io
import wave
import numpy as np
from datetime import datetime
from fpdf import FPDF

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Live Audio Translator", page_icon="🎙️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif}
.hdr{background:linear-gradient(135deg,#667eea,#764ba2);padding:2rem;border-radius:16px;
     text-align:center;color:white;margin-bottom:1.5rem;box-shadow:0 8px 32px rgba(102,126,234,.3)}
.hdr h1{font-size:2.4rem;margin:0;font-weight:700}
.hdr p{margin:.4rem 0 0;opacity:.9;font-size:1.05rem}
.tbox{background:#0f0f1a;border:1px solid #2d2d4e;border-radius:12px;padding:1.5rem;
      min-height:320px;max-height:420px;overflow-y:auto;line-height:1.9;color:#e8e8f0}
.en{color:#7dd3fc;padding:.35rem .8rem;border-left:3px solid #3b82f6;
    background:rgba(59,130,246,.07);border-radius:0 6px 6px 0;margin-bottom:.3rem}
.tr{color:#86efac;padding:.35rem .8rem;border-left:3px solid #22c55e;
    background:rgba(34,197,94,.07);border-radius:0 6px 6px 0;margin-bottom:.9rem;font-size:1.1rem}
.ts{color:#6b7280;font-size:.74rem;margin-right:6px}
.badge{display:inline-block;background:linear-gradient(135deg,#667eea,#764ba2);
       color:white;padding:.25rem .9rem;border-radius:50px;font-weight:600;font-size:.9rem}
</style>
""", unsafe_allow_html=True)

# ── Language Config ─────────────────────────────────────────────────────────────
LANGUAGES = {
    "Tamil (தமிழ்)":      "Tamil",
    "Hindi (हिंदी)":       "Hindi",
    "Telugu (తెలుగు)":     "Telugu",
    "Kannada (ಕನ್ನಡ)":    "Kannada",
    "Malayalam (മലയാളം)": "Malayalam",
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
    for k, v in dict(transcripts=[], words=0, segs=0, api_key="").items():
        if k not in st.session_state:
            st.session_state[k] = v
init()

# ── Claude Translation ──────────────────────────────────────────────────────────
def translate(text: str, lang: str, api_key: str) -> str:
    client = anthropic.Anthropic(api_key=api_key)
    prompt = (
        f"You are a professional translator specializing in Indian languages.\n"
        f"Translate the following English text to {lang}.\n"
        f"{HINTS.get(lang,'')}\n"
        f"Return ONLY the translated text in native script — no explanations, no romanization.\n\n"
        f"English: {text}"
    )
    r = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )
    return r.content[0].text.strip()

# ── Speech-to-Text from uploaded/recorded bytes ─────────────────────────────────
def stt_from_bytes(audio_bytes: bytes) -> str | None:
    recognizer = sr.Recognizer()
    buf = io.BytesIO(audio_bytes)
    with sr.AudioFile(buf) as source:
        audio = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio)
    except Exception:
        return None

# ── PDF Export ──────────────────────────────────────────────────────────────────
def make_pdf(transcripts, lang, incl_en):
    pdf = FPDF(); pdf.add_page()
    pdf.set_font("Helvetica","B",18); pdf.set_text_color(80,60,160)
    pdf.cell(0,12,"Live Audio Transcript & Translation",ln=True,align="C")
    pdf.set_font("Helvetica","",10); pdf.set_text_color(120,120,120)
    pdf.cell(0,7,f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  |  Language: {lang}",ln=True,align="C")
    pdf.ln(4); pdf.set_draw_color(180,160,220); pdf.set_line_width(.5)
    pdf.line(10,pdf.get_y(),200,pdf.get_y()); pdf.ln(5)
    for i,e in enumerate(transcripts,1):
        pdf.set_font("Helvetica","B",9); pdf.set_text_color(160,130,200)
        pdf.cell(0,6,f"Segment {i}  [{e.get('ts','')}]",ln=True)
        if incl_en:
            pdf.set_font("Helvetica","B",10); pdf.set_text_color(40,100,180)
            pdf.cell(0,6,"English:",ln=True)
            pdf.set_font("Helvetica","",10); pdf.set_text_color(30,30,30)
            pdf.multi_cell(0,6,e.get("en","")); pdf.ln(2)
        pdf.set_font("Helvetica","B",10); pdf.set_text_color(30,140,70)
        pdf.cell(0,6,f"{lang} Translation:",ln=True)
        pdf.set_font("Helvetica","",10); pdf.set_text_color(30,30,30)
        safe = e.get("translated","").encode("latin-1",errors="replace").decode("latin-1")
        pdf.multi_cell(0,6,safe); pdf.ln(4)
        pdf.set_draw_color(220,215,235); pdf.line(10,pdf.get_y(),200,pdf.get_y()); pdf.ln(4)
    pdf.set_font("Helvetica","I",8); pdf.set_text_color(150,150,150)
    pdf.multi_cell(0,5,"NOTE: Use JSON export for full native-script Unicode text.")
    return pdf.output(dest="S").encode("latin-1")

# ═══════════════════════════════════════ UI ════════════════════════════════════

st.markdown(
    '<div class="hdr"><h1>🎙️ Live Audio Translator</h1>'
    '<p>English speech → Indian Language Translation &nbsp;|&nbsp; Powered by Claude AI</p></div>',
    unsafe_allow_html=True
)

# ── Sidebar ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration\n---")
    key_in = st.text_input("🔑 Anthropic API Key", type="password",
                           value=st.session_state.api_key, placeholder="sk-ant-...")
    if key_in: st.session_state.api_key = key_in

    st.markdown("---\n### 🌐 Target Language")
    lbl  = st.selectbox("Translate to:", list(LANGUAGES.keys()))
    lang = LANGUAGES[lbl]
    st.markdown(f'<span class="badge">→ {lang}</span>', unsafe_allow_html=True)

    st.markdown("---\n### 📄 PDF Options")
    incl_en = st.checkbox("Include English", value=True)
    incl_tr = st.checkbox("Include translation", value=True)

    st.markdown("---\n### 📊 Stats")
    c1,c2 = st.columns(2)
    c1.metric("Segments", st.session_state.segs)
    c2.metric("Words",    st.session_state.words)
    st.markdown("---")
    if st.button("🗑️ Clear All"):
        st.session_state.transcripts=[]; st.session_state.segs=0; st.session_state.words=0
        st.rerun()

# ── Main Layout ─────────────────────────────────────────────────────────────────
L, R = st.columns([2, 1])

with L:
    st.markdown("### 📜 Live Transcript & Translation")

    # ── Browser-based audio recorder (no PyAudio needed) ────────────────────────
    st.markdown("#### 🎤 Record from Browser Microphone")
    
    # Inject a JS recorder component
    audio_bytes = st.audio_input("Click to record, click again to stop")

    if audio_bytes and st.session_state.api_key:
        api_ok = True
        raw = audio_bytes.read()
        with st.spinner("Transcribing…"):
            en_text = stt_from_bytes(raw)
        if en_text:
            with st.spinner(f"Translating to {lang}…"):
                translated = translate(en_text, lang, st.session_state.api_key)
            entry = {
                "en": en_text,
                "translated": translated,
                "ts": datetime.now().strftime("%H:%M:%S"),
            }
            st.session_state.transcripts.append(entry)
            st.session_state.segs  += 1
            st.session_state.words += len(en_text.split())
            st.rerun()
        else:
            st.warning("⚠️ Could not recognise speech. Please try again.")
    elif audio_bytes and not st.session_state.api_key:
        st.error("⚠️ Please enter your Anthropic API key in the sidebar first.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📜 Transcript")

    html = '<div class="tbox">'
    if not st.session_state.transcripts:
        html += '<span style="color:#4b5563;font-style:italic">Transcript will appear here after you record…</span>'
    else:
        for e in st.session_state.transcripts:
            ts = e.get("ts","")
            if incl_en:
                html += f'<div class="en"><span class="ts">{ts}</span>🇬🇧 {e["en"]}</div>'
            if incl_tr:
                html += f'<div class="tr">🌐 {e["translated"]}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

with R:
    st.markdown("### 📥 Download")
    if st.session_state.transcripts:
        pdf_b = make_pdf(st.session_state.transcripts, lang, incl_en)
        st.download_button("📄 Download PDF", pdf_b,
            file_name=f"transcript_{lang.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf", use_container_width=True)
        json_b = json.dumps(st.session_state.transcripts,
                            ensure_ascii=False, indent=2).encode("utf-8")
        st.download_button("📋 Download JSON (full Unicode)", json_b,
            file_name=f"transcript_{lang.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json", use_container_width=True)
    else:
        st.info("Record audio to enable downloads.")

    st.markdown("---")
    st.markdown("""
**How it works**
1. 🎤 Click mic → speak → click again to stop
2. 🗣️ Google STT → English text
3. 🤖 Claude LLM → Indian language
4. 📜 Transcript updates automatically
5. 📄 Download PDF or JSON anytime
    """)
    st.markdown("---")
    st.markdown("""
**Supported Languages**
- 🇮🇳 Tamil · Hindi · Telugu
- 🇮🇳 Kannada · Malayalam
    """)
