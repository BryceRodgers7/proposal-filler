"""
Kindr Swipe page for donors.
A Tinder-style interface for swiping through organization cards with preference-based matching.
"""
import streamlit as st
from helpers.db import get_db, OrganizationCard, CardAction, DonorProfile, ProposalSubmission, User
from helpers.auth import get_current_user_id, get_current_user_type
from helpers.storage import get_s3_url
from views.tinderish import calculate_match_score


def render_kindr_swipe():
    """
    Render the Kindr Swipe page for donors to swipe through organization cards.
    Cards are sorted by match score based on donor preferences.
    """
    st.title("💙 Kindr Swipe")
    
    # Check if user is a donor
    user_type = get_current_user_type()
    if user_type != "donor":
        st.error("❌ This page is only accessible to donor users.")
        return
    
    user_id = get_current_user_id()
    if user_id is None:
        st.error("You must be logged in to access this page.")
        return
    
    # Load donor profile
    donor_profile = None
    try:
        db = next(get_db())
        donor_profile = db.query(DonorProfile).filter(
            DonorProfile.user_id == user_id
        ).first()
        db.close()
    except Exception as e:
        st.warning(f"Could not load your donor profile: {str(e)}")
    
    # Display subtitle based on whether profile exists
    if donor_profile:
        st.write("📊 Cards are ranked by how well organizations match your preferences")
    else:
        st.write("Discover organizations through their highlight cards")
        st.info("💡 Tip: Complete your donor profile to see cards ranked by match!")
    
    # Initialize session state for deck navigation
    if "card_deck_index" not in st.session_state:
        st.session_state.card_deck_index = 0
    
    # Check if we need to rebuild the deck
    rebuild_deck = False
    if "card_deck" not in st.session_state:
        rebuild_deck = True
    elif "card_deck_user_id" not in st.session_state or st.session_state.card_deck_user_id != user_id:
        rebuild_deck = True
    elif "card_deck_has_profile" not in st.session_state or st.session_state.card_deck_has_profile != (donor_profile is not None):
        rebuild_deck = True
    
    if rebuild_deck:
        # Build the card deck
        try:
            db = next(get_db())
            
            # Get all organizations with proposals (excluding current user and soft-deleted)
            organizations = db.query(ProposalSubmission).filter(
                ProposalSubmission.user_id != user_id,
                ProposalSubmission.is_deleted == False,
                ProposalSubmission.full_organization_name != None,
                ProposalSubmission.full_organization_name != ""
            ).all()
            
            if not organizations:
                db.close()
                st.warning("No organizations found. Please check back later!")
                return
            
            # Calculate match scores and sort organizations
            if donor_profile:
                orgs_with_scores = []
                for org in organizations:
                    score = calculate_match_score(org, donor_profile)
                    orgs_with_scores.append((org, score))
                
                # Sort by score (highest first)
                orgs_with_scores.sort(key=lambda x: x[1], reverse=True)
                sorted_orgs = [org for org, score in orgs_with_scores]
                score_dict = {org.user_id: score for org, score in orgs_with_scores}
            else:
                # No profile - use default order (newest first)
                sorted_orgs = sorted(organizations, key=lambda x: x.id, reverse=True)
                score_dict = {}
            
            # Build card deck: for each org, get all cards (up to 3) in sequence
            card_deck = []
            for org in sorted_orgs:
                org_cards = db.query(OrganizationCard).filter(
                    OrganizationCard.user_id == org.user_id,
                    OrganizationCard.is_deleted == False
                ).order_by(OrganizationCard.created_at).limit(3).all()
                
                # Add each card with associated org info
                for card in org_cards:
                    card_deck.append({
                        "card": card,
                        "org": org,
                        "org_user": db.query(User).filter(User.id == org.user_id).first()
                    })
            
            db.close()
            
            if not card_deck:
                st.warning("No cards found. Organizations need to create cards first!")
                return
            
            # Store in session state
            st.session_state.card_deck = card_deck
            st.session_state.card_deck_score_dict = score_dict
            st.session_state.card_deck_user_id = user_id
            st.session_state.card_deck_has_profile = (donor_profile is not None)
            st.session_state.card_deck_index = 0  # Reset to beginning
            
        except Exception as e:
            st.error(f"Error building card deck: {str(e)}")
            return
    else:
        # Use cached deck
        card_deck = st.session_state.card_deck
        score_dict = st.session_state.card_deck_score_dict
    
    # Ensure index is within bounds
    if st.session_state.card_deck_index >= len(card_deck):
        st.session_state.card_deck_index = 0
    
    # Get current card
    current_item = card_deck[st.session_state.card_deck_index]
    current_card = current_item["card"]
    current_org = current_item["org"]
    current_org_user = current_item["org_user"]
    
    # Get match score for this organization
    current_score = score_dict.get(current_org.user_id, 0) if score_dict else 0
    
    # Display progress and match score
    col_left, col_right = st.columns([2, 1])
    with col_left:
        st.caption(f"Card {st.session_state.card_deck_index + 1} of {len(card_deck)}")
    with col_right:
        if donor_profile:
            # Calculate match percentage
            max_score = 105  # Same as tinderish
            match_percent = min(100, int((current_score / max_score) * 100))
            
            # Color code the match percentage
            if match_percent >= 70:
                color = "#28a745"  # Green
                emoji = "🔥"
            elif match_percent >= 40:
                color = "#ffc107"  # Yellow
                emoji = "👍"
            elif match_percent > 0:
                color = "#6c757d"  # Gray
                emoji = "📊"
            else:
                color = "#dc3545"  # Red
                emoji = "⚪"
            
            st.markdown(f"<p style='text-align: right; margin: 0;'>{emoji} <span style='color: {color}; font-weight: bold;'>{match_percent}% Match</span></p>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Three-column layout: Pass button | Card content | Like button
    col_pass, col_card, col_like = st.columns([1, 4, 1])
    
    # MIDDLE COLUMN - Card Content
    with col_card:
        # Display card image if available
        if current_card.image_path:
            try:
                image_url, error_msg = get_s3_url(current_card.image_path)
                if image_url:
                    st.image(image_url, use_column_width=True, caption="")
                else:
                    st.warning(f"📷 Could not load card image")
            except Exception as e:
                st.error(f"Error loading card image: {str(e)}")
        
        # Card content styled box
        import html
        card_title = html.escape(current_card.title)
        card_subtitle = html.escape(current_card.subtitle or "")
        org_name = html.escape(current_org.full_organization_name or "Unknown Organization")
        
        card_html = f"""
        <div style="background-color: #f8f9fa; border: 1px solid #e0e0e0; border-radius: 10px; padding: 25px; margin: 20px 0;">
            <h2 style="color: #1f77b4; margin-top: 0;">{card_title}</h2>
            <hr style="border: 1px solid #e0e0e0; margin: 15px 0;">
            <p style="font-size: 1.1em; color: #333; line-height: 1.6;">{card_subtitle}</p>
            <hr style="border: 1px solid #e0e0e0; margin: 15px 0;">
            <p style="font-size: 0.95em; color: #666; margin-bottom: 0;">
                <strong>Organization:</strong> {org_name}
            </p>
        </div>
        """
        
        st.markdown(card_html, unsafe_allow_html=True)
        
        # Show match details for donors with a profile
        if donor_profile:
            with st.expander("🔍 See why this matches your preferences", expanded=False):
                # Check cause areas overlap
                proposal_causes = current_org.primary_cause_area if isinstance(current_org.primary_cause_area, list) else []
                donor_causes = donor_profile.primary_cause_areas if isinstance(donor_profile.primary_cause_areas, list) else []
                overlapping_causes = set(proposal_causes) & set(donor_causes) if proposal_causes and donor_causes else set()
                
                # Check populations overlap
                proposal_pops = current_org.populations if isinstance(current_org.populations, list) else []
                donor_pops = donor_profile.populations if isinstance(donor_profile.populations, list) else []
                overlapping_pops = set(proposal_pops) & set(donor_pops) if proposal_pops and donor_pops else set()
                
                # Check geographic focus
                proposal_geo = current_org.geographic_focus or ""
                donor_geo = donor_profile.geographic_focus or ""
                geo_match = proposal_geo and donor_geo and proposal_geo == donor_geo
                
                # Display matches
                if overlapping_causes:
                    st.markdown(f"✅ **Matching Cause Areas:** {', '.join(overlapping_causes)}")
                elif donor_causes and proposal_causes:
                    st.markdown(f"⚪ **Cause Areas:** No overlap with your preferences")
                
                if overlapping_pops:
                    st.markdown(f"✅ **Matching Populations:** {', '.join(overlapping_pops)}")
                elif donor_pops and proposal_pops:
                    st.markdown(f"⚪ **Populations:** No overlap with your preferences")
                
                if geo_match:
                    st.markdown(f"✅ **Geographic Focus:** {proposal_geo} (matches your preference)")
                elif donor_geo and proposal_geo:
                    st.markdown(f"⚪ **Geographic Focus:** {proposal_geo} (you prefer {donor_geo})")
    
    # LEFT COLUMN - Pass Button
    with col_pass:
        st.markdown("<br>" * 10, unsafe_allow_html=True)  # Vertical spacing
        if st.button("❌\n\nPass", type="secondary", use_container_width=True, key="pass_card_button"):
            # Save pass action in database
            db = None
            try:
                db = next(get_db())
                # Check if action already exists
                existing_action = db.query(CardAction).filter(
                    CardAction.card_id == current_card.id,
                    CardAction.user_id == user_id
                ).first()
                
                if existing_action:
                    # Update existing action
                    existing_action.action_type = "pass"
                else:
                    # Create new action
                    action = CardAction(
                        card_id=current_card.id,
                        user_id=user_id,
                        action_type="pass"
                    )
                    db.add(action)
                db.commit()
            except Exception as e:
                if db:
                    db.rollback()
                st.error(f"Error saving pass: {str(e)}")
            finally:
                if db:
                    db.close()
            
            # Move to next card
            st.session_state.card_deck_index = (st.session_state.card_deck_index + 1) % len(card_deck)
            st.rerun()
    
    # RIGHT COLUMN - Like Button
    with col_like:
        st.markdown("<br>" * 10, unsafe_allow_html=True)  # Vertical spacing
        if st.button("❤️\n\nLike", type="primary", use_container_width=True, key="like_card_button"):
            # Save like action in database
            db = None
            try:
                db = next(get_db())
                # Check if action already exists
                existing_action = db.query(CardAction).filter(
                    CardAction.card_id == current_card.id,
                    CardAction.user_id == user_id
                ).first()
                
                if existing_action:
                    # Update existing action
                    existing_action.action_type = "like"
                else:
                    # Create new action
                    action = CardAction(
                        card_id=current_card.id,
                        user_id=user_id,
                        action_type="like"
                    )
                    db.add(action)
                db.commit()
            except Exception as e:
                if db:
                    db.rollback()
                st.error(f"Error saving like: {str(e)}")
            finally:
                if db:
                    db.close()
            
            # Move to next card
            st.session_state.card_deck_index = (st.session_state.card_deck_index + 1) % len(card_deck)
            st.rerun()
    
    # Add a reset button
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Reset Deck", use_container_width=False):
        st.session_state.card_deck_index = 0
        # Clear cached deck to force rebuild
        if "card_deck" in st.session_state:
            del st.session_state.card_deck
        if "card_deck_score_dict" in st.session_state:
            del st.session_state.card_deck_score_dict
        if "card_deck_user_id" in st.session_state:
            del st.session_state.card_deck_user_id
        if "card_deck_has_profile" in st.session_state:
            del st.session_state.card_deck_has_profile
        st.rerun()

