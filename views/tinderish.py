import streamlit as st
from helpers.db import get_db, ProposalSubmission, ProposalAction, DonorProfile
from helpers.auth import get_current_user_id
from helpers.storage import get_s3_url


def calculate_match_score(proposal, donor_profile):
    """
    Calculate a match score between a proposal and a donor's profile.
    Returns a score (higher is better) based on how many preferences match.
    """
    if not donor_profile:
        return 0
    
    score = 0
    
    # Check primary cause areas overlap
    proposal_causes = proposal.primary_cause_area if isinstance(proposal.primary_cause_area, list) else []
    donor_causes = donor_profile.primary_cause_areas if isinstance(donor_profile.primary_cause_areas, list) else []
    
    if proposal_causes and donor_causes:
        # Count how many cause areas overlap
        overlapping_causes = set(proposal_causes) & set(donor_causes)
        score += len(overlapping_causes) * 10  # Weight: 10 points per matching cause area
    
    # Check populations overlap
    proposal_pops = proposal.populations if isinstance(proposal.populations, list) else []
    donor_pops = donor_profile.populations if isinstance(donor_profile.populations, list) else []
    
    if proposal_pops and donor_pops:
        # Count how many populations overlap
        overlapping_pops = set(proposal_pops) & set(donor_pops)
        score += len(overlapping_pops) * 8  # Weight: 8 points per matching population
    
    # Check geographic focus match
    proposal_geo = proposal.geographic_focus or ""
    donor_geo = donor_profile.geographic_focus or ""
    
    if proposal_geo and donor_geo and proposal_geo == donor_geo:
        score += 15  # Weight: 15 points for exact geographic match
    
    # Note: donation_style and organization_characteristics are donor preferences
    # but don't have corresponding fields in ProposalSubmission, so we can't match them yet
    
    return score


def render_tinderish():
    """
    Render the Tinder-style deck page for reviewing proposals.
    For donors, proposals are ordered by match score based on their profile preferences.
    """
    st.title("🎴 Tinder-ish")
    
    # Get current user ID and type
    user_id = get_current_user_id()
    if user_id is None:
        st.error("You must be logged in to access this page.")
        return
    
    user_type = st.session_state.get("user_type", "representative")
    
    # Load donor profile if user is a donor
    donor_profile = None
    if user_type == "donor":
        try:
            db = next(get_db())
            donor_profile = db.query(DonorProfile).filter(
                DonorProfile.user_id == user_id
            ).first()
            db.close()
        except Exception as e:
            st.warning(f"Could not load your donor profile: {str(e)}")
    
    # Display different subtitle based on whether profile exists
    if donor_profile:
        st.write("📊 Organizations are ranked by how well they match your donor preferences")
    else:
        st.write("Review and rate proposals from the database")
        if user_type == "donor":
            st.info("💡 Tip: Complete your donor profile to see organizations ranked by match!")
    
    # Initialize session state for deck navigation
    if "deck_index" not in st.session_state:
        st.session_state.deck_index = 0
    
    # Check if we need to rebuild the deck (first time or if profile changed)
    rebuild_deck = False
    if "deck_proposals" not in st.session_state:
        rebuild_deck = True
    elif "deck_user_id" not in st.session_state or st.session_state.deck_user_id != user_id:
        rebuild_deck = True
    elif "deck_has_profile" not in st.session_state or st.session_state.deck_has_profile != (donor_profile is not None):
        rebuild_deck = True
    
    if rebuild_deck:
        # Fetch all proposals from database, excluding the current user's profile and soft-deleted profiles
        try:
            db = next(get_db())
            proposals = db.query(ProposalSubmission).filter(
                ProposalSubmission.user_id != user_id,
                ProposalSubmission.is_deleted == False  # Exclude soft-deleted profiles
            ).all()
            db.close()
            
            # Filter out incomplete profiles (empty profiles created for image upload)
            # A profile is complete if it has an organization name
            proposals = [p for p in proposals if p.full_organization_name and p.full_organization_name.strip()]
            
        except Exception as e:
            st.error(f"Error loading proposals: {str(e)}")
            proposals = []
        
        if not proposals:
            st.warning("No proposals found in the database (excluding your own profile). Please wait for other users to add proposals.")
            return
        
        # Sort proposals by match score if donor profile exists
        if donor_profile:
            # Calculate match scores and attach them to proposals
            proposals_with_scores = []
            for proposal in proposals:
                score = calculate_match_score(proposal, donor_profile)
                proposals_with_scores.append((proposal, score))
            
            # Sort by score (highest first)
            proposals_with_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Extract just the proposals (but keep scores in a dict for display)
            score_dict = {p.id: score for p, score in proposals_with_scores}
            proposals = [p for p, _ in proposals_with_scores]
        else:
            # No donor profile - use default order (newest first)
            proposals.sort(key=lambda x: x.id, reverse=True)
            score_dict = {}
        
        # Store in session state
        st.session_state.deck_proposals = proposals
        st.session_state.deck_score_dict = score_dict
        st.session_state.deck_user_id = user_id
        st.session_state.deck_has_profile = (donor_profile is not None)
        st.session_state.deck_index = 0  # Reset to beginning when rebuilding
    else:
        # Use cached proposals and scores
        proposals = st.session_state.deck_proposals
        score_dict = st.session_state.deck_score_dict
    
    # Ensure index is within bounds
    if st.session_state.deck_index >= len(proposals):
        st.session_state.deck_index = 0
    
    # Get current proposal
    current_proposal = proposals[st.session_state.deck_index]
    current_score = score_dict.get(current_proposal.id, 0)
    
    # Display progress and match score
    col_left, col_right = st.columns([2, 1])
    with col_left:
        st.caption(f"Profile {st.session_state.deck_index + 1} of {len(proposals)}")
    with col_right:
        if donor_profile:
            # Calculate match percentage (normalize to 0-100%)
            # Max possible score estimate: 5 causes * 10 + 5 pops * 8 + 15 geo = 105
            max_score = 105
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
    
    # Create a card-style container for the profile
    st.markdown("---")
    
    # Three-column layout: Pass button | Profile content | Like button
    col_pass, col_profile, col_like = st.columns([1, 4, 1])
    
    # MIDDLE COLUMN - Profile Content
    with col_profile:
        # Display organization image if available
        if current_proposal.image_path:
            try:
                image_url, error_msg = get_s3_url(current_proposal.image_path)
                if image_url:
                    st.image(image_url, use_column_width=True, caption="")
                else:
                    st.warning(f"📷 Could not load organization image")
                    with st.expander("🔍 Debug - Why image didn't load"):
                        st.error(error_msg)
                        st.code(f"S3 Key: {current_proposal.image_path}\nOrg ID: {current_proposal.id}")
            except Exception as e:
                st.error(f"Exception loading organization image: {str(e)}")
                with st.expander("🔍 Debug - Exception Details"):
                    import traceback
                    st.code(traceback.format_exc())
        
        # Profile card with custom styling
        org_name = current_proposal.full_organization_name or 'Unnamed Organization'
        
        # Prepare additional fields - escape HTML to prevent injection
        import html
        org_name_escaped = html.escape(str(org_name))
        legal_designation = html.escape(str(current_proposal.legal_designation or 'Not specified'))
        what_we_do = html.escape(str(current_proposal.what_we_do_in_one_sentence or 'Not specified'))
        biggest_accomplishment = html.escape(str(current_proposal.biggest_accomplishment or 'Not specified'))
        location_served = html.escape(str(current_proposal.location_served or 'Not specified'))
        geographic_focus = html.escape(str(current_proposal.geographic_focus or 'Not specified'))
        
        # Format cause areas and populations for display
        cause_areas_display = "Not specified"
        if current_proposal.primary_cause_area and isinstance(current_proposal.primary_cause_area, list):
            cause_areas_display = ", ".join(current_proposal.primary_cause_area)
        cause_areas_display = html.escape(cause_areas_display)
        
        populations_display = "Not specified"
        if current_proposal.populations and isinstance(current_proposal.populations, list):
            populations_display = ", ".join(current_proposal.populations)
        populations_display = html.escape(populations_display)
        
        # Create a styled box with all content in a single HTML block
        profile_html = f"""
        <div style="background-color: #f8f9fa; border: 1px solid #e0e0e0; border-radius: 10px; padding: 25px; margin: 20px 0;">
            <h3 style="color: #1f77b4; margin-top: 0;">{org_name_escaped}</h3>
            <hr style="border: 1px solid #e0e0e0; margin: 15px 0;">
            <p><strong>🏛️ Legal Designation:</strong><br>{legal_designation}</p>
            <p><strong>💼 What we do:</strong><br>{what_we_do}</p>
            <p><strong>🏆 Biggest Accomplishment:</strong><br>{biggest_accomplishment}</p>
            <p><strong>🎯 Cause Areas:</strong><br>{cause_areas_display}</p>
            <p><strong>👥 Populations Served:</strong><br>{populations_display}</p>
            <p><strong>📍 Location Served:</strong><br>{location_served}</p>
            <p><strong>🌍 Geographic Focus:</strong><br>{geographic_focus}</p>
            <hr style="border: 1px solid #e0e0e0; margin: 15px 0;">
            <p style="font-size: 0.9em; color: #666; text-align: center; margin-bottom: 0;">Database ID: {current_proposal.id}</p>
        </div>
        """
        
        st.markdown(profile_html, unsafe_allow_html=True)
        
        # Show match details for donors with a profile
        if donor_profile:
            with st.expander("🔍 See why this matches your preferences", expanded=False):
                # Check cause areas overlap
                proposal_causes = current_proposal.primary_cause_area if isinstance(current_proposal.primary_cause_area, list) else []
                donor_causes = donor_profile.primary_cause_areas if isinstance(donor_profile.primary_cause_areas, list) else []
                overlapping_causes = set(proposal_causes) & set(donor_causes) if proposal_causes and donor_causes else set()
                
                # Check populations overlap
                proposal_pops = current_proposal.populations if isinstance(current_proposal.populations, list) else []
                donor_pops = donor_profile.populations if isinstance(donor_profile.populations, list) else []
                overlapping_pops = set(proposal_pops) & set(donor_pops) if proposal_pops and donor_pops else set()
                
                # Check geographic focus
                proposal_geo = current_proposal.geographic_focus or ""
                donor_geo = donor_profile.geographic_focus or ""
                geo_match = proposal_geo and donor_geo and proposal_geo == donor_geo
                
                # Display matches - always show all categories
                if overlapping_causes:
                    st.markdown(f"✅ **Matching Cause Areas:** {', '.join(overlapping_causes)}")
                elif donor_causes and proposal_causes:
                    st.markdown(f"⚪ **Cause Areas:** No overlap with your preferences")
                elif donor_causes:
                    st.markdown(f"⚪ **Cause Areas:** Organization has not specified cause areas")
                elif proposal_causes:
                    st.markdown(f"⚪ **Cause Areas:** You have not set cause area preferences")
                else:
                    st.markdown(f"⚪ **Cause Areas:** No data to compare")
                
                if overlapping_pops:
                    st.markdown(f"✅ **Matching Populations:** {', '.join(overlapping_pops)}")
                elif donor_pops and proposal_pops:
                    st.markdown(f"⚪ **Populations:** No overlap with your preferences")
                elif donor_pops:
                    st.markdown(f"⚪ **Populations:** Organization has not specified populations served")
                elif proposal_pops:
                    st.markdown(f"⚪ **Populations:** You have not set population preferences")
                else:
                    st.markdown(f"⚪ **Populations:** No data to compare")
                
                if geo_match:
                    st.markdown(f"✅ **Geographic Focus:** {proposal_geo} (matches your preference)")
                elif donor_geo and proposal_geo:
                    st.markdown(f"⚪ **Geographic Focus:** {proposal_geo} (you prefer {donor_geo})")
                elif donor_geo:
                    st.markdown(f"⚪ **Geographic Focus:** Organization has not specified ({donor_geo} is your preference)")
                elif proposal_geo:
                    st.markdown(f"⚪ **Geographic Focus:** You have not set a geographic preference ({proposal_geo} is theirs)")
                else:
                    st.markdown(f"⚪ **Geographic Focus:** No data to compare")
    
    # LEFT COLUMN - Pass Button
    with col_pass:
        st.markdown("<br>" * 10, unsafe_allow_html=True)  # Vertical spacing to center button
        if st.button("❌\n\nPass", type="secondary", use_container_width=True, key="pass_button"):
            # Save or update pass action in database
            db = None
            try:
                db = next(get_db())
                # Check if action already exists for this proposal and user
                existing_action = db.query(ProposalAction).filter(
                    ProposalAction.proposal_id == current_proposal.id,
                    ProposalAction.user_id == user_id
                ).first()
                
                if existing_action:
                    # Update existing action
                    existing_action.action_type = "pass"
                else:
                    # Create new action
                    action = ProposalAction(
                        proposal_id=current_proposal.id,
                        user_id=user_id,
                        action_type="pass"
                    )
                    db.add(action)
                db.commit()
            except Exception as e:
                if db:
                    db.rollback()
                st.error(f"Error saving pass: {str(e)}")
                # Continue even if save fails
            finally:
                if db:
                    db.close()
            
            # Move to next profile
            st.session_state.deck_index = (st.session_state.deck_index + 1) % len(proposals)
            st.rerun()
    
    # RIGHT COLUMN - Like Button
    with col_like:
        st.markdown("<br>" * 10, unsafe_allow_html=True)  # Vertical spacing to center button
        if st.button("❤️\n\nLike", type="primary", use_container_width=True, key="like_button"):
            # Save or update like action in database
            db = None
            try:
                db = next(get_db())
                # Check if action already exists for this proposal and user
                existing_action = db.query(ProposalAction).filter(
                    ProposalAction.proposal_id == current_proposal.id,
                    ProposalAction.user_id == user_id
                ).first()
                
                if existing_action:
                    # Update existing action
                    existing_action.action_type = "like"
                else:
                    # Create new action
                    action = ProposalAction(
                        proposal_id=current_proposal.id,
                        user_id=user_id,
                        action_type="like"
                    )
                    db.add(action)
                db.commit()
            except Exception as e:
                if db:
                    db.rollback()
                st.error(f"Error saving like: {str(e)}")
                # Continue even if save fails
            finally:
                if db:
                    db.close()
            
            # Move to next profile
            st.session_state.deck_index = (st.session_state.deck_index + 1) % len(proposals)
            st.rerun()
    
    # Add a reset button to go back to the beginning and rebuild deck
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Reset Deck", use_container_width=False):
        st.session_state.deck_index = 0
        # Clear cached deck to force rebuild with fresh data
        if "deck_proposals" in st.session_state:
            del st.session_state.deck_proposals
        if "deck_score_dict" in st.session_state:
            del st.session_state.deck_score_dict
        if "deck_user_id" in st.session_state:
            del st.session_state.deck_user_id
        if "deck_has_profile" in st.session_state:
            del st.session_state.deck_has_profile
        st.rerun()

