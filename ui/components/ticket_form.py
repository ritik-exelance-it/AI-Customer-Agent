"""Streamlit form for explicitly submitting a support ticket."""

from __future__ import annotations

import streamlit as st

from services.ticket_service import create_support_ticket


def render_ticket_form() -> None:
    """Render the ticket form and display the submission result."""
    with st.expander("Create a support ticket", expanded=False):
        st.caption(
            "Submit an issue to create a support ticket. "
            "Use your existing customer ID."
        )

        with st.form("create_support_ticket_form", clear_on_submit=False):
            customer_id = st.text_input(
                "Customer ID",
                placeholder="e.g. CUST-1001",
            )
            subject = st.text_input(
                "Subject",
                placeholder="Briefly describe the issue",
                max_chars=200,
            )
            description = st.text_area(
                "Description",
                placeholder="Explain what happened and what help you need.",
                max_chars=5000,
            )
            priority = st.selectbox(
                "Priority",
                options=["low", "medium", "high", "urgent"],
                index=1,
                format_func=lambda value: value.title(),
            )
            confirmed = st.checkbox(
                "I confirm that I want to submit this support ticket."
            )

            submitted = st.form_submit_button(
                "Submit ticket",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            result = create_support_ticket(
                customer_id=customer_id,
                subject=subject,
                description=description,
                priority=priority,
                confirmed=confirmed,
            )

            if not result.get("ok"):
                st.error(result.get("error", "Could not create the ticket."))
                return

            ticket = result.get("ticket", result)
            ticket_id = ticket.get("ticket_id", "Created")
            st.success(f"Ticket submitted successfully. Ticket ID: {ticket_id}")
            st.caption("Save the ticket ID so you can refer to this issue later.")