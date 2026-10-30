"""Streamlit frontend for the existing AI Customer Support backend."""
from __future__ import annotations

import json
import streamlit as st

from services.chat_service import stream_chat
from services.conversation_service import (
    create_support_conversation,
    get_conversation_history,
    list_support_conversations,
)
from ui.components.activity import render_activity
from ui.components.chat import render_history
from ui.components.sidebar import render_sidebar
from ui.components.sources import render_sources
from ui.styles import apply_styles

st.set_page_config(page_title="Support Desk", page_icon="S", layout="wide", initial_sidebar_state="expanded")
apply_styles()


def _new_conversation() -> str | None:
    created = create_support_conversation(title="Customer support")
    if not created.get("ok"):
        st.error(created.get("error", "Could not start a conversation."))
        return None
    return created["conversation"]["conversation_id"]


if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = _new_conversation()
if "activity_events" not in st.session_state:
    st.session_state.activity_events = []
if "request_in_progress" not in st.session_state:
    st.session_state.request_in_progress = False
if "last_error" not in st.session_state:
    st.session_state.last_error = None
if "agent_activity_state" not in st.session_state:
    st.session_state.agent_activity_state = "ready"

if not st.session_state.conversation_id:
    st.stop()

conversations = list_support_conversations(limit=100)
selected_id, new_requested = render_sidebar(conversations, st.session_state.conversation_id)
if new_requested:
    new_id = _new_conversation()
    if new_id:
        st.session_state.conversation_id = new_id
        st.session_state.activity_events = []
        st.session_state.last_error = None
        st.session_state.agent_activity_state = "ready"
        st.rerun()
elif selected_id and selected_id != st.session_state.conversation_id:
    st.session_state.conversation_id = selected_id
    st.session_state.activity_events = []
    st.session_state.last_error = None
    st.session_state.agent_activity_state = "ready"
    st.rerun()

conversation_id = st.session_state.conversation_id
history_result = get_conversation_history(conversation_id)
if not history_result.get("ok"):
    st.error(history_result.get("error", "Could not load this conversation."))
    if st.button("Start a new conversation"):
        st.session_state.conversation_id = _new_conversation()
        st.rerun()
    st.stop()

messages = history_result.get("messages", [])
conversation = history_result.get("conversation", {})

header_left, header_right = st.columns([0.78, 0.22])
with header_left:
    st.markdown("<div class='brand-kicker'>SUPPORT WORKSPACE</div>", unsafe_allow_html=True)
    st.markdown("<h1 class='page-title'>Customer Support</h1>", unsafe_allow_html=True)
    st.markdown("<p class='page-subtitle'>Helpful answers, grounded in your support information.</p>", unsafe_allow_html=True)
with header_right:
    status = str(conversation.get("status", "active")).replace("_", " ").title()
    st.markdown(f"<div class='status-label'><span class='status-dot'></span>{status}</div>", unsafe_allow_html=True)

chat_col, context_col = st.columns([0.69, 0.31], gap="large")
assistant_messages = [m for m in messages if m.get("role") == "assistant"]
latest_assistant = assistant_messages[-1] if assistant_messages else {}
latest_metadata = latest_assistant.get("metadata") or {}

activity_status_labels = {
    "ready": ("Ready for your support question", "Ask a question to start."),
    "working": ("Agent is working", "Reviewing your request and available support information."),
    "completed": ("Response ready", "The request has completed."),
    "failed": ("Request needs attention", "The request did not complete successfully. Check the message and try again."),
}


def render_agent_activity(status_slot, events_slot) -> None:
    state = st.session_state.agent_activity_state
    label, detail = activity_status_labels.get(state, activity_status_labels["ready"])
    status_slot.markdown(
        f"<div class='agent-status agent-status--{state}'>"
        f"<span class='agent-status-dot'></span>"
        f"<span class='agent-status-copy'><strong>{label}</strong>"
        f"<small>{detail}</small></span></div>",
        unsafe_allow_html=True,
    )
    with events_slot.container():
        events = st.session_state.activity_events[-8:]
        if events:
            for event in events:
                render_activity(event)
        else:
            st.caption("Workflow stages will appear here while the agent works.")


with context_col:
    st.markdown("<div class='context-heading'>Response details</div>", unsafe_allow_html=True)
    st.markdown("<div class='panel-title'>Sources</div>", unsafe_allow_html=True)
    sources = latest_metadata.get("sources") or []
    if sources:
        render_sources(sources, expanded=True)
    else:
        st.caption("Sources for the latest saved response will appear here when available.")
    st.divider()
    st.markdown("<div class='panel-title'>Agent activity</div>", unsafe_allow_html=True)
    agent_status_slot = st.empty()
    agent_events_slot = st.empty()
    render_agent_activity(agent_status_slot, agent_events_slot)
    st.divider()
    st.markdown("<div class='panel-title'>Conversation status</div>", unsafe_allow_html=True)
    st.write(f"**Status:** {str(conversation.get('status', 'active')).replace('_', ' ').title()}")
    if latest_metadata.get("requires_human") or conversation.get("status") == "escalated":
        st.warning("Human review is required. Check your support team's escalation process for actual notification status.")
    if latest_assistant.get("content"):
        export_text = latest_assistant.get("content", "")
        st.download_button("Download latest answer (.md)", data=export_text, file_name="support-response.md", mime="text/markdown", use_container_width=True)

with chat_col:
    transcript = st.container()
    with transcript:
        if not messages:
            welcome_left, welcome_right = st.columns([0.58, 0.42], gap="medium")
            with welcome_left:
                st.markdown("<div class='welcome-eyebrow'>WE'RE HERE TO HELP</div>", unsafe_allow_html=True)
                st.markdown("<h2 class='welcome-title'>How can we help you today?</h2>", unsafe_allow_html=True)
                st.markdown("<p class='welcome-copy'>Ask about policies, orders, or an existing support issue. If a case needs specialist attention, the assistant can flag it for human review.</p>", unsafe_allow_html=True)
            with welcome_right:
                st.image("assets/support_welcome.png", use_container_width=True)
            st.markdown("<div class='prompt-label'>COMMON QUESTIONS</div>", unsafe_allow_html=True)
            prompt_cols = st.columns(2)
            suggestions = ["What is your return policy?", "How can I track my order?", "My order arrived damaged.", "I want to raise a support ticket."]
            for i, suggestion in enumerate(suggestions):
                with prompt_cols[i % 2]:
                    if st.button(suggestion, key=f"suggestion_{i}", use_container_width=True):
                        st.session_state.pending_prompt = suggestion
                        st.rerun()
        render_history(messages)

    prompt = st.chat_input("Write your support question…", disabled=st.session_state.request_in_progress)
    if not prompt:
        prompt = st.session_state.pop("pending_prompt", None)
    if prompt:
        st.session_state.request_in_progress = True
        st.session_state.activity_events = []
        st.session_state.last_error = None
        st.session_state.agent_activity_state = "working"
        render_agent_activity(agent_status_slot, agent_events_slot)
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            status_box = st.status("Working on your request…", expanded=True)
            final_event = None
            try:
                for event in stream_chat(conversation_id, prompt):
                    if event.get("type") == "activity":
                        st.session_state.activity_events.append(event)
                        render_activity(event, status_box)
                        render_agent_activity(agent_status_slot, agent_events_slot)
                    elif event.get("type") == "error":
                        st.session_state.last_error = event.get("message", "The request could not be completed.")
                    elif event.get("type") == "final":
                        final_event = event
                if final_event:
                    request_failed = bool(final_event.get("error") or st.session_state.last_error)
                    st.session_state.agent_activity_state = "failed" if request_failed else "completed"
                    render_agent_activity(agent_status_slot, agent_events_slot)
                    status_box.update(
                        label="Request needs attention" if request_failed else "Response ready",
                        state="error" if request_failed else "complete",
                        expanded=False,
                    )
                    st.markdown(final_event.get("answer", "I couldn't prepare a response."))
                    if request_failed:
                        st.warning(st.session_state.last_error or "The model could not complete this request.")
                    render_sources(final_event.get("sources"))
                    if final_event.get("requires_human"):
                        st.info("This conversation needs human review. A representative may not have been notified.")
                else:
                    st.session_state.agent_activity_state = "failed"
                    render_agent_activity(agent_status_slot, agent_events_slot)
                    status_box.update(label="Request not completed", state="error", expanded=False)
                    st.warning(st.session_state.last_error or "The support workflow did not return a response.")
            except Exception:
                st.session_state.agent_activity_state = "failed"
                st.session_state.last_error = "The support service is temporarily unavailable."
                render_agent_activity(agent_status_slot, agent_events_slot)
                status_box.update(label="Request not completed", state="error", expanded=False)
                st.error("The support service is temporarily unavailable. Please try again shortly.")
            finally:
                st.session_state.request_in_progress = False
        st.rerun()

st.markdown("<div class='footer-note'>AI-generated support can be imperfect. Verify important account or order actions with the support team.</div>", unsafe_allow_html=True)
