import streamlit as st


def render_sidebar():
    """
    Render the sidebar navigation menu.
    Returns the selected page name.
    """
    st.sidebar.title("📋 Navigation")
    
    # Define available pages
    pages = {
        "🏠 Home": "home",
        "📄 Page 2": "page2"
    }
    
    # Initialize session state for current page if not set
    if "current_page" not in st.session_state:
        st.session_state.current_page = "home"
    
    # Create navigation buttons
    selected = st.sidebar.radio(
        "Go to",
        list(pages.keys()),
        index=list(pages.values()).index(st.session_state.current_page) if st.session_state.current_page in pages.values() else 0
    )
    
    # Update session state with selected page
    st.session_state.current_page = pages[selected]
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.info("AI-Powered Proposal Form Filler")
    
    return st.session_state.current_page

