"""
Card Creator page for organization representatives.
Allows creating, editing, and managing up to 3 organization cards with AI generation.
"""
import streamlit as st
from helpers.db import get_db, OrganizationCard, ProposalSubmission, ProposalFile
from helpers.auth import get_current_user_id, get_current_user_type
from helpers.storage import get_s3_url, process_image, upload_file_to_s3
from helpers.openai_client import generate_organization_card


def render_card_creator():
    """
    Render the card creator page for organization representatives.
    Allows creating up to 3 cards with AI generation support.
    """
    st.title("🎴 Card Creator")
    st.write("Create and manage your organization's cards for the Kindr Swipe feature")
    
    # Check if user is a representative
    user_type = get_current_user_type()
    if user_type != "representative":
        st.error("❌ This page is only accessible to organization representatives.")
        return
    
    user_id = get_current_user_id()
    if user_id is None:
        st.error("You must be logged in to access this page.")
        return
    
    # Clear AI-generated content if it belongs to a different user session
    # This prevents pre-populated forms when switching between users
    if "ai_generated_user_id" in st.session_state:
        if st.session_state.ai_generated_user_id != user_id:
            # Different user - clear the AI-generated content
            if "ai_generated_title" in st.session_state:
                del st.session_state.ai_generated_title
            if "ai_generated_subtitle" in st.session_state:
                del st.session_state.ai_generated_subtitle
            del st.session_state.ai_generated_user_id
    
    # Load existing cards and available proposals
    db = None
    try:
        db = next(get_db())
        
        # Load proposal files (new system)
        proposal_files = db.query(ProposalFile).filter(
            ProposalFile.user_id == user_id,
            ProposalFile.is_deleted == False
        ).order_by(ProposalFile.created_at.desc()).all()

        has_proposals = len(proposal_files) > 0
        
        # Load existing cards
        existing_cards = db.query(OrganizationCard).filter(
            OrganizationCard.user_id == user_id,
            OrganizationCard.is_deleted == False
        ).order_by(OrganizationCard.created_at).all()
        
        card_count = len(existing_cards)
        
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        if db:
            db.close()
        return
    finally:
        if db:
            db.close()
    
    # Display card limit info
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(f"📊 You have created **{card_count} of 3** cards")
    with col2:
        if not has_proposals:
            st.warning("⚠️ Upload a proposal to enable AI generation")
    
    # Show existing cards
    if existing_cards:
        st.markdown("---")
        st.subheader("Your Cards")
        
        for idx, card in enumerate(existing_cards, 1):
            with st.expander(f"Card #{idx}: {card.title}", expanded=False):
                # Display card preview
                col_img, col_content = st.columns([1, 2])
                
                with col_img:
                    if card.image_path:
                        try:
                            image_url, error_msg = get_s3_url(card.image_path)
                            if image_url:
                                st.image(image_url, use_column_width=True)
                            else:
                                st.warning("📷 Image not available")
                        except Exception:
                            st.warning("📷 Image not available")
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
                    st.markdown(f"**Title:** {card.title}")
                    st.markdown(f"**Subtitle:** {card.subtitle or 'No subtitle'}")
                    st.caption(f"Created: {card.created_at.strftime('%Y-%m-%d %H:%M')}")
                
                # Edit and delete buttons
                col_edit, col_delete = st.columns(2)
                
                with col_edit:
                    if st.button(f"✏️ Edit Card #{idx}", key=f"edit_{card.id}", use_container_width=True):
                        st.session_state[f"editing_card_{card.id}"] = True
                        st.rerun()
                
                with col_delete:
                    if st.button(f"🗑️ Delete Card #{idx}", key=f"delete_{card.id}", type="secondary", use_container_width=True):
                        # Soft delete the card
                        try:
                            db = next(get_db())
                            card_to_delete = db.query(OrganizationCard).filter(
                                OrganizationCard.id == card.id
                            ).first()
                            if card_to_delete:
                                card_to_delete.is_deleted = True
                                db.commit()
                                st.success(f"Card #{idx} deleted successfully!")
                                st.rerun()
                        except Exception as e:
                            if db:
                                db.rollback()
                            st.error(f"Error deleting card: {str(e)}")
                        finally:
                            if db:
                                db.close()
                
                # Show edit form if editing
                if st.session_state.get(f"editing_card_{card.id}", False):
                    st.markdown("### Edit Card")
                    with st.form(key=f"edit_form_{card.id}"):
                        edit_title = st.text_input("Title*", value=card.title, max_chars=100)
                        edit_subtitle = st.text_area("Subtitle", value=card.subtitle or "", max_chars=300)
                        
                        proposal_options = {}
                        for pf in proposal_files:
                            if pf.extracted_text:  # Only show proposals with extracted text
                                label = f"{pf.display_name} (uploaded {pf.created_at.strftime('%Y-%m-%d')})"
                                proposal_options[label] = ("file", pf.id)

                        if proposal_options:
                            selected_proposal_label = st.selectbox(
                                "Select proposal to use for AI generation",
                                options=list(proposal_options.keys()),
                                key=f"card_creator_proposal_selector_edit_{card.id}"
                            )
                            
                            selected_proposal_type, selected_proposal_id = proposal_options[selected_proposal_label]
                        else:
                            st.info("💡 No proposals uploaded yet. Visit the **Proposal Manager** page to upload proposal files.")
                            
                        edit_image = st.file_uploader(
                            "Upload new image (optional)", 
                            type=["jpg", "jpeg", "png"],
                            key=f"edit_image_{card.id}"
                        )
                        
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            save_button = st.form_submit_button("💾 Save Changes", use_container_width=True)
                        with col_cancel:
                            cancel_button = st.form_submit_button("❌ Cancel", use_container_width=True)
                        
                        if save_button:
                            if not edit_title or not edit_title.strip():
                                st.error("Title is required!")
                            else:
                                try:
                                    db = next(get_db())
                                    card_to_edit = db.query(OrganizationCard).filter(
                                        OrganizationCard.id == card.id
                                    ).first()
                                    
                                    if card_to_edit:
                                        card_to_edit.title = edit_title.strip()
                                        card_to_edit.subtitle = edit_subtitle.strip() if edit_subtitle else None
                                        
                                        # Handle image upload
                                        if edit_image:
                                            processed_image, content_type = process_image(edit_image)
                                            if processed_image:
                                                s3_key = f"card_images/{user_id}_{card.id}.jpg"
                                                result = upload_file_to_s3(processed_image, s3_key, content_type)
                                                if result:
                                                    card_to_edit.image_path = result
                                                else:
                                                    st.warning("Failed to upload image, but card will be saved")
                                        
                                        db.commit()
                                        st.success("Card updated successfully!")
                                        del st.session_state[f"editing_card_{card.id}"]
                                        st.rerun()
                                except Exception as e:
                                    if db:
                                        db.rollback()
                                    st.error(f"Error updating card: {str(e)}")
                                finally:
                                    if db:
                                        db.close()
                        
                        if cancel_button:
                            del st.session_state[f"editing_card_{card.id}"]
                            st.rerun()
    
    # Add new card section
    st.markdown("---")
    
    if card_count >= 3:
        st.warning("⚠️ You have reached the maximum of 3 cards. Delete a card to create a new one.")
    else:
        st.subheader("Create New Card")
        
        # AI Generation section
        if has_proposals:
            # Show proposal selector
            st.markdown("#### 🤖 AI Card Generation")
            
            # Build proposal options
            proposal_options = {}
            
            # Add new proposal files
            for pf in proposal_files:
                if pf.extracted_text:  # Only show proposals with extracted text
                    label = f"{pf.display_name} (uploaded {pf.created_at.strftime('%Y-%m-%d')})"
                    proposal_options[label] = ("file", pf.id)
            
            if proposal_options:
                selected_proposal_label = st.selectbox(
                    "Select proposal to use for AI generation",
                    options=list(proposal_options.keys()),
                    key="card_creator_proposal_selector"
                )
                
                selected_proposal_type, selected_proposal_id = proposal_options[selected_proposal_label]
                
                if st.button("✨ Generate Card with AI", use_container_width=True, type="primary"):
                    with st.spinner("Generating card with AI..."):
                        try:
                            db = next(get_db())
                            
                            # Get the proposal to use
                            if selected_proposal_type == "file":
                                # Use new proposal file
                                proposal_file = db.query(ProposalFile).filter(
                                    ProposalFile.id == selected_proposal_id
                                ).first()
                                
                                if proposal_file and proposal_file.extracted_text:
                                    # Create a mock proposal object for compatibility with generate_organization_card
                                    class MockProposal:
                                        def __init__(self, pf):
                                            self.extracted_text = pf.extracted_text
                                            self.full_organization_name = pf.display_name
                                            self.mission_statement = ""
                                    
                                    proposal = MockProposal(proposal_file)
                                else:
                                    st.error("Selected proposal file not found or has no extracted text")
                                    proposal = None
                            else:
                                # Use legacy proposal
                                proposal = db.query(ProposalSubmission).filter(
                                    ProposalSubmission.user_id == user_id,
                                    ProposalSubmission.is_deleted == False
                                ).first()
                            
                            if proposal:
                                existing_cards = db.query(OrganizationCard).filter(
                                    OrganizationCard.user_id == user_id,
                                    OrganizationCard.is_deleted == False
                                ).all()
                                
                                result = generate_organization_card(proposal, existing_cards)
                                
                                if result:
                                    st.session_state["ai_generated_title"] = result.get("title", "")
                                    st.session_state["ai_generated_subtitle"] = result.get("subtitle", "")
                                    st.session_state["ai_generated_user_id"] = user_id
                                    st.success("✅ Card generated! Review and edit below before saving.")
                                    st.rerun()
                                else:
                                    st.error("Failed to generate card. Please try again.")
                            else:
                                st.error("Could not load selected proposal")
                        except Exception as e:
                            st.error(f"Error generating card: {str(e)}")
                        finally:
                            if db:
                                db.close()
            else:
                st.info("💡 No proposals with extracted text available. Upload a proposal in the Proposal Manager.")
        else:
            st.info("💡 Upload a proposal in the Proposal Manager to enable AI card generation")
        
        st.markdown("### Manual Card Creation")
        
        with st.form(key="create_card_form"):
            # Use AI-generated content if available
            default_title = st.session_state.get("ai_generated_title", "")
            default_subtitle = st.session_state.get("ai_generated_subtitle", "")
            
            new_title = st.text_input("Title*", value=default_title, max_chars=100, help="Compelling headline for your card")
            new_subtitle = st.text_area("Subtitle", value=default_subtitle, max_chars=300, help="Additional details or context")
            new_image = st.file_uploader("Upload image (optional)", type=["jpg", "jpeg", "png"])
            
            submit_button = st.form_submit_button("➕ Save This Card", use_container_width=True)
            
            if submit_button:
                if not new_title or not new_title.strip():
                    st.error("Title is required!")
                else:
                    try:
                        db = next(get_db())
                        
                        # Double-check card limit
                        current_card_count = db.query(OrganizationCard).filter(
                            OrganizationCard.user_id == user_id,
                            OrganizationCard.is_deleted == False
                        ).count()
                        
                        if current_card_count >= 3:
                            st.error("You have reached the maximum of 3 cards!")
                        else:
                            # Create new card
                            new_card = OrganizationCard(
                                user_id=user_id,
                                title=new_title.strip(),
                                subtitle=new_subtitle.strip() if new_subtitle else None
                            )
                            
                            db.add(new_card)
                            db.flush()  # Get the card ID
                            
                            # Handle image upload
                            if new_image:
                                processed_image, content_type = process_image(new_image)
                                if processed_image:
                                    s3_key = f"card_images/{user_id}_{new_card.id}.jpg"
                                    result = upload_file_to_s3(processed_image, s3_key, content_type)
                                    if result:
                                        new_card.image_path = result
                                    else:
                                        st.warning("Failed to upload image, but card will be saved")
                            
                            db.commit()
                            st.success("✅ Card created successfully!")
                            
                            # Clear AI-generated content from session state
                            if "ai_generated_title" in st.session_state:
                                del st.session_state["ai_generated_title"]
                            if "ai_generated_subtitle" in st.session_state:
                                del st.session_state["ai_generated_subtitle"]
                            if "ai_generated_user_id" in st.session_state:
                                del st.session_state["ai_generated_user_id"]
                            
                            st.rerun()
                    except Exception as e:
                        if db:
                            db.rollback()
                        st.error(f"Error creating card: {str(e)}")
                    finally:
                        if db:
                            db.close()

