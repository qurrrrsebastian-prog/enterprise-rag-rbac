"""Enterprise RAG with Role-Based Access Control (RBAC) — v2.0 production upgrade.

Document Q&A with role-gated access. Uses pure-Python keyword matching (NO vector
database) plus the Groq LLM for grounded answers. v2.0 adds a real login system
(salted PBKDF2 hashes), session management with idle auto-logout, an access audit
trail, role-gated document upload, an admin dashboard (user CRUD + analytics), and
a user profile with password change.

Author: Avatar Putra Sigit | GitHub: qurrrrsebastian-prog
"""

import os
import re
import time
from typing import Dict, List

import pandas as pd
import plotly.express as px
import streamlit as st

import database as db
from security import sanitize_input
from ui_components import (PRIMARY, render_footer, render_header,
                           render_role_badge)

st.set_page_config(page_title="Enterprise RAG with RBAC", layout="wide", page_icon="🔐")

GROQ_MODEL = "llama-3.3-70b-versatile"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
IDLE_TIMEOUT = 30 * 60  # 30 minutes

RBAC_CONFIG: Dict[str, List[str]] = {
    "Admin": ["admin_docs.txt", "staff_docs.txt", "intern_docs.txt"],
    "Staff": ["staff_docs.txt", "intern_docs.txt"],
    "Intern": ["intern_docs.txt"],
}

STOP_WORDS = {
    "apa", "yang", "dan", "di", "ke", "dari", "untuk", "dengan", "itu", "ini",
    "adalah", "ada", "pada", "atau", "saya", "anda", "kami", "kita", "berapa",
    "bagaimana", "kapan", "siapa", "dimana", "kenapa", "mengapa",
    "the", "a", "an", "is", "of", "to", "in",
}

db.init_db()


# --------------------------------------------------------------------------- #
# Groq helpers
# --------------------------------------------------------------------------- #
def get_groq_client(api_key: str):
    """Create a Groq client, or raise ValueError."""
    try:
        if not api_key:
            raise ValueError("API key is empty.")
        from groq import Groq
        return Groq(api_key=api_key)
    except ValueError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Failed to initialize Groq client: {exc}") from exc


def groq_chat(client, system: str, user: str, temp: float = 0.3) -> str:
    """Send a chat completion request to Groq."""
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            temperature=temp,
        )
        return (response.choices[0].message.content or "").strip()
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Groq API Error: {exc}") from exc


# --------------------------------------------------------------------------- #
# Document access + search
# --------------------------------------------------------------------------- #
def load_documents(role: str) -> List[Dict[str, str]]:
    """Load built-in files plus uploaded docs the role is allowed to see."""
    docs: List[Dict[str, str]] = []
    for filename in RBAC_CONFIG.get(role, []):
        path = os.path.join(DATA_DIR, filename)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as fh:
                docs.append({"source": filename, "content": fh.read()})
    docs.extend(db.get_documents_for_role(role))
    return docs


def simple_search(docs: List[Dict[str, str]], question: str) -> List[Dict[str, str]]:
    """Rank documents by keyword overlap (no vector DB). Top 2 results."""
    if not docs:
        return []
    keywords = [w for w in re.findall(r"\w+", question.lower())
                if w not in STOP_WORDS and len(w) > 1]
    scored = [(sum(d["content"].lower().count(kw) for kw in keywords), d)
              for d in docs]
    scored.sort(key=lambda x: x[0], reverse=True)
    if scored and scored[0][0] == 0:
        return docs[:2]
    return [d for _, d in scored[:2]]


def query_rbac(client, docs, question: str, role: str) -> str:
    """Answer a question grounded in role-accessible documents."""
    relevant = simple_search(docs, question)
    if not relevant:
        return "Maaf, tidak ada dokumen yang relevan dengan pertanyaan Anda."
    context = "\n\n---\n\n".join(
        f"[Source: {d['source']}]\n{d['content']}" for d in relevant)
    system = (
        "You are an enterprise document assistant. Answer based ONLY on the "
        "provided context. Cite the source document name. If the answer is not "
        "in the context, say 'Informasi tidak ditemukan dalam dokumen yang Anda "
        "akses.' Be concise."
    )
    user = f"User Role: {role}\n\nContext Documents:\n{context}\n\nQuestion: {question}"
    return groq_chat(client, system, user)


# --------------------------------------------------------------------------- #
# Session management
# --------------------------------------------------------------------------- #
def current_user():
    """Return the logged-in user dict, or None — enforcing the idle timeout."""
    user = st.session_state.get("user")
    if not user:
        return None
    last = st.session_state.get("last_activity", 0)
    if time.time() - last > IDLE_TIMEOUT:
        logout(expired=True)
        return None
    st.session_state.last_activity = time.time()
    return user


def logout(expired: bool = False) -> None:
    """Clear the session."""
    user = st.session_state.get("user")
    if user:
        db.add_log("logout", "expired" if expired else "manual", user["username"])
    for k in ("user", "session_token", "last_activity"):
        st.session_state.pop(k, None)
    if expired:
        st.session_state["_expired"] = True


def login_screen() -> None:
    """Render the auth-first login page."""
    render_header("🔐 Enterprise RAG with RBAC",
                  "Secure role-based document intelligence · v2.0 Slate Enterprise")
    if st.session_state.pop("_expired", False):
        st.warning("⏱️ Session expired after 30 minutes of inactivity. Please log in again.")
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown("#### Sign in")
        with st.form("login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("🔓 Login", type="primary",
                                              use_container_width=True)
        if submitted:
            from security import generate_session_token
            user = db.authenticate(sanitize_input(username, 50), password)
            if user:
                st.session_state.user = user
                st.session_state.session_token = generate_session_token()
                st.session_state.last_activity = time.time()
                db.add_log("login", f"role={user['role']}", user["username"])
                st.rerun()
            else:
                st.error("Invalid credentials or inactive account.")
        st.caption("Demo accounts — admin/admin123 · staff/staff123 · intern/intern123")


# --------------------------------------------------------------------------- #
# Main application (post-login)
# --------------------------------------------------------------------------- #
def main_app(user: dict) -> None:
    """Render the authenticated application."""
    role = user["role"]
    with st.sidebar:
        st.markdown(f"### 👤 {user['full_name']}")
        render_role_badge(role)
        st.caption(f"@{user['username']}")
        st.divider()
        api_key = st.text_input("Groq API Key", type="password",
                                value=os.environ.get("GROQ_API_KEY", ""),
                                help="Set $env:GROQ_API_KEY or paste here.")
        st.info("📂 Access: " + ", ".join(RBAC_CONFIG.get(role, [])))
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            logout()
            st.rerun()

    render_header("🔐 Enterprise RAG with RBAC",
                  f"Signed in as {user['full_name']} ({role}) · v2.0 Slate Enterprise")

    tab_labels = ["💬 Ask", "📁 Documents", "👤 Profile"]
    if role == "Admin":
        tab_labels.append("🛡️ Admin")
    tabs = st.tabs(tab_labels)

    # --- Ask -------------------------------------------------------------- #
    with tabs[0]:
        st.subheader("❓ Tanya Dokumen")
        question = st.text_input("Pertanyaan:", "Berapa nilai kontrak Mega Tower?")
        if st.button("🔍 Jawab", type="primary"):
            q = sanitize_input(question, 1000)
            try:
                client = get_groq_client(api_key)
            except ValueError as exc:
                st.error(f"Groq API Error: {exc}")
                st.stop()
            docs = load_documents(role)
            if not docs:
                st.error("No documents found for your role.")
                st.stop()
            with st.spinner("Searching documents..."):
                try:
                    answer = query_rbac(client, docs, q, role)
                except RuntimeError as exc:
                    answer = str(exc)
            st.subheader("💡 Jawaban")
            st.markdown(answer)
            st.caption(f"🔒 Access Level: {role} | Documents searched: {len(docs)}")
            db.log_access(user["username"], role, "query", q, answer,
                          ", ".join(d["source"] for d in docs))
        st.divider()
        st.caption("Every question is recorded in the access audit trail.")

    # --- Documents -------------------------------------------------------- #
    with tabs[1]:
        st.subheader("📁 Accessible Documents")
        for d in load_documents(role):
            with st.expander(f"📄 {d['source']}"):
                st.text(d["content"][:1500])
        if role == "Admin":
            st.divider()
            st.markdown("##### ⬆️ Upload document (Admin)")
            up = st.file_uploader("Text document", type=["txt", "md"])
            access = st.selectbox("Minimum role to access", ["Intern", "Staff", "Admin"])
            if up and st.button("Save document"):
                content = up.read().decode("utf-8", errors="ignore")
                db.add_document(sanitize_input(up.name, 120), content, access)
                db.add_log("upload_doc", f"{up.name} -> {access}", user["username"])
                st.success(f"Uploaded {up.name} (access: {access}).")
                st.rerun()
            st.markdown("##### 📚 Uploaded documents")
            udocs = db.list_documents()
            if udocs.empty:
                st.caption("No uploaded documents yet.")
            else:
                st.dataframe(udocs, use_container_width=True, hide_index=True)
                del_id = st.selectbox("Delete document id", [None] + udocs["id"].tolist())
                if del_id and st.button("🗑️ Delete selected doc"):
                    db.delete_document(int(del_id))
                    st.rerun()

    # --- Profile ---------------------------------------------------------- #
    with tabs[2]:
        st.subheader("👤 Profile")
        st.write(f"**Name:** {user['full_name']}")
        st.write(f"**Email:** {user['email']}")
        st.write(f"**Role:** {role}")
        st.write(f"**Last login:** {user.get('last_login', '—')}")
        st.divider()
        st.markdown("##### 🔑 Change password")
        with st.form("change_pw"):
            old = st.text_input("Current password", type="password")
            new = st.text_input("New password", type="password")
            confirm = st.text_input("Confirm new password", type="password")
            if st.form_submit_button("Update password"):
                if new != confirm:
                    st.error("New passwords do not match.")
                elif len(new) < 6:
                    st.error("Password must be at least 6 characters.")
                elif db.change_password(user["username"], old, new):
                    db.add_log("change_password", "", user["username"])
                    st.success("Password updated.")
                else:
                    st.error("Current password incorrect.")

    # --- Admin ------------------------------------------------------------ #
    if role == "Admin":
        with tabs[3]:
            st.subheader("🛡️ Admin Dashboard")
            atab1, atab2, atab3 = st.tabs(
                ["👥 Users", "📊 Analytics", "📜 Access Trail"])

            with atab1:
                st.dataframe(db.get_users(), use_container_width=True, hide_index=True)
                st.markdown("##### ➕ Create user")
                with st.form("new_user", clear_on_submit=True):
                    cu1, cu2 = st.columns(2)
                    nu = cu1.text_input("Username")
                    npw = cu2.text_input("Password", type="password")
                    nfn = cu1.text_input("Full name")
                    nem = cu2.text_input("Email")
                    nrole = st.selectbox("Role", ["Admin", "Staff", "Intern"])
                    if st.form_submit_button("Create") and nu and npw:
                        if db.create_user(sanitize_input(nu, 50), npw, nrole,
                                          sanitize_input(nfn, 80), sanitize_input(nem, 120)):
                            db.add_log("create_user", nu, user["username"])
                            st.success(f"Created {nu}.")
                            st.rerun()
                        else:
                            st.error("Username already exists.")
                st.markdown("##### ✏️ Manage user")
                users = db.get_users()
                edit_id = st.selectbox(
                    "Select user", users["id"].tolist(),
                    format_func=lambda i: users.loc[users["id"] == i, "username"].iloc[0])
                urow = users[users["id"] == edit_id].iloc[0]
                ec1, ec2, ec3 = st.columns(3)
                e_role = ec1.selectbox("Role", ["Admin", "Staff", "Intern"],
                                       index=["Admin", "Staff", "Intern"].index(urow["role"]))
                e_active = ec2.selectbox("Active", [1, 0],
                                         index=0 if urow["is_active"] else 1)
                e_email = ec3.text_input("Email", urow["email"] or "")
                mc1, mc2 = st.columns(2)
                if mc1.button("💾 Save user"):
                    db.update_user(int(edit_id), e_role, urow["full_name"],
                                   sanitize_input(e_email, 120), int(e_active))
                    db.add_log("update_user", urow["username"], user["username"])
                    st.rerun()
                if mc2.button("🗑️ Delete user", disabled=urow["username"] == user["username"]):
                    db.delete_user(int(edit_id))
                    db.add_log("delete_user", urow["username"], user["username"])
                    st.rerun()

            with atab2:
                qpr = db.questions_per_role()
                if qpr.empty:
                    st.info("No questions logged yet.")
                else:
                    fig = px.bar(qpr, x="role", y="questions", color="role",
                                 title="Questions per role")
                    st.plotly_chart(fig, use_container_width=True)
                log = db.get_access_log()
                queries = log[log["action"] == "query"]
                st.metric("Total questions asked", len(queries))

            with atab3:
                st.dataframe(db.get_access_log(), use_container_width=True,
                             hide_index=True)

    render_footer()


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
user = current_user()
if user:
    main_app(user)
else:
    login_screen()
    render_footer()
