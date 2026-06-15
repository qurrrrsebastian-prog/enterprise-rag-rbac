# 🔐 Enterprise RAG with RBAC

![Python](https://img.shields.io/badge/Python-3.14-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-LLM-F55036?logo=groq&logoColor=white)

A Retrieval-Augmented Generation (RAG) document Q&A system with **Role-Based Access Control**. Different roles see different documents — and the AI can only answer from what the active role is allowed to read.

**No vector database.** Retrieval uses pure-Python keyword matching, so it runs cleanly on Python 3.14 without `chromadb`, `fastembed`, or `langchain`.

---

## ✨ Features

- **3-tier RBAC** — Admin, Staff, and Intern each get a different document scope.
- **Pure-Python retrieval** — keyword-overlap ranking, no embeddings, no vector store.
- **Source attribution** — every answer cites the document it came from.
- **Grounded answers** — the model is instructed to answer *only* from accessible context, or admit it doesn't know.

### Access matrix

| Role | admin_docs | staff_docs | intern_docs |
|------|:---------:|:----------:|:-----------:|
| **Admin** | ✅ | ✅ | ✅ |
| **Staff** | ❌ | ✅ | ✅ |
| **Intern** | ❌ | ❌ | ✅ |

---

## 🛠️ Tech Stack

| Layer | Tool |
|-------|------|
| UI | Streamlit (wide layout) |
| LLM | Groq (`llama-3.3-70b-versatile`) |
| Retrieval | Pure Python keyword matching |
| Language | Python 3.14 |

---

## 🚀 Run It

```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your Groq API key (PowerShell)
$env:GROQ_API_KEY = "gsk_your_key_here"

# 3. Launch
streamlit run app.py
```

> No API key in your environment? Paste it directly into the sidebar.

---

## 🎬 Demo Example — Admin vs Intern

Ask the **same question** under different roles:

> **Question:** "Berapa nilai kontrak Mega Tower?"

- **As Admin** → ✅ *"Berdasarkan `admin_docs.txt`, nilai kontrak Mega Tower adalah Rp 85.000.000..."*
- **As Intern** → ❌ *"Informasi tidak ditemukan dalam dokumen yang Anda akses."*

The Intern role never loads `admin_docs.txt`, so the financial data is physically out of reach — access control happens *before* retrieval, not just in the prompt.

---

## 📊 Key Insights

1. **3 access tiers** enforced at load time — Admin reads 3 docs, Staff 2, Intern 1.
2. **0 vector-DB dependencies** — retrieval is ~30 lines of keyword scoring, returning the **top 2** documents per query.
3. **Defense in depth:** RBAC filters documents *before* the LLM sees them, and the system prompt blocks any leak from out-of-scope context — two independent layers.

---

## 👤 Author

**Avatar Putra Sigit**
- GitHub: [qurrrrsebastian-prog](https://github.com/qurrrrsebastian-prog)
- LinkedIn: [avatarputrasigit](https://www.linkedin.com/in/avatarputrasigit)
