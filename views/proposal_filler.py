"""
Profile page for the Proposal Filler application.
Contains the form filler functionality with AI extraction.
"""
import json
import io
import os
import uuid
import streamlit as st
import pdfplumber  
from docx import Document  
from helpers.db import ProposalSubmission, get_db, User
from helpers.storage import upload_file_to_s3, upload_organization_image, get_s3_url
from helpers.auth import get_current_user_id, has_account_tier, get_user_account_tier, get_current_user
from helpers.stripe_checkout import create_checkout_session
from helpers.openai_client import (
    call_llm_to_structure,
    PRIMARY_CAUSE_AREAS,
    POPULATIONS,
    GEOGRAPHIC_FOCUS_OPTIONS,
    LEGAL_DESIGNATION_OPTIONS,
    DEFAULT_FORM
)
import traceback


def is_streamlit_cloud():
    """
    Check if the app is running on Streamlit Community Cloud.
    
    Returns:
        True if running on Streamlit Cloud, False otherwise
    """
    # Streamlit Community Cloud sets STREAMLIT_SHARING_MODE to "SHARED"
    if os.environ.get("STREAMLIT_SHARING_MODE") == "SHARED":
        return True
    # Alternative check: check if running on streamlit.app domain
    try:
        import socket
        hostname = socket.gethostname()
        if "streamlit.app" in hostname or "streamlit.io" in hostname:
            return True
    except:
        pass
    return False



# ----- FILE → TEXT HELPERS -----
def extract_text_from_pdf(file) -> str:
    # file is a BytesIO-like object from Streamlit
    with pdfplumber.open(file) as pdf:
        texts = [(page.extract_text() or "") for page in pdf.pages]
    return "\n\n".join(texts)


def extract_text_from_docx(file) -> str:
    # streamlit gives us a SpooledTemporaryFile; wrap for python-docx
    data = file.read()
    file.seek(0)
    mem_file = io.BytesIO(data)
    doc = Document(mem_file)
    return "\n".join(p.text for p in doc.paragraphs)


def extract_text(uploaded_file) -> str:
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


def render_profile_page():
    """Render the profile page content."""
    # Get initialization flags from session state (set by app.py)
    db_initialized = st.session_state.get("db_initialized", False)
    s3_available = st.session_state.get("s3_available", False)
    user_id = get_current_user_id()
    
    if user_id is None:
        st.error("You must be logged in to access this page.")
        return
    
    # Check if user is a representative
    user_type = st.session_state.get("user_type", "representative")
    if user_type != "representative":
        st.error("❌ This page is only accessible to representatives. Donors should use the 'My Donor Profile' page instead.")
        return
    
    # Load existing profile for current user if it exists
    # Track if we've loaded the profile for this user session
    # Check if the user has changed (e.g., logged out and back in)
    if "last_loaded_user_id" not in st.session_state or st.session_state.last_loaded_user_id != user_id:
        # User has changed - clear profile loading state
        st.session_state.last_loaded_user_id = user_id
        # Clear any profile-related session state
        keys_to_clear = [key for key in st.session_state.keys() if key.startswith("profile_loaded_user_")]
        for key in keys_to_clear:
            del st.session_state[key]
        # Clear form_data so it gets reloaded
        if "form_data" in st.session_state:
            del st.session_state.form_data
        if "existing_submission_id" in st.session_state:
            del st.session_state.existing_submission_id
    
    profile_loaded_key = f"profile_loaded_user_{user_id}"
    
    existing_submission = None
    existing_submission_id = None
    
    # Always check for existing submission
    try:
        db = next(get_db())
        existing_submission = db.query(ProposalSubmission).filter(
            ProposalSubmission.user_id == user_id
        ).order_by(ProposalSubmission.updated_at.desc()).first()
        db.close()
        
        if existing_submission:
            existing_submission_id = existing_submission.id
            st.session_state.existing_submission_id = existing_submission_id
        else:
            # No profile exists yet - this is normal for new users
            st.session_state.no_profile_yet = True
            # Clear any stale existing_submission_id
            if "existing_submission_id" in st.session_state:
                del st.session_state.existing_submission_id
    except Exception as e:
        # Only show error for actual database errors
        st.error(f"Error loading profile: {str(e)}")
        existing_submission = None
    
    # Initialize or populate form_data with existing profile data
    # If we haven't loaded the profile for this user session yet, or form_data doesn't exist, populate it
    if not st.session_state.get(profile_loaded_key, False) or "form_data" not in st.session_state:
        if existing_submission:
            # We have an existing profile - populate form_data with it
            st.session_state.form_data = {
                "full_organization_name": existing_submission.full_organization_name or "",
                "legal_designation": existing_submission.legal_designation or "",
                "mission_statement": existing_submission.mission_statement or "",
                "ein": existing_submission.ein or "",
                "year_founded": existing_submission.year_founded or "",
                "location_served": existing_submission.location_served or "",
                "biggest_accomplishment": existing_submission.biggest_accomplishment or "",
                "what_we_do_in_one_sentence": existing_submission.what_we_do_in_one_sentence or "",
                "primary_cause_area": existing_submission.primary_cause_area if isinstance(existing_submission.primary_cause_area, list) else [],
                "populations": existing_submission.populations if isinstance(existing_submission.populations, list) else [],
                "geographic_focus": existing_submission.geographic_focus or ""
            }
            st.session_state.extracted_text = existing_submission.extracted_text or ""
            st.session_state[profile_loaded_key] = True
        else:
            # No existing profile - initialize with empty form
            st.session_state.form_data = DEFAULT_FORM.copy()
            st.session_state[profile_loaded_key] = True
    else:
        # Form data exists and we've already loaded - but check if it's empty and we have existing data
        current_form = st.session_state.form_data
        is_default_form = (
            not current_form.get("full_organization_name") and
            not current_form.get("mission_statement") and
            not current_form.get("ein")
        )
        if is_default_form and existing_submission:
            # Form is empty but we have existing data - populate it
            st.session_state.form_data = {
                "full_organization_name": existing_submission.full_organization_name or "",
                "legal_designation": existing_submission.legal_designation or "",
                "mission_statement": existing_submission.mission_statement or "",
                "ein": existing_submission.ein or "",
                "year_founded": existing_submission.year_founded or "",
                "location_served": existing_submission.location_served or "",
                "biggest_accomplishment": existing_submission.biggest_accomplishment or "",
                "what_we_do_in_one_sentence": existing_submission.what_we_do_in_one_sentence or "",
                "primary_cause_area": existing_submission.primary_cause_area if isinstance(existing_submission.primary_cause_area, list) else [],
                "populations": existing_submission.populations if isinstance(existing_submission.populations, list) else [],
                "geographic_focus": existing_submission.geographic_focus or ""
            }
            if existing_submission.extracted_text:
                st.session_state.extracted_text = existing_submission.extracted_text

    st.title("👤 AI-Powered Profile Builder")
    
    # Show info if editing existing profile
    if "existing_submission_id" in st.session_state:
        st.info(f"📝 Editing your existing profile (ID: {st.session_state.existing_submission_id}). Upload a new file or edit the fields below.")
    elif st.session_state.get("no_profile_yet", False):
        st.info("👋 Welcome! You don't have a profile yet. Upload a proposal file below to get started, or fill out the form manually.")
    
    # --- SECTION 1: Organization Image Upload ---
    st.markdown("---")
    st.subheader("🖼️ Organization Image")
    st.write("Upload a logo or image for your organization (recommended size: 800x600px or similar)")
    
    col_img1, col_img2 = st.columns(2)
    
    with col_img1:
        # Display current image if it exists
        if existing_submission and existing_submission.image_path:
            st.write("**Current Saved Image:**")
            st.caption(f"S3 Key: `{existing_submission.image_path}`")
            try:
                image_url, error_msg = get_s3_url(existing_submission.image_path)
                if image_url:
                    st.image(image_url, width=300, caption="Current organization image")
                    with st.expander("🔍 Debug Info"):
                        st.code(f"S3 Key: {existing_submission.image_path}\nURL: {image_url}")
                else:
                    st.error(f"Could not load image: {error_msg}")
                    with st.expander("🔍 Debug Info"):
                        st.code(f"S3 Key: {existing_submission.image_path}\nError: {error_msg}")
            except Exception as e:
                st.error(f"Exception loading image: {str(e)}")
                st.code(traceback.format_exc())
        else:
            st.info("No image uploaded yet")
    
    with col_img2:
        # Image upload widget
        uploaded_image = st.file_uploader(
            "Upload new image (JPG, PNG, or GIF)",
            type=["jpg", "jpeg", "png", "gif"],
            key="org_image_uploader",
            help="Image will be automatically resized to fit the page. Recommended aspect ratio: 4:3"
        )
        
        # Preview the newly uploaded image before saving
        if uploaded_image is not None:
            st.write("**Preview of New Image:**")
            st.image(uploaded_image, width=300, caption=uploaded_image.name)
            st.session_state.uploaded_image = uploaded_image
            
            # Button to save just the image
            if st.button("💾 Save Image Only", type="secondary", key="save_image_only"):
                if existing_submission:
                    if s3_available:
                        try:
                            with st.spinner("Uploading image..."):
                                # Upload image to S3
                                image_s3_path = upload_organization_image(
                                    st.session_state.uploaded_image,
                                    existing_submission.id
                                )
                                
                                if image_s3_path:
                                    # Update submission with image path
                                    db = next(get_db())
                                    existing_submission.image_path = image_s3_path
                                    db.add(existing_submission)
                                    db.commit()
                                    db.close()
                                    st.success(f"✅ Organization image uploaded successfully!")
                                    # Clear the uploaded image from session state
                                    del st.session_state.uploaded_image
                                    st.rerun()
                                else:
                                    st.error("❌ Could not upload organization image to S3")
                        except Exception as img_e:
                            st.error(f"❌ Error uploading image: {str(img_e)}")
                    else:
                        st.error("❌ S3 storage not available. Cannot upload organization image.")
                else:
                    st.warning("⚠️ Please save your profile first before uploading an image.")
    
    # --- SECTION 2: Proposal File Upload ---
    st.markdown("---")
    st.subheader("📄 Proposal Document Upload")
    st.write(
        "Upload a proposal (PDF, DOCX, or TXT). "
        "The app will use AI to extract key fields into a structured form you can edit."
    )

    uploaded_file = st.file_uploader("Upload proposal", type=["pdf", "docx", "txt"])

    # Optional: show the raw text for debugging
    with st.expander("Show extracted raw text (debug)", expanded=False):
        if uploaded_file is not None:
            raw_text = extract_text(uploaded_file)
            st.text_area("Raw extracted text", raw_text, height=200)
        else:
            st.info("Upload a file to see extracted text.")

    # Store uploaded file info in session state
    if uploaded_file is not None:
        # Check if this is a new file (different from previous upload)
        current_file_name = uploaded_file.name
        if ("uploaded_file_info" not in st.session_state or 
            st.session_state.uploaded_file_info.get("original_name") != current_file_name):
            file_id = str(uuid.uuid4())
            file_extension = os.path.splitext(uploaded_file.name)[1]
            s3_key = f"uploads/{file_id}{file_extension}"
            
            # Try to upload file to S3 (if available)
            s3_path = None
            s3_upload_success = False
            if s3_available:
                try:
                    # Read file data as bytes (getbuffer() returns memoryview, need to convert to bytes)
                    file_buffer = uploaded_file.getbuffer()
                    file_data = bytes(file_buffer)
                    content_type = uploaded_file.type
                    s3_path = upload_file_to_s3(file_data, s3_key, content_type)
                    if s3_path:
                        print(f"✅ File uploaded to S3: {s3_path}")
                        s3_upload_success = True
                        st.success(f"✅ File successfully uploaded to S3: {uploaded_file.name}")
                    else:
                        print(f"⚠️ Warning: Could not upload file to S3")
                        st.warning("⚠️ Could not upload file to S3. File will be stored in memory only.")
                except Exception as e:
                    print(f"⚠️ Warning: Error uploading file to S3: {str(e)}")
                    st.error(f"⚠️ Error uploading file to S3: {str(e)}")
                    s3_path = None
            else:
                st.info("ℹ️ S3 storage is not available. File will be stored in memory only.")
            
            # Store file info in session state
            st.session_state.uploaded_file_info = {
                "original_name": uploaded_file.name,
                "saved_path": s3_path or f"in_memory:{file_id}",  # S3 key or in-memory marker
                "file_type": uploaded_file.type or file_extension[1:].lower(),
                "file_id": file_id
            }
            st.session_state.extracted_text = None  # Will be set after extraction
            # Reset form data when new file is uploaded
            st.session_state.form_data = DEFAULT_FORM.copy()

    # --- Extract button ---
    if uploaded_file is not None and st.button("Extract with AI"):
        with st.spinner("Extracting fields with AI..."):
            text = extract_text(uploaded_file)
            st.session_state.extracted_text = text
            st.session_state.form_data = call_llm_to_structure(text)
        st.success("Extraction complete! Scroll down to review and edit the form.")

    # --- SECTION 3: Structured Form ---
    st.markdown("---")
    st.subheader("📝 Structured Form (Editable)")

    fd = st.session_state.form_data

    col1, col2 = st.columns(2)
    with col1:
        fd["full_organization_name"] = st.text_input("Full organization name", value=fd.get("full_organization_name", ""))
        fd["mission_statement"] = st.text_input("Mission statement", value=fd.get("mission_statement", ""))
        fd["ein"] = st.text_input("EIN", value=fd.get("ein", ""))
        fd["year_founded"] = st.text_input("Year founded", value=fd.get("year_founded", ""))
        fd["location_served"] = st.text_input("Location served", value=fd.get("location_served", ""))
        fd["biggest_accomplishment"] = st.text_input("Biggest accomplishment", value=fd.get("biggest_accomplishment", ""))    
        fd["what_we_do_in_one_sentence"] = st.text_input("What we do in one sentence", value=fd.get("what_we_do_in_one_sentence", ""))

    # Legal designation - single select dropdown
    current_legal_designation = fd.get("legal_designation", "")
    if not isinstance(current_legal_designation, str):
        current_legal_designation = ""
    if current_legal_designation not in LEGAL_DESIGNATION_OPTIONS:
        current_legal_designation = ""
    # Calculate index safely
    if current_legal_designation and current_legal_designation in LEGAL_DESIGNATION_OPTIONS:
        legal_index = LEGAL_DESIGNATION_OPTIONS.index(current_legal_designation) + 1
    else:
        legal_index = 0
    fd["legal_designation"] = st.selectbox(
        "Legal designation",
        options=[""] + LEGAL_DESIGNATION_OPTIONS,  # Empty string for "not selected"
        index=legal_index,
        format_func=lambda x: "Select..." if x == "" else x
    )

    # Primary cause area(s) - multiselect dropdown
    current_cause_areas = fd.get("primary_cause_area", [])
    if not isinstance(current_cause_areas, list):
        current_cause_areas = []
    # Filter to only include values that exist in the options list
    current_cause_areas = [area for area in current_cause_areas if area in PRIMARY_CAUSE_AREAS]
    fd["primary_cause_area"] = st.multiselect(
        "Primary cause area(s)",
        options=PRIMARY_CAUSE_AREAS,
        default=current_cause_areas
    )

    # Population(s) - multiselect dropdown
    current_populations = fd.get("populations", [])
    if not isinstance(current_populations, list):
        current_populations = []
    # Filter to only include values that exist in the options list
    current_populations = [pop for pop in current_populations if pop in POPULATIONS]
    fd["populations"] = st.multiselect(
        "Population(s)",
        options=POPULATIONS,
        default=current_populations
    )

    # Geographic focus - single select dropdown
    current_geographic_focus = fd.get("geographic_focus", "")
    if not isinstance(current_geographic_focus, str):
        current_geographic_focus = ""
    if current_geographic_focus not in GEOGRAPHIC_FOCUS_OPTIONS:
        current_geographic_focus = ""
    # Calculate index safely
    if current_geographic_focus and current_geographic_focus in GEOGRAPHIC_FOCUS_OPTIONS:
        focus_index = GEOGRAPHIC_FOCUS_OPTIONS.index(current_geographic_focus) + 1
    else:
        focus_index = 0
    fd["geographic_focus"] = st.selectbox(
        "Geographic focus",
        options=[""] + GEOGRAPHIC_FOCUS_OPTIONS,  # Empty string for "not selected"
        index=focus_index,
        format_func=lambda x: "Select..." if x == "" else x
    )

    st.session_state.form_data = fd

    # --- Save to Database button ---
    st.markdown("### Save & Export")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Save to Database", type="primary"):
            if not db_initialized:
                st.error("⚠️ Database is not available. Please check your database configuration.")
            elif "uploaded_file_info" not in st.session_state and "existing_submission_id" not in st.session_state:
                st.error("Please upload a file first or have an existing profile to update.")
            else:
                try:
                    db = next(get_db())
                    
                    # Check if we're updating an existing submission or creating a new one
                    existing_id = st.session_state.get("existing_submission_id")
                    is_new_profile = False
                    
                    if existing_id:
                        # Update existing submission
                        submission = db.query(ProposalSubmission).filter(
                            ProposalSubmission.id == existing_id,
                            ProposalSubmission.user_id == user_id
                        ).first()
                        
                        if not submission:
                            # Couldn't find the existing profile, so we'll create a new one
                            submission = None
                            is_new_profile = True
                    
                    if not existing_id or not submission:
                        # Create new submission
                        is_new_profile = True
                        # Get file path - use S3 key or in-memory marker
                        if "uploaded_file_info" in st.session_state:
                            file_path = st.session_state.uploaded_file_info["saved_path"]
                            file_name = st.session_state.uploaded_file_info["original_name"]
                            file_type = st.session_state.uploaded_file_info["file_type"]
                        else:
                            # No file uploaded, use placeholder values
                            file_path = "no_file"
                            file_name = "manual_entry"
                            file_type = "text/plain"
                        
                        submission = ProposalSubmission(
                            user_id=user_id,
                            file_name=file_name,
                            file_path=file_path,
                            file_type=file_type,
                            full_organization_name=fd.get("full_organization_name", ""),
                            legal_designation=fd.get("legal_designation", ""),
                            mission_statement=fd.get("mission_statement", ""),
                            ein=fd.get("ein", ""),
                            year_founded=fd.get("year_founded", ""),
                            location_served=fd.get("location_served", ""),
                            biggest_accomplishment=fd.get("biggest_accomplishment", ""),
                            what_we_do_in_one_sentence=fd.get("what_we_do_in_one_sentence", ""),
                            primary_cause_area=fd.get("primary_cause_area", []),
                            populations=fd.get("populations", []),
                            geographic_focus=fd.get("geographic_focus", ""),
                            extracted_text=st.session_state.get("extracted_text", "")
                        )
                        db.add(submission)
                    else:
                        # Update existing submission fields
                        if "uploaded_file_info" in st.session_state:
                            submission.file_name = st.session_state.uploaded_file_info["original_name"]
                            submission.file_path = st.session_state.uploaded_file_info["saved_path"]
                            submission.file_type = st.session_state.uploaded_file_info["file_type"]
                        
                        submission.full_organization_name = fd.get("full_organization_name", "")
                        submission.legal_designation = fd.get("legal_designation", "")
                        submission.mission_statement = fd.get("mission_statement", "")
                        submission.ein = fd.get("ein", "")
                        submission.year_founded = fd.get("year_founded", "")
                        submission.location_served = fd.get("location_served", "")
                        submission.biggest_accomplishment = fd.get("biggest_accomplishment", "")
                        submission.what_we_do_in_one_sentence = fd.get("what_we_do_in_one_sentence", "")
                        submission.primary_cause_area = fd.get("primary_cause_area", [])
                        submission.populations = fd.get("populations", [])
                        submission.geographic_focus = fd.get("geographic_focus", "")
                        if "extracted_text" in st.session_state:
                            submission.extracted_text = st.session_state.extracted_text
                    
                    db.commit()
                    db.refresh(submission)
                    
                    # Handle image upload if present (and not already saved separately)
                    if "uploaded_image" in st.session_state and st.session_state.uploaded_image is not None:
                        if s3_available:
                            try:
                                with st.spinner("Uploading image..."):
                                    # Upload image to S3
                                    image_s3_path = upload_organization_image(
                                        st.session_state.uploaded_image,
                                        submission.id
                                    )
                                    
                                    if image_s3_path:
                                        # Update submission with image path
                                        submission.image_path = image_s3_path
                                        db.commit()
                                        st.success(f"✅ Organization image uploaded successfully!")
                                        # Clear the uploaded image from session state
                                        del st.session_state.uploaded_image
                                    else:
                                        st.warning("⚠️ Could not upload organization image to S3")
                            except Exception as img_e:
                                st.error(f"⚠️ Error uploading image: {str(img_e)}")
                        else:
                            st.warning("⚠️ S3 storage not available. Cannot upload organization image.")
                    
                    # Show appropriate success message
                    if is_new_profile:
                        st.success("✅ Profile created!")
                    else:
                        st.success(f"✅ Profile updated! Submission ID: {submission.id}")
                    st.session_state.last_saved_id = submission.id
                    st.session_state.existing_submission_id = submission.id
                    
                except Exception as e:
                    # Show full error details if running on Streamlit Cloud
                    if is_streamlit_cloud():
                        st.error(f"❌ Error saving to database: {str(e)}")
                        with st.expander("🔍 Full Error Details (Click to expand)", expanded=True):
                            st.code(traceback.format_exc(), language="python")
                    else:
                        # Show simplified error message when running locally
                        st.error(f"Error saving to database: {str(e)}")
                    db.rollback()
                finally:
                    db.close()

    with col2:
        download_json = json.dumps(st.session_state.form_data, indent=2)
        st.download_button(
            label="📥 Download as JSON",
            data=download_json,
            file_name="structured_proposal.json",
            mime="application/json",
        )

        # Show last saved ID if available
        if "last_saved_id" in st.session_state:
            st.info(f"Last saved submission ID: {st.session_state.last_saved_id}")
    
    # --- Account Tier & Upgrade Section ---
    current_tier = get_user_account_tier()
    if current_tier and current_tier.lower() != "premium" and current_tier.lower() != "enterprise":
        st.markdown("---")
        st.markdown("### ⭐ Upgrade to Premium")
        st.info(f"Your current account tier: **{current_tier}**")
        
        # Check for checkout success/cancel messages
        # Use experimental_get_query_params for compatibility with older Streamlit versions
        try:
            # Try new API first (Streamlit 1.28.0+)
            query_params = st.query_params
        except AttributeError:
            # Fall back to experimental API (older Streamlit versions)
            try:
                query_params = st.experimental_get_query_params()
                # Convert to dict format for consistency
                query_params = {k: v[0] if isinstance(v, list) and len(v) > 0 else v for k, v in query_params.items()}
            except AttributeError:
                # If neither exists, use empty dict
                query_params = {}
        
        if query_params.get("checkout") == "success":
            st.success("✅ Payment successful! Your account has been upgraded to Premium. Please refresh the page to see premium features.")
        elif query_params.get("checkout") == "cancel":
            st.info("ℹ️ Checkout was cancelled. You can try again anytime.")
        
        if st.button("🚀 Upgrade to Premium", type="primary", use_container_width=True):
            try:
                user = get_current_user()
                if user:
                    checkout_url = create_checkout_session(user)
                    # Store checkout URL in session state and redirect
                    st.session_state.checkout_url = checkout_url
                    st.rerun()
                else:
                    st.error("Error: User not found. Please log in again.")
            except Exception as e:
                st.error(f"Error creating checkout session: {str(e)}")
        
        # Show checkout link if URL is in session state
        if "checkout_url" in st.session_state:
            st.markdown("---")
            st.markdown("### Complete Your Purchase")
            st.markdown(f"[Click here to complete your purchase →]({st.session_state.checkout_url})")
            st.info("🔄 You will be redirected to Stripe to complete your payment.")
            # Clear the checkout URL after showing it
            if st.button("Cancel", key="cancel_checkout"):
                del st.session_state.checkout_url
                st.rerun()

