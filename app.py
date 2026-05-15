import os
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv

from prompts import PROMPTS
from utils import export_chat, get_word_count, get_session_start
from document_reader import extract_text

# ----------------------------
# Load environment variables
# ----------------------------
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("GEMINI_API_KEY not found in .env file.")
    st.stop()

# Configure Gemini
genai.configure(api_key=api_key)

# ----------------------------
# Page configuration
# ----------------------------
st.set_page_config(
    page_title="Smart AI Assistant",
    page_icon="🤖",
    layout="wide"
)

# ----------------------------
# Custom CSS
# ----------------------------
st.markdown("""
<style>
.main-title {
    text-align: center;
    font-size: 3rem;
    font-weight: bold;
    background: linear-gradient(90deg, #4F46E5, #06B6D4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.subtitle {
    text-align: center;
    color: gray;
    margin-bottom: 2rem;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------
# Session State Initialization
# ----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hello! I'm your Smart AI Assistant. How can I help you today?"
        }
    ]

if "session_start" not in st.session_state:
    st.session_state.session_start = get_session_start()

if "document_text" not in st.session_state:
    st.session_state.document_text = ""

# ----------------------------
# Sidebar Controls
# ----------------------------
with st.sidebar:
    st.title("⚙️ Settings")

    personality = st.selectbox(
        "Choose Personality",
        list(PROMPTS.keys())
    )

    model_name = st.selectbox(
        "Choose Gemini Model",
        [
            "gemini-2.5-flash",
            "gemini-2.5-pro"
        ]
    )

    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.1
    )

    max_tokens = st.slider(
        "Max Output Tokens",
        min_value=256,
        max_value=4096,
        value=1024,
        step=256
    )

    st.markdown("---")
    st.subheader("📄 Document Q&A")

    uploaded_file = st.file_uploader(
        "Upload PDF, DOCX, or TXT",
        type=["pdf", "docx", "txt"]
    )

    if uploaded_file:
        with st.spinner("Reading document..."):
            st.session_state.document_text = extract_text(uploaded_file)
        st.success("Document loaded successfully!")

    st.markdown("---")
    st.subheader("📊 Usage Statistics")

    st.metric("Messages", len(st.session_state.messages))
    st.metric("Words", get_word_count(st.session_state.messages))
    st.write(f"Started: {st.session_state.session_start}")

    if st.session_state.document_text:
        st.success("Document context is active.")

    st.markdown("---")
    st.subheader("💾 Export Chat")

    txt_data = export_chat(st.session_state.messages, "txt")
    md_data = export_chat(st.session_state.messages, "md")

    st.download_button(
        "Download TXT",
        data=txt_data,
        file_name="chat_history.txt",
        mime="text/plain"
    )

    st.download_button(
        "Download Markdown",
        data=md_data,
        file_name="chat_history.md",
        mime="text/markdown"
    )

    st.markdown("---")

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Chat cleared. How can I help you now?"
            }
        ]
        st.rerun()

# ----------------------------
# Load selected model
# ----------------------------
generation_config = {
    "temperature": temperature,
    "max_output_tokens": max_tokens
}

model = genai.GenerativeModel(
    model_name=model_name,
    generation_config=generation_config
)

# ----------------------------
# Main Header
# ----------------------------
st.markdown(
    '<div class="main-title">🤖 Smart AI Assistant</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Powered by Google Gemini + Streamlit</div>',
    unsafe_allow_html=True
)

# ----------------------------
# Display Chat History
# ----------------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ----------------------------
# Chat Input
# ----------------------------
if prompt := st.chat_input("Type your message here..."):
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    # Build system prompt
    system_prompt = PROMPTS[personality]

    # Add document context if available
    document_context = ""
    if st.session_state.document_text:
        document_context = (
            "\n\nDocument Context:\n"
            + st.session_state.document_text[:15000]
        )

    # Build conversation history
    history = ""
    for msg in st.session_state.messages:
        role = msg["role"].capitalize()
        history += f"{role}: {msg['content']}\n"

    full_prompt = (
        system_prompt
        + document_context
        + "\n\nConversation History:\n"
        + history
        + f"\nUser: {prompt}"
    )

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = model.generate_content(full_prompt)
                reply = response.text

                st.markdown(reply)

                # Save assistant response
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": reply
                })

            except Exception as e:
                error_message = f"Error: {str(e)}"
                st.error(error_message)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_message
                })