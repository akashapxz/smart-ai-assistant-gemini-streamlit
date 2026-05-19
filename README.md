# 🤖 Smart AI Assistant — Gemini + Streamlit

A full-featured, multi-domain AI assistant with authentication, persistent chat history, FAQ knowledge base, and a premium dark UI. Powered by **Google Gemini** and **Streamlit**.

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

### 🧠 Prompt Engineering
- Zero-Shot, One-Shot, Few-Shot Prompting
- Chain-of-Thought, Role-Based, Structured Output
- Multiple personality modes

### 📄 Document Q&A
- Upload PDF, DOCX, and TXT files
- Ask questions about uploaded content

### ❓ FAQ Knowledge Base
- 40 realistic FAQs across 4 domains
- Search & filter with keyword matching
- "Ask AI" button to discuss any FAQ in chat

### 📜 Persistent Chat History
- All chats saved to SQLite database
- Browse, search, filter, and re-open past conversations
- Survives page refresh and re-login
- Delete conversations you no longer need

### 🎨 Premium UI
- Dark gradient theme with glassmorphism
- Inter font, smooth animations, custom scrollbars
- Domain-specific color coding

---

## 📂 Project Structure

```
smart_ai_assistant/
├── app.py                    # Main app (auth gate + multi-page router)
├── database.py               # SQLite database layer
├── auth.py                   # Authentication (login/signup/sessions)
├── faqs.py                   # FAQ loader and search
├── prompts.py                # Personality & domain system prompts
├── prompting_techniques.py   # Prompt engineering techniques
├── utils.py                  # Utility functions
├── document_reader.py        # PDF/DOCX/TXT reader
├── data/
│   └── faq_dataset.csv       # FAQ dataset (40 entries, 4 domains)
├── .streamlit/
│   ├── config.toml           # Streamlit theme configuration
│   └── secrets.toml.example  # Template for Streamlit Cloud secrets
├── requirements.txt
├── .env                      # Local API key (not committed)
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

### 4. Set up environment variables
Create a `.env` file in the project root:
```
GEMINI_API_KEY=your_api_key_here
```
Get your API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

### 5. Run the app
```bash
streamlit run app.py
```

---

## 🌐 Deploy to Streamlit Cloud

### 1. Push to GitHub
```bash
git add .
git commit -m "Add authentication, chat history, FAQ system, and premium UI"
git push origin main
```

### 2. Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **"New app"**
3. Connect your GitHub repo: `akashapxz/smart-ai-assistant-gemini-streamlit`
4. Set **Main file path**: `app.py`
5. Click **"Advanced settings"** → **Secrets**
6. Add your secret:
   ```
   GEMINI_API_KEY = "your_actual_api_key_here"
   ```
7. Click **"Deploy"**

> ⚠️ **Note**: Streamlit Cloud has an ephemeral filesystem. The SQLite database will reset on each app restart. For production use, consider upgrading to a cloud database like PostgreSQL or Supabase.

---

## 🛡️ Security Notes

- Passwords are **bcrypt-hashed** — never stored in plain text
- API keys are loaded from environment variables (`.env` or `st.secrets`)
- `.env`, `*.db`, and `secrets.toml` are in `.gitignore` — never committed
- Session tokens expire after 30 days

---

## 🧰 Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend  | Streamlit |
| AI Model  | Google Gemini (Flash / Pro) |
| Database  | SQLite |
| Auth      | bcrypt |
| Styling   | Custom CSS (glassmorphism, gradients) |

---

## 📄 License

MIT License — feel free to use and modify.