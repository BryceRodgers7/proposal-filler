"""
Script to export all proposal submissions from the database to a CSV file.
"""
import csv
import json
import os
from datetime import datetime
from db import SessionLocal, ProposalSubmission


def export_to_csv(output_file="proposal_submissions.csv"):
    """
    Export all proposal submissions from the database to a CSV file.
    
    Args:
        output_file: Path to the output CSV file
    """
    db = SessionLocal()
    
    try:
        # Query all submissions
        submissions = db.query(ProposalSubmission).order_by(ProposalSubmission.created_at.desc()).all()
        
        if not submissions:
            print("No records found in the database.")
            return
        
        # Define CSV columns
        fieldnames = [
            "id",
            "file_name",
            "file_path",
            "file_type",
            "full_organization_name",
            "legal_designation",
            "mission_statement",
            "ein",
            "year_founded",
            "location_served",
            "biggest_accomplishment",
            "what_we_do_in_one_sentence",
            "primary_cause_area",
            "populations",
            "geographic_focus",
            "created_at",
            "updated_at"
        ]
        
        # Write to CSV
        with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for submission in submissions:
                # Convert JSON fields to readable strings
                primary_cause_area_str = ""
                if submission.primary_cause_area:
                    if isinstance(submission.primary_cause_area, list):
                        primary_cause_area_str = "; ".join(submission.primary_cause_area)
                    else:
                        primary_cause_area_str = str(submission.primary_cause_area)
                
                populations_str = ""
                if submission.populations:
                    if isinstance(submission.populations, list):
                        populations_str = "; ".join(submission.populations)
                    else:
                        populations_str = str(submission.populations)
                
                # Format datetime fields
                created_at_str = submission.created_at.strftime("%Y-%m-%d %H:%M:%S") if submission.created_at else ""
                updated_at_str = submission.updated_at.strftime("%Y-%m-%d %H:%M:%S") if submission.updated_at else ""
                
                writer.writerow({
                    "id": submission.id,
                    "file_name": submission.file_name or "",
                    "file_path": submission.file_path or "",
                    "file_type": submission.file_type or "",
                    "full_organization_name": submission.full_organization_name or "",
                    "legal_designation": submission.legal_designation or "",
                    "mission_statement": submission.mission_statement or "",
                    "ein": submission.ein or "",
                    "year_founded": submission.year_founded or "",
                    "location_served": submission.location_served or "",
                    "biggest_accomplishment": submission.biggest_accomplishment or "",
                    "what_we_do_in_one_sentence": submission.what_we_do_in_one_sentence or "",
                    "primary_cause_area": primary_cause_area_str,
                    "populations": populations_str,
                    "geographic_focus": submission.geographic_focus or "",
                    "created_at": created_at_str,
                    "updated_at": updated_at_str
                })
        
        print(f"✅ Successfully exported {len(submissions)} record(s) to {output_file}")
        
    except Exception as e:
        print(f"❌ Error exporting to CSV: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # Default output file
    output_file = "proposal_submissions.csv"
    
    # Allow command line argument for output file
    import sys
    if len(sys.argv) > 1:
        output_file = sys.argv[1]
    
    export_to_csv(output_file)

