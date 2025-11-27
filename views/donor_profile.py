"""
Donor profile page for managing donor preferences and giving criteria.
"""
import streamlit as st
from helpers.db import get_db, DonorProfile
from helpers.auth import get_current_user_id
from helpers.openai_client import PRIMARY_CAUSE_AREAS, POPULATIONS, GEOGRAPHIC_FOCUS_OPTIONS

# Donor-specific options
DONATION_STYLE_OPTIONS = [
    "One-Time Donations",
    "Recurring/Monthly Donations",
    "Operating Support",
    "Project-Based Funding",
    "Endowment Gifts",
    "Matching Gifts"
]

ORGANIZATION_CHARACTERISTICS_OPTIONS = [
    "Large Organizations",
    "Small Organizations",
    "Established Organizations",
    "Startup/New Organizations",
    "Direct Service Organizations",
    "Advocacy Organizations",
    "Research Organizations",
    "Grassroots Organizations",
    "Faith-Based Organizations",
    "Secular Organizations"
]


def render_donor_profile_page():
    """
    Render the donor profile page where donors can fill out their preferences.
    """
    st.title("💰 My Donor Profile")
    st.write("Tell us about your giving preferences so we can help you find the right organizations.")
    
    # Get current user ID
    user_id = get_current_user_id()
    if user_id is None:
        st.error("You must be logged in to access this page.")
        return
    
    # Check if user is a donor
    user_type = st.session_state.get("user_type", "representative")
    if user_type != "donor":
        st.error("❌ This page is only accessible to donors. Representatives should use the 'Organization Profile' page instead.")
        return
    
    # Load existing donor profile if it exists
    existing_profile = None
    try:
        db = next(get_db())
        existing_profile = db.query(DonorProfile).filter(
            DonorProfile.user_id == user_id
        ).first()
        db.close()
    except Exception as e:
        st.error(f"Error loading donor profile: {str(e)}")
    
    # Initialize form data
    if "donor_profile_data" not in st.session_state or st.session_state.get("donor_profile_user_id") != user_id:
        if existing_profile:
            st.session_state.donor_profile_data = {
                "primary_cause_areas": existing_profile.primary_cause_areas if isinstance(existing_profile.primary_cause_areas, list) else [],
                "populations": existing_profile.populations if isinstance(existing_profile.populations, list) else [],
                "geographic_focus": existing_profile.geographic_focus or "",
                "donation_style": existing_profile.donation_style if isinstance(existing_profile.donation_style, list) else [],
                "organization_characteristics": existing_profile.organization_characteristics if isinstance(existing_profile.organization_characteristics, list) else []
            }
        else:
            st.session_state.donor_profile_data = {
                "primary_cause_areas": [],
                "populations": [],
                "geographic_focus": "",
                "donation_style": [],
                "organization_characteristics": []
            }
        st.session_state.donor_profile_user_id = user_id
    
    # Show info if editing existing profile
    if existing_profile:
        st.info(f"📝 Editing your donor profile. Update your preferences below.")
    else:
        st.info("👋 Welcome! Let's create your donor profile to help match you with organizations.")
    
    st.markdown("---")
    
    # Form fields
    dpd = st.session_state.donor_profile_data
    
    st.subheader("Cause Areas")
    st.write("What causes are you most passionate about?")
    current_cause_areas = dpd.get("primary_cause_areas", [])
    if not isinstance(current_cause_areas, list):
        current_cause_areas = []
    current_cause_areas = [area for area in current_cause_areas if area in PRIMARY_CAUSE_AREAS]
    dpd["primary_cause_areas"] = st.multiselect(
        "Primary cause areas",
        options=PRIMARY_CAUSE_AREAS,
        default=current_cause_areas,
        help="Select all that apply"
    )
    
    st.markdown("---")
    
    st.subheader("Populations")
    st.write("Which populations would you like to support?")
    current_populations = dpd.get("populations", [])
    if not isinstance(current_populations, list):
        current_populations = []
    current_populations = [pop for pop in current_populations if pop in POPULATIONS]
    dpd["populations"] = st.multiselect(
        "Populations served",
        options=POPULATIONS,
        default=current_populations,
        help="Select all that apply"
    )
    
    st.markdown("---")
    
    st.subheader("Geographic Focus")
    st.write("Where would you like your donations to have impact?")
    current_geographic_focus = dpd.get("geographic_focus", "")
    if not isinstance(current_geographic_focus, str):
        current_geographic_focus = ""
    if current_geographic_focus not in GEOGRAPHIC_FOCUS_OPTIONS:
        current_geographic_focus = ""
    
    if current_geographic_focus and current_geographic_focus in GEOGRAPHIC_FOCUS_OPTIONS:
        geo_index = GEOGRAPHIC_FOCUS_OPTIONS.index(current_geographic_focus) + 1
    else:
        geo_index = 0
    
    dpd["geographic_focus"] = st.selectbox(
        "Geographic focus",
        options=[""] + GEOGRAPHIC_FOCUS_OPTIONS,
        index=geo_index,
        format_func=lambda x: "Select..." if x == "" else x
    )
    
    st.markdown("---")
    
    st.subheader("Donation Style")
    st.write("How do you prefer to give?")
    current_donation_style = dpd.get("donation_style", [])
    if not isinstance(current_donation_style, list):
        current_donation_style = []
    current_donation_style = [style for style in current_donation_style if style in DONATION_STYLE_OPTIONS]
    dpd["donation_style"] = st.multiselect(
        "Donation style preferences",
        options=DONATION_STYLE_OPTIONS,
        default=current_donation_style,
        help="Select all that apply"
    )
    
    st.markdown("---")
    
    st.subheader("Organization Characteristics")
    st.write("What types of organizations do you prefer to support?")
    current_org_chars = dpd.get("organization_characteristics", [])
    if not isinstance(current_org_chars, list):
        current_org_chars = []
    current_org_chars = [char for char in current_org_chars if char in ORGANIZATION_CHARACTERISTICS_OPTIONS]
    dpd["organization_characteristics"] = st.multiselect(
        "Organization characteristics",
        options=ORGANIZATION_CHARACTERISTICS_OPTIONS,
        default=current_org_chars,
        help="Select all that apply"
    )
    
    st.session_state.donor_profile_data = dpd
    
    st.markdown("---")
    
    # Save button
    if st.button("💾 Save Donor Profile", type="primary", use_container_width=True):
        try:
            db = next(get_db())
            
            if existing_profile:
                # Update existing profile
                existing_profile.primary_cause_areas = dpd.get("primary_cause_areas", [])
                existing_profile.populations = dpd.get("populations", [])
                existing_profile.geographic_focus = dpd.get("geographic_focus", "")
                existing_profile.donation_style = dpd.get("donation_style", [])
                existing_profile.organization_characteristics = dpd.get("organization_characteristics", [])
            else:
                # Create new profile
                new_profile = DonorProfile(
                    user_id=user_id,
                    primary_cause_areas=dpd.get("primary_cause_areas", []),
                    populations=dpd.get("populations", []),
                    geographic_focus=dpd.get("geographic_focus", ""),
                    donation_style=dpd.get("donation_style", []),
                    organization_characteristics=dpd.get("organization_characteristics", [])
                )
                db.add(new_profile)
            
            db.commit()
            st.success("✅ Donor profile saved successfully!")
            
        except Exception as e:
            st.error(f"Error saving donor profile: {str(e)}")
            db.rollback()
        finally:
            db.close()

