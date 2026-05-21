"""
Smart AI Assistant — Main Application
Multi-domain AI chatbot with authentication, persistent chat history, FAQ browser, and premium UI.
Powered by Google Gemini + Streamlit.
"""

import os
import time
from collections import deque
import streamlit as st
import google.generativeai as genai
from openai import OpenAI
from dotenv import load_dotenv

from database import init_db, create_conversation, save_message, get_conversations, get_messages, delete_conversation, update_conversation_title, get_conversation, get_message_count
from auth import init_auth_state, check_persistent_session, check_google_callback, handle_logout, render_auth_page
from prompts import PROMPTS, DOMAIN_PROMPTS
from prompting_techniques import TECHNIQUES
from utils import export_chat, get_word_count, get_session_start, format_timestamp, truncate_text, generate_chat_title
from document_reader import extract_text
from faqs import load_all_faqs, get_faqs_by_domain, search_faqs, get_all_domains, get_domain_config, DOMAIN_CONFIG

# ----------------------------
# Load environment variables
# ----------------------------
load_dotenv()
# Support both .env (local) and st.secrets (Streamlit Cloud)
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        api_key = None

groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    try:
        groq_api_key = st.secrets.get("GROQ_API_KEY")
    except Exception:
        groq_api_key = None

# ----------------------------
# Page configuration (MUST be first Streamlit command)
# ----------------------------
st.set_page_config(
    page_title="Smart AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------
# Initialize database
# ----------------------------
init_db()

# ----------------------------
# Initialize session state
# ----------------------------
init_auth_state()

defaults = {
    "messages": [],
    "session_start": get_session_start(),
    "document_text": "",
    "current_page": "chat",
    "current_domain": "General",
    "current_conversation_id": None,
    "doc_processed_name": None,
    "api_request_times": deque(maxlen=5),
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ----------------------------
# Global Premium CSS
# ----------------------------
def inject_global_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ── Global Theme ── */
    .stApp {
        background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3e 50%, #0d0d2b 100%);
        font-family: 'Inter', sans-serif;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: rgba(15, 15, 35, 0.95) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }

    section[data-testid="stSidebar"] .stMarkdown {
        color: rgba(255, 255, 255, 0.85);
    }

    /* ── Cards / Glassmorphism ── */
    .glass-card {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.2rem;
        margin-bottom: 0.8rem;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        transition: all 0.3s ease;
    }
    .glass-card:hover {
        background: rgba(255, 255, 255, 0.07);
        border-color: rgba(129, 140, 248, 0.2);
        transform: translateY(-1px);
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.1);
    }

    /* ── Gradient Title ── */
    .main-title {
        text-align: center;
        font-family: 'Inter', sans-serif;
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #818cf8, #06b6d4, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
        letter-spacing: -0.02em;
    }

    .subtitle {
        text-align: center;
        color: rgba(255, 255, 255, 0.4);
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        font-weight: 400;
        margin-bottom: 1.5rem;
    }

    /* ── Domain Badge ── */
    .domain-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        letter-spacing: 0.02em;
    }

    /* ── Chat Bubbles ── */
    .stChatMessage {
        border-radius: 16px !important;
        margin-bottom: 0.5rem !important;
    }

    /* ── Input Styling ── */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: rgba(255, 255, 255, 0.06) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: white !important;
        font-family: 'Inter', sans-serif !important;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #818cf8 !important;
        box-shadow: 0 0 0 2px rgba(129, 140, 248, 0.15) !important;
    }

    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.06) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
    }

    /* ── Buttons ── */
    div.stButton > button {
        border-radius: 10px !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        transition: all 0.25s ease !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        background: rgba(255, 255, 255, 0.05) !important;
        color: rgba(255, 255, 255, 0.8) !important;
    }
    div.stButton > button:hover {
        background: rgba(129, 140, 248, 0.15) !important;
        border-color: rgba(129, 140, 248, 0.3) !important;
        transform: translateY(-1px) !important;
    }

    /* ── Navigation buttons ── */
    .nav-active {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(6, 182, 212, 0.15)) !important;
        border-color: rgba(129, 140, 248, 0.3) !important;
    }

    /* ── Conversation List Item ── */
    .conv-item {
        padding: 0.8rem 1rem;
        border-radius: 12px;
        cursor: pointer;
        transition: all 0.2s ease;
        border: 1px solid transparent;
        margin-bottom: 0.3rem;
    }
    .conv-item:hover {
        background: rgba(255, 255, 255, 0.05);
        border-color: rgba(255, 255, 255, 0.08);
    }
    .conv-item-active {
        background: rgba(99, 102, 241, 0.12) !important;
        border-color: rgba(129, 140, 248, 0.2) !important;
    }
    .conv-title {
        color: rgba(255, 255, 255, 0.9);
        font-weight: 500;
        font-size: 0.85rem;
        margin-bottom: 0.15rem;
    }
    .conv-meta {
        color: rgba(255, 255, 255, 0.35);
        font-size: 0.72rem;
    }

    /* ── FAQ Card ── */
    .faq-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 14px;
        padding: 1.2rem;
        margin-bottom: 0.7rem;
        transition: all 0.3s ease;
    }
    .faq-card:hover {
        background: rgba(255, 255, 255, 0.06);
        border-color: rgba(129, 140, 248, 0.15);
    }
    .faq-question {
        color: rgba(255, 255, 255, 0.95);
        font-weight: 600;
        font-size: 0.95rem;
        margin-bottom: 0.5rem;
    }
    .faq-answer {
        color: rgba(255, 255, 255, 0.6);
        font-size: 0.85rem;
        line-height: 1.6;
    }

    /* ── Metrics ── */
    [data-testid="stMetricValue"] {
        color: #818cf8 !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* ── Expander ── */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.03) !important;
        border-radius: 12px !important;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 8px 16px;
        font-family: 'Inter', sans-serif;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(99, 102, 241, 0.15) !important;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }

    /* ── Hide defaults ── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* ── User profile ── */
    .user-profile {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        padding: 0.8rem;
        background: rgba(255, 255, 255, 0.04);
        border-radius: 12px;
        margin-bottom: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }
    .user-avatar {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background: linear-gradient(135deg, #6366f1, #06b6d4);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
        color: white;
        font-weight: 700;
    }
    .user-name {
        color: rgba(255, 255, 255, 0.9);
        font-weight: 600;
        font-size: 0.85rem;
    }
    .user-role {
        color: rgba(255, 255, 255, 0.4);
        font-size: 0.72rem;
    }
    </style>
    """, unsafe_allow_html=True)


# ----------------------------
# Check authentication
# ----------------------------
inject_global_css()

if not api_key and not groq_api_key:
    st.error("⚠️ No API keys found. Add GEMINI_API_KEY or GROQ_API_KEY to your .env file.")
    st.stop()

if api_key:
    genai.configure(api_key=api_key)

# Check persistent session (remember me)
check_persistent_session()

# Check Google OAuth callback (code exchange)
check_google_callback()

# If not authenticated, show auth page
if not st.session_state.authenticated:
    render_auth_page()
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# MAIN APP (only shown when authenticated)
# ══════════════════════════════════════════════════════════════════════════════

user = st.session_state.user

# ----------------------------
# Sidebar
# ----------------------------
with st.sidebar:
    # User profile
    initial = user["full_name"][0].upper() if user["full_name"] else "U"
    st.markdown(f"""
    <div class="user-profile">
        <div class="user-avatar">{initial}</div>
        <div>
            <div class="user-name">{user["full_name"]}</div>
            <div class="user-role">@{user["username"]}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Navigation
    st.markdown("##### Navigation")
    nav_col1, nav_col2, nav_col3 = st.columns(3)
    with nav_col1:
        if st.button("💬 Chat", key="nav_chat", use_container_width=True):
            st.session_state.current_page = "chat"
            st.rerun()
    with nav_col2:
        if st.button("❓ FAQs", key="nav_faq", use_container_width=True):
            st.session_state.current_page = "faq"
            st.rerun()
    with nav_col3:
        if st.button("📜 History", key="nav_history", use_container_width=True):
            st.session_state.current_page = "history"
            st.rerun()

    st.markdown("---")

    # ➕ New Chat — always visible, right below navigation
    if st.button("➕ New Chat", key="new_chat_btn", use_container_width=True):
        st.session_state.current_conversation_id = None
        st.session_state.messages = []
        st.session_state.document_text = ""
        st.session_state.doc_processed_name = None
        st.session_state.current_page = "chat"
        st.rerun()

    st.markdown("---")

    # Domain selector
    st.markdown("##### 🌐 Assistant Mode")
    domain_options = ["General"] + get_all_domains()
    domain_labels = {
        "General": "💬 General Assistant",
        "College": "🎓 College FAQ Assistant",
        "HR": "👥 HR Support Assistant",
        "Customer Support": "🛒 Customer Support Assistant",
        "Product": "📦 Product Assistance Assistant",
    }
    selected_domain = st.selectbox(
        "Select Mode",
        domain_options,
        format_func=lambda x: domain_labels.get(x, x),
        key="domain_selector",
        label_visibility="collapsed",
    )
    if selected_domain != st.session_state.current_domain:
        st.session_state.current_domain = selected_domain

    st.markdown("---")

    # Page-specific sidebar content
    if st.session_state.current_page == "chat":
        # Chat settings
        st.markdown("##### ⚙️ Chat Settings")

        personality = st.selectbox("Personality", list(PROMPTS.keys()), key="personality_sel")
        technique = st.selectbox("🧠 Prompting Technique", list(TECHNIQUES.keys()), key="technique_sel")
        temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1, key="temp_slider")
        max_tokens = st.slider("Max Tokens", 256, 4096, 1024, 256, key="token_slider")

        st.markdown("---")

        # Conversations list
        st.markdown("##### 💬 Conversations")
        convos = get_conversations(user["id"])
        for conv in convos[:10]:
            is_active = conv["id"] == st.session_state.current_conversation_id
            icon = domain_labels.get(conv["domain"], "💬")[:2]
            label = f"{icon} {truncate_text(conv['title'], 25)}"
            if st.button(label, key=f"conv_{conv['id']}", use_container_width=True):
                st.session_state.current_conversation_id = conv["id"]
                msgs = get_messages(conv["id"])
                st.session_state.messages = [{"role": m["role"], "content": m["content"]} for m in msgs]
                st.session_state.current_domain = conv["domain"]
                st.rerun()

    st.markdown("---")

    # Export
    if st.session_state.messages:
        st.markdown("##### 💾 Export")
        txt_data = export_chat(st.session_state.messages, "txt")
        md_data = export_chat(st.session_state.messages, "md")
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            st.download_button("📄 TXT", data=txt_data, file_name="chat.txt", mime="text/plain", use_container_width=True)
        with col_e2:
            st.download_button("📝 MD", data=md_data, file_name="chat.md", mime="text/markdown", use_container_width=True)
        st.markdown("---")

    # Logout
    if st.button("🚪 Logout", key="logout_btn", use_container_width=True):
        handle_logout()
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE ROUTER
# ══════════════════════════════════════════════════════════════════════════════

def render_chat_page():
    """Main chat interface."""
    domain = st.session_state.current_domain
    d_conf = get_domain_config(domain) if domain != "General" else {"icon": "💬", "color": "#818cf8", "label": "General Assistant"}

    # Determine active provider name for subtitle
    provider = st.session_state.get("provider_sel", "Gemini")

    st.markdown(f'<div class="main-title">{d_conf["icon"]} Smart AI Assistant</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="subtitle">{d_conf["label"]} Mode • Powered by {provider}</div>', unsafe_allow_html=True)

    # Show relevant FAQs as quick suggestions for domain modes
    if domain != "General":
        faqs = get_faqs_by_domain(domain)
        if faqs:
            with st.expander(f"💡 Quick {d_conf['label']} Questions", expanded=False):
                cols = st.columns(2)
                for i, faq in enumerate(faqs[:6]):
                    with cols[i % 2]:
                        if st.button(f"❓ {truncate_text(faq['question'], 50)}", key=f"faq_quick_{i}", use_container_width=True):
                            st.session_state["pending_faq_question"] = faq["question"]
                            st.rerun()

    # Validate current conversation (could be stale after DB reset)
    if st.session_state.current_conversation_id:
        existing = get_conversation(st.session_state.current_conversation_id)
        if not existing:
            st.session_state.current_conversation_id = None
            st.session_state.messages = []

    # Toolbar row — provider/model selector + document upload (like modern LLMs)
    tool_col1, tool_col2, tool_col3 = st.columns([3, 3, 6])
    with tool_col1:
        provider_options = ["Gemini"]
        if groq_api_key:
            provider_options.append("Groq")
        provider = st.selectbox("Provider", provider_options, key="provider_sel", label_visibility="collapsed")
    with tool_col2:
        if provider == "Groq":
            st.selectbox("Model", ["llama-3.3-70b-versatile"], key="groq_model_sel", label_visibility="collapsed")
        else:
            st.selectbox("Model", ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-pro"], key="model_sel", label_visibility="collapsed")
    with tool_col3:
        tc1, tc2 = st.columns([1, 11])
        with tc1:
            with st.popover("📎"):
                uploaded_file = st.file_uploader(
                    "Upload PDF, DOCX, or TXT",
                    type=["pdf", "docx", "txt"],
                    key="doc_upload",
                )
                if uploaded_file:
                    if st.session_state.doc_processed_name != uploaded_file.name:
                        with st.spinner("Reading document..."):
                            st.session_state.document_text = extract_text(uploaded_file)
                            st.session_state.doc_processed_name = uploaded_file.name
                        st.success("✅ Document loaded!")
                    else:
                        st.success(f"📄 {uploaded_file.name} active")
        with tc2:
            if st.session_state.document_text:
                st.caption(f"📄 **{st.session_state.doc_processed_name}** attached")

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Check for pending FAQ question
    pending = st.session_state.pop("pending_faq_question", None)

    # Chat input
    prompt = st.chat_input("Type your message here...")
    if pending:
        prompt = pending

    if prompt:
        # Create conversation on first message (prevents duplicate "New Chat" entries)
        if not st.session_state.current_conversation_id:
            title = generate_chat_title(prompt)
            conv_id = create_conversation(user["id"], title, domain)
            st.session_state.current_conversation_id = conv_id

        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        save_message(st.session_state.current_conversation_id, "user", prompt)

        # Auto-title conversation from first message (if conversation existed before)
        if len([m for m in st.session_state.messages if m["role"] == "user"]) == 1:
            title = generate_chat_title(prompt)
            update_conversation_title(st.session_state.current_conversation_id, title)

        with st.chat_message("user"):
            st.markdown(prompt)

        # Build prompt context
        personality = st.session_state.get("personality_sel", "General Assistant")
        technique = st.session_state.get("technique_sel", "None")
        temp = st.session_state.get("temp_slider", 0.7)
        max_tok = st.session_state.get("token_slider", 1024)

        # Domain prompt takes priority
        system_prompt = DOMAIN_PROMPTS.get(domain, PROMPTS.get(personality, ""))
        technique_prompt = TECHNIQUES.get(technique, "")

        # Add FAQ context for domain modes
        faq_context = ""
        if domain != "General":
            relevant_faqs = search_faqs(prompt, domain)
            if relevant_faqs:
                faq_context = "\n\nRelevant FAQ Reference:\n"
                for faq in relevant_faqs[:3]:
                    faq_context += f"Q: {faq['question']}\nA: {faq['answer']}\n\n"
                faq_context += "Use the above FAQ information to inform your response when relevant, but answer naturally.\n"

        # Document context
        document_context = ""
        if st.session_state.document_text:
            document_context = "\n\nDocument Context:\n" + st.session_state.document_text[:15000]

        # Conversation history
        history = ""
        for msg in st.session_state.messages[-20:]:  # Last 20 messages for context window
            role = msg["role"].capitalize()
            history += f"{role}: {msg['content']}\n"

        full_prompt = (
            system_prompt + "\n\n"
            + technique_prompt
            + faq_context
            + document_context
            + "\n\nConversation History:\n" + history
            + f"\nUser: {prompt}"
        )

        with st.chat_message("assistant"):
            # ── Proactive rate limiter (5 RPM free tier — Gemini only) ──
            if provider == "Gemini":
                req_times = st.session_state.api_request_times
                now = time.time()
                while req_times and now - req_times[0] > 60:
                    req_times.popleft()
                if len(req_times) >= 4:
                    wait_until = req_times[0] + 62
                    wait_secs = int(wait_until - now)
                    if wait_secs > 0:
                        countdown = st.empty()
                        for remaining in range(wait_secs, 0, -1):
                            countdown.info(f"⏳ Pacing requests to stay within free tier limits. Ready in {remaining}s...")
                            time.sleep(1)
                        countdown.empty()

            # ── Generate with retry ──
            reply = None
            for attempt in range(3):
                try:
                    with st.spinner("Thinking..." if attempt == 0 else f"Retrying ({attempt + 1}/3)..."):
                        if provider == "Groq":
                            # ── Groq API (OpenAI-compatible) ──
                            groq_client = OpenAI(
                                api_key=groq_api_key,
                                base_url="https://api.groq.com/openai/v1",
                            )
                            groq_model = st.session_state.get("groq_model_sel", "llama-3.3-70b-versatile")
                            messages = [{"role": "system", "content": system_prompt + "\n" + technique_prompt + faq_context + document_context}]
                            for msg in st.session_state.messages[-20:]:
                                messages.append({"role": msg["role"], "content": msg["content"]})
                            completion = groq_client.chat.completions.create(
                                model=groq_model,
                                messages=messages,
                                temperature=temp,
                                max_tokens=max_tok,
                            )
                            reply = completion.choices[0].message.content
                        else:
                            # ── Gemini API ──
                            model_name = st.session_state.get("model_sel", "gemini-2.5-flash")
                            generation_config = {"temperature": temp, "max_output_tokens": max_tok}
                            model = genai.GenerativeModel(model_name=model_name, generation_config=generation_config)
                            response = model.generate_content(full_prompt)
                            reply = response.text

                    st.session_state.api_request_times.append(time.time())
                    break
                except Exception as e:
                    if "429" in str(e) and attempt < 2:
                        countdown = st.empty()
                        for remaining in range(30, 0, -1):
                            countdown.info(f"⏳ Rate limit hit. Retrying in {remaining}s...")
                            time.sleep(1)
                        countdown.empty()
                    else:
                        reply = f"⚠️ Error: {str(e)}"
                        st.error(reply)
                        break

            if reply:
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
                save_message(st.session_state.current_conversation_id, "assistant", reply)


def render_faq_page():
    """FAQ browser with search and domain tabs."""
    st.markdown('<div class="main-title">❓ FAQ Knowledge Base</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Browse frequently asked questions across all domains</div>', unsafe_allow_html=True)

    # Search bar
    search_query = st.text_input("🔍 Search FAQs", placeholder="Type to search...", key="faq_search")

    # Domain tabs
    domains = get_all_domains()
    tab_labels = [f"{get_domain_config(d)['icon']} {d}" for d in domains]
    tabs = st.tabs(tab_labels)

    for tab, domain in zip(tabs, domains):
        with tab:
            d_conf = get_domain_config(domain)

            if search_query:
                faqs = search_faqs(search_query, domain)
                if not faqs:
                    st.info(f"No results for '{search_query}' in {domain}")
                    continue
            else:
                faqs = get_faqs_by_domain(domain)

            for i, faq in enumerate(faqs):
                with st.expander(f"❓ {faq['question']}", expanded=False):
                    st.markdown(faq["answer"])
                    st.markdown(f"**Keywords:** {', '.join(faq['keywords'])}")
                    if st.button(f"💬 Ask AI about this", key=f"ask_faq_{domain}_{i}"):
                        st.session_state.current_page = "chat"
                        st.session_state.current_domain = domain
                        st.session_state.pending_faq_question = faq["question"]
                        # Create new conversation for this FAQ
                        conv_id = create_conversation(user["id"], generate_chat_title(faq["question"]), domain)
                        st.session_state.current_conversation_id = conv_id
                        st.session_state.messages = []
                        st.rerun()


def render_history_page():
    """Chat history browser."""
    st.markdown('<div class="main-title">📜 Chat History</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Browse and manage your past conversations</div>', unsafe_allow_html=True)

    # Filters
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        search = st.text_input("🔍 Search conversations", placeholder="Search by title...", key="history_search")
    with col_f2:
        domain_filter = st.selectbox(
            "Filter by domain",
            ["All", "General"] + get_all_domains(),
            key="history_domain_filter",
        )

    convos = get_conversations(
        user["id"],
        domain=domain_filter if domain_filter != "All" else None,
        search=search if search else None,
    )

    if not convos:
        st.info("No conversations found. Start a new chat! 💬")
        return

    st.markdown(f"**{len(convos)} conversation(s)**")

    for conv in convos:
        d_conf = get_domain_config(conv["domain"]) if conv["domain"] != "General" else {"icon": "💬", "color": "#818cf8"}
        msg_count = get_message_count(conv["id"])
        time_str = format_timestamp(conv["updated_at"])

        col1, col2, col3 = st.columns([5, 1, 1])

        with col1:
            st.markdown(f"""
            <div class="glass-card" style="padding:0.8rem 1rem;">
                <div style="display:flex;align-items:center;gap:0.5rem;">
                    <span style="font-size:1.2rem;">{d_conf['icon']}</span>
                    <div>
                        <div style="color:rgba(255,255,255,0.9);font-weight:600;font-size:0.9rem;">
                            {conv['title']}
                        </div>
                        <div style="color:rgba(255,255,255,0.4);font-size:0.75rem;">
                            {msg_count} messages • {time_str} • {conv['domain']}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            if st.button("💬 Open", key=f"open_{conv['id']}", use_container_width=True):
                st.session_state.current_page = "chat"
                st.session_state.current_conversation_id = conv["id"]
                st.session_state.current_domain = conv["domain"]
                msgs = get_messages(conv["id"])
                st.session_state.messages = [{"role": m["role"], "content": m["content"]} for m in msgs]
                st.rerun()

        with col3:
            if st.button("🗑️", key=f"del_{conv['id']}", use_container_width=True):
                delete_conversation(conv["id"])
                if st.session_state.current_conversation_id == conv["id"]:
                    st.session_state.current_conversation_id = None
                    st.session_state.messages = []
                st.rerun()


# ── Route to current page ──
page = st.session_state.current_page

if page == "chat":
    render_chat_page()
elif page == "faq":
    render_faq_page()
elif page == "history":
    render_history_page()
else:
    render_chat_page()