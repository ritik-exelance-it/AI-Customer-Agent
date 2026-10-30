"""Sidebar for starting and switching between real saved conversations."""
from __future__ import annotations
from datetime import datetime
import streamlit as st


def _label(item: dict) -> str:
    title = (item.get("title") or "Support conversation").strip()
    updated = item.get("updated_at") or item.get("created_at") or ""
    if updated:
        try:
            dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
            return f"{title[:34]} · {dt.strftime('%b %d, %H:%M')}"
        except (ValueError, TypeError):
            pass
    return title[:48]


def render_sidebar(conversations: list[dict], active_id: str) -> tuple[str | None, bool]:
    with st.sidebar:
        st.markdown("<div class='sidebar-brand'>support.ai</div>", unsafe_allow_html=True)
        st.caption("Customer support, made simpler")
        st.divider()
        new_conversation = st.button("＋  New conversation", use_container_width=True, type="primary")
        st.markdown("**Recent conversations**")
        selected_id = active_id
        if conversations:
            ids = [str(item.get("conversation_id")) for item in conversations if item.get("conversation_id")]
            labels = {str(item.get("conversation_id")): _label(item) for item in conversations}
            if ids:
                try:
                    default_index = ids.index(active_id)
                except ValueError:
                    default_index = 0
                chosen = st.radio("Saved conversations", ids, index=default_index,
                                  format_func=lambda cid: labels.get(cid, "Support conversation"),
                                  label_visibility="collapsed", key=f"saved_conversation_picker_{active_id}")
                selected_id = chosen
        else:
            st.caption("Your saved conversations will appear here.")
        st.divider()
        st.markdown("**Support information**")
        st.caption("Ask questions about policies, orders, or support issues. Responses and available sources depend on the connected support service.")
        st.caption("Do not enter passwords or payment-card details.")
    return selected_id, new_conversation
