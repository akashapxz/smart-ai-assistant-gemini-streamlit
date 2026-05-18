# Prompt Engineering Playground: Smart AI Assistant with Gemini and Streamlit

A professional AI assistant and prompt engineering playground built using Google Gemini and Streamlit.

## 🚀 Features

### 🤖 Core AI Features
- Google Gemini API integration
- Multiple personality modes
- Model selection (Gemini Flash / Pro)
- Temperature and max token controls

### 🧠 Prompt Engineering Techniques
- Zero-Shot Prompting
- One-Shot Prompting
- Few-Shot Prompting
- Chain-of-Thought Prompting
- Role-Based Prompting
- Structured Output Prompting

### 📄 Document Q&A
- Upload PDF, DOCX, and TXT files
- Ask questions about uploaded content

### 📊 Productivity Features
- Usage statistics
- Chat export (TXT and Markdown)
- Clear chat functionality

### 🎨 UI
- Professional Streamlit interface
- Custom styling

## 📂 Project Structure

smart_ai_assistant/
├── app.py
├── prompts.py
├── prompting_techniques.py
├── utils.py
├── document_reader.py
├── requirements.txt
├── .env
├── .gitignore
└── README.md

## ⚙️ Installation

pip install -r requirements.txt

## 🔑 Environment Variables

Create a `.env` file:

GEMINI_API_KEY=YOUR_API_KEY_HERE

## ▶️ Run

streamlit run app.py

## 🌐 Deployment

Deploy easily to:
- Streamlit Community Cloud
- Hugging Face Spaces