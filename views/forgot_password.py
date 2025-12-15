"""
Forgot Password page for requesting password reset.
"""
import streamlit as st
from helpers.auth import request_password_reset


def render_forgot_password_page():
    """
    Render the forgot password page where users can request a password reset link.
    """
    st.title("🔐 Forgot Password")
    st.write("Enter your email address and we'll send you a link to reset your password.")
    
    with st.form("forgot_password_form"):
        email = st.text_input("Email Address", key="forgot_password_email")
        submit = st.form_submit_button("Send Reset Link", type="primary", use_container_width=True)
        
        if submit:
            if not email or not email.strip():
                st.error("Please enter your email address")
            else:
                success, message = request_password_reset(email.strip().lower())
                if success:
                    st.success(message)
                    st.info("💡 Please check your email inbox (and spam folder) for the reset link.")
                else:
                    st.error(message)
    
    st.markdown("---")
    
    # Back to login button
    if st.button("← Back to Login", use_container_width=True):
        st.session_state.page = "login"
        st.rerun()

