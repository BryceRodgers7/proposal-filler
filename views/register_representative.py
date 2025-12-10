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
        st.markdown("#### Account Information")
        username = st.text_input("Username *", key="rep_register_username")
        email = st.text_input("Email *", key="rep_register_email")
        password = st.text_input("Password *", type="password", key="rep_register_password")
        confirm_password = st.text_input("Confirm Password *", type="password", key="rep_register_confirm_password")
        
        st.markdown("---")
        st.markdown("#### Personal Information")
        
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First Name *", key="rep_first_name")
        with col2:
            last_name = st.text_input("Last Name *", key="rep_last_name")
        
        company = st.text_input("Company / Organization", key="rep_company", help="Optional")
        
        st.markdown("---")
        st.markdown("#### Address Information")
        
        street_address = st.text_input("Street Address *", key="rep_street_address")
        
        col_city, col_state, col_zip = st.columns([2, 1, 1])
        with col_city:
            city = st.text_input("City *", key="rep_city")
        with col_state:
            state = st.text_input("State *", key="rep_state")
        with col_zip:
            zip_code = st.text_input("ZIP *", key="rep_zip")
        
        phone_number = st.text_input("Phone Number", key="rep_phone", help="Optional")
        
        st.markdown("---")
        st.caption("* Required fields")
        
        submit = st.form_submit_button("Register as Representative", type="primary", use_container_width=True)
        
        if submit:
            success, message, user = register(
                username=username, 
                email=email, 
                password=password, 
                confirm_password=confirm_password, 
                user_type="representative",
                first_name=first_name,
                last_name=last_name,
                company=company,
                street_address=street_address,
                city=city,
                state=state,
                zip_code=zip_code,
                phone_number=phone_number
            )
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
