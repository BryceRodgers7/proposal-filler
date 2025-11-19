import streamlit as st
from auth import get_current_user, logout, has_account_tier


def render_sidebar():
    """
    Render the sidebar navigation menu.
    Returns the selected page name.
    """
    st.sidebar.title("📋 Navigation")
    
    # Show current user info
    user = get_current_user()
    if user:
        account_tier = user.account_tier or "free"
        tier_emoji = "⭐" if account_tier.lower() in ["premium", "enterprise"] else "👤"
        st.sidebar.markdown(f"**Logged in as:** {user.username}")
        st.sidebar.markdown(f"**Account tier:** {tier_emoji} {account_tier.capitalize()}")
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            logout()
            st.rerun()
        st.sidebar.markdown("---")
    
    # Define available pages
    pages = {
        "👤 Profile": "profile",
        "📄 Tinderish": "tinderish",
        "📋 Profile Browser": "profilebrowser",
        "❤️ Like Browser": "likebrowser"
    }
    
    # Add premium pages if user has premium access
    if has_account_tier(required_tier="premium"):
        pages["⭐ Premium Profile Browser"] = "premiumprofilebrowser"
    
    # Initialize session state for current page if not set
    if "current_page" not in st.session_state:
        st.session_state.current_page = "profile"
    
    # Use the radio button's key to manage state - this ensures immediate updates
    # If the key exists in session state, use it; otherwise use current_page
    if "page_navigation" not in st.session_state:
        # Initialize based on current_page
        current_index = 0
        if st.session_state.current_page in pages.values():
            current_index = list(pages.values()).index(st.session_state.current_page)
        st.session_state.page_navigation = list(pages.keys())[current_index]
    
    # Create navigation buttons with a key to ensure proper state management
    selected = st.sidebar.radio(
        "Go to",
        list(pages.keys()),
        key="page_navigation"
    )
    
    # Update session state with selected page based on radio button value
    selected_page = pages[selected]
    st.session_state.current_page = selected_page
    
    return st.session_state.current_page

