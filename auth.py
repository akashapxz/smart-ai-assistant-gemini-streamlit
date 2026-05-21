"""
Authentication module for Smart AI Assistant.
Handles login, signup, Google OAuth, session management, and cookie-based persistent sessions.
"""

import re
import streamlit as st
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


def check_google_oauth():
    """Check if user authenticated via Google OAuth (st.login). Bridge to app session."""
    if st.session_state.get("authenticated"):
        return True

    try:
        if st.user.is_logged_in:
            email = st.user.email
            name = getattr(st.user, "name", "") or email.split("@")[0]

            # Find or create user in our database
            user = get_or_create_google_user(email, name)
            if user:
                st.session_state.authenticated = True
                st.session_state.user = user
                st.session_state.auth_provider = "google"
                return True
    except Exception:
        pass
    return False


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

    # If user logged in via Google, also clear the OIDC cookie
    if st.session_state.get("auth_provider") == "google":
        try:
            st.logout()
        except Exception:
            pass

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
    """Render a styled 'Continue with Google' button."""
    st.markdown("""
    <div style="display:flex;align-items:center;justify-content:center;margin:0.5rem 0;">
        <div style="flex:1;height:1px;background:rgba(255,255,255,0.1);"></div>
        <span style="padding:0 1rem;color:rgba(255,255,255,0.4);font-size:0.8rem;">or</span>
        <div style="flex:1;height:1px;background:rgba(255,255,255,0.1);"></div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔵 Continue with Google", key="google_login_btn", use_container_width=True):
        st.login("google")


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
        # Google Sign-In (top, prominent)
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
        # Google Sign-Up (top, prominent)
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
