import streamlit as st


def render_sidebar():
    """
    Render the sidebar navigation menu.
    Returns the selected page name.
    """
    st.sidebar.title("📋 Navigation")
    
    # Define available pages
    pages = {
        "👤 Profile": "profile",
        "📄 Tinderish": "tinderish",
        "📋 Profile Browser": "profilebrowser"
    }
    
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
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.info("AI-Powered Proposal Form Filler")
    
    return st.session_state.current_page

