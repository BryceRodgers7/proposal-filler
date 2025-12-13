"""
Card Browser page for admins.
Allows viewing all organization cards in the database.
"""
import streamlit as st
from sqlalchemy.orm import joinedload
from helpers.db import get_db, OrganizationCard, User
from helpers.auth import get_current_user_type
from helpers.storage import get_s3_url


def render_card_browser():
    """
    Render a read-only browser page for viewing all organization cards.
    Only accessible to admin users. Shows all cards including deactivated ones.
    """
    # Check if user is an admin
    user_type = get_current_user_type()
    if user_type != "admin":
        st.title("🔒 Admin Access Required")
        st.error("❌ This page is only accessible to admin users.")
        return
    
    st.title("🎴 Card Browser")
    st.write("Browse all organization cards in the database (read-only)")
    
    # Fetch ALL cards from database (including soft-deleted for admin view)
    try:
        db = next(get_db())
        cards = db.query(OrganizationCard).options(
            joinedload(OrganizationCard.user)
        ).order_by(OrganizationCard.created_at.desc()).all()
        db.close()
    except Exception as e:
        st.error(f"Error loading cards: {str(e)}")
        cards = []
    
    if not cards:
        st.warning("No cards found in the database. Organizations need to create cards first.")
        return
    
    # Count active vs deactivated
    active_count = sum(1 for c in cards if not c.is_deleted)
    deleted_count = sum(1 for c in cards if c.is_deleted)
    st.info(f"Total cards: {len(cards)} (✅ {active_count} active, 🗑️ {deleted_count} deactivated)")
    
    # Filter options
    col1, col2 = st.columns(2)
    
    with col1:
        # Search functionality
        search_term = st.text_input("🔍 Search by organization name or card title", "")
    
    with col2:
        # Status filter
        status_filter = st.selectbox(
            "Filter by status",
            options=["All", "Active Only", "Deactivated Only"],
            index=0
        )
    
    # Filter cards based on status
    filtered_cards = cards
    if status_filter == "Active Only":
        filtered_cards = [c for c in filtered_cards if not c.is_deleted]
    elif status_filter == "Deactivated Only":
        filtered_cards = [c for c in filtered_cards if c.is_deleted]
    
    # Filter cards based on search
    if search_term:
        search_lower = search_term.lower()
        filtered_cards = [
            c for c in filtered_cards
            if (c.title and search_lower in c.title.lower())
            or (c.user and c.user.username and search_lower in c.user.username.lower())
        ]
    
    st.caption(f"Showing {len(filtered_cards)} of {len(cards)} cards")
    
    if not filtered_cards:
        st.warning("No cards match your filter criteria.")
        return
    
    # Display cards in expandable sections
    for idx, card in enumerate(filtered_cards, 1):
        # Add status indicator to title
        status_indicator = "🗑️ [DEACTIVATED] " if card.is_deleted else ""
        user_status = "🗑️ " if card.user and card.user.is_deleted else ""
        
        # Get organization name
        org_name = "Unknown Organization"
        if card.user:
            org_name = card.user.username
        
        with st.expander(
            f"{status_indicator}{user_status}Card #{card.id} - {card.title} (by {org_name})",
            expanded=False
        ):
            # Show deactivation warnings
            if card.is_deleted:
                st.warning("⚠️ This card has been deactivated")
            if card.user and card.user.is_deleted:
                st.warning(f"⚠️ The organization '{org_name}' has been deactivated")
            
            # Display card image and content
            col_img, col_content = st.columns([1, 2])
            
            with col_img:
                if card.image_path:
                    try:
                        image_url, error_msg = get_s3_url(card.image_path)
                        if image_url:
                            st.image(image_url, use_column_width=True, caption="Card Image")
                        else:
                            st.warning("📷 Image not available")
                            st.caption(f"Error: {error_msg}")
                    except Exception as e:
                        st.warning("📷 Image not available")
                        st.caption(f"Error: {str(e)}")
                else:
                    st.markdown(
                        """
                        <div style="width: 100%; height: 150px; background-color: #f0f0f0; 
                                    border: 2px dashed #ccc; border-radius: 8px; 
                                    display: flex; align-items: center; justify-content: center;">
                            <span style="color: #888;">No image</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            
            with col_content:
                st.markdown("### Card Details")
                st.write(f"**Card ID:** {card.id}")
                st.write(f"**Organization:** {org_name}")
                st.write(f"**User ID:** {card.user_id}")
                st.write(f"**Status:** {'🗑️ Deactivated' if card.is_deleted else '✅ Active'}")
                st.write(f"**Created:** {card.created_at.strftime('%Y-%m-%d %H:%M:%S') if card.created_at else 'N/A'}")
                st.write(f"**Updated:** {card.updated_at.strftime('%Y-%m-%d %H:%M:%S') if card.updated_at else 'N/A'}")
            
            # Full-width content
            st.markdown("### Card Content")
            st.write(f"**Title:**")
            st.info(card.title)
            
            st.write(f"**Subtitle:**")
            if card.subtitle:
                st.info(card.subtitle)
            else:
                st.caption("No subtitle")
            
            # Show image path for debugging
            if card.image_path:
                st.markdown("### Technical Details")
                st.code(f"Image Path (S3 Key): {card.image_path}")
            
            st.markdown("---")

