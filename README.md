<div align="center">

# ⚡ TechDebt Analyzer

### Find technical debt before it finds you.

AI-powered code health analysis for Python repositories —
line-level issues, security risks, complexity scores, and plain-English fixes in under 90 seconds.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat&logo=fastapi&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind-CSS-38B2AC?style=flat&logo=tailwind-css&logoColor=white)
![OpenAI](https://img.shields.io/badge/GPT--4o-OpenAI-412991?style=flat&logo=openai&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-LLaMA3-F55036?style=flat)

</div>

---

## 🚀 What It Does

Paste any public Python GitHub repository URL and get a full AI-powered technical debt report including:

- 🤖 **GPT-4o / Groq AI** — Line-level code review on every function
- 📈 **Radon** — Cyclomatic complexity scoring per file
- 🔒 **Bandit** — Security vulnerability detection
- 🧠 **Gradient Boosting ML** — 0–100 debt score per file
- 📋 **AI Recommendations** — Plain-English fix suggestions

---

## 🖥️ Screenshots

> Add screenshots here after deployment

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Python 3.10+ |
| Frontend | HTML, Tailwind CSS, Vanilla JS |
| AI Review | OpenAI GPT-4o-mini (primary), Groq LLaMA 3.3-70b (fallback) |
| Complexity | Radon |
| Security | Bandit |
| ML Scoring | scikit-learn Gradient Boosting |
| Animations | Spline 3D, CSS Keyframes |

---

## ⚙️ Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/tech-debt-analyzer.git
cd tech-debt-analyzer
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Create `.env` file
```env
OPENAI_API_KEY=sk-...        # Primary AI (optional)
GROQ_API_KEY=gsk_...         # Free fallback AI (recommended)
GITHUB_TOKEN=ghp_...         # For higher GitHub API rate limits
```

### 4. Run the app
```bash
python run.py
```

Open [http://localhost:8000](http://localhost:8000)

---

## 🔑 Getting API Keys

| Key | Where to get | Cost |
|---|---|---|
| `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com) | Paid |
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) | ✅ Free |
| `GITHUB_TOKEN` | [github.com/settings/tokens](https://github.com/settings/tokens) | ✅ Free |

---

## 📁 Project Structure
    tech-debt-analyzer/
├── app/
│ ├── services/
│ │ ├── ai_reviewer.py # GPT-4o / Groq code review
│ │ ├── analysis_engine.py # Main orchestrator
│ │ ├── complexity_scanner.py # Radon complexity
│ │ ├── security_scanner.py # Bandit security
│ │ ├── ml_scorer.py # Gradient Boosting scorer
│ │ ├── github_service.py # GitHub API + cloning
│ │ └── report_generator.py # AI summary + recommendations
│ ├── templates/
│ │ ├── landing.html # Landing page
│ │ └── index.html # Analyzer page
│ └── static/
│ └── js/app.js # Frontend logic
├── .env # API keys (never commit this)
├── requirements.txt
└── run.py