"""
Card Like Browser page for admins.
Allows viewing all card actions (likes and passes) in the database.
"""
import streamlit as st
from sqlalchemy.orm import joinedload
from helpers.db import get_db, CardAction, OrganizationCard, User
from helpers.auth import get_current_user_type


def render_card_like_browser():
    """
    Render a browser page for viewing all card likes and passes.
    Only accessible to admin users. Shows all actions including from/on deactivated accounts.
    """
    # Check if user is an admin
    user_type = get_current_user_type()
    if user_type != "admin":
        st.title("🔒 Admin Access Required")
        st.error("❌ This page is only accessible to admin users.")
        return
    
    st.title("💙 Card Like Browser")
    st.write("View all likes and passes on organization cards from all users (including deactivated)")
    
    # Fetch ALL card actions from database with related data (including soft-deleted)
    try:
        db = next(get_db())
        actions = db.query(CardAction).options(
            joinedload(CardAction.card).joinedload(OrganizationCard.user),
            joinedload(CardAction.user)
        ).order_by(CardAction.created_at.desc()).all()
        db.close()
    except Exception as e:
        st.error(f"Error loading card actions: {str(e)}")
        actions = []
    
    if not actions:
        st.warning("No card actions found in the database. Donors need to swipe on cards first.")
        return
    
    # Display total counts
    likes_count = sum(1 for a in actions if a.action_type == "like")
    passes_count = sum(1 for a in actions if a.action_type == "pass")
    
    # Count actions involving deactivated users/cards
    deactivated_user_actions = sum(1 for a in actions if a.user and a.user.is_deleted)
    deactivated_card_actions = sum(1 for a in actions if a.card and a.card.is_deleted)
    
    st.info(f"Total actions: {len(actions)} (❤️ {likes_count} likes, ❌ {passes_count} passes)")
    if deactivated_user_actions > 0 or deactivated_card_actions > 0:
        st.caption(f"🗑️ {deactivated_user_actions} from deactivated users, {deactivated_card_actions} on deactivated cards")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        action_filter = st.selectbox(
            "Filter by action type",
            options=["All", "Like", "Pass"],
            index=0
        )
    
    with col2:
        # Get unique donor usernames for filter
        try:
            db = next(get_db())
            all_donors = db.query(User).filter(User.user_type == "donor").all()
            db.close()
            donor_options = ["All Donors"] + [f"{'🗑️ ' if donor.is_deleted else ''}{donor.username}" for donor in all_donors]
            selected_donor = st.selectbox(
                "Filter by donor",
                options=donor_options,
                index=0
            )
        except Exception:
            selected_donor = "All Donors"
    
    with col3:
        # Status filter for deactivated
        status_filter = st.selectbox(
            "Filter by status",
            options=["All", "Active Only", "Deactivated Only"],
            index=0,
            help="Filter by whether the donor, card, or organization is deactivated"
        )
    
    # Filter actions based on selections
    filtered_actions = actions
    
    if action_filter != "All":
        action_type_filter = action_filter.lower()
        filtered_actions = [a for a in filtered_actions if a.action_type == action_type_filter]
    
    if selected_donor != "All Donors":
        # Remove the deactivated emoji if present for comparison
        clean_username = selected_donor.replace("🗑️ ", "")
        filtered_actions = [a for a in filtered_actions if a.user and a.user.username == clean_username]
    
    if status_filter == "Active Only":
        filtered_actions = [a for a in filtered_actions 
                          if a.user and not a.user.is_deleted 
                          and a.card and not a.card.is_deleted
                          and a.card.user and not a.card.user.is_deleted]
    elif status_filter == "Deactivated Only":
        filtered_actions = [a for a in filtered_actions 
                          if (a.user and a.user.is_deleted) 
                          or (a.card and a.card.is_deleted)
                          or (a.card and a.card.user and a.card.user.is_deleted)]
    
    if not filtered_actions:
        st.warning("No card actions match your filter criteria.")
        return
    
    st.caption(f"Showing {len(filtered_actions)} of {len(actions)} actions")
    
    # Display actions in a table-like format
    for idx, action in enumerate(filtered_actions, 1):
        # Get card and user info from relationships
        card = action.card
        donor = action.user
        
        if not card or not donor:
            continue
        
        # Get organization info
        org_user = card.user if card else None
        org_name = org_user.username if org_user else "Unknown Organization"
        
        # Determine emoji and color based on action type
        action_emoji = "❤️" if action.action_type == "like" else "❌"
        
        # Add deactivation indicators
        donor_status = "🗑️ " if donor.is_deleted else ""
        card_status = "🗑️ " if card.is_deleted else ""
        org_status = "🗑️ " if org_user and org_user.is_deleted else ""
        
        # Create expandable section for each action
        expander_title = f"{action_emoji} {donor_status}{donor.username} - {action.action_type.upper()} on {card_status}'{card.title}' by {org_status}{org_name}"
        
        with st.expander(expander_title, expanded=False):
            # Show deactivation warnings
            if donor.is_deleted:
                st.warning(f"⚠️ Donor '{donor.username}' has deactivated their account")
            if card.is_deleted:
                st.warning(f"⚠️ Card '{card.title}' has been deactivated")
            if org_user and org_user.is_deleted:
                st.warning(f"⚠️ Organization '{org_name}' has been deactivated")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Action Details")
                st.write(f"**Action Type:** {action_emoji} {action.action_type.upper()}")
                st.write(f"**Action ID:** {action.id}")
                st.write(f"**Action Date:** {action.created_at.strftime('%Y-%m-%d %H:%M:%S') if action.created_at else 'N/A'}")
                
                st.markdown("### Donor Details")
                st.write(f"**Donor:** {donor.username} {'(🗑️ Deactivated)' if donor.is_deleted else ''}")
                st.write(f"**Donor Email:** {donor.email}")
                st.write(f"**Donor ID:** {donor.id}")
            
            with col2:
                st.markdown("### Card Details")
                st.write(f"**Card Title:** {card.title} {'(🗑️ Deactivated)' if card.is_deleted else ''}")
                st.write(f"**Card ID:** {card.id}")
                
                st.markdown("### Organization Details")
                st.write(f"**Organization:** {org_name} {'(🗑️ Deactivated)' if org_user and org_user.is_deleted else ''}")
                st.write(f"**Org User ID:** {card.user_id}")
                if org_user:
                    st.write(f"**Org Email:** {org_user.email}")
            
            # Show card content
            st.markdown("### Card Content")
            st.write(f"**Title:** {card.title}")
            if card.subtitle:
                st.write(f"**Subtitle:**")
                st.info(card.subtitle)
            else:
                st.write(f"**Subtitle:** No subtitle")
            
            # Show image path if available
            if card.image_path:
                st.write(f"**Image Path:** {card.image_path}")
            
            st.markdown("---")

