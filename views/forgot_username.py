"""
Forgot Username page for requesting username reminder.
"""
import streamlit as st
from helpers.auth import request_username_reminder


def render_forgot_username_page():
    """
    Render the forgot username page where users can request a username reminder.
    """
    st.title("👤 Forgot Username")
    st.write("Enter your email address and we'll send you a reminder with your username.")
    
    with st.form("forgot_username_form"):
        email = st.text_input("Email Address", key="forgot_username_email")
        submit = st.form_submit_button("Send Username Reminder", type="primary", use_container_width=True)
        
        if submit:
            if not email or not email.strip():
                st.error("Please enter your email address")
            else:
                success, message = request_username_reminder(email.strip().lower())
                if success:
                    st.success(message)
                    st.info("💡 Please check your email inbox (and spam folder) for your username.")
                else:
                    st.error(message)
    
    st.markdown("---")
    
    # Back to login button
    if st.button("← Back to Login", use_container_width=True):
        st.session_state.page = "login"
        st.rerun()

