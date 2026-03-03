import streamlit as st
import anthropic
import speech_recognition as sr
import json
import io
import wave
from datetime import datetime
from fpdf import FPDF

st.set_page_config(page_title="🎙️ Live Audio Translator", page_icon="🎙️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Mono&display=swap');
*,html,body{font-family:'DM Sans',sans-serif}
#MainMenu,footer,header{visibility:hidden}
.block-container{padding-top:1.5rem !important}

.app-header{background:linear-gradient(135deg,#0f172a,#1e1b4b,#0f172a);
  border:1px solid rgba(139,92,246,.3);border-radius:20px;padding:2rem 2.5rem;
  margin-bottom:1.5rem;position:relative;overflow:hidden}
.app-header::before{content:'';position:absolute;inset:0;
  background:radial-gradient(ellipse at 30% 50%,rgba(139,92,246,.15),transparent 60%),
             radial-gradient(ellipse at 70% 50%,rgba(34,211,238,.08),transparent 60%);pointer-events:none}
.app-header h1{color:#f1f5f9;font-size:2rem;font-weight:700;margin:0 0 .3rem;letter-spacing:-.5px}
.app-header p{color:#94a3b8;font-size:1rem;margin:0}
.hbadge{display:inline-flex;align-items:center;gap:6px;background:rgba(139,92,246,.2);
  border:1px solid rgba(139,92,246,.4);color:#a78bfa;padding:.25rem .8rem;border-radius:50px;
  font-size:.78rem;font-weight:600;letter-spacing:.5px;text-transform:uppercase;margin-bottom:.7rem}

.t-box{background:#020617;border:1px solid #1e293b;border-radius:12px;padding:1.2rem 1.5rem;
  min-height:360px;max-height:480px;overflow-y:auto;scroll-behavior:smooth}
.t-empty{color:#334155;font-style:italic;font-size:.95rem;display:flex;align-items:center;
  justify-content:center;height:200px;text-align:center;line-height:1.8}
.seg{margin-bottom:1.2rem;animation:fi .4s ease}
@keyframes fi{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}
.seg-meta{color:#475569;font-size:.72rem;font-family:'DM Mono',monospace;
  margin-bottom:.35rem;display:flex;align-items:center;gap:8px}
.seg-num{background:rgba(139,92,246,.15);color:#8b5cf6;border-radius:4px;
  padding:.1rem .4rem;font-size:.7rem;font-weight:700}
.seg-en{background:rgba(30,58,138,.25);border-left:3px solid #3b82f6;border-radius:0 8px 8px 0;
  padding:.5rem 1rem;color:#93c5fd;font-size:.95rem;line-height:1.6;margin-bottom:.3rem}
.seg-tr{background:rgba(6,78,59,.25);border-left:3px solid #10b981;border-radius:0 8px 8px 0;
  padding:.5rem 1rem;color:#6ee7b7;font-size:1.05rem;line-height:1.7}
.slbl{font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.5px;opacity:.6;margin-bottom:.2rem}

.stats-row{display:flex;gap:.75rem;margin-bottom:1rem}
.stat-box{flex:1;background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:.8rem;text-align:center}
.stat-num{color:#a78bfa;font-size:1.6rem;font-weight:700;line-height:1}
.stat-lbl{color:#475569;font-size:.72rem;text-transform:uppercase;letter-spacing:.5px;margin-top:.2rem}
.lang-pill{display:inline-flex;align-items:center;gap:6px;
  background:linear-gradient(135deg,rgba(139,92,246,.2),rgba(34,211,238,.1));
  border:1px solid rgba(139,92,246,.4);color:#c4b5fd;padding:.35rem 1rem;
  border-radius:50px;font-weight:600;font-size:.9rem;margin-top:.3rem}
</style>
""", unsafe_allow_html=True)

# ── Language config ────────────────────────────────────────────────────────────
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

# ── Session state ──────────────────────────────────────────────────────────────
for k, v in dict(transcripts=[], words=0, segs=0, api_key="", last_audio_id=None).items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Claude translation ─────────────────────────────────────────────────────────
def translate_text(text: str, lang: str, api_key: str) -> str:
    client = anthropic.Anthropic(api_key=api_key)
    prompt = (
        f"You are a professional translator specializing in Indian languages.\n"
        f"Translate the following English text to {lang}.\n"
        f"{HINTS.get(lang, '')}\n"
        f"Return ONLY the translated text in native script. No explanations. No romanization.\n\n"
        f"English: {text}"
    )
    r = client.messages.create(
        model="claude-sonnet-4-20250514", max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )
    return r.content[0].text.strip()

# ── Speech-to-text ─────────────────────────────────────────────────────────────
def audio_to_text(audio_bytes: bytes) -> str | None:
    recognizer = sr.Recognizer()
    # Attempt 1: direct AudioFile parse (works for WAV)
    try:
        buf = io.BytesIO(audio_bytes)
        with sr.AudioFile(buf) as source:
            audio = recognizer.record(source)
        return recognizer.recognize_google(audio)
    except Exception:
        pass
    # Attempt 2: pydub conversion (handles webm/ogg from browser)
    try:
        from pydub import AudioSegment
        seg = AudioSegment.from_file(io.BytesIO(audio_bytes))
        seg = seg.set_channels(1).set_frame_rate(16000).set_sample_width(2)
        wav_buf = io.BytesIO()
        seg.export(wav_buf, format="wav")
        wav_buf.seek(0)
        with sr.AudioFile(wav_buf) as source:
            audio = recognizer.record(source)
        return recognizer.recognize_google(audio)
    except Exception:
        pass
    return None

# ── PDF builder ────────────────────────────────────────────────────────────────
def build_pdf(transcripts, lang, incl_en, incl_tr) -> bytes:
    pdf = FPDF(); pdf.add_page()
    pdf.set_fill_color(15,23,42); pdf.rect(0,0,210,38,'F')
    pdf.set_font("Helvetica","B",16); pdf.set_text_color(225,225,255)
    pdf.set_y(10); pdf.cell(0,9,"Audio Transcript & Translation",ln=True,align="C")
    pdf.set_font("Helvetica","",8); pdf.set_text_color(148,163,184)
    pdf.cell(0,6,f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}   |   Language: {lang}   |   Segments: {len(transcripts)}",ln=True,align="C")
    pdf.ln(10)
    for i,e in enumerate(transcripts,1):
        pdf.set_font("Helvetica","B",8); pdf.set_text_color(139,92,246)
        pdf.cell(0,5,f"SEGMENT {i}  —  {e.get('ts','')}",ln=True)
        pdf.set_draw_color(139,92,246); pdf.set_line_width(.2)
        pdf.line(10,pdf.get_y(),200,pdf.get_y()); pdf.ln(2)
        if incl_en:
            pdf.set_font("Helvetica","B",9); pdf.set_text_color(59,130,246)
            pdf.cell(0,5,"English",ln=True)
            pdf.set_font("Helvetica","",10); pdf.set_text_color(30,30,60)
            pdf.set_fill_color(239,246,255)
            pdf.multi_cell(0,6,e.get("en",""),fill=True); pdf.ln(2)
        if incl_tr:
            pdf.set_font("Helvetica","B",9); pdf.set_text_color(16,185,129)
            pdf.cell(0,5,f"{lang} Translation",ln=True)
            pdf.set_font("Helvetica","",10); pdf.set_text_color(20,50,30)
            pdf.set_fill_color(240,253,244)
            safe = e.get("translated","").encode("latin-1",errors="replace").decode("latin-1")
            pdf.multi_cell(0,6,safe,fill=True); pdf.ln(3)
        pdf.ln(2)
    pdf.set_font("Helvetica","I",7); pdf.set_text_color(150,150,150)
    pdf.multi_cell(0,4,"Note: Use JSON/TXT export for full native-script Unicode text.")
    return pdf.output(dest="S").encode("latin-1")

def build_txt(transcripts, lang) -> str:
    lines = [f"Audio Transcript & Translation — {lang}",
             f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
             "="*60, ""]
    for i,e in enumerate(transcripts,1):
        lines += [f"[Segment {i}]  {e.get('ts','')}",
                  f"English   : {e.get('en','')}",
                  f"{lang:10}: {e.get('translated','')}",""]
    return "\n".join(lines)

# ══════════════════════════════ UI ════════════════════════════════════════════

st.markdown("""
<div class="app-header">
  <div class="hbadge">⚡ Claude AI Powered</div>
  <h1>🎙️ Live Audio Translator</h1>
  <p>Record English speech → instant transcription + Indian language translation → download PDF / JSON / TXT</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Setup")
    key_in = st.text_input("🔑 Anthropic API Key", type="password",
                           value=st.session_state.api_key, placeholder="sk-ant-...")
    if key_in: st.session_state.api_key = key_in
    api_ok = bool(st.session_state.api_key)
    st.success("✅ API key set") if api_ok else st.warning("⚠️ API key required")

    st.markdown("---\n### 🌐 Target Language")
    lbl  = st.selectbox("", list(LANGUAGES.keys()), label_visibility="collapsed")
    lang = LANGUAGES[lbl]
    st.markdown(f'<div class="lang-pill">🇮🇳 {lang}</div>', unsafe_allow_html=True)

    st.markdown("---\n### 📄 Export Options")
    incl_en = st.checkbox("Include English text", value=True)
    incl_tr = st.checkbox("Include translation",  value=True)

    st.markdown("---")
    st.markdown(f"""
    <div class="stats-row">
      <div class="stat-box"><div class="stat-num">{st.session_state.segs}</div><div class="stat-lbl">Segments</div></div>
      <div class="stat-box"><div class="stat-num">{st.session_state.words}</div><div class="stat-lbl">Words</div></div>
    </div>""", unsafe_allow_html=True)

    if st.button("🗑️ Clear All", use_container_width=True):
        st.session_state.transcripts=[]; st.session_state.segs=0
        st.session_state.words=0; st.session_state.last_audio_id=None
        st.rerun()

    st.markdown("---")
    st.markdown("""<small style='color:#475569'>
<b style='color:#94a3b8'>Steps:</b><br>
1. Enter Anthropic API key<br>2. Choose language<br>
3. Click mic → speak → click stop<br>4. Transcript appears below<br>
5. Repeat for more segments<br>6. Download PDF / JSON / TXT
</small>""", unsafe_allow_html=True)

# ── Main area ──────────────────────────────────────────────────────────────────
col1, col2 = st.columns([3, 2], gap="large")

with col1:
    st.markdown("### 🎤 Record Audio")
    if not api_ok:
        st.error("❌ Enter your Anthropic API key in the sidebar first.")

    # ── Core recorder widget ───────────────────────────────────────────────────
    audio_value = st.audio_input(
        "Click 🎙️ to record. Click ⏹️ to stop. Transcript will auto-update.",
        key="mic"
    )

    # ── Process new recording ──────────────────────────────────────────────────
    if audio_value is not None:
        current_id = id(audio_value)
        if current_id != st.session_state.last_audio_id:
            st.session_state.last_audio_id = current_id
            if not api_ok:
                st.error("❌ Enter your API key first.")
            else:
                raw = audio_value.read()
                with st.status("⚙️ Processing audio…", expanded=True) as status:
                    st.write("🗣️ Transcribing to English…")
                    en_text = audio_to_text(raw)
                    if not en_text:
                        status.update(label="⚠️ Speech not recognised — please try again.", state="error")
                    else:
                        st.write(f"✅ Heard: *{en_text}*")
                        st.write(f"🤖 Translating to **{lang}**…")
                        try:
                            translated = translate_text(en_text, lang, st.session_state.api_key)
                            st.session_state.transcripts.append({
                                "en": en_text, "translated": translated,
                                "ts": datetime.now().strftime("%H:%M:%S"), "lang": lang,
                            })
                            st.session_state.segs  += 1
                            st.session_state.words += len(en_text.split())
                            status.update(label="✅ Done! See transcript below.", state="complete")
                            st.rerun()
                        except Exception as ex:
                            status.update(label=f"❌ Error: {ex}", state="error")

    # ── Transcript ─────────────────────────────────────────────────────────────
    st.markdown("### 📜 Transcript")
    if not st.session_state.transcripts:
        st.markdown('<div class="t-box"><div class="t-empty">🎙️ No transcript yet.<br>Record audio above — it will appear here automatically.</div></div>', unsafe_allow_html=True)
    else:
        html = '<div class="t-box">'
        for i, e in enumerate(st.session_state.transcripts, 1):
            html += f'<div class="seg"><div class="seg-meta"><span class="seg-num">#{i}</span><span>{e.get("ts","")}</span><span>→ {e.get("lang",lang)}</span></div>'
            if incl_en:
                html += f'<div class="slbl" style="color:#3b82f6">🇬🇧 English</div><div class="seg-en">{e["en"]}</div>'
            if incl_tr:
                html += f'<div class="slbl" style="color:#10b981;margin-top:.4rem">🌐 {e.get("lang",lang)}</div><div class="seg-tr">{e["translated"]}</div>'
            html += '</div>'
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

with col2:
    st.markdown("### 📥 Download")
    has = bool(st.session_state.transcripts)

    if not has:
        st.markdown("""<div style='background:#0f172a;border:2px dashed #1e293b;border-radius:12px;
          padding:2.5rem;text-align:center;color:#334155;font-size:.9rem'>
          📄 Downloads appear here<br>after your first recording.
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""<div style='background:linear-gradient(135deg,rgba(139,92,246,.1),rgba(34,211,238,.05));
          border:1px solid rgba(139,92,246,.25);border-radius:12px;padding:1rem 1.2rem;margin-bottom:1rem'>
          <div style='color:#a78bfa;font-weight:700;font-size:.8rem;margin-bottom:.3rem'>READY TO DOWNLOAD</div>
          <div style='color:#e2e8f0;font-size:.9rem'>{st.session_state.segs} segment(s) · {st.session_state.words} words · {lang}</div>
        </div>""", unsafe_allow_html=True)

        # PDF
        try:
            pdf_b = build_pdf(st.session_state.transcripts, lang, incl_en, incl_tr)
            st.download_button("📄 Download PDF", pdf_b,
                file_name=f"transcript_{lang.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf", use_container_width=True)
        except Exception as e:
            st.error(f"PDF error: {e}")

        # JSON (full Unicode native script preserved)
        json_b = json.dumps(st.session_state.transcripts, ensure_ascii=False, indent=2).encode("utf-8")
        st.download_button("📋 Download JSON (full Unicode)",
            json_b, file_name=f"transcript_{lang.lower()}.json",
            mime="application/json", use_container_width=True)

        # Plain text
        txt_b = build_txt(st.session_state.transcripts, lang).encode("utf-8")
        st.download_button("📝 Download Text (.txt)",
            txt_b, file_name=f"transcript_{lang.lower()}.txt",
            mime="text/plain", use_container_width=True)

    # Latest segment preview
    if has:
        st.markdown("---\n### 🔍 Latest Segment")
        e = st.session_state.transcripts[-1]
        st.markdown(f"""<div style='background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:1.2rem'>
          <div style='color:#3b82f6;font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.5px;margin-bottom:.4rem'>🇬🇧 English</div>
          <div style='color:#bfdbfe;font-size:.95rem;margin-bottom:.9rem'>{e["en"]}</div>
          <div style='color:#10b981;font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.5px;margin-bottom:.4rem'>🌐 {e.get("lang",lang)}</div>
          <div style='color:#a7f3d0;font-size:1.05rem'>{e["translated"]}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---\n### 🇮🇳 Languages")
    for d in LANGUAGES.keys():
        st.markdown(f"- {d}")
