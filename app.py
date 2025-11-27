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
from helpers.auth import is_authenticated
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
    # User is authenticated, show the app
    # ----- SIDEBAR NAVIGATION -----
    current_page = render_sidebar()

    # ----- PAGE ROUTING -----
    if current_page == "tinderish":
        render_tinderish()
    elif current_page == "profilebrowser":
        render_profile_browser()
    elif current_page == "likebrowser":
        render_like_browser()
    elif current_page == "premiumprofilebrowser":
        render_premium_profile_browser()
    elif current_page == "profile":
        render_profile_page()
    elif current_page == "donorprofile":
        render_donor_profile_page()
    else:
        # Default based on user type
        user_type = st.session_state.get("user_type", "representative")
        if user_type == "donor":
            render_donor_profile_page()
        else:
            render_profile_page()

