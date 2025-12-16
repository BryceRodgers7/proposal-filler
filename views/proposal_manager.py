"""
Proposal Manager page for organization representatives.
Allows uploading and managing multiple proposal files.
"""
import os
import uuid
import streamlit as st
import pdfplumber
import io
from docx import Document
from helpers.db import get_db, ProposalFile
from helpers.auth import get_current_user_id, get_current_user_type
from helpers.storage import upload_file_to_s3, is_s3_available


def extract_text_from_pdf(file) -> str:
    """Extract text from a PDF file."""
    with pdfplumber.open(file) as pdf:
        texts = [(page.extract_text() or "") for page in pdf.pages]
    return "\n\n".join(texts)


def extract_text_from_docx(file) -> str:
    """Extract text from a DOCX file."""
    data = file.read()
    file.seek(0)
    mem_file = io.BytesIO(data)
    doc = Document(mem_file)
    return "\n".join(p.text for p in doc.paragraphs)


def extract_text(uploaded_file) -> str:
    """Extract text from an uploaded file (PDF, DOCX, or TXT)."""
    if uploaded_file is None:
        return ""

    file_type = uploaded_file.type or ""
    file_name = uploaded_file.name.lower()

    # PDF
    if "pdf" in file_type or file_name.endswith(".pdf"):
        return extract_text_from_pdf(uploaded_file)

    # DOCX
    if (
        "word" in file_type
        or file_name.endswith(".docx")
        or file_name.endswith(".doc")
    ):
        return extract_text_from_docx(uploaded_file)

    # Fallback: assume text
    raw_bytes = uploaded_file.read()
    uploaded_file.seek(0)
    return raw_bytes.decode("utf-8", errors="ignore")


def render_proposal_manager():
    """
    Render the proposal manager page for organization representatives.
    Allows uploading and managing multiple proposal files.
    """
    st.title("📂 Proposal Manager")
    st.write("Upload and manage your organization's proposal documents. Select a proposal from the dropdown on other pages to use it for AI features.")
    
    # Check if user is a representative
    user_type = get_current_user_type()
    if user_type != "representative":
        st.error("❌ This page is only accessible to organization representatives.")
        return
    
    user_id = get_current_user_id()
    if user_id is None:
        st.error("You must be logged in to access this page.")
        return
    
    # Check S3 availability
    s3_available = is_s3_available()
    
    # Load existing proposal files
    db = None
    try:
        db = next(get_db())
        proposal_files = db.query(ProposalFile).filter(
            ProposalFile.user_id == user_id,
            ProposalFile.is_deleted == False
        ).order_by(ProposalFile.created_at.desc()).all()
        
        file_count = len(proposal_files)
        
    except Exception as e:
        st.error(f"Error loading proposal files: {str(e)}")
        if db:
            db.close()
        return
    finally:
        if db:
            db.close()
    
    # Display file count
    st.info(f"📊 You have uploaded **{file_count}** proposal file(s)")
    
    # Show existing files
    if proposal_files:
        st.markdown("---")
        st.subheader("Your Proposal Files")
        
        for idx, proposal_file in enumerate(proposal_files, 1):
            with st.expander(f"📄 {proposal_file.display_name}", expanded=False):
                # Display file info
                col_info, col_actions = st.columns([2, 1])
                
                with col_info:
                    st.markdown(f"**Display Name:** {proposal_file.display_name}")
                    st.markdown(f"**File Name:** {proposal_file.file_name}")
                    st.markdown(f"**File Type:** {proposal_file.file_type}")
                    st.caption(f"Uploaded: {proposal_file.created_at.strftime('%Y-%m-%d %H:%M')}")
                    if proposal_file.extracted_text:
                        st.text_area(
                            "Extracted text preview",
                            value=proposal_file.extracted_text[:2000] + ("..." if len(proposal_file.extracted_text) > 2000 else ""),
                            height=200,
                            disabled=True,
                            key=f"text_preview_{proposal_file.id}"
                        )
                
                with col_actions:
                    # Edit button
                    if st.button(f"✏️ Edit", key=f"edit_{proposal_file.id}", use_container_width=True):
                        st.session_state[f"editing_proposal_{proposal_file.id}"] = True
                        st.rerun()
                    
                    # Delete button
                    if st.button(f"🗑️ Delete", key=f"delete_{proposal_file.id}", type="secondary", use_container_width=True):
                        # Confirm deletion
                        if st.session_state.get(f"confirm_delete_{proposal_file.id}", False):
                            try:
                                db = next(get_db())
                                file_to_delete = db.query(ProposalFile).filter(
                                    ProposalFile.id == proposal_file.id
                                ).first()
                                if file_to_delete:
                                    file_to_delete.is_deleted = True
                                    db.commit()
                                    st.success("Proposal file deleted successfully!")
                                    # Clear confirmation flag
                                    del st.session_state[f"confirm_delete_{proposal_file.id}"]
                                    st.rerun()
                            except Exception as e:
                                if db:
                                    db.rollback()
                                st.error(f"Error deleting file: {str(e)}")
                            finally:
                                if db:
                                    db.close()
                        else:
                            st.session_state[f"confirm_delete_{proposal_file.id}"] = True
                            st.warning("⚠️ Click delete again to confirm")
                            st.rerun()
                
                # Show edit form if editing
                if st.session_state.get(f"editing_proposal_{proposal_file.id}", False):
                    st.markdown("### Edit Proposal File")
                    with st.form(key=f"edit_form_{proposal_file.id}"):
                        edit_display_name = st.text_input(
                            "Display Name*",
                            value=proposal_file.display_name,
                            max_chars=255,
                            help="This name will appear in dropdown menus"
                        )
                        
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            save_button = st.form_submit_button("💾 Save Changes", use_container_width=True)
                        with col_cancel:
                            cancel_button = st.form_submit_button("❌ Cancel", use_container_width=True)
                        
                        if save_button:
                            if not edit_display_name or not edit_display_name.strip():
                                st.error("Display name is required!")
                            else:
                                try:
                                    db = next(get_db())
                                    file_to_edit = db.query(ProposalFile).filter(
                                        ProposalFile.id == proposal_file.id
                                    ).first()
                                    
                                    if file_to_edit:
                                        file_to_edit.display_name = edit_display_name.strip()
                                        db.commit()
                                        st.success("Display name updated successfully!")
                                        del st.session_state[f"editing_proposal_{proposal_file.id}"]
                                        st.rerun()
                                except Exception as e:
                                    if db:
                                        db.rollback()
                                    st.error(f"Error updating file: {str(e)}")
                                finally:
                                    if db:
                                        db.close()
                        
                        if cancel_button:
                            del st.session_state[f"editing_proposal_{proposal_file.id}"]
                            st.rerun()
    
    # Upload new proposal file section
    st.markdown("---")
    st.subheader("Upload New Proposal")
    
    with st.form(key="upload_proposal_form", clear_on_submit=False):
        display_name = st.text_input(
            "Display Name*",
            max_chars=255,
            help="Give this proposal a memorable name (e.g., 'Q4 2024 Grant Proposal', 'Education Initiative')"
        )
        
        uploaded_file = st.file_uploader(
            "Select Proposal File*",
            type=["pdf", "docx", "txt"],
            help="Upload a PDF, DOCX, or TXT file"
        )
        
        extract_text_checkbox = st.checkbox(
            "Extract text for AI features",
            value=True,
            help="Extract text from the file to enable AI-powered features"
        )
        
        submit_button = st.form_submit_button("📤 Upload Proposal", use_container_width=True, type="primary")
        
        if submit_button:
            if not display_name or not display_name.strip():
                st.error("❌ Display name is required!")
            elif not uploaded_file:
                st.error("❌ Please select a file to upload!")
            else:
                # Process the upload
                try:
                    with st.spinner("Uploading proposal file..."):
                        # Generate unique file ID
                        file_id = str(uuid.uuid4())
                        file_extension = os.path.splitext(uploaded_file.name)[1]
                        s3_key = f"proposal_files/{user_id}/{file_id}{file_extension}"
                        
                        # Upload to S3
                        s3_path = None
                        if s3_available:
                            try:
                                file_buffer = uploaded_file.getbuffer()
                                file_data = bytes(file_buffer)
                                content_type = uploaded_file.type
                                s3_path = upload_file_to_s3(file_data, s3_key, content_type)
                                
                                if not s3_path:
                                    st.error("Failed to upload file to S3")
                                    st.stop()
                            except Exception as e:
                                st.error(f"Error uploading to S3: {str(e)}")
                                st.stop()
                        else:
                            st.error("S3 storage is not available. Cannot upload file.")
                            st.stop()
                        
                        # Extract text if requested
                        extracted_text = None
                        if extract_text_checkbox:
                            try:
                                with st.spinner("Extracting text..."):
                                    extracted_text = extract_text(uploaded_file)
                            except Exception as e:
                                st.warning(f"Could not extract text: {str(e)}")
                        
                        # Save to database
                        db = next(get_db())
                        new_proposal_file = ProposalFile(
                            user_id=user_id,
                            file_name=uploaded_file.name,
                            file_path=s3_path,
                            file_type=uploaded_file.type or file_extension[1:].lower(),
                            display_name=display_name.strip(),
                            extracted_text=extracted_text
                        )
                        
                        db.add(new_proposal_file)
                        db.commit()
                        db.close()
                        
                        st.success(f"✅ Proposal file '{display_name}' uploaded successfully!")
                        st.rerun()
                        
                except Exception as e:
                    if db:
                        db.rollback()
                        db.close()
                    st.error(f"Error uploading proposal: {str(e)}")
    
    # Help section
    st.markdown("---")
    with st.expander("ℹ️ How to use proposal files", expanded=False):
        st.markdown("""
        ### Using Proposal Files
        
        1. **Upload**: Upload your proposal documents using the form above
        2. **Organize**: Give each proposal a descriptive display name
        3. **Select**: On the Organization Profile and Card Creator pages, use the dropdown to select which proposal to use for AI features
        4. **Extract**: Enable text extraction to power AI-driven content generation
        
        ### Tips
        - Use clear, descriptive names for easy identification
        - Upload different versions or types of proposals for different purposes
        - The extracted text is used by AI to generate cards and fill forms
        """)

