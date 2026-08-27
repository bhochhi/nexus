"""Next-generation Streamlit member chat for the live-support demo."""

import html
import os
from typing import Any, Dict
from urllib.parse import quote
import uuid

import streamlit as st
import streamlit.components.v1 as components

from member_assistant.ui_client import RealtimeWebSocketClient


st.set_page_config(page_title="Nexus Member", page_icon="✦", layout="centered")

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@600;700&display=swap');
:root { --ink:#10213a; --muted:#6b7a90; --aqua:#35d2ba; --blue:#2356d8; --panel:#ffffff; }
.stApp { background: radial-gradient(circle at 10% 0%, #dff9f3 0, transparent 33%), radial-gradient(circle at 95% 12%, #e3eaff 0, transparent 30%), #f5f7fb; color:var(--ink); }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
h1,h2,h3 { font-family:'Manrope',sans-serif; letter-spacing:-.04em; }
.block-container { max-width:820px; padding-top:2rem; }
.hero { padding:1rem 1.25rem; border-radius:14px; color:white; background:linear-gradient(135deg,#112b52,#2356d8 68%,#25bca8); box-shadow:0 16px 35px rgba(31,73,156,.18); margin-bottom:1rem; }
.hero h1 { color:white; margin:0 0 .2rem; font-size:1.35rem; }
.hero p { opacity:.9; margin:0; font-size:.9rem; }
.statusbar { display:flex; align-items:center; justify-content:space-between; padding:.72rem 1rem; background:rgba(255,255,255,.82); border:1px solid rgba(29,63,114,.09); border-radius:18px; backdrop-filter:blur(12px); margin:.7rem 0 1rem; }
.statusdot { width:9px; height:9px; border-radius:50%; background:#35d2ba; box-shadow:0 0 0 5px rgba(53,210,186,.14); display:inline-block; margin-right:.55rem; }
.soft { color:var(--muted); font-size:.86rem; }
[data-testid="stVerticalBlock"][style*="height"] { height:min(480px, calc(100vh - 320px)) !important; }
[data-testid="stChatMessage"] { border:1px solid rgba(26,54,92,.07); border-radius:20px; padding:.2rem .65rem; background:rgba(255,255,255,.78); box-shadow:0 8px 25px rgba(35,61,100,.055); }
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] [data-testid="stCaptionContainer"] { color:#10213a !important; }
[data-testid="stTextInput"] [data-baseweb="input"], [data-testid="stTextInput"] [data-baseweb="input"] > div, [data-testid="stChatInput"], [data-testid="stChatInput"] > div, [data-testid="stChatInput"] [data-baseweb="textarea"], [data-testid="stChatInput"] [data-baseweb="textarea"] > div { border-radius:20px; background-color:#fff !important; box-shadow:0 12px 30px rgba(35,61,100,.1); }
[data-testid="stTextInput"] input, [data-testid="stChatInput"] textarea { background-color:#fff !important; color:#10213a !important; -webkit-text-fill-color:#10213a !important; caret-color:#2356d8 !important; }
[data-testid="stTextInput"] input::placeholder, [data-testid="stChatInput"] textarea::placeholder { color:#6b7a90 !important; -webkit-text-fill-color:#6b7a90 !important; opacity:1; }
[data-testid="stButton"] button { background:#fff; border:1px solid rgba(26,54,92,.12); }
[data-testid="stButton"] button p { color:#10213a !important; }
[data-testid="stFormSubmitButton"] button { background:linear-gradient(90deg,#2356d8,#24bca8); border:0; }
[data-testid="stFormSubmitButton"] button p { color:#fff !important; }
[data-testid="stForm"] { background:rgba(255,255,255,.82); border:1px solid rgba(26,54,92,.08); border-radius:24px; padding:1.2rem; box-shadow:0 18px 45px rgba(35,61,100,.08); }
.livecard { border:1px solid rgba(35,86,216,.16); background:linear-gradient(135deg,#fff,#eef3ff); padding:1rem 1.1rem; border-radius:20px; margin-bottom:1rem; }
</style>
""",
    unsafe_allow_html=True,
)


def _base_url() -> str:
    return os.getenv("MEMBER_ASSISTANT_SERVER_URL", "ws://127.0.0.1:8000").rstrip("/")


def _reset() -> None:
    client = st.session_state.get("client")
    if client:
        client.close()
    for key in list(st.session_state):
        del st.session_state[key]


st.session_state.setdefault("client", None)
st.session_state.setdefault("messages", [])
st.session_state.setdefault("event_ids", set())
st.session_state.setdefault("mode", "virtual")
st.session_state.setdefault("case", None)
st.session_state.setdefault("connection", "connecting")
st.session_state.setdefault("notice", "")
st.session_state.setdefault("member_ready", False)
st.session_state.setdefault("last_scrolled_message_count", 0)

st.markdown(
    """<div class="hero"><h1>Conversation-First Member Experience</h1>
    <p>Conversationally adaptive, operationally governed</p></div>""",
    unsafe_allow_html=True,
)

if st.session_state.client is None:
    with st.form("member_login"):
        st.subheader("Start your secure conversation")
        name = st.text_input("Name", placeholder="Your name")
        member_id = st.text_input(
            "Member ID",
            placeholder="member-1001",
            help="This becomes the durable session ID. Reuse it in another window to reconnect.",
        )
        submitted = st.form_submit_button("Enter member space", type="primary", use_container_width=True)
    if submitted:
        clean_name = " ".join(name.split())
        clean_id = member_id.strip()
        if not clean_name or not clean_id:
            st.error("Name and Member ID are required.")
        else:
            socket_url = "{}/v1/sessions/{}/stream".format(
                _base_url(), quote(clean_id, safe="")
            )
            st.session_state.name = clean_name
            st.session_state.member_id = clean_id
            st.session_state.client = RealtimeWebSocketClient(
                socket_url,
                {"type": "member.join", "name": clean_name},
            )
            st.rerun()
    st.stop()


def _add_message(
    role: str, content: str, identity: str = "", message_id: str = ""
) -> None:
    st.session_state.messages.append(
        {
            "role": role,
            "content": content,
            "identity": identity,
            "message_id": message_id,
        }
    )


def _process(event: Dict[str, Any]) -> None:
    event_type = event.get("type")
    event_id = event.get("event_id")
    if event_id and event_id in st.session_state.event_ids:
        return
    if event_id:
        st.session_state.event_ids.add(event_id)
    if event_type == "connection.open":
        st.session_state.connection = "connected"
    elif event_type == "member.ready":
        st.session_state.name = str(event.get("member_name", st.session_state.name))
        st.session_state.member_ready = True
    elif event_type == "connection.error":
        st.session_state.connection = "reconnecting"
        st.session_state.notice = event.get("error", "Connection interrupted")
    elif event_type == "session.ready":
        st.session_state.messages = [
            {
                "role": item.get("role", "assistant"),
                "content": item.get("content", ""),
                "identity": "",
                "message_id": "",
            }
            for item in event.get("messages", [])
        ]
        case = event.get("live_case")
        if case:
            st.session_state.case = case
            st.session_state.mode = case.get("status", "waiting")
            for message in case.get("messages", []):
                role = (
                    "assistant"
                    if message.get("sender_type") == "agent"
                    else "user"
                )
                _add_message(
                    role,
                    str(message.get("content", "")),
                    str(message.get("sender_name", "")),
                    str(message.get("message_id", "")),
                )
    elif event_type in {
        "assistant.message",
        "assistant.request_input",
        "assistant.request_confirmation",
        "handoff.offered",
    }:
        _add_message("assistant", str(event.get("content", "")), "Nexus assistant")
        st.session_state.notice = ""
    elif event_type == "turn.accepted":
        st.session_state.notice = "Nexus is thinking…"
    elif event_type == "turn.completed":
        st.session_state.notice = ""
    elif event_type == "live_support.waiting":
        st.session_state.case = event.get("case")
        st.session_state.mode = "waiting"
        st.session_state.notice = event.get("message", "Waiting for an MSR")
    elif event_type == "live_support.assigned":
        st.session_state.case = event.get("case")
        st.session_state.mode = "connected"
        agent = (event.get("case") or {}).get("agent_name", "your MSR")
        _add_message("assistant", "You're now connected with {}.".format(agent), "System")
        st.session_state.notice = ""
    elif event_type == "live.message":
        message = event.get("message", {})
        message_id = str(message.get("message_id", ""))
        if not any(
            item.get("message_id") == message_id
            for item in st.session_state.messages
            if message_id
        ):
            role = "assistant" if message.get("sender_type") == "agent" else "user"
            _add_message(
                role,
                str(message.get("content", "")),
                str(message.get("sender_name", "MSR")),
                message_id,
            )
    elif event_type in {"live_support.ended", "live_support.cancelled"}:
        st.session_state.case = None
        st.session_state.mode = "virtual"
        st.session_state.notice = ""
    elif event_type == "protocol.error":
        st.session_state.notice = str(event.get("error", "Something went wrong"))


@st.fragment(run_every=0.6)
def conversation() -> None:
    for incoming in st.session_state.client.drain():
        _process(incoming)

    mode = st.session_state.mode
    case = st.session_state.case or {}
    status_label = {
        "virtual": "Nexus assistant",
        "waiting": "Waiting for a specialist",
        "connected": "Live with {}".format(case.get("agent_name", "an MSR")),
    }.get(mode, "Connected")
    st.markdown(
        '<div class="statusbar"><div><span class="statusdot"></span><b>{}</b></div><div class="soft">Member ID · {}</div></div>'.format(
            html.escape(status_label), html.escape(st.session_state.member_id)
        ),
        unsafe_allow_html=True,
    )

    if mode == "waiting":
        st.markdown(
            '<div class="livecard"><b>{} queue</b><br><span class="soft">{} You may cancel and continue with the virtual assistant.</span></div>'.format(
                html.escape(str(case.get("queue", "live support")).title()),
                html.escape(st.session_state.notice or "We’ll connect you automatically."),
            ),
            unsafe_allow_html=True,
        )
        if st.button("Cancel live support", use_container_width=True):
            try:
                st.session_state.client.send({"type": "live_support.cancel"})
            except ConnectionError as exc:
                st.session_state.notice = str(exc)

    with st.container(height=480, border=False):
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                if message.get("identity"):
                    st.caption(message["identity"])
                st.markdown(message["content"])

    message_count = len(st.session_state.messages)
    if message_count != st.session_state.last_scrolled_message_count:
        components.html(
            """
            <script>
            window.parent.requestAnimationFrame(() => {
                const transcript = [...window.parent.document.querySelectorAll('[data-testid="stVerticalBlock"]')]
                    .find(node => window.parent.getComputedStyle(node).overflowY === "auto");
                if (transcript) transcript.scrollTo({ top: transcript.scrollHeight, behavior: "smooth" });
            });
            </script>
            """,
            height=0,
        )
        st.session_state.last_scrolled_message_count = message_count

    if st.session_state.notice and mode != "waiting":
        st.caption(st.session_state.notice)

    disabled = mode == "waiting" or not st.session_state.member_ready
    prompt = (
        "Message your MSR…  (/end to finish)"
        if mode == "connected"
        else "Connecting your member profile…"
        if not st.session_state.member_ready
        else "How can we help?"
    )
    message = st.chat_input(prompt, disabled=disabled)
    if message:
        message_id = "msg_{}".format(uuid.uuid4().hex)
        if message.strip() != "/end":
            _add_message("user", message, st.session_state.name, message_id)
        try:
            st.session_state.client.send(
                {
                    "type": "member.message",
                    "message_id": message_id,
                    "content": message,
                }
            )
        except ConnectionError as exc:
            st.session_state.notice = str(exc)
        st.rerun(scope="fragment")

    st.divider()
    left, right = st.columns([3, 1])
    left.caption("Signed in as {} · responses are shared across windows using this Member ID.".format(st.session_state.name))
    if right.button("Leave UI", use_container_width=True):
        _reset()
        st.rerun()


conversation()
