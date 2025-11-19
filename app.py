"""
Main entry point for the Proposal Filler application.
This file handles app initialization, configuration, and page routing.
"""
import os
import streamlit as st
from db import init_db
from storage import is_s3_available
from sidebar import render_sidebar
from proposal_filler import render_profile_page
from tinderish import render_tinderish
from profilebrowser import render_profile_browser

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

# ----- SIDEBAR NAVIGATION -----
current_page = render_sidebar()

# ----- PAGE ROUTING -----
if current_page == "tinderish":
    render_tinderish()
elif current_page == "profilebrowser":
    render_profile_browser()
elif current_page == "profile":
    render_profile_page()
else:
    render_profile_page()  # Default to profile page

