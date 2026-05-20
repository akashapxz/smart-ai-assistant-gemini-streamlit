# 🤖 Smart AI Assistant — Gemini + Groq + Streamlit

A full-featured, multi-domain AI assistant with authentication, persistent cloud-backed chat history, FAQ knowledge base, and a premium dark UI. Powered by **Google Gemini**, **Groq (Llama 3.3)**, **Supabase**, and **Streamlit**.

---

## 🚀 Features

### 🔐 Authentication System
- Signup & login with bcrypt-hashed passwords
- 30-day "Remember Me" persistent sessions
- User profile display in sidebar

### 💬 Multi-Domain AI Chat
- **💬 General Assistant** — default conversational mode
- **🎓 College FAQ Assistant** — admissions, courses, fees, placements
- **👥 HR Support Assistant** — leave, payroll, benefits, appraisals
- **🛒 Customer Support Assistant** — orders, returns, shipping, payments
- **📦 Product Assistance Assistant** — setup, troubleshooting, specs

### 🔌 Dual AI Provider Support
- **Google Gemini** — Gemini 2.0 Flash, 2.5 Flash, 2.5 Pro
- **Groq** — Llama 3.3 70B Versatile (ultra-fast inference)
- Switch between providers seamlessly via sidebar dropdown
- Helps avoid rate limits by using an alternative provider

### 🧠 Prompt Engineering
- Zero-Shot, One-Shot, Few-Shot Prompting
- Chain-of-Thought, Role-Based, Structured Output
- Multiple personality modes

### 📄 Document Q&A
- Upload PDF, DOCX, and TXT files via 📎 attachment button (near chat input)
- Ask questions about uploaded content
- Clean, modern attachment UI similar to ChatGPT/Claude

### ❓ FAQ Knowledge Base
- 40 realistic FAQs across 4 domains
- Search & filter with keyword matching
- "Ask AI" button to discuss any FAQ in chat

### 📜 Persistent Chat History
- All chats saved to **Supabase (PostgreSQL)** — persists across deployments
- Browse, search, filter, and re-open past conversations
- Survives page refresh, re-login, and server restarts
- Delete conversations you no longer need

### ⚡ Smart Rate Limit Handling
- Auto-retry with countdown timer on Gemini API rate limits
- Graceful fallback with up to 3 retry attempts
- Switch to Groq when Gemini limits are hit

### 🎨 Premium UI
- Dark gradient theme with glassmorphism
- Inter font, smooth animations, custom scrollbars
- Domain-specific color coding
- Clean sidebar with quick-access New Chat button

---

## 📂 Project Structure

```
smart_ai_assistant/
├── app.py                    # Main app (auth gate + multi-page router)
├── database.py               # Supabase (PostgreSQL) database layer
├── auth.py                   # Authentication (login/signup/sessions)
├── faqs.py                   # FAQ loader and search
├── prompts.py                # Personality & domain system prompts
├── prompting_techniques.py   # Prompt engineering techniques
├── utils.py                  # Utility functions
├── document_reader.py        # PDF/DOCX/TXT reader
├── supabase_schema.sql       # PostgreSQL schema (run once in Supabase SQL Editor)
├── data/
│   └── faq_dataset.csv       # FAQ dataset (40 entries, 4 domains)
├── .streamlit/
│   ├── config.toml           # Streamlit theme configuration
│   └── secrets.toml.example  # Template for Streamlit Cloud secrets
├── requirements.txt
├── .env                      # Local env vars (not committed)
├── .gitignore
└── README.md
```

---

## ⚙️ Local Setup

### 1. Clone the repository
```bash
git clone https://github.com/akashapxz/smart-ai-assistant-gemini-streamlit.git
cd smart-ai-assistant-gemini-streamlit
```

### 2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up Supabase (free)
1. Go to [supabase.com](https://supabase.com) → Create a free account
2. Create a **New Project** (pick a name, region, and database password)
3. Once provisioned, go to **SQL Editor** → **New Query**
4. Paste the contents of `supabase_schema.sql` and click **Run**
5. Go to **Settings → API** and copy your **Project URL** and **`service_role` key**

### 5. Set up environment variables
Create a `.env` file in the project root:
```
GEMINI_API_KEY=your_gemini_api_key
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your_service_role_key
GROQ_API_KEY=your_groq_api_key
```

- Get your Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
- Get your Groq API key from [Groq Console](https://console.groq.com/keys) (free tier available)
- Get your Supabase credentials from the Supabase dashboard (Settings → API)

> **Note:** At least one of `GEMINI_API_KEY` or `GROQ_API_KEY` is required. Both are recommended for the best experience.

### 6. Run the app
```bash
streamlit run app.py
```

---

## 🌐 Deploy to Streamlit Cloud

### 1. Push to GitHub
```bash
git add .
git commit -m "Deploy with Groq + Gemini dual provider support"
git push origin main
```

### 2. Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **"New app"**
3. Connect your GitHub repo: `akashapxz/smart-ai-assistant-gemini-streamlit`
4. Set **Main file path**: `app.py`
5. Click **"Advanced settings"** → **Secrets**
6. Add your secrets:
   ```toml
   GEMINI_API_KEY = "your_gemini_api_key"
   SUPABASE_URL = "https://your-project-id.supabase.co"
   SUPABASE_KEY = "your_service_role_key"
   GROQ_API_KEY = "your_groq_api_key"
   ```
7. Click **"Deploy"**

> ✅ **Cloud-ready**: User data, chat history, and sessions are stored in Supabase (PostgreSQL) and persist across redeployments and server restarts.

---

## 🛡️ Security Notes

- Passwords are **bcrypt-hashed** — never stored in plain text
- API keys are loaded from environment variables (`.env` or `st.secrets`)
- `.env`, `*.db`, and `secrets.toml` are in `.gitignore` — never committed
- Session tokens expire after 30 days
- Supabase uses the `service_role` key server-side with RLS policies

---

## 🧰 Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend  | Streamlit |
| AI Models | Google Gemini 2.5 (Flash / Pro), Groq Llama 3.3 70B |
| Database  | Supabase (PostgreSQL) |
| Auth      | bcrypt |
| Styling   | Custom CSS (glassmorphism, gradients) |

---

## 📄 License

MIT License — feel free to use and modify.