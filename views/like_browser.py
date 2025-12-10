import streamlit as st
from sqlalchemy.orm import joinedload
from helpers.db import get_db, ProposalAction, ProposalSubmission, User
from helpers.auth import get_current_user_type


def render_like_browser():
    """
    Render a browser page for viewing all likes and passes (proposal actions).
    Only accessible to admin users. Shows all actions including from/on deactivated profiles.
    """
    # Check if user is an admin
    user_type = st.session_state.get("user_type", "")
    if user_type != "admin":
        st.title("🔒 Admin Access Required")
        st.error("❌ This page is only accessible to admin users.")
        return
    
    st.title("❤️ Like Browser")
    st.write("View all likes and passes from all users (including deactivated)")
    
    # Fetch ALL actions from database with related data (including soft-deleted)
    try:
        db = next(get_db())
        # Query actions with eager loading of relationships
        actions = db.query(ProposalAction).options(
            joinedload(ProposalAction.proposal),
            joinedload(ProposalAction.user)
        ).order_by(ProposalAction.created_at.desc()).all()
        db.close()
    except Exception as e:
        st.error(f"Error loading actions: {str(e)}")
        actions = []
    
    if not actions:
        st.warning("No likes or passes found in the database. Users need to interact with proposals first.")
        return
    
    # Display total counts
    likes_count = sum(1 for a in actions if a.action_type == "like")
    passes_count = sum(1 for a in actions if a.action_type == "pass")
    
    # Count actions involving deactivated users/profiles
    deactivated_user_actions = sum(1 for a in actions if a.user and a.user.is_deleted)
    deactivated_profile_actions = sum(1 for a in actions if a.proposal and a.proposal.is_deleted)
    
    st.info(f"Total actions: {len(actions)} (❤️ {likes_count} likes, ❌ {passes_count} passes)")
    if deactivated_user_actions > 0 or deactivated_profile_actions > 0:
        st.caption(f"🗑️ {deactivated_user_actions} from deactivated users, {deactivated_profile_actions} on deactivated profiles")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        action_filter = st.selectbox(
            "Filter by action type",
            options=["All", "Like", "Pass"],
            index=0
        )
    
    with col2:
        # Get unique usernames for filter
        try:
            db = next(get_db())
            all_users = db.query(User).all()
            db.close()
            user_options = ["All Users"] + [f"{'🗑️ ' if user.is_deleted else ''}{user.username}" for user in all_users]
            selected_user = st.selectbox(
                "Filter by user",
                options=user_options,
                index=0
            )
        except Exception:
            selected_user = "All Users"
    
    with col3:
        # Status filter for deactivated
        status_filter = st.selectbox(
            "Filter by status",
            options=["All", "Active Only", "Deactivated Only"],
            index=0,
            help="Filter by whether the user or organization is deactivated"
        )
    
    # Filter actions based on selections
    filtered_actions = actions
    
    if action_filter != "All":
        action_type_filter = action_filter.lower()
        filtered_actions = [a for a in filtered_actions if a.action_type == action_type_filter]
    
    if selected_user != "All Users":
        # Remove the deactivated emoji if present for comparison
        clean_username = selected_user.replace("🗑️ ", "")
        filtered_actions = [a for a in filtered_actions if a.user and a.user.username == clean_username]
    
    if status_filter == "Active Only":
        filtered_actions = [a for a in filtered_actions 
                          if a.user and not a.user.is_deleted 
                          and a.proposal and not a.proposal.is_deleted]
    elif status_filter == "Deactivated Only":
        filtered_actions = [a for a in filtered_actions 
                          if (a.user and a.user.is_deleted) or (a.proposal and a.proposal.is_deleted)]
    
    if not filtered_actions:
        st.warning("No actions match your filter criteria.")
        return
    
    st.caption(f"Showing {len(filtered_actions)} of {len(actions)} actions")
    
    # Display actions in a table-like format
    for idx, action in enumerate(filtered_actions, 1):
        # Get proposal and user info from relationships
        proposal = action.proposal
        user = action.user
        
        if not proposal or not user:
            continue
        
        # Determine emoji and color based on action type
        action_emoji = "❤️" if action.action_type == "like" else "❌"
        
        # Add deactivation indicators
        user_status = "🗑️" if user.is_deleted else ""
        proposal_status = "🗑️" if proposal.is_deleted else ""
        
        # Create expandable section for each action
        expander_title = f"{action_emoji} {user_status}{user.username} - {action.action_type.upper()} on {proposal_status}'{proposal.full_organization_name or 'Unnamed Organization'}'"
        
        with st.expander(expander_title, expanded=False):
            # Show deactivation warnings
            if user.is_deleted:
                st.warning(f"⚠️ User '{user.username}' has deactivated their account")
            if proposal.is_deleted:
                st.warning(f"⚠️ Organization '{proposal.full_organization_name}' has been deactivated")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Action Details")
                st.write(f"**Action Type:** {action_emoji} {action.action_type.upper()}")
                st.write(f"**User:** {user.username} {'(🗑️ Deactivated)' if user.is_deleted else ''}")
                st.write(f"**User Email:** {user.email}")
                st.write(f"**User Type:** {user.user_type}")
                st.write(f"**Action Date:** {action.created_at.strftime('%Y-%m-%d %H:%M:%S') if action.created_at else 'N/A'}")
            
            with col2:
                st.markdown("### Proposal Details")
                st.write(f"**Organization:** {proposal.full_organization_name or 'N/A'} {'(🗑️ Deactivated)' if proposal.is_deleted else ''}")
                st.write(f"**Proposal ID:** {proposal.id}")
                st.write(f"**EIN:** {proposal.ein or 'N/A'}")
                st.write(f"**Location:** {proposal.location_served or 'N/A'}")
            
            # Show mission statement if available
            if proposal.mission_statement:
                st.markdown("### Mission Statement")
                st.info(proposal.mission_statement)
            
            # Show cause areas and populations
            col3, col4 = st.columns(2)
            
            with col3:
                st.markdown("### Primary Cause Area(s)")
                if proposal.primary_cause_area:
                    if isinstance(proposal.primary_cause_area, list):
                        for area in proposal.primary_cause_area:
                            st.write(f"• {area}")
                    else:
                        st.write(str(proposal.primary_cause_area))
                else:
                    st.write("N/A")
            
            with col4:
                st.markdown("### Population(s)")
                if proposal.populations:
                    if isinstance(proposal.populations, list):
                        for pop in proposal.populations:
                            st.write(f"• {pop}")
                    else:
                        st.write(str(proposal.populations))
                else:
                    st.write("N/A")
            
            st.markdown("---")
