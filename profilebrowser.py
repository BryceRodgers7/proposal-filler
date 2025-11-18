import streamlit as st
from db import get_db, ProposalSubmission


def render_profile_browser():
    """
    Render a read-only browser page for viewing all proposal submissions.
    """
    st.title("📋 Profile Browser")
    st.write("Browse all proposal submissions in the database (read-only)")
    
    # Fetch all proposals from database
    try:
        db = next(get_db())
        proposals = db.query(ProposalSubmission).order_by(ProposalSubmission.created_at.desc()).all()
        db.close()
    except Exception as e:
        st.error(f"Error loading proposals: {str(e)}")
        proposals = []
    
    if not proposals:
        st.warning("No proposals found in the database. Please add some proposals first.")
        return
    
    # Display total count
    st.info(f"Total submissions: {len(proposals)}")
    
    # Search/filter functionality
    search_term = st.text_input("🔍 Search by organization name, EIN, or location", "")
    
    # Filter proposals based on search
    filtered_proposals = proposals
    if search_term:
        search_lower = search_term.lower()
        filtered_proposals = [
            p for p in proposals
            if (p.full_organization_name and search_lower in p.full_organization_name.lower())
            or (p.ein and search_lower in p.ein.lower())
            or (p.location_served and search_lower in p.location_served.lower())
        ]
        st.caption(f"Showing {len(filtered_proposals)} of {len(proposals)} submissions")
    
    if not filtered_proposals:
        st.warning("No proposals match your search criteria.")
        return
    
    # Display proposals in expandable sections
    for idx, proposal in enumerate(filtered_proposals, 1):
        with st.expander(
            f"#{proposal.id} - {proposal.full_organization_name or 'Unnamed Organization'}",
            expanded=False
        ):
            # Organize fields into columns
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Basic Information")
                st.write(f"**Organization Name:** {proposal.full_organization_name or 'N/A'}")
                st.write(f"**Legal Designation:** {proposal.legal_designation or 'N/A'}")
                st.write(f"**EIN:** {proposal.ein or 'N/A'}")
                st.write(f"**Year Founded:** {proposal.year_founded or 'N/A'}")
                st.write(f"**Location Served:** {proposal.location_served or 'N/A'}")
                st.write(f"**Geographic Focus:** {proposal.geographic_focus or 'N/A'}")
            
            with col2:
                st.markdown("### File Information")
                st.write(f"**File Name:** {proposal.file_name or 'N/A'}")
                st.write(f"**File Type:** {proposal.file_type or 'N/A'}")
                st.write(f"**File Path:** {proposal.file_path or 'N/A'}")
                st.write(f"**Created At:** {proposal.created_at.strftime('%Y-%m-%d %H:%M:%S') if proposal.created_at else 'N/A'}")
                st.write(f"**Updated At:** {proposal.updated_at.strftime('%Y-%m-%d %H:%M:%S') if proposal.updated_at else 'N/A'}")
            
            # Full-width fields
            st.markdown("### Mission & Description")
            if proposal.mission_statement:
                st.write(f"**Mission Statement:**")
                st.info(proposal.mission_statement)
            else:
                st.write("**Mission Statement:** N/A")
            
            if proposal.what_we_do_in_one_sentence:
                st.write(f"**What We Do (One Sentence):**")
                st.info(proposal.what_we_do_in_one_sentence)
            else:
                st.write("**What We Do (One Sentence):** N/A")
            
            if proposal.biggest_accomplishment:
                st.write(f"**Biggest Accomplishment:**")
                st.info(proposal.biggest_accomplishment)
            else:
                st.write("**Biggest Accomplishment:** N/A")
            
            # Cause areas and populations
            col3, col4 = st.columns(2)
            
            with col3:
                st.markdown("### Primary Cause Area(s)")
                if proposal.primary_cause_area:
                    if isinstance(proposal.primary_cause_area, list):
                        for area in proposal.primary_cause_area:
                            st.write(f"• {area}")
                    else:
                        st.write(str(proposal.primary_cause_area))
                else:
                    st.write("N/A")
            
            with col4:
                st.markdown("### Population(s)")
                if proposal.populations:
                    if isinstance(proposal.populations, list):
                        for pop in proposal.populations:
                            st.write(f"• {pop}")
                    else:
                        st.write(str(proposal.populations))
                else:
                    st.write("N/A")
            
            # Extracted text (if available)
            if proposal.extracted_text:
                st.markdown("### Extracted Text")
                st.text_area(
                    "Raw extracted text from document",
                    proposal.extracted_text,
                    height=200,
                    disabled=True,
                    key=f"extracted_text_{proposal.id}"
                )
            
            st.markdown("---")

