# 🤖 Smart AI Assistant — Gemini + Groq + Streamlit

A full-featured, multi-domain AI assistant with Google Sign-In, persistent cloud-backed chat history, FAQ knowledge base, and a premium dark UI. Powered by **Google Gemini**, **Groq (Llama 3.3)**, **Supabase**, and **Streamlit**.

---

## ✨ Live Demo

[**smart-ai-assistant-gemini-app.streamlit.app**](https://smart-ai-assistant-gemini-app-qodxezfwapqbymzibodojf.streamlit.app)

---

## 🚀 Features

### 🔐 Authentication
- **🔵 Continue with Google** — one-click Google OAuth sign-in (popup → token exchange)
- Signup & login with bcrypt-hashed passwords
- 30-day "Remember Me" persistent sessions
- Google users automatically created in the database (no password needed)

### 💬 Multi-Domain AI Chat
- **💬 General Assistant** — default conversational mode
- **🎓 College FAQ** — admissions, courses, fees, placements
- **👥 HR Support** — leave, payroll, benefits, appraisals
- **🛒 Customer Support** — orders, returns, shipping, payments
- **📦 Product Assistance** — setup, troubleshooting, specs

### 🔌 Dual AI Provider Support
- **Google Gemini** — Gemini 2.5 Flash (default), 2.0 Flash, 2.5 Pro
- **Groq** — Llama 3.3 70B Versatile (ultra-fast inference)
- Provider & model selector in the chat toolbar (near input area)
- Switch providers seamlessly to avoid rate limits

### 🧠 Prompt Engineering
- Zero-Shot, One-Shot, Few-Shot Prompting
- Chain-of-Thought, Role-Based, Structured Output
- Multiple personality modes

### 📄 Document Q&A
- Upload PDF, DOCX, and TXT files via 📎 button (in chat toolbar)
- Ask questions about uploaded content

### ❓ FAQ Knowledge Base
- 40 realistic FAQs across 4 domains
- Search & filter with keyword matching
- "Ask AI" button to discuss any FAQ in chat

### 📜 Persistent Chat History
- All chats saved to **Supabase (PostgreSQL)**
- Browse, search, filter, and re-open past conversations
- Conversations created on first message (no empty entries)

### ⚡ Smart Rate Limit Handling
- Auto-retry with countdown timer on Gemini API rate limits
- Graceful fallback with up to 3 retry attempts

### 🎨 Premium UI
- Dark gradient theme with glassmorphism
- Inter font, smooth animations, custom scrollbars
- Domain-specific color coding
- Modern chat toolbar with provider/model/attachment controls

---

## 📂 Project Structure

```
smart_ai_assistant/
├── app.py                    # Main app (auth gate + multi-page router)
├── database.py               # Supabase (PostgreSQL) database layer
├── auth.py                   # Auth (login/signup/Google OAuth/sessions)
├── faqs.py                   # FAQ loader and search
├── prompts.py                # Personality & domain system prompts
├── prompting_techniques.py   # Prompt engineering techniques
├── utils.py                  # Utility functions
├── document_reader.py        # PDF/DOCX/TXT reader
├── supabase_schema.sql       # PostgreSQL schema
├── data/
│   └── faq_dataset.csv       # FAQ dataset (40 entries, 4 domains)
├── .streamlit/
│   ├── config.toml           # Streamlit theme configuration
│   └── secrets.toml.example  # Template for secrets
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

### 4. Set up Supabase
1. Go to [supabase.com](https://supabase.com) → Create a free project
2. Go to **SQL Editor** → **New Query** → paste `supabase_schema.sql` → **Run**
3. Go to **Settings → API** → copy **Project URL** and **service_role key**

### 5. Set up Google OAuth
1. Go to [Google Cloud Console](https://console.cloud.google.com/) → Create/select a project
2. **APIs & Services → OAuth consent screen** → Configure (External) → **Publish App**
3. **APIs & Services → Credentials → Create Credentials → OAuth Client ID** (Web app)
4. Add **Authorized JavaScript origins**: `http://localhost:8501`
5. Add **Authorized redirect URIs**: `http://localhost:8501`
6. Copy the **Client ID** and **Client Secret**

### 6. Configure secrets
Create `.env`:
```env
GEMINI_API_KEY=your_gemini_api_key
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your_service_role_key
GROQ_API_KEY=your_groq_api_key
```

Create `.streamlit/secrets.toml`:
```toml
GEMINI_API_KEY = "your_gemini_api_key"
SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_KEY = "your_service_role_key"
GROQ_API_KEY = "your_groq_api_key"

[auth]
redirect_uri = "http://localhost:8501"

[auth.google]
client_id = "your_google_client_id"
client_secret = "your_google_client_secret"
```

**Where to get API keys:**
| Key | Source |
|-----|--------|
| Gemini | [Google AI Studio](https://aistudio.google.com/app/apikey) |
| Groq | [Groq Console](https://console.groq.com/keys) |
| Supabase | Dashboard → Settings → API |
| Google OAuth | [Google Cloud Console](https://console.cloud.google.com/) → Credentials |

### 7. Run the app
```bash
streamlit run app.py
```

---

## 🌐 Deploy to Streamlit Cloud

### 1. Push to GitHub
```bash
git add .
git commit -m "Deploy"
git push origin main
```

### 2. Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
2. Connect repo: `akashapxz/smart-ai-assistant-gemini-streamlit`
3. Main file: `app.py` → Click **Advanced settings → Secrets**
4. Paste your secrets:
   ```toml
   GEMINI_API_KEY = "..."
   SUPABASE_URL = "..."
   SUPABASE_KEY = "..."
   GROQ_API_KEY = "..."

   [auth]
   redirect_uri = "https://YOUR-APP-NAME.streamlit.app"

   [auth.google]
   client_id = "..."
   client_secret = "..."
   ```
5. Click **Deploy**

### 3. Update Google Cloud Console
Add your production URL to both:
- **Authorized JavaScript origins**: `https://YOUR-APP-NAME.streamlit.app`
- **Authorized redirect URIs**: `https://YOUR-APP-NAME.streamlit.app`

---

## 🛡️ Security Notes

- Passwords are **bcrypt-hashed** — never stored in plain text
- Google OAuth users have no password (Google handles identity verification)
- API keys loaded from environment variables / `st.secrets`
- `.env`, `*.db`, and `secrets.toml` are gitignored
- Session tokens expire after 30 days
- Google ID tokens are verified server-side against the registered client ID

---

## 🧰 Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend  | Streamlit (≥1.42) |
| AI Models | Google Gemini 2.5 (Flash/Pro), Groq Llama 3.3 70B |
| Database  | Supabase (PostgreSQL) |
| Auth      | Google OAuth 2.0 + bcrypt |
| Styling   | Custom CSS (glassmorphism, gradients) |

---

## 📄 License

MIT License — feel free to use and modify.