"""Render truthful, high-level activity events from the service layer."""
from __future__ import annotations
from html import escape
import streamlit as st


def render_activity(event: dict, status_container=None) -> None:
    stage = str(event.get("stage", "working")).replace("_", " ").title()
    message = str(event.get("message", "Working on your request…"))
    line = (
        "<div class='activity-entry'>"
        f"<strong>{escape(stage)}</strong>"
        f"<span> — {escape(message)}</span>"
        "</div>"
    )
    if status_container is not None:
        status_container.markdown(line, unsafe_allow_html=True)
    else:
        st.markdown(line, unsafe_allow_html=True)
