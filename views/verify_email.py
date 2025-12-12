"""
Email verification page.
Handles token validation from email links.
"""
import streamlit as st
from helpers.auth import verify_email_token


def render_verify_email_page(token: str):
    """
    Render the email verification page.
    
    Args:
        token (str): The verification token from the URL query params
    """
    st.title("💚 Tinder for Non-Profits")
    st.markdown("### ✉️ Email Verification")
    
    if not token:
        st.error("No verification token provided. Please check your email for the verification link.")
        _show_back_to_login()
        return
    
    # Show a loading spinner while verifying
    with st.spinner("Verifying your email..."):
        success, message, user = verify_email_token(token)
    
    if success:
        st.success(message)
        st.balloons()  # Celebrate!
        
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            margin: 20px 0;
        ">
            <h3 style="color: white; margin: 0;">🎉 Welcome aboard!</h3>
            <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0;">
                Your account is now active. Click below to log in and get started.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔐 Go to Login", type="primary", use_container_width=True):
            # Set flag to skip verification on next load (query params persist in URL)
            st.session_state.skip_verification = True
            st.session_state.page = "login"
            st.rerun()
    else:
        # Determine the type of error
        if "expired" in message.lower():
            st.error("⏰ " + message)
            st.markdown("""
            <div style="
                background: #fef3c7;
                border: 1px solid #f59e0b;
                padding: 15px;
                border-radius: 8px;
                margin: 15px 0;
            ">
                <strong>What to do:</strong>
                <ol style="margin: 10px 0 0 0; padding-left: 20px;">
                    <li>Go to the login page</li>
                    <li>Enter your username and password</li>
                    <li>Click "Resend verification email" to get a new link</li>
                </ol>
            </div>
            """, unsafe_allow_html=True)
        elif "invalid" in message.lower() or "incorrect" in message.lower():
            st.error("❌ " + message)
            st.info("If you've already verified your email, you can proceed to login.")
        else:
            st.error("❌ " + message)
        
        _show_back_to_login()


def _show_back_to_login():
    """Helper to show the back to login button."""
    st.markdown("---")
    if st.button("← Back to Login", use_container_width=True):
        # Set flag to skip verification on next load (query params persist in URL)
        st.session_state.skip_verification = True
        st.session_state.page = "login"
        st.rerun()

