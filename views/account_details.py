"""
Account details page for viewing and editing user profile information.
Also includes account deactivation (soft-delete) and reactivation.
"""
import streamlit as st
from helpers.auth import (
    get_current_user, 
    get_current_user_id,
    update_user_details, 
    soft_delete_user, 
    reactivate_user,
    is_user_deleted
)


def render_account_details_page():
    """
    Render the account details page where users can view/edit their info
    and deactivate/reactivate their account.
    """
    st.title("⚙️ Account Details")
    
    # Show success message if set (from previous action)
    if st.session_state.get("account_update_success"):
        st.success("✅ " + st.session_state.account_update_success)
        del st.session_state.account_update_success
    
    user = get_current_user()
    if not user:
        st.error("Unable to load account details. Please try logging in again.")
        return
    
    user_id = get_current_user_id()
    is_deleted = is_user_deleted(user_id)
    
    # If account is deleted, show reactivation UI first
    if is_deleted:
        _render_deleted_account_view(user)
        return
    
    # Normal account view
    _render_account_info(user)
    _render_edit_form(user)
    _render_danger_zone(user)


def _render_deleted_account_view(user):
    """
    Render the view for a soft-deleted account with reactivation option.
    """
    st.warning("⚠️ Your account has been deactivated")
    
    st.markdown("""
    <div style="
        background: #fef3c7;
        border: 1px solid #f59e0b;
        padding: 20px;
        border-radius: 12px;
        margin: 15px 0;
    ">
        <h4 style="color: #92400e; margin: 0 0 10px 0;">Account Status: Deactivated</h4>
        <p style="color: #78350f; margin: 0;">
            Your account and profiles are currently hidden from other users.<br>
            You can reactivate your account at any time to restore full functionality.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Show basic account info (read-only)
    st.markdown("### Account Information")
    
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Username", value=user.username, disabled=True)
        st.text_input("Email", value=user.email, disabled=True)
        st.text_input("First Name", value=user.first_name or "", disabled=True)
        st.text_input("Last Name", value=user.last_name or "", disabled=True)
    
    with col2:
        st.text_input("Account Type", value=user.user_type.capitalize() if user.user_type else "", disabled=True)
        st.text_input("Account Tier", value=user.account_tier.capitalize() if user.account_tier else "", disabled=True)
        st.text_input("Company", value=user.company or "", disabled=True)
        st.text_input("Phone", value=user.phone_number or "", disabled=True)
    
    st.text_input("Street Address", value=user.street_address or "", disabled=True)
    col_city, col_state, col_zip = st.columns([2, 1, 1])
    with col_city:
        st.text_input("City", value=user.city or "", disabled=True)
    with col_state:
        st.text_input("State", value=user.state or "", disabled=True)
    with col_zip:
        st.text_input("ZIP", value=user.zip_code or "", disabled=True)
    
    st.markdown("---")
    
    # Reactivation section
    st.markdown("### 🔄 Reactivate Account")
    st.info("Reactivating your account will restore your profile visibility and access to all features.")
    
    if st.button("✅ Reactivate My Account", type="primary", use_container_width=True):
        success, message = reactivate_user(user.id)
        if success:
            st.success(message)
            st.balloons()
            st.info("Please refresh the page to access all features.")
            st.rerun()
        else:
            st.error(message)


def _render_account_info(user):
    """
    Render read-only account information section.
    """
    st.markdown("### 👤 Account Information")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div style="
            background: #f0fdf4;
            border: 1px solid #86efac;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        ">
            <div style="color: #166534; font-size: 12px; text-transform: uppercase;">Username</div>
            <div style="color: #15803d; font-size: 18px; font-weight: 600;">{user.username}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        user_type_display = user.user_type.capitalize() if user.user_type else "Unknown"
        user_type_emoji = "🏢" if user.user_type == "representative" else "💰"
        st.markdown(f"""
        <div style="
            background: #eff6ff;
            border: 1px solid #93c5fd;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        ">
            <div style="color: #1e40af; font-size: 12px; text-transform: uppercase;">Account Type</div>
            <div style="color: #1d4ed8; font-size: 18px; font-weight: 600;">{user_type_emoji} {user_type_display}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        tier_display = user.account_tier.capitalize() if user.account_tier else "Free"
        tier_emoji = "⭐" if tier_display.lower() in ["premium", "enterprise"] else "🆓"
        st.markdown(f"""
        <div style="
            background: #fef3c7;
            border: 1px solid #fcd34d;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        ">
            <div style="color: #92400e; font-size: 12px; text-transform: uppercase;">Account Tier</div>
            <div style="color: #b45309; font-size: 18px; font-weight: 600;">{tier_emoji} {tier_display}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("")  # Spacing
    
    # Email (read-only)
    st.text_input("📧 Email Address", value=user.email, disabled=True, 
                  help="Contact support to change your email address")
    
    st.markdown("---")


def _render_edit_form(user):
    """
    Render the editable form for user details.
    """
    st.markdown("### ✏️ Edit Your Details")
    
    with st.form("edit_account_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            first_name = st.text_input(
                "First Name *", 
                value=user.first_name or "",
                key="edit_first_name"
            )
        
        with col2:
            last_name = st.text_input(
                "Last Name *", 
                value=user.last_name or "",
                key="edit_last_name"
            )
        
        company = st.text_input(
            "Company / Organization", 
            value=user.company or "",
            key="edit_company",
            help="Optional"
        )
        
        st.markdown("#### 📍 Address")
        
        street_address = st.text_input(
            "Street Address *", 
            value=user.street_address or "",
            key="edit_street_address"
        )
        
        col_city, col_state, col_zip = st.columns([2, 1, 1])
        with col_city:
            city = st.text_input(
                "City *", 
                value=user.city or "",
                key="edit_city"
            )
        with col_state:
            state = st.text_input(
                "State *", 
                value=user.state or "",
                key="edit_state"
            )
        with col_zip:
            zip_code = st.text_input(
                "ZIP *", 
                value=user.zip_code or "",
                key="edit_zip"
            )
        
        phone_number = st.text_input(
            "Phone Number", 
            value=user.phone_number or "",
            key="edit_phone",
            help="Optional"
        )
        
        st.caption("* Required fields")
        
        submit = st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True)
        
        if submit:
            success, message = update_user_details(
                user_id=user.id,
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
                st.session_state.account_update_success = message
                st.rerun()
            else:
                st.error(message)
    
    st.markdown("---")


def _render_danger_zone(user):
    """
    Render the danger zone section with account deactivation.
    """
    st.markdown("### ⚠️ Danger Zone")
    
    with st.expander("🗑️ Deactivate Account", expanded=False):
        st.markdown("""
        <div style="
            background: #fee2e2;
            border: 1px solid #ef4444;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
        ">
            <strong style="color: #991b1b;">Warning:</strong>
            <p style="color: #7f1d1d; margin: 10px 0 0 0;">
                Deactivating your account will:
            </p>
            <ul style="color: #7f1d1d; margin: 5px 0 0 0; padding-left: 20px;">
                <li>Hide your profile from other users</li>
                <li>Hide any organization profiles you've created</li>
                <li>Remove your likes/passes from visibility</li>
                <li>Restrict your access to only this Account Details page</li>
            </ul>
            <p style="color: #7f1d1d; margin: 10px 0 0 0;">
                <strong>Your data will NOT be permanently deleted.</strong> 
                You can reactivate your account at any time.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Confirmation checkbox
        confirm = st.checkbox(
            "I understand that my account will be deactivated",
            key="confirm_deactivate"
        )
        
        if st.button("🗑️ Deactivate My Account", type="secondary", use_container_width=True, disabled=not confirm):
            success, message = soft_delete_user(user.id)
            if success:
                st.warning(message)
                st.info("Your account has been deactivated. Refreshing page...")
                st.rerun()
            else:
                st.error(message)

