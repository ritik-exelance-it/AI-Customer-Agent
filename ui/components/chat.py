"""Render saved conversation messages without duplicating backend state."""
from __future__ import annotations
from typing import Any
import streamlit as st
from ui.components.sources import render_sources


def render_history(messages: list[dict[str, Any]]) -> None:
    for item in messages:
        role = item.get("role", "assistant")
        if role not in {"user", "assistant", "human"}:
            continue
        ui_role = "assistant" if role == "human" else role
        with st.chat_message(ui_role):
            content = item.get("content", "")
            st.markdown(content)
            if ui_role == "assistant":
                metadata = item.get("metadata") or {}
                render_sources(metadata.get("sources"))
                col1, col2 = st.columns([0.15, 0.85])
                with col1:
                    st.download_button("Download", data=content, file_name="support-response.md", mime="text/markdown", key=f"download_{item.get('message_id', id(item))}")
                if metadata.get("requires_human"):
                    st.info("This conversation requires human review. A representative may not have been notified.")
