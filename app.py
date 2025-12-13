"""
Main entry point for the Proposal Filler application.
This file handles app initialization, configuration, and page routing.
"""
import os
import streamlit as st
from helpers.db import init_db
from helpers.storage import is_s3_available
from views.sidebar import render_sidebar
from views.proposal_filler import render_profile_page
from views.tinderish import render_tinderish
from views.profilebrowser import render_profile_browser
from views.like_browser import render_like_browser
from views.premium_profile_browser import render_premium_profile_browser
from views.donor_profile import render_donor_profile_page
from views.register_representative import render_register_representative_page
from views.register_donor import render_register_donor_page
from views.verify_email import render_verify_email_page
from views.account_details import render_account_details_page
from views.account_browser import render_account_browser
from views.card_creator import render_card_creator
from views.kindr_swipe import render_kindr_swipe
from views.card_browser import render_card_browser
from views.card_like_browser import render_card_like_browser
from helpers.auth import is_authenticated, is_user_deleted
from views.login import render_login_page

# ----- CONFIG -----
st.set_page_config(page_title="Proposal Form Filler", page_icon="🤖", layout="centered")

# Initialize database
_db_initialized = False
try:
    init_db()
    _db_initialized = True
except Exception as e:
    # Log error but don't crash the app
    print(f"⚠️ Database initialization warning: {str(e)}")
    print("The app will continue to run, but database features may not work.")

# Initialize S3 storage
_s3_available = is_s3_available()
if not _s3_available:
    print("⚠️ S3 storage is not available. Please check your AWS credentials in secrets.toml")
    print("The app will continue to run, but uploaded files may not be saved to S3.")

# Store initialization flags in session state so they can be accessed by pages
st.session_state.db_initialized = _db_initialized
st.session_state.s3_available = _s3_available

# ----- CHECK FOR EMAIL VERIFICATION PAGE -----
# Handle verification page first (before auth check) since users won't be logged in
# Use experimental_get_query_params for compatibility with older Streamlit versions
query_params = st.experimental_get_query_params()
verification_token = query_params.get("token", [None])[0]

if query_params.get("page", [None])[0] == "verify" and verification_token:
    # Track which tokens we've already processed in this session to prevent re-verification
    if "processed_tokens" not in st.session_state:
        st.session_state.processed_tokens = set()
    
    # If this token was already processed, skip to login
    if verification_token in st.session_state.processed_tokens:
        # Token already processed - user is navigating back or refreshing
        # Don't show verification page again
        pass  # Fall through to normal auth flow below
    else:
        # New token - process verification
        st.session_state.processed_tokens.add(verification_token)
        render_verify_email_page(verification_token)
        st.stop()  # Don't render anything else

# ----- AUTHENTICATION CHECK -----
if not is_authenticated():
    # User is not logged in - check if they want to register
    page = st.session_state.get("page", "login")
    
    if page == "register_representative":
        render_register_representative_page()
    elif page == "register_donor":
        render_register_donor_page()
    else:
        # Default to login page
        render_login_page()
else:
    # User is authenticated, check if account is soft-deleted
    if is_user_deleted():
        # Soft-deleted users can only access the account details page (to reactivate)
        st.sidebar.title("📋 Navigation")
        st.sidebar.warning("⚠️ Account Deactivated")
        st.sidebar.info("Your account is currently deactivated. You can only access Account Details to reactivate.")
        
        # Show logout button in sidebar
        from helpers.auth import logout
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            logout()
            st.rerun()
        
        # Force render account details page
        render_account_details_page()
    else:
        # Normal flow - show the app
        # ----- SIDEBAR NAVIGATION -----
        current_page = render_sidebar()

        # ----- PAGE ROUTING -----
        if current_page == "tinderish":
            render_tinderish()
        elif current_page == "profilebrowser":
            render_profile_browser()
        elif current_page == "likebrowser":
            render_like_browser()
        elif current_page == "accountbrowser":
            render_account_browser()
        elif current_page == "premiumprofilebrowser":
            render_premium_profile_browser()
        elif current_page == "profile":
            render_profile_page()
        elif current_page == "donorprofile":
            render_donor_profile_page()
        elif current_page == "accountdetails":
            render_account_details_page()
        elif current_page == "cardcreator":
            render_card_creator()
        elif current_page == "kindrswipe":
            render_kindr_swipe()
        elif current_page == "cardbrowser":
            render_card_browser()
        elif current_page == "cardlikebrowser":
            render_card_like_browser()
        else:
            # Default based on user type
            user_type = st.session_state.get("user_type", "representative")
            if user_type == "donor":
                render_donor_profile_page()
            else:
                render_profile_page()
