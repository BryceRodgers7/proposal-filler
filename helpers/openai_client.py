"""
OpenAI client and interactions for the Proposal Filler application.
Handles API key management and LLM calls for extracting structured data from proposals.
"""
import json
import os
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

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


def get_api_key():
    """
    Get OpenAI API key from environment variables or Streamlit secrets.
    
    Returns:
        str or None: API key if found, None otherwise
    """
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


def get_openai_client():
    """
    Get an initialized OpenAI client.
    
    Returns:
        OpenAI: Initialized OpenAI client, or None if API key is not available
    """
    api_key = get_api_key()
    if api_key is None:
        return None
    return OpenAI(api_key=api_key)


def call_llm_to_structure(text: str) -> dict:
    """
    Call OpenAI LLM to extract structured data from proposal text.
    
    Args:
        text (str): Raw text from the proposal document
        
    Returns:
        dict: Structured form data with extracted fields
    """
    client = get_openai_client()
    if client is None:
        st.error("OpenAI API key not found. Please configure your API key.")
        return DEFAULT_FORM.copy()
    
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

    try:
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
    except Exception as e:
        st.error(f"Error calling OpenAI API: {str(e)}")
        return DEFAULT_FORM.copy()

