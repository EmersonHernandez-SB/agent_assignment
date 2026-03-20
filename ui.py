import uuid
import requests
import streamlit as st

try:
    import markdown as md_lib
    _HAS_MD = True
except ImportError:
    _HAS_MD = False

API_URL = "http://localhost:8000"

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────

st.set_page_config(page_title="EmerClinic Support", layout="centered")

# ─────────────────────────────────────────────
# GLOBAL STYLES
# ─────────────────────────────────────────────

st.markdown("""
<style>
  #MainMenu, footer, header { visibility: hidden; }

  html, body, [class*="css"] {
    font-family: "Inter", "Segoe UI", system-ui, sans-serif;
  }

  .stApp { background-color: #f8fafc; }

  section[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #e2e8f0;
  }

  /* ── Buttons ──────────────────────────────── */
  .stButton > button {
    background-color: #1e40af !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 0.84rem !important;
    font-weight: 500 !important;
    transition: background 0.15s !important;
  }
  .stButton > button:hover { background-color: #1d3a9e !important; }

  div[data-testid="stForm"] button {
    background-color: #1e40af !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
  }
  div[data-testid="stForm"] button:hover {
    background-color: #1d3a9e !important;
  }

  /* ── Text input ───────────────────────────── */
  div[data-testid="stTextInput"] input {
    border-radius: 8px !important;
    border: 1px solid #e2e8f0 !important;
    background: #ffffff !important;
    font-size: 0.88rem !important;
    color: #0f172a !important;
  }
  div[data-testid="stTextInput"] input:focus {
    border-color: #1e40af !important;
    box-shadow: 0 0 0 2px rgba(30,64,175,0.12) !important;
  }

  /* ── Chat window ──────────────────────────── */
  /*
   * flex-direction: column-reverse means the first DOM element appears at the
   * bottom. We render messages newest-first so the most recent is always
   * visible without any JS scroll tricks.
   */
  #chat-window {
    height: 460px;
    overflow-y: auto;
    display: flex;
    flex-direction: column-reverse;
    gap: 2px;
    padding: 10px 12px 6px 12px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    margin-bottom: 12px;
  }

  /* ── Message bubbles ──────────────────────── */
  .msg-user {
    display: flex;
    justify-content: flex-end;
    margin: 2px 0;
  }
  .msg-user .bubble {
    background: #1e40af;
    color: #ffffff;
    padding: 9px 13px;
    border-radius: 16px 16px 4px 16px;
    max-width: 74%;
    font-size: 0.875rem;
    line-height: 1.55;
    word-wrap: break-word;
  }

  .msg-agent {
    display: flex;
    justify-content: flex-start;
    margin: 2px 0;
  }
  .msg-agent .bubble {
    background: #f1f5f9;
    color: #0f172a;
    padding: 9px 13px;
    border-radius: 16px 16px 16px 4px;
    max-width: 74%;
    font-size: 0.875rem;
    line-height: 1.55;
    word-wrap: break-word;
  }

  /* Markdown inside agent bubbles */
  .msg-agent .bubble h1,
  .msg-agent .bubble h2,
  .msg-agent .bubble h3 {
    font-size: 0.95rem;
    font-weight: 700;
    margin: 8px 0 4px 0;
    color: #0f172a;
  }
  .msg-agent .bubble ul,
  .msg-agent .bubble ol { padding-left: 16px; margin: 4px 0; }
  .msg-agent .bubble li { margin: 2px 0; }
  .msg-agent .bubble p  { margin: 3px 0; }
  .msg-agent .bubble code {
    background: #e2e8f0;
    padding: 1px 4px;
    border-radius: 3px;
    font-size: 0.82em;
    font-family: monospace;
  }
  .msg-agent .bubble table {
    border-collapse: collapse;
    font-size: 0.82rem;
    margin: 6px 0;
    width: 100%;
  }
  .msg-agent .bubble th,
  .msg-agent .bubble td {
    border: 1px solid #cbd5e1;
    padding: 4px 8px;
    text-align: left;
  }
  .msg-agent .bubble th { background: #e2e8f0; font-weight: 600; }

  .agent-label {
    font-size: 0.67rem;
    color: #94a3b8;
    margin-bottom: 3px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }

  /* ── Typing dots ──────────────────────────── */
  .typing-dots {
    display: flex;
    gap: 5px;
    padding: 11px 14px;
    background: #f1f5f9;
    border-radius: 16px 16px 16px 4px;
    align-items: center;
    width: fit-content;
  }
  .typing-dots span {
    width: 7px;
    height: 7px;
    background: #94a3b8;
    border-radius: 50%;
    display: inline-block;
    animation: typingBounce 1.3s infinite ease-in-out;
  }
  .typing-dots span:nth-child(1) { animation-delay: 0.0s; }
  .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
  .typing-dots span:nth-child(3) { animation-delay: 0.4s; }
  @keyframes typingBounce {
    0%, 60%, 100% { transform: translateY(0);   opacity: 0.45; }
    30%            { transform: translateY(-7px); opacity: 1;    }
  }

  /* ── Sidebar ──────────────────────────────── */
  .sb-title {
    font-size: 0.71rem;
    font-weight: 600;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin: 16px 0 6px 0;
  }
  .thread-pill {
    display: inline-block;
    background: #f1f5f9;
    color: #475569;
    border-radius: 999px;
    padding: 3px 10px;
    font-size: 0.71rem;
    font-family: monospace;
    border: 1px solid #e2e8f0;
  }
  .cap-list { margin: 0; padding-left: 0; list-style: none; }
  .cap-list li {
    font-size: 0.81rem;
    color: #475569;
    padding: 4px 0;
    border-bottom: 1px solid #f1f5f9;
  }
  .cap-list li::before { content: "–"; color: #cbd5e1; margin-right: 8px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thinking" not in st.session_state:
    st.session_state.thinking = False

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

_LOGO = (
    '<svg width="28" height="28" viewBox="0 0 28 28" xmlns="http://www.w3.org/2000/svg">'
    '<rect width="28" height="28" rx="6" fill="#1e40af"/>'
    '<rect x="11" y="5" width="6" height="18" rx="2" fill="white"/>'
    '<rect x="5" y="11" width="18" height="6" rx="2" fill="white"/>'
    '</svg>'
)

_LOGO_LG = (
    '<svg width="34" height="34" viewBox="0 0 34 34" xmlns="http://www.w3.org/2000/svg">'
    '<rect width="34" height="34" rx="7" fill="#1e40af"/>'
    '<rect x="14" y="7" width="6" height="20" rx="2" fill="white"/>'
    '<rect x="7" y="14" width="20" height="6" rx="2" fill="white"/>'
    '</svg>'
)

_DOTS = (
    '<div class="msg-agent">'
    '<div class="typing-dots"><span></span><span></span><span></span></div>'
    '</div>'
)


def _md(text: str) -> str:
    """Convert markdown to HTML for agent bubbles."""
    if _HAS_MD:
        return md_lib.markdown(text, extensions=["tables", "nl2br"])
    return text.replace("\n", "<br>")


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_chat_html(messages: list, thinking: bool = False) -> str:
    """
    Build the full inner HTML for #chat-window.
    Messages are rendered newest-first in the DOM so that
    flex-direction: column-reverse shows the latest at the bottom.
    """
    parts = []

    if thinking:
        parts.append(_DOTS)

    for msg in reversed(messages):
        if msg["role"] == "user":
            parts.append(
                f'<div class="msg-user">'
                f'<div class="bubble">{_escape(msg["content"])}</div>'
                f'</div>'
            )
        else:
            agent   = msg.get("agent", "agent").replace("_", " ").title()
            content = _md(msg["content"])
            parts.append(
                f'<div class="msg-agent"><div>'
                f'<div class="agent-label">{agent}</div>'
                f'<div class="bubble">{content}</div>'
                f'</div></div>'
            )

    return "\n".join(parts)


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:9px;padding:8px 0 4px 0;">'
        f'{_LOGO}'
        f'<span style="font-size:0.95rem;font-weight:700;color:#0f172a;">EmerClinic</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<p class="sb-title">Session</p>', unsafe_allow_html=True)
    st.markdown(
        f'<span class="thread-pill">{st.session_state.thread_id[:20]}…</span>',
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("New conversation", use_container_width=True):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.messages  = []
        st.session_state.thinking  = False
        st.rerun()

    st.markdown('<p class="sb-title" style="margin-top:20px;">Capabilities</p>', unsafe_allow_html=True)
    st.markdown("""
<ul class="cap-list">
  <li>Appointment scheduling</li>
  <li>Patient record lookup</li>
  <li>Billing &amp; subscription</li>
  <li>Software how-to (FAQ)</li>
  <li>Escalation to human agent</li>
</ul>
""", unsafe_allow_html=True)

    st.markdown('<p class="sb-title" style="margin-top:20px;">API</p>', unsafe_allow_html=True)
    api_url = st.text_input("api", value=API_URL, label_visibility="collapsed")

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────

st.markdown(
    f'<div style="display:flex;align-items:center;gap:12px;padding:16px 0 14px 0;'
    f'border-bottom:1px solid #e2e8f0;margin-bottom:16px;">'
    f'{_LOGO_LG}'
    f'<div>'
    f'<div style="font-size:1.2rem;font-weight:700;color:#0f172a;line-height:1.2;">'
    f'EmerClinic Support</div>'
    f'<div style="font-size:0.77rem;color:#64748b;">'
    f'AI-powered assistant — scheduling, billing, clinic operations</div>'
    f'</div></div>',
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# CHAT WINDOW
# ─────────────────────────────────────────────

is_thinking = st.session_state.thinking
msgs_html   = build_chat_html(st.session_state.messages, thinking=is_thinking)

if msgs_html:
    window_inner = msgs_html
else:
    window_inner = (
        '<div style="margin:auto;text-align:center;color:#94a3b8;font-size:0.88rem;">'
        'How can I help you today?'
        '</div>'
    )

# st.empty() lets us write to this slot immediately; the browser shows
# the content (including dots) while the API call below is blocking.
chat_slot = st.empty()
chat_slot.markdown(
    f'<div id="chat-window">{window_inner}</div>',
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# API CALL (blocking — dots are visible here)
# ─────────────────────────────────────────────

if is_thinking:
    last_user = next(
        m["content"] for m in reversed(st.session_state.messages)
        if m["role"] == "user"
    )
    try:
        resp = requests.post(
            f"{api_url}/chat",
            json={"message": last_user, "thread_id": st.session_state.thread_id},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        st.session_state.messages.append({
            "role":    "agent",
            "content": data["reply"],
            "agent":   data.get("agent", "agent"),
        })
    except requests.exceptions.ConnectionError:
        st.session_state.messages.append({
            "role":    "agent",
            "content": f"Could not reach the API at `{api_url}`. Make sure the server is running.",
            "agent":   "system",
        })
    except Exception as exc:
        st.session_state.messages.append({
            "role":    "agent",
            "content": f"Unexpected error: {exc}",
            "agent":   "system",
        })

    st.session_state.thinking = False
    st.rerun()

# ─────────────────────────────────────────────
# INPUT FORM
# ─────────────────────────────────────────────

st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)

with st.form("chat_form", clear_on_submit=True):
    col_input, col_btn = st.columns([6, 1])
    with col_input:
        user_input = st.text_input(
            "message",
            placeholder="Type a message...",
            label_visibility="collapsed",
        )
    with col_btn:
        submitted = st.form_submit_button("Send", use_container_width=True)

if submitted and user_input.strip() and not st.session_state.thinking:
    st.session_state.messages.append({"role": "user", "content": user_input.strip()})
    st.session_state.thinking = True
    st.rerun()
