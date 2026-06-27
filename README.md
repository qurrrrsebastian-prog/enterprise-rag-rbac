# Project #19 — Enterprise RAG with RBAC

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white" />
  <img src="https://img.shields.io/badge/RBAC-Security-green?style=flat&logo=shield&logoColor=white" />
  <img src="https://img.shields.io/badge/RAG-7B2CBF?style=flat" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat" />
</p>

> RAG Document Q&A enterprise dengan Role-Based Access Control: Admin / Staff / Intern. Setiap role punya akses dokumen berbeda.

---

## Demo Langsung

[![Deploy to Streamlit Cloud](https://img.shields.io/badge/Deploy-Streamlit%20Cloud-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://share.streamlit.io/deploy?repository=qurrrrsebastian-prog/enterprise-rag-rbac)

**Tech Stack:** `LangChain` · `ChromaDB` · `RBAC` · `Streamlit` · `Auth`

---

## Fitur

| Fitur | Status |
|-------|--------|
| Role-based access control | ✅ |
| 3 roles: Admin / Staff / Intern | ✅ |
| Document access by role | ✅ |
| RAG Q&A dengan source | ✅ |
| User management | ✅ |
| Tema gelap AVA purple | ✅ |

---

## Cara Menjalankan

```bash
git clone https://github.com/qurrrrsebastian-prog/enterprise-rag-rbac.git
cd enterprise-rag-rbac
pip install -r requirements.txt
$env:GEMINI_API_KEY="your_api_key_here"
streamlit run app.py
```

## Deploy ke Streamlit Cloud (GRATIS)

1. [share.streamlit.io](https://share.streamlit.io) → Login GitHub
2. **New app** → Pilih repo ini
3. Tambahkan secret: `GEMINI_API_KEY`
4. **Deploy**

---

## Struktur Akses RBAC

```
┌─────────┐  ┌─────────┐  ┌─────────┐
│  Admin  │  │  Staff  │  │  Intern │
│  (All)  │  │ (Most)  │  │ (Limit) │
└─────────┘  └─────────┘  └─────────┘
```

---

## Struktur Project

```
enterprise-rag-rbac/
├── app.py              # Main Streamlit app (8KB)
├── requirements.txt    # Dependencies
├── data/               # Document storage
├── .streamlit/
│   └── config.toml    # AVA purple branding
├── .gitignore
└── LICENSE            # MIT License
```

---

**Dibuat oleh:** [Avatar Putra Sigit](https://github.com/qurrrrsebastian-prog) · Founder @AVA.Group
