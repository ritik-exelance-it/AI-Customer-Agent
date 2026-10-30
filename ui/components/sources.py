"""Render only source metadata returned by the backend."""
from __future__ import annotations
from urllib.parse import urlparse
import streamlit as st


def render_sources(sources: list[dict] | None, expanded: bool = False) -> None:
    if not sources:
        return
    with st.expander(f"Sources · {len(sources)}", expanded=expanded):
        for idx, source in enumerate(sources):
            if not isinstance(source, dict):
                continue
            title = source.get("title") or source.get("source") or source.get("document_title") or "Retrieved source"
            st.markdown(f"**{title}**")
            source_type = source.get("source_type") or source.get("type")
            section = source.get("section") or source.get("page") or source.get("page_number")
            details = [str(x) for x in (source_type, f"Page/section: {section}" if section is not None else None) if x]
            if details:
                st.caption(" · ".join(details))
            excerpt = source.get("excerpt") or source.get("content") or source.get("text")
            if excerpt:
                st.write(str(excerpt)[:1200])
            url = source.get("url") or source.get("link")
            if isinstance(url, str) and urlparse(url).scheme in {"http", "https"} and urlparse(url).netloc:
                st.link_button("Open source", url, key=f"source_link_{idx}_{abs(hash(url))}")
            elif source.get("chunk_index") is not None:
                st.caption(f"Retrieved chunk {source['chunk_index']}")
            if idx < len(sources) - 1:
                st.divider()
