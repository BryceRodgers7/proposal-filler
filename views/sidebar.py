import streamlit as st
from helpers.auth import get_current_user, logout, has_account_tier, get_current_user_type
from helpers.db import get_db, ProposalSubmission, DonorProfile
from helpers.storage import get_s3_url


def render_sidebar():
    """
    Render the sidebar navigation menu.
    Returns the selected page name.
    """
    st.sidebar.title("📋 Navigation")
    
    # Show current user info
    user = get_current_user()
    user_type = get_current_user_type()
    
    if user:
        account_tier = user.account_tier or "free"
        tier_emoji = "⭐" if account_tier.lower() in ["premium", "enterprise"] else "👤"
        user_type_display = user_type.capitalize() if user_type else "Unknown"
        
        # Set emoji based on user type
        if user_type == "admin":
            user_type_emoji = "🔧"
        elif user_type == "representative":
            user_type_emoji = "🏢"
        else:
            user_type_emoji = "💰"
        
        # Show profile image for representatives and donors
        if user_type == "representative":
            # For representatives, show organization image thumbnail
            try:
                db = next(get_db())
                org_profile = db.query(ProposalSubmission).filter(
                    ProposalSubmission.user_id == user.id
                ).first()
                db.close()
                
                if org_profile and org_profile.image_path:
                    # Show organization image thumbnail
                    image_url, error_msg = get_s3_url(org_profile.image_path)
                    if image_url:
                        st.sidebar.image(image_url, width=120, caption="")
                    else:
                        # Image path exists but can't load - show placeholder
                        st.sidebar.markdown(
                            """
                            <div style="width: 120px; height: 90px; background-color: #e0e0e0; 
                                        border-radius: 8px; display: flex; align-items: center; 
                                        justify-content: center; margin-bottom: 10px;">
                                <span style="color: #666; font-size: 11px; text-align: center;">
                                    📷 Image loading...
                                </span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                else:
                    # No image uploaded - show placeholder with message
                    st.sidebar.markdown(
                        """
                        <div style="width: 120px; height: 90px; background-color: #f0f0f0; 
                                    border: 2px dashed #ccc; border-radius: 8px; 
                                    display: flex; align-items: center; justify-content: center; 
                                    margin-bottom: 10px;">
                            <span style="color: #888; font-size: 11px; text-align: center;">
                                📷<br>Add org image
                            </span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            except Exception as e:
                # Error loading profile - show simple placeholder
                st.sidebar.markdown(
                    """
                    <div style="width: 120px; height: 90px; background-color: #f0f0f0; 
                                border: 2px dashed #ccc; border-radius: 8px; 
                                display: flex; align-items: center; justify-content: center; 
                                margin-bottom: 10px;">
                        <span style="color: #888; font-size: 11px; text-align: center;">
                            📷<br>Add org image
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        
        elif user_type == "donor":
            # For donors, show profile image thumbnail
            try:
                db = next(get_db())
                donor_profile = db.query(DonorProfile).filter(
                    DonorProfile.user_id == user.id
                ).first()
                db.close()
                
                if donor_profile and donor_profile.image_path:
                    # Show donor profile image thumbnail
                    image_url, error_msg = get_s3_url(donor_profile.image_path)
                    if image_url:
                        st.sidebar.image(image_url, width=120, caption="")
                    else:
                        # Image path exists but can't load - show placeholder
                        st.sidebar.markdown(
                            """
                            <div style="width: 120px; height: 90px; background-color: #e0e0e0; 
                                        border-radius: 8px; display: flex; align-items: center; 
                                        justify-content: center; margin-bottom: 10px;">
                                <span style="color: #666; font-size: 11px; text-align: center;">
                                    📷 Image loading...
                                </span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                else:
                    # No image uploaded - show placeholder with message
                    st.sidebar.markdown(
                        """
                        <div style="width: 120px; height: 90px; background-color: #f0f0f0; 
                                    border: 2px dashed #ccc; border-radius: 8px; 
                                    display: flex; align-items: center; justify-content: center; 
                                    margin-bottom: 10px;">
                            <span style="color: #888; font-size: 11px; text-align: center;">
                                📷<br>Add profile pic
                            </span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            except Exception as e:
                # Error loading profile - show simple placeholder
                st.sidebar.markdown(
                    """
                    <div style="width: 120px; height: 90px; background-color: #f0f0f0; 
                                border: 2px dashed #ccc; border-radius: 8px; 
                                display: flex; align-items: center; justify-content: center; 
                                margin-bottom: 10px;">
                        <span style="color: #888; font-size: 11px; text-align: center;">
                            📷<br>Add profile pic
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        
        st.sidebar.markdown(f"**Logged in as:** {user.username}")
        st.sidebar.markdown(f"**User type:** {user_type_emoji} {user_type_display}")
        if user_type != "admin":
            st.sidebar.markdown(f"**Account tier:** {tier_emoji} {account_tier.capitalize()}")
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            logout()
            st.rerun()
        st.sidebar.markdown("---")
    
    # Define available pages based on user type
    if user_type == "admin":
        # Admins only see: Profile Browser and Like Browser
        pages = {
            "📋 Profile Browser": "profilebrowser",
            "❤️ Like Browser": "likebrowser"
        }
        
        # Set default page for admins
        default_page = "profilebrowser"
    elif user_type == "representative":
        # Representatives see: Organization Profile, Premium Profile Browser (if premium)
        pages = {
            "👤 Organization Profile": "profile"
        }
        
        # Add premium pages if user has premium access
        if has_account_tier(required_tier="premium"):
            pages["⭐ Premium Profile Browser"] = "premiumprofilebrowser"
        
        # Set default page for representatives
        default_page = "profile"
    elif user_type == "donor":
        # Donors see: My Donor Profile, Tinder-ish
        pages = {
            "💰 My Donor Profile": "donorprofile",
            "🎴 Tinder-ish": "tinderish"
        }
        
        # Set default page for donors
        default_page = "donorprofile"
    else:
        # Fallback for unknown user types - show nothing useful, force login
        pages = {
            "🔒 Access Denied": "accessdenied"
        }
        default_page = "accessdenied"
    
    # Initialize session state for current page if not set
    if "current_page" not in st.session_state:
        st.session_state.current_page = default_page
    
    # Check if current page is still valid for this user type
    if st.session_state.current_page not in pages.values():
        st.session_state.current_page = default_page
    
    # Use the radio button's key to manage state - this ensures immediate updates
    # If the key exists in session state, use it; otherwise use current_page
    if "page_navigation" not in st.session_state or st.session_state.page_navigation not in pages.keys():
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

