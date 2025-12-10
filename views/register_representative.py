"""
Registration page for representatives with email verification.
"""
import streamlit as st
from helpers.auth import register


def render_register_representative_page():
    """
    Render the registration page for representatives.
    After registration, user must verify email before logging in.
    """
    st.title("💚 Tinder for Non-Profits")
    st.markdown("### 🏢 Register as a Representative")
    st.write("Representatives can create organization profiles and upgrade to premium features.")
    
    # Check if registration was just successful
    if st.session_state.get("registration_success"):
        _render_registration_success()
        return
    
    with st.form("register_representative_form"):
        username = st.text_input("Username", key="rep_register_username")
        email = st.text_input("Email", key="rep_register_email")
        password = st.text_input("Password", type="password", key="rep_register_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="rep_register_confirm_password")
        submit = st.form_submit_button("Register as Representative", type="primary", use_container_width=True)
        
        if submit:
            success, message, user = register(username, email, password, confirm_password, user_type="representative")
            if success:
                # Store registration info for success page
                st.session_state.registration_success = True
                st.session_state.registered_email = email
                st.session_state.registered_username = username
                st.rerun()
            else:
                st.error(message)
    
    st.markdown("---")
    st.markdown("Already have an account? [Go to Login](#)")
    if st.button("← Back to Login", use_container_width=True):
        st.session_state.page = "login"
        st.rerun()


def _render_registration_success():
    """
    Render the success page after registration.
    """
    email = st.session_state.get("registered_email", "your email")
    username = st.session_state.get("registered_username", "there")
    
    st.balloons()
    
    st.success(f"🎉 Welcome, **{username}**! Your account has been created.")
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        padding: 25px;
        border-radius: 12px;
        text-align: center;
        margin: 20px 0;
        color: white;
    ">
        <h3 style="margin: 0 0 15px 0; color: white;">📧 Check Your Email</h3>
        <p style="margin: 0; font-size: 16px; opacity: 0.95;">
            We've sent a verification link to:<br>
            <strong style="font-size: 18px;">{email}</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="
        background: #f0fdf4;
        border: 1px solid #86efac;
        padding: 20px;
        border-radius: 8px;
        margin: 15px 0;
    ">
        <h4 style="color: #166534; margin: 0 0 10px 0;">📋 Next Steps:</h4>
        <ol style="color: #15803d; margin: 0; padding-left: 20px;">
            <li>Check your email inbox (and spam folder)</li>
            <li>Click the verification link in the email</li>
            <li>Return here to log in and start creating your organization profile!</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("💡 **Tip:** The verification link expires in 2 hours. If you don't see the email, you can request a new one from the login page.")
    
    st.markdown("---")
    
    if st.button("🔐 Go to Login", type="primary", use_container_width=True):
        # Clear registration success state
        if "registration_success" in st.session_state:
            del st.session_state.registration_success
        if "registered_email" in st.session_state:
            del st.session_state.registered_email
        if "registered_username" in st.session_state:
            del st.session_state.registered_username
        st.session_state.page = "login"
        st.rerun()
