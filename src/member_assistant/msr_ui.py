"""Streamlit workspace for multi-member live support representatives."""

import html
import os
from typing import Any, Dict
from urllib.parse import quote
import uuid

import streamlit as st

from member_assistant.live_support import LIVE_SUPPORT_QUEUES
from member_assistant.ui_client import RealtimeWebSocketClient


st.set_page_config(page_title="Nexus MSR Console", page_icon="◈", layout="wide")
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@600;700&display=swap');
.stApp { background:linear-gradient(145deg,#071527 0,#0b203a 54%,#0d2944 100%); color:#edf5ff; }
html,body,[class*="css"] { font-family:'DM Sans',sans-serif; }
h1,h2,h3,p,label,[data-testid="stCaptionContainer"] { color:#edf5ff !important; }
h1,h2,h3 { font-family:'Manrope',sans-serif; letter-spacing:-.035em; }
.block-container { max-width:1480px; padding-top:1.4rem; }
.topbar { display:flex; align-items:center; justify-content:space-between; background:rgba(13,40,68,.68); border:1px solid rgba(136,196,255,.14); border-radius:22px; padding:1.1rem 1.3rem; box-shadow:0 22px 50px rgba(0,0,0,.22); }
.brand { font-family:'Manrope'; font-size:1.35rem; font-weight:700; }.brand span{color:#54dfc3}.tiny{color:#91a8c3;font-size:.8rem;}
.metric { background:rgba(255,255,255,.055); border:1px solid rgba(135,194,255,.12); border-radius:18px; padding:.85rem 1rem; min-height:84px; }
.metric strong { font-size:1.65rem; color:#fff; }.metric small{display:block;color:#91a8c3;text-transform:uppercase;letter-spacing:.1em;font-size:.67rem;}
.summary { background:linear-gradient(135deg,rgba(50,91,158,.34),rgba(22,119,112,.2)); border:1px solid rgba(84,223,195,.22); border-radius:18px; padding:1rem 1.15rem; margin:.7rem 0 1rem; color:#dcecff; }
.summary b {color:#68ead0;text-transform:uppercase;letter-spacing:.12em;font-size:.7rem;}
[data-testid="stChatMessage"] { background:rgba(255,255,255,.055); border:1px solid rgba(135,194,255,.09); border-radius:18px; }
[data-testid="stChatInput"] { background:#fff; border-radius:18px; }
[data-testid="stForm"] { background:rgba(255,255,255,.06); border:1px solid rgba(135,194,255,.15); border-radius:22px; padding:1.2rem; }
.sentiment { display:grid; grid-template-columns:repeat(5,1fr); gap:.5rem; padding:.7rem 0 .25rem; }
.sentiment .item {text-align:center;color:#8299b5;font-size:.67rem}.sentiment .dot{width:12px;height:12px;border-radius:50%;background:#31465f;margin:0 auto .42rem;box-shadow:inset 0 0 0 1px #49617c}
.sentiment .active .dot{background:#54dfc3;box-shadow:0 0 0 5px rgba(84,223,195,.12),0 0 18px rgba(84,223,195,.55)}
.sentiment .negative.active .dot{background:#ffb94e}.sentiment .frustrated.active .dot{background:#ff6577}.sentiment .active{color:#eaf4ff;font-weight:700}
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
st.session_state.setdefault("cases", {})
st.session_state.setdefault("queue_status", {})
st.session_state.setdefault("connection", "connecting")
st.session_state.setdefault("notice", "")
st.session_state.setdefault("selected_case", None)

if st.session_state.client is None:
    st.markdown('<div class="topbar"><div><div class="brand">Nexus <span>Live</span></div><div class="tiny">Member Service Representative workspace</div></div></div>', unsafe_allow_html=True)
    st.write("")
    center = st.columns([1, 1.35, 1])[1]
    with center:
        with st.form("agent_login"):
            st.subheader("Join a service queue")
            name = st.text_input("MSR name", placeholder="Morgan Taylor")
            service_queue = st.selectbox("Queue", LIVE_SUPPORT_QUEUES, format_func=str.title)
            submitted = st.form_submit_button("Go available", type="primary", use_container_width=True)
        if submitted:
            clean_name = " ".join(name.split())
            if not clean_name:
                st.error("Your name is required.")
            else:
                agent_id = "agent_{}".format(uuid.uuid4().hex)
                socket_url = "{}/v1/live-support/agents/{}/stream".format(
                    _base_url(), quote(agent_id, safe="")
                )
                st.session_state.agent_id = agent_id
                st.session_state.name = clean_name
                st.session_state.queue = service_queue
                st.session_state.client = RealtimeWebSocketClient(
                    socket_url,
                    {"type": "agent.join", "name": clean_name, "queue": service_queue},
                )
                st.rerun()
    st.stop()


def _merge_case(case: Dict[str, Any]) -> None:
    case_id = str(case.get("case_id", ""))
    if not case_id:
        return
    existing = st.session_state.cases.get(case_id, {})
    merged = {**existing, **case}
    merged.setdefault("messages", existing.get("messages", []))
    st.session_state.cases[case_id] = merged
    if not st.session_state.selected_case:
        st.session_state.selected_case = case_id


def _process(event: Dict[str, Any]) -> None:
    event_type = event.get("type")
    if event_type == "connection.open":
        st.session_state.connection = "connected"
    elif event_type == "connection.error":
        st.session_state.connection = "reconnecting"
        st.session_state.notice = event.get("error", "Connection interrupted")
    elif event_type == "agent.ready":
        st.session_state.connection = "available"
        st.session_state.queue_status = event.get("queue_status", {})
        for case in event.get("cases", []):
            _merge_case(case)
    elif event_type == "queue.updated":
        st.session_state.queue_status = event.get("queue_status", {})
    elif event_type == "live_support.assigned":
        _merge_case(event.get("case", {}))
        st.session_state.notice = "New member assigned"
    elif event_type == "live.message":
        message = event.get("message", {})
        case_id = str(message.get("case_id", ""))
        case = st.session_state.cases.get(case_id)
        if case is not None and not any(
            item.get("message_id") == message.get("message_id")
            for item in case.setdefault("messages", [])
        ):
            case["messages"].append(message)
    elif event_type == "sentiment.updated":
        case = st.session_state.cases.get(str(event.get("case_id", "")))
        if case is not None:
            case["sentiment"] = event.get("sentiment", "unknown")
            case["sentiment_confidence"] = event.get("confidence", 0.0)
    elif event_type == "live_support.ended":
        case = event.get("case", {})
        case_id = str(case.get("case_id", ""))
        st.session_state.cases.pop(case_id, None)
        st.session_state.selected_case = next(iter(st.session_state.cases), None)
    elif event_type == "protocol.error":
        st.session_state.notice = str(event.get("error", "Something went wrong"))


def _sentiment_html(value: str) -> str:
    values = ["positive", "neutral", "negative", "frustrated", "unknown"]
    cells = []
    for item in values:
        active = value == item and item != "unknown"
        classes = "item {} {}".format(item, "active" if active else "")
        cells.append('<div class="{}"><div class="dot"></div>{}</div>'.format(classes, item.title()))
    return '<div class="sentiment">{}</div>'.format("".join(cells))


@st.fragment(run_every=0.6)
def console() -> None:
    for incoming in st.session_state.client.drain():
        _process(incoming)

    queue_data = st.session_state.queue_status.get(st.session_state.queue, {})
    st.markdown(
        '<div class="topbar"><div><div class="brand">Nexus <span>Live</span></div><div class="tiny">{} · {} queue · {}</div></div><div class="tiny">● {}</div></div>'.format(
            html.escape(st.session_state.name),
            html.escape(st.session_state.queue.title()),
            html.escape(st.session_state.agent_id[-8:]),
            html.escape(st.session_state.connection.title()),
        ),
        unsafe_allow_html=True,
    )
    st.write("")
    metrics = st.columns(4)
    values = [
        (len(st.session_state.cases), "Active members"),
        (queue_data.get("waiting", 0), "Waiting"),
        (queue_data.get("online_agents", 0), "MSRs online"),
        (queue_data.get("connected", 0), "Queue conversations"),
    ]
    for column, (value, label) in zip(metrics, values):
        column.markdown('<div class="metric"><strong>{}</strong><small>{}</small></div>'.format(value, label), unsafe_allow_html=True)

    st.write("")
    case_ids = list(st.session_state.cases)
    if not case_ids:
        st.info("You’re available. A member will appear here automatically when assigned.")
    else:
        labels = {
            case_id: "{} · {}".format(
                st.session_state.cases[case_id].get("member_name", "Member"),
                st.session_state.cases[case_id].get("sentiment", "unknown").title(),
            )
            for case_id in case_ids
        }
        selected = st.radio(
            "Member conversations",
            case_ids,
            index=max(0, case_ids.index(st.session_state.selected_case)) if st.session_state.selected_case in case_ids else 0,
            format_func=lambda value: labels[value],
            horizontal=True,
            label_visibility="collapsed",
        )
        st.session_state.selected_case = selected
        case = st.session_state.cases[selected]
        left, right = st.columns([2.15, 1])
        with left:
            st.subheader(case.get("member_name", "Member"))
            st.caption("Member ID · {}  |  Case · {}".format(case.get("session_id"), case.get("case_id")))
            st.markdown(
                '<div class="summary"><b>System message · Summary</b><br>{}</div>'.format(
                    html.escape(
                        str(case.get("summary", "No summary available."))
                    ).replace("\n", "<br>")
                ),
                unsafe_allow_html=True,
            )
            for message in case.get("messages", []):
                role = "user" if message.get("sender_type") == "member" else "assistant"
                with st.chat_message(role):
                    st.caption(message.get("sender_name", ""))
                    st.markdown(str(message.get("content", "")))
            response = st.chat_input("Reply to {}…  (/end to finish)".format(case.get("member_name", "member")), key="msr_reply")
            if response:
                try:
                    st.session_state.client.send(
                        {
                            "type": "agent.message",
                            "case_id": selected,
                            "message_id": "live_msg_{}".format(uuid.uuid4().hex),
                            "content": response,
                        }
                    )
                except ConnectionError as exc:
                    st.session_state.notice = str(exc)
                st.rerun(scope="fragment")
        with right:
            st.subheader("Member signal")
            sentiment = str(case.get("sentiment", "unknown"))
            st.markdown(_sentiment_html(sentiment), unsafe_allow_html=True)
            confidence = float(case.get("sentiment_confidence", 0.0))
            st.caption("Signal confidence · {:.0%}".format(confidence))
            st.divider()
            st.caption("ROUTED QUEUE")
            st.markdown("### {}".format(str(case.get("queue", "")).title()))
            st.caption("REASON")
            st.write(case.get("reason", "Not provided"))
            st.divider()
            if st.button("End conversation", type="primary", use_container_width=True):
                try:
                    st.session_state.client.send({"type": "agent.end", "case_id": selected})
                except ConnectionError as exc:
                    st.session_state.notice = str(exc)

    if st.session_state.notice:
        st.caption(st.session_state.notice)
    st.divider()
    if st.button("Go offline", use_container_width=False):
        _reset()
        st.rerun()


console()
