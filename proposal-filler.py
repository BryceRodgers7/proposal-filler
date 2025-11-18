# app.py
import json
import io
import os
import uuid
import streamlit as st
from openai import OpenAI
import pdfplumber  
from dotenv import load_dotenv
from docx import Document  
from db import init_db, SessionLocal, ProposalSubmission, get_db
from datetime import datetime
from storage import upload_file_to_s3, is_s3_available, get_s3_url
import traceback
from sidebar import render_sidebar
from page2 import render_page2


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


# Initialize database
_db_initialized = False
try:
    init_db()
    _db_initialized = True
except Exception as e:
    # Log error but don't crash the app
    print(f"⚠️ Database initialization warning: {str(e)}")
    print("The app will continue to run, but database features may not work.")

# Initialize S3 storage
_s3_available = is_s3_available()
if not _s3_available:
    print("⚠️ S3 storage is not available. Please check your AWS credentials in secrets.toml")
    print("The app will continue to run, but uploaded files may not be saved to S3.")


def get_api_key():
    # Check if secrets file exists and load it first
    # Try environment.env first, then .env
    env_file = None
    if os.path.exists("environment.env"):
        env_file = "environment.env"
    elif os.path.exists(".env"):
        env_file = ".env"
    
    if env_file:
        load_dotenv(env_file)
    
    # Local development → use environment variable (from .env or system)
    if "OPENAI_API_KEY" in os.environ:
        return os.environ["OPENAI_API_KEY"]
    
    # Streamlit Cloud → use st.secrets
    if "OPENAI_API_KEY" in st.secrets:
        return st.secrets["OPENAI_API_KEY"]

    # No key found
    return None

api_key = get_api_key()

client = OpenAI(api_key=api_key)
# ----- CONFIG -----
st.set_page_config(page_title="Proposal Form Filler", page_icon="🤖", layout="centered")

# ----- DISCRETE OPTIONS FOR FIELDS -----
PRIMARY_CAUSE_AREAS = [
    "Agriculture & Food Security",
    "Animal Welfare",
    "Arts & Culture",
    "Arts Education",
    "Civic Engagement & Community Leadership",
    "Community & Economic Development",
    "Disability Services & Accessibility",
    "Disaster Relief & Public Safety",
    "Education",
    "Environment & Conservation",
    "Health & Wellness",
    "Housing & Homelessness",
    "Human Rights & Civil Liberties",
    "Human Services",
    "Information & Communications",
    "International & Global Affairs",
    "Mental Health & Wellness",
    "Philanthropy & Volunteering",
    "Poverty Alleviation",
    "Public Policy & Advocacy",
    "Religion & Spiritual Development",
    "Science & Technology",
    "Seniors & Aging Services",
    "Social Science Research",
    "Sports, Recreation & Leisure",
    "Youth Development",
    "Other"
]

POPULATIONS = [
    "Children & Youth",
    "Families",
    "Seniors / Elderly",
    "Women & Girls",
    "Men & Boys",
    "People Experiencing Homelessness",
    "People with Disabilities",
    "LGBTQ+ Communities",
    "Immigrants & Refugees",
    "Veterans & Military Families",
    "Indigenous / Native Communities",
    "Low-Income / Economically Disadvantaged Populations",
    "Racial & Ethnic Minorities",
    "Survivors of Domestic Violence / Abuse",
    "Patients / People with Chronic Illnesses",
    "Mental Health Communities",
    "Animals / Wildlife",
    "General Public / Community at Large",
    "Students / Educationally Underserved",
    "Artists & Creative Communities",
    "Other"
]

GEOGRAPHIC_FOCUS_OPTIONS = [
    "Local",
    "Regional",
    "National",
    "Global"
]

LEGAL_DESIGNATION_OPTIONS = [
    "501(c)(3) – Public Charity",
    "501(c)(3) – Private Foundation",
    "501(c)(4) – Social Welfare Organization",
    "501(c)(6) – Business League / Trade Association",
    "501(c)(7) – Social Club",
    "501(c)(19) – Veterans Organization",
    "501(c)(5) – Labor, Agricultural, or Horticultural Organization",
    "Fiscal Sponsor"
]

# ----- SIMPLE SCHEMA WE'LL USE FOR NOW -----
# You can expand this later to multiple jobs, skills, etc.
DEFAULT_FORM = {
    "full_organization_name": "",
    "legal_designation": "",
    "mission_statement": "",
    "ein": "",
    "year_founded": "",
    "location_served": "",
    "biggest_accomplishment": "",
    "what_we_do_in_one_sentence": "",
    "primary_cause_area": [],  # List of selected cause areas
    "populations": [],  # List of selected populations
    "geographic_focus": ""  # Single selected geographic focus
}

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


def call_llm_to_structure(text: str) -> dict:
    cause_areas_list = ", ".join([f'"{area}"' for area in PRIMARY_CAUSE_AREAS])
    populations_list = ", ".join([f'"{pop}"' for pop in POPULATIONS])
    geographic_focus_list = ", ".join([f'"{focus}"' for focus in GEOGRAPHIC_FOCUS_OPTIONS])
    legal_designation_list = ", ".join([f'"{designation}"' for designation in LEGAL_DESIGNATION_OPTIONS])
    system_prompt = f"""
    You are an information extraction engine.
    Given a proposal or organizational document as raw text, extract the following fields:
    - full_organization_name
    - legal_designation: This should be a single string. Select one legal designation from this exact list: {legal_designation_list}. Match the text as closely as possible to one of these options. Common variations: "501c3" or "501(c)3" should map to "501(c)(3) – Public Charity" or "501(c)(3) – Private Foundation" based on context. "501c4" should map to "501(c)(4) – Social Welfare Organization", etc.
    - mission_statement
    - ein
    - year_founded
    - location_served
    - biggest_accomplishment
    - what_we_do_in_one_sentence
    - primary_cause_area: This should be a JSON array of strings. Select one or more cause areas from this exact list: {cause_areas_list}. Match the text as closely as possible to one of these options. If none match exactly, use "Other".
    - populations: This should be a JSON array of strings. Select one or more populations from this exact list: {populations_list}. Match the text as closely as possible to one of these options. If none match exactly, use "Other".
    - geographic_focus: This should be a single string. Select one geographic focus from this exact list: {geographic_focus_list}. Match the text as closely as possible to one of these options.

    Return ONLY a JSON object with these keys.
    If some value is missing, use an empty string for text fields or an empty array [] for primary_cause_area and populations.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",            # or gpt-4.1-mini, gpt-4o
        temperature=0.1,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": text},
        ],
    )

    content = response.choices[0].message.content

    try:
        data = json.loads(content)
    except Exception:
        st.warning("Invalid JSON; using defaults")
        return DEFAULT_FORM.copy()

    merged = DEFAULT_FORM.copy()
    merged.update({k: v for k, v in data.items() if k in merged})
    
    # Normalize primary_cause_area to always be a list
    if "primary_cause_area" in merged:
        if isinstance(merged["primary_cause_area"], str):
            # If it's a string, try to convert to list or wrap it
            if merged["primary_cause_area"]:
                merged["primary_cause_area"] = [merged["primary_cause_area"]]
            else:
                merged["primary_cause_area"] = []
        elif not isinstance(merged["primary_cause_area"], list):
            merged["primary_cause_area"] = []
    
    # Normalize populations to always be a list
    if "populations" in merged:
        if isinstance(merged["populations"], str):
            # If it's a string, try to convert to list or wrap it
            if merged["populations"]:
                merged["populations"] = [merged["populations"]]
            else:
                merged["populations"] = []
        elif not isinstance(merged["populations"], list):
            merged["populations"] = []
    
    # Normalize geographic_focus to always be a string
    if "geographic_focus" in merged:
        if not isinstance(merged["geographic_focus"], str):
            merged["geographic_focus"] = ""
        # Ensure it's one of the valid options
        if merged["geographic_focus"] and merged["geographic_focus"] not in GEOGRAPHIC_FOCUS_OPTIONS:
            merged["geographic_focus"] = ""
    
    # Normalize legal_designation to always be a string and validate it
    if "legal_designation" in merged:
        if not isinstance(merged["legal_designation"], str):
            merged["legal_designation"] = ""
        # Ensure it's one of the valid options
        if merged["legal_designation"] and merged["legal_designation"] not in LEGAL_DESIGNATION_OPTIONS:
            merged["legal_designation"] = ""
    
    return merged


def render_home_page():
    """Render the home page content."""
    # ----- STREAMLIT APP -----
    if "form_data" not in st.session_state:
        st.session_state.form_data = DEFAULT_FORM.copy()

    st.title("🤖 AI-Powered Form Filler")
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
            if _s3_available:
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

    st.markdown("---")

    st.subheader("Structured Form (Editable)")

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
            if not _db_initialized:
                st.error("⚠️ Database is not available. Please check your database configuration.")
            elif "uploaded_file_info" not in st.session_state:
                st.error("Please upload a file first.")
            else:
                try:
                    db = next(get_db())
                    
                    # Get file path - use S3 key or in-memory marker
                    file_path = st.session_state.uploaded_file_info["saved_path"]
                    
                    # If it's an S3 path, we can optionally store the full URL
                    # For now, we'll store the S3 key (path) which can be used to construct the URL later
                    if file_path and not file_path.startswith("in_memory:"):
                        # It's an S3 key, store it as is
                        pass
                    else:
                        # File wasn't saved to S3, store reference
                        file_path = file_path
                    
                    # Create new submission record
                    submission = ProposalSubmission(
                        file_name=st.session_state.uploaded_file_info["original_name"],
                        file_path=file_path,  # This will be the S3 key or in_memory marker
                        file_type=st.session_state.uploaded_file_info["file_type"],
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
                    db.commit()
                    db.refresh(submission)
                    
                    st.success(f"✅ Saved to database! Submission ID: {submission.id}")
                    st.session_state.last_saved_id = submission.id
                    
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


# ----- SIDEBAR NAVIGATION -----
current_page = render_sidebar()

# ----- PAGE ROUTING -----
if current_page == "page2":
    render_page2()
else:
    render_home_page()
