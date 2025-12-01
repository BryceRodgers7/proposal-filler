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
    
    # Form fields - use widget keys to avoid state conflicts
    st.subheader("Cause Areas")
    st.write("What causes are you most passionate about?")
    
    # Initialize widget keys if not present
    if "donor_primary_cause_areas" not in st.session_state:
        dpd = st.session_state.donor_profile_data
        current_cause_areas = dpd.get("primary_cause_areas", [])
        if isinstance(current_cause_areas, list):
            st.session_state.donor_primary_cause_areas = [area for area in current_cause_areas if area in PRIMARY_CAUSE_AREAS]
        else:
            st.session_state.donor_primary_cause_areas = []
    
    primary_cause_areas = st.multiselect(
        "Primary cause areas",
        options=PRIMARY_CAUSE_AREAS,
        key="donor_primary_cause_areas",
        help="Select all that apply"
    )
    
    st.markdown("---")
    
    st.subheader("Populations")
    st.write("Which populations would you like to support?")
    
    if "donor_populations" not in st.session_state:
        dpd = st.session_state.donor_profile_data
        current_populations = dpd.get("populations", [])
        if isinstance(current_populations, list):
            st.session_state.donor_populations = [pop for pop in current_populations if pop in POPULATIONS]
        else:
            st.session_state.donor_populations = []
    
    populations = st.multiselect(
        "Populations served",
        options=POPULATIONS,
        key="donor_populations",
        help="Select all that apply"
    )
    
    st.markdown("---")
    
    st.subheader("Geographic Focus")
    st.write("Where would you like your donations to have impact?")
    
    if "donor_geographic_focus" not in st.session_state:
        dpd = st.session_state.donor_profile_data
        current_geographic_focus = dpd.get("geographic_focus", "")
        if isinstance(current_geographic_focus, str) and current_geographic_focus in GEOGRAPHIC_FOCUS_OPTIONS:
            st.session_state.donor_geographic_focus = current_geographic_focus
        else:
            st.session_state.donor_geographic_focus = ""
    
    current_geo_focus = st.session_state.donor_geographic_focus
    if current_geo_focus and current_geo_focus in GEOGRAPHIC_FOCUS_OPTIONS:
        geo_index = GEOGRAPHIC_FOCUS_OPTIONS.index(current_geo_focus) + 1
    else:
        geo_index = 0
    
    geographic_focus = st.selectbox(
        "Geographic focus",
        options=[""] + GEOGRAPHIC_FOCUS_OPTIONS,
        index=geo_index,
        format_func=lambda x: "Select..." if x == "" else x,
        key="donor_geographic_focus_selector"
    )
    
    st.markdown("---")
    
    st.subheader("Donation Style")
    st.write("How do you prefer to give?")
    
    if "donor_donation_style" not in st.session_state:
        dpd = st.session_state.donor_profile_data
        current_donation_style = dpd.get("donation_style", [])
        if isinstance(current_donation_style, list):
            st.session_state.donor_donation_style = [style for style in current_donation_style if style in DONATION_STYLE_OPTIONS]
        else:
            st.session_state.donor_donation_style = []
    
    donation_style = st.multiselect(
        "Donation style preferences",
        options=DONATION_STYLE_OPTIONS,
        key="donor_donation_style",
        help="Select all that apply"
    )
    
    st.markdown("---")
    
    st.subheader("Organization Characteristics")
    st.write("What types of organizations do you prefer to support?")
    
    if "donor_org_characteristics" not in st.session_state:
        dpd = st.session_state.donor_profile_data
        current_org_chars = dpd.get("organization_characteristics", [])
        if isinstance(current_org_chars, list):
            st.session_state.donor_org_characteristics = [char for char in current_org_chars if char in ORGANIZATION_CHARACTERISTICS_OPTIONS]
        else:
            st.session_state.donor_org_characteristics = []
    
    organization_characteristics = st.multiselect(
        "Organization characteristics",
        options=ORGANIZATION_CHARACTERISTICS_OPTIONS,
        key="donor_org_characteristics",
        help="Select all that apply"
    )
    
    st.markdown("---")
    
    # Save button
    if st.button("💾 Save Donor Profile", type="primary", use_container_width=True):
        try:
            db = next(get_db())
            
            # Get values from widget keys (not from geographic_focus_selector)
            geo_focus_value = st.session_state.get("donor_geographic_focus_selector", "")
            
            if existing_profile:
                # Update existing profile
                existing_profile.primary_cause_areas = primary_cause_areas
                existing_profile.populations = populations
                existing_profile.geographic_focus = geo_focus_value
                existing_profile.donation_style = donation_style
                existing_profile.organization_characteristics = organization_characteristics
            else:
                # Create new profile
                new_profile = DonorProfile(
                    user_id=user_id,
                    primary_cause_areas=primary_cause_areas,
                    populations=populations,
                    geographic_focus=geo_focus_value,
                    donation_style=donation_style,
                    organization_characteristics=organization_characteristics
                )
                db.add(new_profile)
            
            db.commit()
            
            # Update the main session state data for consistency
            # Note: We don't update the individual widget keys as they're managed by Streamlit
            st.session_state.donor_profile_data = {
                "primary_cause_areas": primary_cause_areas,
                "populations": populations,
                "geographic_focus": geo_focus_value,
                "donation_style": donation_style,
                "organization_characteristics": organization_characteristics
            }
            
            st.success("✅ Donor profile saved successfully!")
            
        except Exception as e:
            st.error(f"Error saving donor profile: {str(e)}")
            db.rollback()
        finally:
            db.close()

