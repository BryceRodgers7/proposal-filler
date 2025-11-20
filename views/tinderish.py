import streamlit as st
from helpers.db import get_db, ProposalSubmission, ProposalAction
from helpers.auth import get_current_user_id


def render_tinderish():
    """
    Render the Tinder-style deck page for reviewing proposals.
    """
    st.title("🎴 Proposal Deck")
    st.write("Review and rate proposals from the database")
    
    # Get current user ID
    user_id = get_current_user_id()
    if user_id is None:
        st.error("You must be logged in to access this page.")
        return
    
    # Initialize session state for deck navigation
    if "deck_index" not in st.session_state:
        st.session_state.deck_index = 0
    
    # Fetch all proposals from database, excluding the current user's profile
    try:
        db = next(get_db())
        proposals = db.query(ProposalSubmission).filter(
            ProposalSubmission.user_id != user_id
        ).order_by(ProposalSubmission.id.desc()).all()
        db.close()
    except Exception as e:
        st.error(f"Error loading proposals: {str(e)}")
        proposals = []
    
    if not proposals:
        st.warning("No proposals found in the database (excluding your own profile). Please wait for other users to add proposals.")
        return
    
    # Ensure index is within bounds
    if st.session_state.deck_index >= len(proposals):
        st.session_state.deck_index = 0
    
    # Get current proposal
    current_proposal = proposals[st.session_state.deck_index]
    
    # Display progress
    st.caption(f"Profile {st.session_state.deck_index + 1} of {len(proposals)}")
    
    # Create a card-style container for the profile
    st.markdown("---")
    
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
    
    # Create a styled box with all content in a single HTML block
    profile_html = f"""
    <div style="background-color: #f8f9fa; border: 1px solid #e0e0e0; border-radius: 10px; padding: 25px; margin: 20px 0;">
        <h3 style="color: #1f77b4; margin-top: 0;">{org_name_escaped}</h3>
        <hr style="border: 1px solid #e0e0e0; margin: 15px 0;">
        <p><strong>🏛️ Legal Designation:</strong><br>{legal_designation}</p>
        <p><strong>💼 What we do:</strong><br>{what_we_do}</p>
        <p><strong>🏆 Biggest Accomplishment:</strong><br>{biggest_accomplishment}</p>
        <p><strong>📍 Location Served:</strong><br>{location_served}</p>
        <p><strong>🌍 Geographical Focus:</strong><br>{geographic_focus}</p>
        <hr style="border: 1px solid #e0e0e0; margin: 15px 0;">
        <p style="font-size: 0.9em; color: #666; text-align: center; margin-bottom: 0;">Database ID: {current_proposal.id}</p>
    </div>
    """
    
    st.markdown(profile_html, unsafe_allow_html=True)
    st.markdown("")
    
    # Like and Pass buttons
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        button_col1, button_col2 = st.columns(2)
        
        with button_col1:
            if st.button("❌ Pass", type="secondary", use_container_width=True):
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
        
        with button_col2:
            if st.button("❤️ Like", type="primary", use_container_width=True):
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
    
    # Add a reset button to go back to the beginning
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Reset Deck", use_container_width=False):
        st.session_state.deck_index = 0
        st.rerun()

