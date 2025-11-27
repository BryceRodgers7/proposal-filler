"""
Login page.
"""
import streamlit as st
from helpers.auth import login


def render_login_page():
    """
    Render the login page.
    """
    st.title("💚 Tinder for Non-Profits")
    st.markdown("### 🔐 Login")
    
    with st.form("login_form"):
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        submit = st.form_submit_button("Login", type="primary", use_container_width=True)
        
        if submit:
            success, message, user = login(username, password)
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    
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

