"""ui_components.py — Reusable UI components.
Author: Avatar Putra Sigit | GitHub: qurrrrsebastian-prog
"""
import streamlit as st

PRIMARY = "#475569"
SECONDARY = "#94A3B8"

ROLE_COLORS = {"Admin": "#DC2626", "Staff": "#2563EB", "Intern": "#059669"}


def render_header(title: str, subtitle: str, color: str = PRIMARY) -> None:
    """Render a gradient page header."""
    st.markdown(
        f"""
    <div style="background: linear-gradient(135deg, {color}33, {color}11);
        border-left: 4px solid {color}; border-radius: 8px; padding: 20px 24px; margin-bottom: 20px;">
        <h1 style="color: #E2E8F0; margin: 0; font-size: 28px;">{title}</h1>
        <p style="color: #94A3B8; margin: 8px 0 0 0; font-size: 14px;">{subtitle}</p>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    """Render the standard footer."""
    st.markdown("---")
    st.markdown(
        """
    <div style="text-align: center; color: #64748B; font-size: 12px; padding: 10px;">
        <p>Built with ❤️ by <a href="https://github.com/qurrrrsebastian-prog" target="_blank">Avatar Putra Sigit</a>
        | Founder @AVA.Group | © 2026</p>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_status_badge(label: str, color: str) -> None:
    """Render a small pill-style status badge."""
    st.markdown(
        f"""
    <span style="background: {color}22; color: {color}; border: 1px solid {color}44;
        border-radius: 12px; padding: 4px 12px; font-size: 12px; font-weight: 600;">{label}</span>
    """,
        unsafe_allow_html=True,
    )


def render_role_badge(role: str) -> None:
    """Render a coloured role badge."""
    render_status_badge(role, ROLE_COLORS.get(role, PRIMARY))


def render_card(title: str, content: str, color: str = PRIMARY) -> None:
    """Render a titled content card."""
    st.markdown(
        f"""
    <div style="background: {color}11; border: 1px solid {color}33; border-radius: 10px;
        padding: 16px; margin: 8px 0;">
        <h4 style="color: #CBD5E1; margin: 0 0 8px 0;">{title}</h4>
        <p style="color: #94A3B8; margin: 0; font-size: 13px;">{content}</p>
    </div>
    """,
        unsafe_allow_html=True,
    )
