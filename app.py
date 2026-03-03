import streamlit as st
import anthropic
import json
import os
from datetime import datetime

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Lecture Interpreter",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

  :root {
    --bg: #0a0e1a; --surface: #111827; --card: #1a2235;
    --border: #2a3a5c; --accent: #3b82f6; --accent2: #06b6d4;
    --text: #e2e8f0; --muted: #64748b; --live: #22c55e;
  }
  html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important; color: var(--text) !important;
    font-family: 'Space Grotesk', sans-serif !important;
  }
  [data-testid="stHeader"] { background: transparent !important; }
  [data-testid="stSidebar"] { background: var(--surface) !important; }

  .main-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
    border: 1px solid var(--border); border-radius: 16px;
    padding: 22px 28px; margin-bottom: 20px;
    position: relative; overflow: hidden;
  }
  .main-header::before {
    content: ''; position: absolute; top: -50%; left: -50%;
    width: 200%; height: 200%;
    background: radial-gradient(circle at 60% 40%, rgba(59,130,246,0.08) 0%, transparent 50%),
                radial-gradient(circle at 20% 80%, rgba(6,182,212,0.06) 0%, transparent 40%);
    pointer-events: none;
  }
  .main-header h1 {
    font-size: 1.8rem; font-weight: 700; margin: 0 0 4px 0;
    background: linear-gradient(135deg, #3b82f6, #06b6d4, #818cf8);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }
  .main-header p { color: var(--muted); font-size: 0.85rem; margin: 0; }

  .lang-picker-wrap {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 14px; padding: 18px 20px; margin-bottom: 20px;
  }
  .lang-picker-title {
    font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em;
    color: var(--muted); font-weight: 600; margin-bottom: 12px;
  }
  .source-chip {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(34,197,94,0.12); border: 1px solid rgba(34,197,94,0.3);
    color: #4ade80; padding: 8px 16px; border-radius: 30px;
    font-size: 0.9rem; font-weight: 600;
  }

  .transcript-box {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 12px; padding: 18px;
    min-height: 260px; max-height: 360px;
    overflow-y: auto; font-size: 1rem; line-height: 1.85; color: var(--text);
  }
  .translation-box {
    background: linear-gradient(135deg, #0f1f3d, #0d1b33);
    border: 1px solid rgba(59,130,246,0.3);
    border-radius: 12px; padding: 18px;
    min-height: 260px; max-height: 360px;
    overflow-y: auto; font-size: 1.1rem; line-height: 1.95; color: #93c5fd;
  }
  .transcript-box::-webkit-scrollbar,
  .translation-box::-webkit-scrollbar { width: 4px; }
  .transcript-box::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
  .translation-box::-webkit-scrollbar-thumb { background: rgba(59,130,246,0.4); border-radius: 4px; }

  .segment-line {
    padding: 8px 12px; border-radius: 8px; margin-bottom: 8px;
    border-left: 3px solid var(--accent);
    animation: fadeIn 0.4s ease;
  }
  .segment-line .ts {
    font-size: 0.68rem; color: var(--muted);
    font-family: monospace; display: block; margin-bottom: 3px;
  }
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(5px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  .section-label {
    font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.1em;
    color: var(--muted); font-weight: 600; margin-bottom: 10px;
    display: flex; align-items: center; gap: 8px;
  }
  .section-label::after { content: ''; flex: 1; height: 1px; background: var(--border); }

  .stat-card {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 10px; padding: 12px 16px; text-align: center;
  }
  .stat-card .num { font-size: 1.6rem; font-weight: 700; color: var(--accent2); display: block; }
  .stat-card .lbl { font-size: 0.72rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; }

  .no-content { color: var(--muted); font-style: italic; font-size: 0.88rem; padding: 20px; text-align: center; }
  .info-bar {
    background: rgba(59,130,246,0.08); border: 1px solid rgba(59,130,246,0.2);
    border-radius: 8px; padding: 11px 14px; font-size: 0.85rem; color: #93c5fd; margin-bottom: 14px;
  }
  .warn-bar {
    background: rgba(245,158,11,0.1); border: 1px solid rgba(245,158,11,0.25);
    border-radius: 8px; padding: 11px 14px; font-size: 0.83rem; color: #fbbf24; margin-bottom: 14px;
  }
  .qna-answer {
    background: rgba(59,130,246,0.08); border-left: 3px solid var(--accent);
    border-radius: 0 8px 8px 0; padding: 12px 16px;
    margin-top: 12px; font-size: 0.95rem; line-height: 1.7; color: #cbd5e1;
  }
  div[data-testid="stButton"] > button {
    font-family: 'Space Grotesk', sans-serif !important; font-weight: 600 !important; border-radius: 8px !important;
  }
  .stTextArea textarea {
    background: var(--card) !important; border-color: var(--border) !important;
    color: var(--text) !important; font-family: 'Space Grotesk', sans-serif !important;
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(0.7); }
  }
</style>
""", unsafe_allow_html=True)


# ─── Constants ────────────────────────────────────────────────────────────────
LANGUAGES = {
    "Tamil":     {"flag": "🇮🇳", "native": "தமிழ்"},
    "Hindi":     {"flag": "🇮🇳", "native": "हिंदी"},
    "Telugu":    {"flag": "🇮🇳", "native": "తెలుగు"},
    "Kannada":   {"flag": "🇮🇳", "native": "ಕನ್ನಡ"},
    "Malayalam": {"flag": "🇮🇳", "native": "മലയാളം"},
    "Marathi":   {"flag": "🇮🇳", "native": "मराठी"},
    "Bengali":   {"flag": "🇮🇳", "native": "বাংলা"},
    "English":   {"flag": "🇬🇧", "native": "English"},
}
LANG_LIST = [l for l in LANGUAGES.keys() if l != "English"]

DEMO_SENTENCES = [
    "— Try a demo sentence —",
    "Good morning everyone. Today we will study the fundamentals of artificial intelligence and machine learning.",
    "Neural networks are computational models inspired by the human brain, consisting of layers of interconnected nodes.",
    "Data preprocessing is a critical step in machine learning pipelines. It includes normalization, encoding, and handling missing values.",
    "Deep learning has revolutionized computer vision tasks such as image classification, object detection, and segmentation.",
    "The gradient descent algorithm minimizes the loss function by iteratively updating model weights in the opposite direction of the gradient.",
]


# ─── Session State ─────────────────────────────────────────────────────────────
for k, v in {
    "segments": [], "word_count": 0, "seg_count": 0,
    "qna_answer": "", "api_key": "", "target_lang": "Tamil",
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ─── Helpers ──────────────────────────────────────────────────────────────────
def get_client():
    key = st.session_state.get("api_key", "") or os.environ.get("ANTHROPIC_API_KEY", "")
    return anthropic.Anthropic(api_key=key) if key else None

def has_key():
    return bool(st.session_state.get("api_key") or os.environ.get("ANTHROPIC_API_KEY"))

def translate_english(english_text: str, target_lang: str) -> dict:
    client = get_client()
    if not client:
        return {"error": "no_key"}
    prompt = f"""You are a professional academic interpreter.
Translate the following English lecture text to {target_lang}.
Preserve all technical and academic terms accurately.

Respond ONLY with valid JSON (no markdown, no extra text):
{{
  "original": "<exact English input>",
  "translation": "<accurate {target_lang} translation>",
  "target_language": "{target_lang}"
}}

English text:
\"\"\"{english_text}\"\"\""""
    try:
        resp = client.messages.create(
            model="claude-opus-4-5", max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = resp.content[0].text.strip().replace("```json","").replace("```","").strip()
        return json.loads(raw)
    except json.JSONDecodeError:
        import re
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            try: return json.loads(m.group())
            except: pass
        return {"error": f"parse_error: {raw[:200]}"}
    except Exception as e:
        return {"error": str(e)}

def answer_in_lang(question: str, context: str, answer_lang: str) -> str:
    client = get_client()
    if not client: return "No API key configured."
    try:
        resp = client.messages.create(
            model="claude-opus-4-5", max_tokens=500,
            messages=[{"role": "user", "content":
                f"""You are a helpful teaching assistant.
Based on this English lecture transcript, answer the student's question.
Provide the answer in {answer_lang}.

Lecture (English):
{context[:3000]}

Student's question: {question}

Answer in {answer_lang}:"""}]
        )
        return resp.content[0].text
    except Exception as e:
        return f"Error: {e}"

def add_segment(original, translation, target_lang):
    st.session_state.segments.append({
        "ts": datetime.now().strftime("%H:%M:%S"),
        "original": original, "translation": translation, "target_lang": target_lang,
    })
    st.session_state.word_count += len(original.split())
    st.session_state.seg_count += 1

def get_full_transcript():
    return " ".join(s["original"] for s in st.session_state.segments if s["original"])


# ══════════════════════════════════════════════════════════════════════════════
#  UI
# ══════════════════════════════════════════════════════════════════════════════

# ── Header ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;">
    <div>
      <h1>🎙️ Guest Lecture Interpreter</h1>
      <p>English lecture → your language · Real-time · Powered by Claude AI</p>
    </div>
    <div style="display:inline-flex;align-items:center;gap:7px;
                background:rgba(34,197,94,0.12);border:1px solid rgba(34,197,94,0.3);
                color:#4ade80;padding:5px 14px;border-radius:20px;font-size:0.75rem;font-weight:600;">
      <span style="width:7px;height:7px;background:#22c55e;border-radius:50%;
                   display:inline-block;animation:pulse 1.4s infinite;"></span>LIVE AI
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar: API key only ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔑 Anthropic API Key")
    st.markdown("Get yours at [console.anthropic.com](https://console.anthropic.com)")
    api_val = st.text_input("API Key", type="password",
        value=st.session_state.api_key, placeholder="sk-ant-...",
        label_visibility="collapsed")
    if api_val:
        st.session_state.api_key = api_val
    st.success("✅ Key set") if has_key() else st.warning("⚠️ Key needed")

    st.markdown("---")
    if st.button("🗑️ Clear All Segments", use_container_width=True):
        st.session_state.segments = []
        st.session_state.word_count = 0
        st.session_state.seg_count = 0
        st.session_state.qna_answer = ""
        st.rerun()
    st.markdown("---")
    st.markdown("""<div style="font-size:0.78rem;color:#64748b;line-height:1.7;">
    <b style="color:#94a3b8;">Steps:</b><br>
    1. Paste API key above<br>
    2. Pick language on main page<br>
    3. Paste English text → Translate<br>
    4. See scrolling transcript + translation<br>
    5. Ask questions in your language
    </div>""", unsafe_allow_html=True)


# ── Step 1: Language Picker ──────────────────────────────────────────────────
st.markdown('<div class="lang-picker-wrap">', unsafe_allow_html=True)
st.markdown('<div class="lang-picker-title">🌐 Step 1 — Select YOUR language (translation target)</div>', unsafe_allow_html=True)

row1, row2, row3 = st.columns([2, 1, 3])
with row1:
    st.markdown('<div class="source-chip">🇬🇧 English &nbsp;<span style="font-size:0.75rem;opacity:0.65">(Lecture source)</span></div>', unsafe_allow_html=True)
with row2:
    st.markdown('<div style="font-size:1.6rem;color:#06b6d4;display:flex;align-items:center;height:100%;padding-top:4px;">→</div>', unsafe_allow_html=True)
with row3:
    chosen_lang = st.selectbox(
        "Your language",
        LANG_LIST,
        index=LANG_LIST.index(st.session_state.target_lang),
        format_func=lambda l: f"{LANGUAGES[l]['flag']} {l}  ({LANGUAGES[l]['native']})",
        label_visibility="collapsed",
        key="lang_selector"
    )
    if chosen_lang != st.session_state.target_lang:
        st.session_state.target_lang = chosen_lang
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)
target_lang = st.session_state.target_lang
tl = LANGUAGES[target_lang]


# ── Stats ────────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f'<div class="stat-card"><span class="num">{st.session_state.seg_count}</span><span class="lbl">Segments</span></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="stat-card"><span class="num">{st.session_state.word_count}</span><span class="lbl">Words</span></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="stat-card"><span class="num" style="font-size:1rem;padding-top:6px">{tl["flag"]} {target_lang}</span><span class="lbl">Your Language</span></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Input Tabs ───────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["✍️ Paste English Text", "📁 Upload File", "❓ Ask About Lecture"])

# Tab 1 — paste text
with tab1:
    st.markdown(f'<div class="info-bar">📋 <b>Step 2:</b> Paste the lecturer\'s English words below → click <b>Translate to {target_lang}</b>.</div>', unsafe_allow_html=True)

    demo_pick = st.selectbox("Quick demo:", DEMO_SENTENCES, label_visibility="collapsed")
    prefill = "" if demo_pick == DEMO_SENTENCES[0] else demo_pick

    text_input = st.text_area(
        "English text",
        value=prefill,
        height=110,
        placeholder="Paste or type the English lecture text here…\nExample: Today we study the basics of neural networks.",
        label_visibility="collapsed"
    )

    if not has_key():
        st.error("⚠️ API key missing — open the **sidebar** (☰ top-left) and paste your Anthropic API key.")

    btn_label = f"🌐  Translate to {target_lang}  ({tl['native']})"
    translate_btn = st.button(btn_label, type="primary", use_container_width=True, disabled=not has_key())

    if translate_btn:
        txt = text_input.strip()
        if not txt:
            st.warning("Please enter some English text first.")
        else:
            with st.spinner(f"Translating to {target_lang}…"):
                result = translate_english(txt, target_lang)
            if result.get("error") == "no_key":
                st.error("No API key — enter it in the sidebar.")
            elif "error" in result:
                st.error(f"Error: {result['error']}")
            else:
                add_segment(result.get("original", txt), result.get("translation", ""), target_lang)
                st.success(f"✅ Translated to {target_lang}!")
                st.rerun()

# Tab 2 — file upload
with tab2:
    st.markdown('<div class="warn-bar">📁 Upload a <b>.txt</b> file of English lecture notes. The app will split it into segments and translate each one.</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload .txt file", type=["txt"], label_visibility="collapsed")

    if uploaded:
        st.info(f"📄 **{uploaded.name}** · {uploaded.size // 1024} KB")
        if not has_key():
            st.error("⚠️ API key missing — open the sidebar.")
        else:
            proc_btn = st.button("🚀 Translate File", type="primary", use_container_width=True)
            if proc_btn:
                content = uploaded.read().decode("utf-8", errors="ignore")
                words = content.split()
                chunks = [" ".join(words[i:i+150]) for i in range(0, min(len(words), 750), 150)]
                prog = st.progress(0, text="Translating…")
                for idx, chunk in enumerate(chunks):
                    if chunk.strip():
                        res = translate_english(chunk, target_lang)
                        if "error" not in res:
                            add_segment(res.get("original", chunk), res.get("translation", ""), target_lang)
                    prog.progress((idx + 1) / len(chunks), text=f"Segment {idx+1}/{len(chunks)}")
                prog.empty()
                st.success(f"✅ {len(chunks)} segment(s) translated!")
                st.rerun()

# Tab 3 — Q&A
with tab3:
    ctx = get_full_transcript()
    if not ctx:
        st.markdown('<div class="no-content">📭 No lecture content yet — add segments in the other tabs first.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="info-bar">💬 Ask anything about the lecture. Your answer will be in <b>{target_lang} ({tl["native"]})</b>.</div>', unsafe_allow_html=True)
        question = st.text_input("Question", placeholder=f"Ask in any language — answer comes in {target_lang}…", label_visibility="collapsed")
        ask_btn = st.button("💬 Get Answer", type="primary", use_container_width=True, disabled=not has_key())
        if ask_btn and question:
            with st.spinner(f"Thinking in {target_lang}…"):
                st.session_state.qna_answer = answer_in_lang(question, ctx, target_lang)
        if st.session_state.qna_answer:
            st.markdown(f'<div class="qna-answer">{st.session_state.qna_answer}</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Transcript + Translation panes ──────────────────────────────────────────
left, right = st.columns(2, gap="large")

with left:
    st.markdown('<div class="section-label">🇬🇧 English — Original</div>', unsafe_allow_html=True)
    if st.session_state.segments:
        html = "".join(f"""<div class="segment-line">
          <span class="ts">{s['ts']} · English</span>{s['original'] or '—'}
        </div>""" for s in reversed(st.session_state.segments[-30:]))
        st.markdown(f'<div class="transcript-box">{html}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="transcript-box"><div class="no-content">English text appears here after translation…</div></div>', unsafe_allow_html=True)

with right:
    st.markdown(f'<div class="section-label">{tl["flag"]} {target_lang} ({tl["native"]}) — Translation</div>', unsafe_allow_html=True)
    if st.session_state.segments:
        html = "".join(f"""<div class="segment-line">
          <span class="ts">{s['ts']} · {s['target_lang']}</span>{s['translation'] or '—'}
        </div>""" for s in reversed(st.session_state.segments[-30:]))
        st.markdown(f'<div class="translation-box">{html}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="translation-box"><div class="no-content">Translation appears here…</div></div>', unsafe_allow_html=True)

# ── Export ───────────────────────────────────────────────────────────────────
if st.session_state.segments:
    st.markdown("---")
    e1, e2 = st.columns(2)
    with e1:
        st.download_button("⬇️ English Transcript (.txt)",
            "\n\n".join(f"[{s['ts']}]\n{s['original']}" for s in st.session_state.segments),
            file_name=f"transcript_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain", use_container_width=True)
    with e2:
        st.download_button(f"⬇️ {target_lang} Translation (.txt)",
            "\n\n".join(f"[{s['ts']}] {s['target_lang']}\n{s['translation']}" for s in st.session_state.segments),
            file_name=f"translation_{target_lang}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain", use_container_width=True)

st.markdown('<div style="text-align:center;padding:24px 0 8px;color:#334155;font-size:0.78rem;">Deploy on Streamlit Cloud · Share URL with students · Each picks their own language 📱</div>', unsafe_allow_html=True)
