"""
Account browser page for admins to view all user accounts.
Shows all users from app_users table with their details.
"""
import streamlit as st
from helpers.db import get_db, User
from helpers.auth import get_current_user_type


def render_account_browser():
    """
    Render a browser page for viewing all user accounts.
    Only accessible to admin users.
    """
    # Check if user is an admin
    user_type = st.session_state.get("user_type", "")
    if user_type != "admin":
        st.title("🔒 Admin Access Required")
        st.error("❌ This page is only accessible to admin users.")
        return
    
    st.title("👥 Account Browser")
    st.write("View all user accounts and their details")
    
    # Fetch all users from database
    try:
        db = next(get_db())
        users = db.query(User).order_by(User.created_at.desc()).all()
        db.close()
    except Exception as e:
        st.error(f"Error loading users: {str(e)}")
        users = []
    
    if not users:
        st.warning("No users found in the database.")
        return
    
    # Count by status and type
    active_count = sum(1 for u in users if not u.is_deleted)
    deleted_count = sum(1 for u in users if u.is_deleted)
    verified_count = sum(1 for u in users if u.is_verified)
    unverified_count = sum(1 for u in users if not u.is_verified)
    
    rep_count = sum(1 for u in users if u.user_type == "representative")
    donor_count = sum(1 for u in users if u.user_type == "donor")
    admin_count = sum(1 for u in users if u.user_type == "admin")
    
    # Display summary stats
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    with col_stat1:
        st.metric("Total Users", len(users))
    with col_stat2:
        st.metric("Active / Deactivated", f"{active_count} / {deleted_count}")
    with col_stat3:
        st.metric("Verified / Unverified", f"{verified_count} / {unverified_count}")
    
    st.caption(f"👤 {rep_count} Representatives, 💰 {donor_count} Donors, 🔧 {admin_count} Admins")
    
    st.markdown("---")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_term = st.text_input("🔍 Search by username, email, or name", "")
    
    with col2:
        user_type_filter = st.selectbox(
            "Filter by user type",
            options=["All Types", "Representative", "Donor", "Admin"],
            index=0
        )
    
    with col3:
        status_filter = st.selectbox(
            "Filter by status",
            options=["All", "Active Only", "Deactivated Only", "Verified Only", "Unverified Only"],
            index=0
        )
    
    # Apply filters
    filtered_users = users
    
    # User type filter
    if user_type_filter != "All Types":
        type_map = {"Representative": "representative", "Donor": "donor", "Admin": "admin"}
        filtered_users = [u for u in filtered_users if u.user_type == type_map.get(user_type_filter)]
    
    # Status filter
    if status_filter == "Active Only":
        filtered_users = [u for u in filtered_users if not u.is_deleted]
    elif status_filter == "Deactivated Only":
        filtered_users = [u for u in filtered_users if u.is_deleted]
    elif status_filter == "Verified Only":
        filtered_users = [u for u in filtered_users if u.is_verified]
    elif status_filter == "Unverified Only":
        filtered_users = [u for u in filtered_users if not u.is_verified]
    
    # Search filter
    if search_term:
        search_lower = search_term.lower()
        filtered_users = [
            u for u in filtered_users
            if (u.username and search_lower in u.username.lower())
            or (u.email and search_lower in u.email.lower())
            or (u.first_name and search_lower in u.first_name.lower())
            or (u.last_name and search_lower in u.last_name.lower())
            or (u.company and search_lower in u.company.lower())
        ]
    
    st.caption(f"Showing {len(filtered_users)} of {len(users)} users")
    
    if not filtered_users:
        st.warning("No users match your filter criteria.")
        return
    
    # Display users
    for user in filtered_users:
        # Build status indicators
        status_icons = []
        if user.is_deleted:
            status_icons.append("🗑️")
        if not user.is_verified:
            status_icons.append("📧")
        
        # User type emoji
        type_emoji = "🏢" if user.user_type == "representative" else ("💰" if user.user_type == "donor" else "🔧")
        
        # Tier emoji
        tier_emoji = "⭐" if user.account_tier and user.account_tier.lower() in ["premium", "enterprise"] else ""
        
        status_str = " ".join(status_icons)
        title = f"{status_str} {type_emoji} {tier_emoji} {user.username} ({user.email})"
        
        with st.expander(title.strip(), expanded=False):
            # Show status warnings
            if user.is_deleted:
                st.warning("⚠️ This account has been deactivated")
            if not user.is_verified:
                st.info("📧 Email not verified")
            
            # Account info
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Account Information")
                st.write(f"**User ID:** {user.id}")
                st.write(f"**Username:** {user.username}")
                st.write(f"**Email:** {user.email}")
                st.write(f"**User Type:** {type_emoji} {user.user_type.capitalize() if user.user_type else 'N/A'}")
                st.write(f"**Account Tier:** {tier_emoji} {user.account_tier.capitalize() if user.account_tier else 'Free'}")
                st.write(f"**Email Verified:** {'✅ Yes' if user.is_verified else '❌ No'}")
                st.write(f"**Account Status:** {'🗑️ Deactivated' if user.is_deleted else '✅ Active'}")
            
            with col2:
                st.markdown("### Personal Information")
                st.write(f"**First Name:** {user.first_name or 'N/A'}")
                st.write(f"**Last Name:** {user.last_name or 'N/A'}")
                st.write(f"**Company:** {user.company or 'N/A'}")
                st.write(f"**Phone:** {user.phone_number or 'N/A'}")
            
            st.markdown("### Address")
            st.write(f"**Street:** {user.street_address or 'N/A'}")
            col_addr1, col_addr2, col_addr3 = st.columns(3)
            with col_addr1:
                st.write(f"**City:** {user.city or 'N/A'}")
            with col_addr2:
                st.write(f"**State:** {user.state or 'N/A'}")
            with col_addr3:
                st.write(f"**ZIP:** {user.zip_code or 'N/A'}")
            
            st.markdown("### Timestamps")
            col_ts1, col_ts2 = st.columns(2)
            with col_ts1:
                st.write(f"**Created:** {user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else 'N/A'}")
            with col_ts2:
                st.write(f"**Updated:** {user.updated_at.strftime('%Y-%m-%d %H:%M:%S') if user.updated_at else 'N/A'}")
            
            # Stripe info if available
            if user.stripe_customer_id:
                st.markdown("### Payment Info")
                st.write(f"**Stripe Customer ID:** {user.stripe_customer_id}")
            
            st.markdown("---")

