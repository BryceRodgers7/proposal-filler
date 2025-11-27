"""
Registration page for donors.
"""
import streamlit as st
from helpers.auth import register


def render_register_donor_page():
    """
    Render the registration page for donors.
    """
    st.title("💚 Tinder for Non-Profits")
    st.markdown("### 💰 Register as a Donor")
    st.write("Donors can browse organization profiles and find causes that align with their values.")
    
    with st.form("register_donor_form"):
        username = st.text_input("Username", key="donor_register_username")
        email = st.text_input("Email", key="donor_register_email")
        password = st.text_input("Password", type="password", key="donor_register_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="donor_register_confirm_password")
        submit = st.form_submit_button("Register as Donor", type="primary", use_container_width=True)
        
        if submit:
            success, message, user = register(username, email, password, confirm_password, user_type="donor")
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

