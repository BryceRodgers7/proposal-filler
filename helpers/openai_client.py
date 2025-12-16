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


def generate_organization_card(proposal, existing_cards):
    """
    Generate a unique organization card using AI based on the organization's profile.
    
    Args:
        proposal: ProposalSubmission object with organization data
        existing_cards: List of existing OrganizationCard objects to avoid duplication
        
    Returns:
        dict: {"title": str, "subtitle": str} or None if generation fails
    """
    client = get_openai_client()
    if client is None:
        st.error("OpenAI API key not found. Please configure your API key.")
        return None
    
    # Build context from proposal
    # Prioritize extracted_text if available (from ProposalFiles), otherwise use structured fields
    context_parts = []
    
    # Check if this proposal has extracted_text (from ProposalFile)
    if hasattr(proposal, 'extracted_text') and proposal.extracted_text:
        # Use the full extracted text as the primary context
        context_parts.append("=== PROPOSAL DOCUMENT ===")
        context_parts.append(proposal.extracted_text)
        context_parts.append("=== END PROPOSAL ===")
        
        # Also include organization name if available
        if hasattr(proposal, 'full_organization_name') and proposal.full_organization_name:
            context_parts.append(f"\nOrganization Name: {proposal.full_organization_name}")
    else:
        # Fall back to structured fields (legacy ProposalSubmission)
        if proposal.full_organization_name:
            context_parts.append(f"Organization Name: {proposal.full_organization_name}")
        
        if proposal.mission_statement:
            context_parts.append(f"Mission: {proposal.mission_statement}")
        
        if proposal.what_we_do_in_one_sentence:
            context_parts.append(f"What We Do: {proposal.what_we_do_in_one_sentence}")
        
        if proposal.biggest_accomplishment:
            context_parts.append(f"Biggest Accomplishment: {proposal.biggest_accomplishment}")
        
        if proposal.primary_cause_area:
            if isinstance(proposal.primary_cause_area, list):
                context_parts.append(f"Cause Areas: {', '.join(proposal.primary_cause_area)}")
            else:
                context_parts.append(f"Cause Areas: {proposal.primary_cause_area}")
        
        if proposal.populations:
            if isinstance(proposal.populations, list):
                context_parts.append(f"Populations Served: {', '.join(proposal.populations)}")
            else:
                context_parts.append(f"Populations Served: {proposal.populations}")
        
        if proposal.location_served:
            context_parts.append(f"Location: {proposal.location_served}")
    
    context_text = "\n".join(context_parts)
    
    # Build list of existing card content to avoid duplication
    existing_content = []
    for card in existing_cards:
        existing_content.append(f"Title: {card.title}")
        if card.subtitle:
            existing_content.append(f"Subtitle: {card.subtitle}")
    
    existing_text = "\n".join(existing_content) if existing_content else "None"
    
    system_prompt = f"""
    You are a copywriting expert specializing in nonprofit marketing and donor engagement.
    
    Your task is to create a compelling organization card that will appeal to potential donors.
    The card should highlight a specific accomplishment, impact, or unique aspect of the organization.
    
    You will receive either a full proposal document or structured organization information.
    Extract the most compelling details to create an engaging card.
    
    IMPORTANT: Create a card that is DIFFERENT from any existing cards for this organization.
    
    Existing cards for this organization:
    {existing_text}
    
    Requirements:
    - Title: Create a compelling, donor-focused headline (max 100 characters). Should be punchy and highlight impact.
    - Subtitle: Provide specific details or context (max 300 characters). Should tell a story or show concrete results.
    - Focus on accomplishments, impact metrics, beneficiaries helped, or unique strengths
    - Make it emotionally engaging but authentic
    - Extract specific numbers, stories, or outcomes from the proposal if available
    - Do NOT repeat content from existing cards
    - If this is the first card, focus on the organization's biggest accomplishment or primary mission
    - If this is the second card, focus on a different aspect (e.g., populations served, mission impact, specific programs)
    - If this is the third card, highlight another unique angle (e.g., community reach, innovation, scale of impact)
    
    Return ONLY a JSON object with these keys: "title" and "subtitle"

    IMPORTANT LENGTH CONSTRAINT:
    - The subtitle MUST be 300 characters or fewer, INCLUDING spaces.
    - You MUST count characters before responding.
    - If the subtitle exceeds 300 characters, you MUST rewrite it until it is within the limit.
    - Do NOT exceed the limit under any circumstances.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.7,  # Higher temperature for more creative variation
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": context_text},
            ],
        )
        
        content = response.choices[0].message.content
        
        try:
            data = json.loads(content)
            
            # Validate required fields
            if "title" not in data or "subtitle" not in data:
                st.error("AI response missing required fields")
                return None
            
            # Truncate to max lengths if needed
            data["title"] = data["title"][:100] if data["title"] else ""
            data["subtitle"] = data["subtitle"][:300] if data["subtitle"] else ""
            
            return data
        except json.JSONDecodeError:
            st.error("Invalid JSON response from AI")
            return None
    
    except Exception as e:
        st.error(f"Error generating card with AI: {str(e)}")
        return None
