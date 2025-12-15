"""
Login page with email verification handling.
"""
import streamlit as st
from helpers.auth import login, resend_verification_email, can_resend_verification


def render_login_page():
    """
    Render the login page with email verification support.
    """
    st.title("💚 Tinder for Non-Profits")
    st.markdown("### 🔐 Login")
    
    # Check if we're showing the unverified user flow
    unverified_user_id = st.session_state.get("unverified_user_id")
    unverified_username = st.session_state.get("unverified_username")
    unverified_email = st.session_state.get("unverified_email")
    
    if unverified_user_id:
        _render_unverified_user_flow(unverified_user_id, unverified_username, unverified_email)
        return
    
    # Normal login form
    with st.form("login_form"):
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        submit = st.form_submit_button("Login", type="primary", use_container_width=True)
        
        if submit:
            success, message, user = login(username, password)
            if success:
                st.success(message)
                st.rerun()
            elif message == "unverified":
                # User exists but not verified - rerun to show the verification flow
                st.rerun()
            else:
                st.error(message)
    
    # Forgot password and username links
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔐 Forgot Password?", use_container_width=True):
            st.session_state.page = "forgot_password"
            st.rerun()
    with col2:
        if st.button("👤 Forgot Username?", use_container_width=True):
            st.session_state.page = "forgot_username"
            st.rerun()
    
    st.markdown("---")
    st.markdown("### New User?")
    st.write("Choose your account type to get started:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🏢 Representative")
        st.write("Create organization profiles and connect with donors")
        if st.button("Register as Representative", use_container_width=True):
            st.session_state.page = "register_representative"
            st.rerun()
    
    with col2:
        st.markdown("#### 💰 Donor")
        st.write("Browse organizations and find causes you care about")
        if st.button("Register as Donor", use_container_width=True):
            st.session_state.page = "register_donor"
            st.rerun()


def _render_unverified_user_flow(user_id: int, username: str, email: str):
    """
    Render the flow for users who haven't verified their email.
    
    Args:
        user_id: The unverified user's ID
        username: The unverified user's username
        email: The unverified user's email
    """
    # Mask the email for privacy
    if email and "@" in email:
        parts = email.split("@")
        local = parts[0]
        domain = parts[1]
        if len(local) > 2:
            masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
        else:
            masked_local = local[0] + "*"
        masked_email = f"{masked_local}@{domain}"
    else:
        masked_email = "your email"
    
    st.warning(f"⚠️ Your email is not verified yet, **{username}**")
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border: 1px solid #f59e0b;
        padding: 20px;
        border-radius: 12px;
        margin: 15px 0;
    ">
        <h4 style="color: #92400e; margin: 0 0 10px 0;">📧 Please verify your email</h4>
        <p style="color: #78350f; margin: 0;">
            We sent a verification link to <strong>{masked_email}</strong>.<br>
            Please check your inbox (and spam folder) and click the link to activate your account.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if user can resend
    can_resend, msg, wait_seconds = can_resend_verification(user_id)
    
    st.markdown("#### Didn't receive the email?")
    
    if can_resend:
        if st.button("📤 Resend verification email", type="primary", use_container_width=True):
            success, message = resend_verification_email(user_id)
            if success:
                st.success(message)
                st.info("Please check your email for the new verification link.")
            else:
                st.error(message)
    else:
        if wait_seconds:
            minutes = wait_seconds // 60
            seconds = wait_seconds % 60
            st.info(f"⏱️ Please wait **{minutes}m {seconds}s** before requesting another email.")
            
            # Show a progress indicator
            progress = 1 - (wait_seconds / (5 * 60))  # 5 minutes cooldown
            st.progress(progress, text="Cooldown in progress...")
        else:
            # Max attempts reached or other error
            st.error(msg)
            st.markdown("""
            <div style="
                background: #fee2e2;
                border: 1px solid #ef4444;
                padding: 15px;
                border-radius: 8px;
                margin: 10px 0;
            ">
                <strong>Need help?</strong><br>
                Please contact support if you're having trouble verifying your email.
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Option to try a different account
    if st.button("← Try a different account", use_container_width=True):
        # Clear the unverified session data
        if "unverified_user_id" in st.session_state:
            del st.session_state.unverified_user_id
        if "unverified_username" in st.session_state:
            del st.session_state.unverified_username
        if "unverified_email" in st.session_state:
            del st.session_state.unverified_email
        st.rerun()
