"""
Login/Registration page.
"""
import streamlit as st
from helpers.auth import login, register


def render_login_page():
    """
    Render the login/registration page.
    """
    st.title("💚 Tinder for Non-Profits")
    st.markdown("### 🔐 Login / Register")
    
    # Create tabs for login and registration
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login")
        
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submit = st.form_submit_button("Login", type="primary")
            
            if submit:
                success, message, user = login(username, password)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
    
    with tab2:
        st.subheader("Register")
        
        with st.form("register_form"):
            username = st.text_input("Username", key="register_username")
            email = st.text_input("Email", key="register_email")
            password = st.text_input("Password", type="password", key="register_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="register_confirm_password")
            submit = st.form_submit_button("Register", type="primary")
            
            if submit:
                success, message, user = register(username, email, password, confirm_password)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

