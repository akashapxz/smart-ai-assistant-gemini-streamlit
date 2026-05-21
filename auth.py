"""
Authentication module for Smart AI Assistant.
Handles login, signup, Google Sign-In (direct redirect), session management,
and cookie-based persistent sessions.
"""

import re
import urllib.parse
import streamlit as st
import requests as http_requests
from database import (
    create_user,
    authenticate_user,
    create_session_token,
    validate_session_token,
    delete_session_token,
    get_or_create_google_user,
)


def init_auth_state():
    """Initialize authentication-related session state."""
    defaults = {
        "authenticated": False,
        "user": None,
        "auth_page": "login",
        "session_token": None,
        "auth_provider": "local",  # "local" or "google"
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def check_persistent_session():
    """Check for a persistent session token in query params. Auto-login if valid."""
    if st.session_state.get("authenticated"):
        return True

    params = st.query_params
    token = params.get("session_token", None)

    if token:
        user = validate_session_token(token)
        if user:
            st.session_state.authenticated = True
            st.session_state.user = user
            st.session_state.session_token = token
            return True
        else:
            st.query_params.clear()
    return False


def _get_google_config():
    """Get Google OAuth config from secrets."""
    try:
        client_id = st.secrets["auth"]["google"]["client_id"]
        client_secret = st.secrets["auth"]["google"]["client_secret"]
        redirect_uri = st.secrets["auth"]["redirect_uri"]
        return client_id, client_secret, redirect_uri
    except Exception:
        return None, None, None


def check_google_callback():
    """Check if Google redirected back with an authorization code."""
    if st.session_state.get("authenticated"):
        return True

    code = st.query_params.get("code", None)
    if not code:
        return False

    client_id, client_secret, redirect_uri = _get_google_config()
    if not client_id:
        st.query_params.clear()
        return False

    try:
        # Exchange authorization code for tokens
        token_response = http_requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=10,
        )

        if token_response.status_code != 200:
            print(f"[AUTH] Token exchange failed: {token_response.text}")
            st.query_params.clear()
            return False

        tokens = token_response.json()
        id_token_str = tokens.get("id_token")

        if not id_token_str:
            st.query_params.clear()
            return False

        # Verify the ID token
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests

        idinfo = id_token.verify_oauth2_token(
            id_token_str, google_requests.Request(), client_id
        )

        if idinfo["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
            st.query_params.clear()
            return False

        email = idinfo.get("email", "")
        name = idinfo.get("name", "") or email.split("@")[0]

        # Find or create user in our database
        user = get_or_create_google_user(email, name)
        if user:
            st.session_state.authenticated = True
            st.session_state.user = user
            st.session_state.auth_provider = "google"
            st.query_params.clear()
            return True

    except Exception as e:
        print(f"[AUTH] Google callback error: {e}")

    st.query_params.clear()
    return False


def _get_google_login_url():
    """Build Google OAuth authorization URL."""
    client_id, _, redirect_uri = _get_google_config()
    if not client_id:
        return None

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "prompt": "select_account",
    }
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)


def handle_login(username, password, remember_me):
    """Process login. Returns (success, message)."""
    if not username or not password:
        return False, "Please fill in all fields."

    user = authenticate_user(username, password)
    if user:
        st.session_state.authenticated = True
        st.session_state.user = user
        st.session_state.auth_provider = "local"
        if remember_me:
            token = create_session_token(user["id"], days=30)
            st.session_state.session_token = token
            st.query_params["session_token"] = token
        return True, "Login successful!"
    return False, "Invalid username or password."


def handle_signup(full_name, email, username, password, confirm_password):
    """Process signup with validation. Returns (success, message)."""
    if not all([full_name, email, username, password, confirm_password]):
        return False, "Please fill in all fields."
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return False, "Username can only contain letters, numbers, and underscores."
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        return False, "Please enter a valid email address."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    if password != confirm_password:
        return False, "Passwords do not match."

    user = create_user(username, email, password, full_name)
    if user:
        return True, "Account created successfully! Please log in."
    return False, "Username or email already exists."


def handle_logout():
    """Clear session and remove persistent token."""
    token = st.session_state.get("session_token")
    if token:
        delete_session_token(token)

    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.session_token = None
    st.session_state.auth_provider = "local"
    st.session_state.current_conversation_id = None
    st.session_state.messages = []
    st.query_params.clear()


def render_auth_page():
    """Render the login or signup page."""
    if st.session_state.auth_page == "login":
        _render_login()
    else:
        _render_signup()


def _render_google_button():
    """Render a styled 'Continue with Google' link button."""
    login_url = _get_google_login_url()
    if not login_url:
        return

    st.markdown("""
    <div style="display:flex;align-items:center;justify-content:center;margin:0.5rem 0;">
        <div style="flex:1;height:1px;background:rgba(255,255,255,0.1);"></div>
        <span style="padding:0 1rem;color:rgba(255,255,255,0.4);font-size:0.8rem;">or</span>
        <div style="flex:1;height:1px;background:rgba(255,255,255,0.1);"></div>
    </div>
    """, unsafe_allow_html=True)

    st.link_button("🔵 Continue with Google", login_url, use_container_width=True)


def _render_login():
    """Render the login form."""
    st.markdown("""
    <div style="text-align:center;margin-bottom:1rem;">
        <div style="font-size:3.5rem;animation:float 3s ease-in-out infinite;">🤖</div>
        <div style="font-size:1.8rem;font-weight:700;background:linear-gradient(135deg,#818cf8,#06b6d4);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;">Welcome Back</div>
        <div style="color:rgba(255,255,255,0.45);font-size:0.9rem;">Sign in to your Smart AI Assistant</div>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        # Google Sign-In link
        _render_google_button()

        st.markdown("")  # spacing

        username = st.text_input("Username", placeholder="Enter your username", key="login_username")
        password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")
        remember_me = st.checkbox("🔒 Remember me for 30 days", key="login_remember")

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🚀 Sign In", key="login_btn", use_container_width=True):
                success, message = handle_login(username, password, remember_me)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
        with col2:
            if st.button("📝 Create Account", key="goto_signup", use_container_width=True):
                st.session_state.auth_page = "signup"
                st.rerun()


def _render_signup():
    """Render the signup form."""
    st.markdown("""
    <div style="text-align:center;margin-bottom:1rem;">
        <div style="font-size:3.5rem;">✨</div>
        <div style="font-size:1.8rem;font-weight:700;background:linear-gradient(135deg,#818cf8,#06b6d4);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;">Create Account</div>
        <div style="color:rgba(255,255,255,0.45);font-size:0.9rem;">Join Smart AI Assistant today</div>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        # Google Sign-Up link
        _render_google_button()

        st.markdown("")  # spacing

        full_name = st.text_input("Full Name", placeholder="Your full name", key="signup_fullname")
        email = st.text_input("Email", placeholder="your.email@example.com", key="signup_email")
        username = st.text_input("Username", placeholder="Choose a username", key="signup_username")
        password = st.text_input("Password", type="password", placeholder="Min. 6 characters", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter password", key="signup_confirm")

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("✨ Create Account", key="signup_btn", use_container_width=True):
                success, message = handle_signup(full_name, email, username, password, confirm_password)
                if success:
                    st.success(message)
                    st.session_state.auth_page = "login"
                    st.rerun()
                else:
                    st.error(message)
        with col2:
            if st.button("🔑 Back to Login", key="goto_login", use_container_width=True):
                st.session_state.auth_page = "login"
                st.rerun()
