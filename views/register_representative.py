"""
Registration page for representatives.
"""
import streamlit as st
from helpers.auth import register


def render_register_representative_page():
    """
    Render the registration page for representatives.
    """
    st.title("💚 Tinder for Non-Profits")
    st.markdown("### 🏢 Register as a Representative")
    st.write("Representatives can create organization profiles and upgrade to premium features.")
    
    with st.form("register_representative_form"):
        username = st.text_input("Username", key="rep_register_username")
        email = st.text_input("Email", key="rep_register_email")
        password = st.text_input("Password", type="password", key="rep_register_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="rep_register_confirm_password")
        submit = st.form_submit_button("Register as Representative", type="primary", use_container_width=True)
        
        if submit:
            success, message, user = register(username, email, password, confirm_password, user_type="representative")
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    
    st.markdown("---")
    st.markdown("Already have an account? [Go to Login](#)")
    if st.button("← Back to Login", use_container_width=True):
        st.session_state.page = "login"
        st.rerun()

