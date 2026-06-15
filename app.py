"""Enterprise RAG with Role-Based Access Control (RBAC).

Document Q&A with role-gated access. Uses pure-Python keyword matching
(NO vector database) plus the Groq LLM for grounded answers — keeping it
fully compatible with Python 3.14.

Author : Avatar Putra Sigit
GitHub : qurrrrsebastian-prog
"""

import os
import sys
import re
import json
from typing import Dict, List

import streamlit as st
from groq import Groq

# --------------------------------------------------------------------------- #
# Page configuration
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title="Enterprise RAG with RBAC",
    layout="wide",
    page_icon="🔐",
)

GROQ_MODEL = "llama-3.3-70b-versatile"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# Role -> allowed document files (most-privileged first).
RBAC_CONFIG: Dict[str, List[str]] = {
    "Admin": ["admin_docs.txt", "staff_docs.txt", "intern_docs.txt"],
    "Staff": ["staff_docs.txt", "intern_docs.txt"],
    "Intern": ["intern_docs.txt"],
}

# Common Indonesian stop words removed during keyword search.
STOP_WORDS = {
    "apa", "yang", "dan", "di", "ke", "dari", "untuk", "dengan", "itu",
    "ini", "adalah", "ada", "pada", "atau", "saya", "anda", "kami", "kita",
    "berapa", "bagaimana", "kapan", "siapa", "dimana", "kenapa", "mengapa",
    "the", "a", "an", "is", "of", "to", "in",
}


# --------------------------------------------------------------------------- #
# Groq helpers
# --------------------------------------------------------------------------- #
def get_groq_client(api_key: str) -> Groq:
    """Create and return a Groq client.

    Args:
        api_key: The Groq API key.

    Returns:
        An initialized :class:`groq.Groq` client.

    Raises:
        ValueError: If the API key is empty or initialization fails.
    """
    try:
        if not api_key:
            raise ValueError("API key is empty.")
        return Groq(api_key=api_key)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Failed to initialize Groq client: {exc}") from exc


def groq_chat(client: Groq, system: str, user: str, temp: float = 0.3) -> str:
    """Send a chat completion request to Groq.

    Args:
        client: An initialized Groq client.
        system: System instruction.
        user: User message.
        temp: Sampling temperature.

    Returns:
        The assistant's text reply.

    Raises:
        RuntimeError: If the API call fails.
    """
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temp,
        )
        return (response.choices[0].message.content or "").strip()
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Groq API Error: {exc}") from exc


# --------------------------------------------------------------------------- #
# Document access + search
# --------------------------------------------------------------------------- #
def load_documents(role: str) -> List[Dict[str, str]]:
    """Load only the documents allowed for the given role.

    Args:
        role: One of "Admin", "Staff", "Intern".

    Returns:
        A list of {"source": filename, "content": text} dicts. Missing
        files are skipped gracefully.
    """
    docs: List[Dict[str, str]] = []
    try:
        allowed = RBAC_CONFIG.get(role, [])
        for filename in allowed:
            path = os.path.join(DATA_DIR, filename)
            if not os.path.exists(path):
                # Skip gracefully and log a warning.
                print(f"Warning: document not found, skipped: {filename}")
                continue
            with open(path, "r", encoding="utf-8") as fh:
                docs.append({"source": filename, "content": fh.read()})
        return docs
    except Exception as exc:  # noqa: BLE001
        print(f"Error loading documents: {exc}")
        return docs


def simple_search(docs: List[Dict[str, str]], question: str) -> List[Dict[str, str]]:
    """Rank documents by keyword overlap with the question (no vector DB).

    Args:
        docs: The accessible documents.
        question: The user's question.

    Returns:
        The top 2 matching documents. Falls back to the first 2 docs if
        no keyword matches are found.
    """
    try:
        if not docs:
            return []
        keywords = [
            w
            for w in re.findall(r"\w+", question.lower())
            if w not in STOP_WORDS and len(w) > 1
        ]
        scored = []
        for doc in docs:
            content_lower = doc["content"].lower()
            score = sum(content_lower.count(kw) for kw in keywords)
            scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)

        if scored and scored[0][0] == 0:
            # No keyword matched anywhere — fall back to first 2 docs.
            return docs[:2]
        return [doc for _, doc in scored[:2]]
    except Exception:  # noqa: BLE001
        return docs[:2]


def query_rbac(
    client: Groq,
    docs: List[Dict[str, str]],
    question: str,
    role: str,
) -> str:
    """Answer a question grounded in role-accessible documents.

    Args:
        client: An initialized Groq client.
        docs: Documents the role is allowed to see.
        question: The user's question.
        role: The active role.

    Returns:
        The grounded answer text.
    """
    try:
        relevant_docs = simple_search(docs, question)
        if not relevant_docs:
            return "Maaf, tidak ada dokumen yang relevan dengan pertanyaan Anda."

        context = "\n\n---\n\n".join(
            f"[Source: {d['source']}]\n{d['content']}" for d in relevant_docs
        )
        system = (
            "You are an enterprise document assistant. Answer based ONLY on "
            "the provided context. Cite the source document name in your "
            "answer. If the answer is not in the context, say 'Informasi "
            "tidak ditemukan dalam dokumen yang Anda akses.' Be concise."
        )
        user = (
            f"User Role: {role}\n\n"
            f"Context Documents:\n{context}\n\n"
            f"Question: {question}"
        )
        return groq_chat(client, system, user)
    except RuntimeError as exc:
        return str(exc)
    except Exception as exc:  # noqa: BLE001
        return f"Error: {exc}"


# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.header("⚙️ Settings")
    api_key = st.text_input(
        "Groq API Key",
        type="password",
        value=os.environ.get("GROQ_API_KEY", ""),
        help="Set $env:GROQ_API_KEY or paste here.",
    )
    role = st.selectbox("Role", ["Admin", "Staff", "Intern"])
    accessible = ", ".join(RBAC_CONFIG.get(role, []))
    st.info(f"📂 Access: {accessible}")


# --------------------------------------------------------------------------- #
# Main UI
# --------------------------------------------------------------------------- #
st.title("🔐 Enterprise RAG with RBAC")
st.caption("Role-based AI document search | NO vector database — pure Python + Groq")

st.subheader("❓ Tanya Dokumen")
question = st.text_input("Pertanyaan:", "Berapa nilai kontrak Mega Tower?")

if st.button("🔍 Jawab", type="primary"):
    if not api_key:
        st.error("Groq API Error: API key belum diisi. Set $env:GROQ_API_KEY.")
        st.stop()

    try:
        client = get_groq_client(api_key)
    except ValueError as exc:
        st.error(f"Groq API Error: {exc}")
        st.stop()

    docs = load_documents(role)
    if not docs:
        st.error("No documents found. Check data/ folder.")
        st.stop()

    with st.spinner("Searching documents..."):
        answer = query_rbac(client, docs, question, role)

    st.subheader("💡 Jawaban")
    st.markdown(answer)
    st.divider()
    st.caption(f"🔒 Access Level: {role} | Documents searched: {len(docs)}")

st.divider()
st.subheader("🧪 RBAC Test Cases")
st.markdown("Coba tanya hal yang sama dengan role berbeda:")
st.markdown("- **Admin:** 'Berapa total pipeline Q3?' → Akses penuh")
st.markdown("- **Staff:** 'Apa SOP safety harness?' → Akses SOP")
st.markdown("- **Intern:** 'Apa itu rope access?' → Akses training only")
st.markdown("- **Intern:** 'Berapa kontrak Mega Tower?' → ❌ Tidak punya akses")
