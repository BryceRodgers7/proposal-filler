"""
Authentication module for user login and registration with email verification.
"""
import secrets
from datetime import datetime, timedelta, timezone
import streamlit as st
from helpers.db import get_db, User
from helpers.email import send_verification_email, send_verification_resent_email


# Constants for verification
VERIFICATION_TOKEN_EXPIRY_HOURS = 2
RESEND_COOLDOWN_MINUTES = 5


def is_authenticated():
    """
    Check if the current user is authenticated.
    
    Returns:
        bool: True if user is logged in, False otherwise
    """
    return st.session_state.get("user_id") is not None


def get_current_user_id():
    """
    Get the current logged-in user's ID.
    
    Returns:
        int or None: User ID if authenticated, None otherwise
    """
    return st.session_state.get("user_id")


def get_current_user():
    """
    Get the current logged-in user object.
    
    Returns:
        User or None: User object if authenticated, None otherwise
    """
    user_id = get_current_user_id()
    if user_id is None:
        return None
    
    try:
        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        db.close()
        return user
    except Exception:
        return None


def get_current_user_type():
    """
    Get the current logged-in user's type.
    
    Returns:
        str or None: User type ("representative" or "donor") if authenticated, None otherwise
    """
    return st.session_state.get("user_type")


def generate_verification_token():
    """
    Generate a secure verification token.
    
    Returns:
        str: A URL-safe token
    """
    return secrets.token_urlsafe(32)


def login(username, password):
    """
    Authenticate a user with username and password.
    Blocks login if user is not verified.
    
    Args:
        username (str): Username
        password (str): Plain text password
        
    Returns:
        tuple: (success: bool, message: str, user: User or None)
               On unverified user, returns (False, "unverified", user) to allow resend flow
    """
    if not username or not password:
        return False, "Username and password are required", None
    
    try:
        db = next(get_db())
        user = db.query(User).filter(User.username == username).first()
        db.close()
        
        if user is None:
            return False, "Invalid username or password", None
        
        if not user.check_password(password):
            return False, "Invalid username or password", None
        
        # Check if user is verified
        if not user.is_verified:
            # Store user info for resend flow (but don't log them in)
            st.session_state.unverified_user_id = user.id
            st.session_state.unverified_username = user.username
            st.session_state.unverified_email = user.email
            return False, "unverified", user
        
        # Set user in session state
        st.session_state.user_id = user.id
        st.session_state.username = user.username
        st.session_state.user_type = user.user_type
        
        # Clear any unverified session data
        if "unverified_user_id" in st.session_state:
            del st.session_state.unverified_user_id
        if "unverified_username" in st.session_state:
            del st.session_state.unverified_username
        if "unverified_email" in st.session_state:
            del st.session_state.unverified_email
        
        return True, "Login successful", user
    except Exception as e:
        return False, f"Error during login: {str(e)}", None


def register(username, email, password, confirm_password, user_type="representative",
             first_name=None, last_name=None, company=None, street_address=None, 
             city=None, state=None, zip_code=None, phone_number=None):
    """
    Register a new user with email verification.
    User is NOT automatically logged in - they must verify email first.
    
    Args:
        username (str): Username
        email (str): Email address
        password (str): Plain text password
        confirm_password (str): Password confirmation
        user_type (str): User type ("representative" or "donor")
        first_name (str): First name (required)
        last_name (str): Last name (required)
        company (str): Company name (optional)
        street_address (str): Street address (required)
        city (str): City (required)
        state (str): State (required)
        zip_code (str): ZIP code (required)
        phone_number (str): Phone number (optional)
        
    Returns:
        tuple: (success: bool, message: str, user: User or None)
    """
    # Validation
    if not username or not email or not password:
        return False, "Username, email, and password are required", None
    
    # Validate required user details
    if not first_name or not first_name.strip():
        return False, "First name is required", None
    
    if not last_name or not last_name.strip():
        return False, "Last name is required", None
    
    if not street_address or not street_address.strip():
        return False, "Street address is required", None
    
    if not city or not city.strip():
        return False, "City is required", None
    
    if not state or not state.strip():
        return False, "State is required", None
    
    if not zip_code or not zip_code.strip():
        return False, "ZIP code is required", None
    
    if password != confirm_password:
        return False, "Passwords do not match", None
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters long", None
    
    if user_type not in ["representative", "donor"]:
        return False, "Invalid user type", None
    
    try:
        db = next(get_db())
        
        # Check if username already exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            db.close()
            return False, "Username already exists", None
        
        # Check if email already exists
        existing_email = db.query(User).filter(User.email == email).first()
        if existing_email:
            db.close()
            return False, "Email already exists", None
        
        # Generate verification token
        token = generate_verification_token()
        token_expiry = datetime.now(timezone.utc) + timedelta(hours=VERIFICATION_TOKEN_EXPIRY_HOURS)
        
        # Create new user with verification fields and user details
        user = User(
            username=username, 
            email=email, 
            account_tier="free", 
            user_type=user_type,
            is_verified=False,
            email_verification_token=token,
            email_verification_expires=token_expiry,
            verification_sent_at=datetime.now(timezone.utc),
            verification_attempts=1,  # First attempt
            verification_max_attempts=5,
            # User details
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            company=company.strip() if company else None,
            street_address=street_address.strip(),
            city=city.strip(),
            state=state.strip(),
            zip_code=zip_code.strip(),
            phone_number=phone_number.strip() if phone_number else None,
            is_deleted=False
        )
        user.set_password(password)
        
        db.add(user)
        db.commit()
        db.refresh(user)
        db.close()
        
        # Send verification email
        email_sent, email_msg = send_verification_email(email, username, token)
        
        if email_sent:
            return True, "Registration successful! Please check your email to verify your account.", user
        else:
            # User was created but email failed - they can use resend
            return True, f"Account created but we couldn't send the verification email. Please use the resend option. ({email_msg})", user
            
    except Exception as e:
        return False, f"Error during registration: {str(e)}", None


def verify_email_token(token):
    """
    Verify an email verification token and activate the user account.
    Also creates empty profile records for the user to enable image uploads.
    
    Args:
        token (str): The verification token from the email link
        
    Returns:
        tuple: (success: bool, message: str, user: User or None)
    """
    from helpers.db import ProposalSubmission, DonorProfile
    
    if not token:
        return False, "No verification token provided", None
    
    try:
        db = next(get_db())
        
        # Find user with this token
        user = db.query(User).filter(User.email_verification_token == token).first()
        
        if user is None:
            db.close()
            return False, "Invalid verification token. The link may have already been used or is incorrect.", None
        
        # Check if already verified
        if user.is_verified:
            db.close()
            return True, "Your email has already been verified. You can now log in.", user
        
        # Check if token is expired
        if user.email_verification_expires and datetime.now(timezone.utc) > user.email_verification_expires:
            db.close()
            return False, "Verification link has expired. Please request a new one.", None
        
        # Verify the user
        user.is_verified = True
        user.email_verification_token = None
        user.email_verification_expires = None
        
        # Create empty profile based on user type
        if user.user_type == "representative":
            # Check if proposal submission already exists
            existing_proposal = db.query(ProposalSubmission).filter(
                ProposalSubmission.user_id == user.id
            ).first()
            
            if not existing_proposal:
                # Create empty proposal submission for image upload
                empty_proposal = ProposalSubmission(
                    user_id=user.id,
                    file_name="",  # Will be updated when user completes profile
                    file_path="",
                    file_type="",
                    is_deleted=False
                )
                db.add(empty_proposal)
        
        elif user.user_type == "donor":
            # Check if donor profile already exists
            existing_profile = db.query(DonorProfile).filter(
                DonorProfile.user_id == user.id
            ).first()
            
            if not existing_profile:
                # Create empty donor profile for image upload
                empty_profile = DonorProfile(
                    user_id=user.id,
                    is_deleted=False
                )
                db.add(empty_profile)
        
        db.commit()
        db.refresh(user)
        db.close()
        
        return True, "Email verified successfully! You can now log in.", user
    except Exception as e:
        return False, f"Error verifying email: {str(e)}", None


def can_resend_verification(user_id):
    """
    Check if a user can resend verification email.
    
    Args:
        user_id (int): The user ID
        
    Returns:
        tuple: (can_resend: bool, message: str, wait_seconds: int or None)
    """
    try:
        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        db.close()
        
        if user is None:
            return False, "User not found", None
        
        if user.is_verified:
            return False, "Email already verified", None
        
        # Check max attempts
        if user.verification_attempts >= user.verification_max_attempts:
            return False, f"Maximum verification attempts ({user.verification_max_attempts}) reached. Please contact support.", None
        
        # Check cooldown (5 minutes)
        if user.verification_sent_at:
            cooldown_end = user.verification_sent_at + timedelta(minutes=RESEND_COOLDOWN_MINUTES)
            now = datetime.now(timezone.utc)
            
            if now < cooldown_end:
                wait_seconds = int((cooldown_end - now).total_seconds())
                return False, f"Please wait before requesting another verification email", wait_seconds
        
        return True, "Can resend verification email", None
    except Exception as e:
        return False, f"Error checking resend status: {str(e)}", None


def resend_verification_email(user_id):
    """
    Resend verification email to a user.
    
    Args:
        user_id (int): The user ID
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # First check if we can resend
    can_resend, msg, wait_seconds = can_resend_verification(user_id)
    
    if not can_resend:
        if wait_seconds:
            minutes = wait_seconds // 60
            seconds = wait_seconds % 60
            return False, f"Please wait {minutes}m {seconds}s before requesting another email"
        return False, msg
    
    try:
        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        
        if user is None:
            db.close()
            return False, "User not found"
        
        # Generate new token
        new_token = generate_verification_token()
        new_expiry = datetime.now(timezone.utc) + timedelta(hours=VERIFICATION_TOKEN_EXPIRY_HOURS)
        
        # Update user
        user.email_verification_token = new_token
        user.email_verification_expires = new_expiry
        user.verification_sent_at = datetime.now(timezone.utc)
        user.verification_attempts += 1
        
        db.commit()
        
        attempts_remaining = user.verification_max_attempts - user.verification_attempts
        
        db.close()
        
        # Send email
        email_sent, email_msg = send_verification_resent_email(
            user.email, 
            user.username, 
            new_token, 
            attempts_remaining
        )
        
        if email_sent:
            return True, f"Verification email sent! You have {attempts_remaining} resend attempt(s) remaining."
        else:
            return False, f"Failed to send email: {email_msg}"
            
    except Exception as e:
        return False, f"Error resending verification: {str(e)}"


def get_user_by_id(user_id):
    """
    Get a user by their ID.
    
    Args:
        user_id (int): User ID
        
    Returns:
        User or None: User object if found, None otherwise
    """
    try:
        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        db.close()
        return user
    except Exception:
        return None


def logout():
    """
    Log out the current user.
    """
    if "user_id" in st.session_state:
        del st.session_state.user_id
    if "username" in st.session_state:
        del st.session_state.username
    if "user_type" in st.session_state:
        del st.session_state.user_type
    # Clear unverified session data too
    if "unverified_user_id" in st.session_state:
        del st.session_state.unverified_user_id
    if "unverified_username" in st.session_state:
        del st.session_state.unverified_username
    if "unverified_email" in st.session_state:
        del st.session_state.unverified_email
    # Clear AI-generated card content
    if "ai_generated_title" in st.session_state:
        del st.session_state.ai_generated_title
    if "ai_generated_subtitle" in st.session_state:
        del st.session_state.ai_generated_subtitle
    # Clear card creator editing state
    keys_to_delete = [key for key in st.session_state.keys() if key.startswith("editing_card_")]
    for key in keys_to_delete:
        del st.session_state[key]


def get_user_account_tier(user_id=None):
    """
    Get the account tier for a user.
    
    Args:
        user_id (int, optional): User ID. If None, uses current logged-in user.
        
    Returns:
        str: Account tier (e.g., "free", "premium", "enterprise") or None if user not found
    """
    if user_id is None:
        user_id = get_current_user_id()
    
    if user_id is None:
        return None
    
    try:
        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        db.close()
        
        if user:
            return user.account_tier
        return None
    except Exception:
        return None


def has_account_tier(user_id=None, required_tier="premium"):
    """
    Check if a user has at least the required account tier.
    Tier hierarchy: free < premium < enterprise
    
    Args:
        user_id (int, optional): User ID. If None, uses current logged-in user.
        required_tier (str): Required tier level ("free", "premium", or "enterprise")
        
    Returns:
        bool: True if user has the required tier or higher, False otherwise
    """
    tier_hierarchy = {"free": 1, "premium": 2, "enterprise": 3}
    
    user_tier = get_user_account_tier(user_id)
    if user_tier is None:
        return False
    
    user_level = tier_hierarchy.get(user_tier.lower(), 0)
    required_level = tier_hierarchy.get(required_tier.lower(), 999)
    
    return user_level >= required_level


def update_user_details(user_id, first_name=None, last_name=None, company=None, 
                        street_address=None, city=None, state=None, zip_code=None, 
                        phone_number=None):
    """
    Update user details for an existing user.
    
    Args:
        user_id (int): User ID
        first_name (str): First name
        last_name (str): Last name
        company (str): Company name (optional)
        street_address (str): Street address
        city (str): City
        state (str): State
        zip_code (str): ZIP code
        phone_number (str): Phone number (optional)
        
    Returns:
        tuple: (success: bool, message: str)
    """
    if not first_name or not first_name.strip():
        return False, "First name is required"
    
    if not last_name or not last_name.strip():
        return False, "Last name is required"
    
    if not street_address or not street_address.strip():
        return False, "Street address is required"
    
    if not city or not city.strip():
        return False, "City is required"
    
    if not state or not state.strip():
        return False, "State is required"
    
    if not zip_code or not zip_code.strip():
        return False, "ZIP code is required"
    
    try:
        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        
        if user is None:
            db.close()
            return False, "User not found"
        
        user.first_name = first_name.strip()
        user.last_name = last_name.strip()
        user.company = company.strip() if company else None
        user.street_address = street_address.strip()
        user.city = city.strip()
        user.state = state.strip()
        user.zip_code = zip_code.strip()
        user.phone_number = phone_number.strip() if phone_number else None
        
        db.commit()
        db.close()
        
        return True, "Account details updated successfully"
    except Exception as e:
        return False, f"Error updating account details: {str(e)}"


def soft_delete_user(user_id):
    """
    Soft-delete a user account and their associated profiles.
    Sets is_deleted=True on user, their donor_profile, and proposal_submissions.
    
    Args:
        user_id (int): User ID
        
    Returns:
        tuple: (success: bool, message: str)
    """
    from helpers.db import DonorProfile, ProposalSubmission
    
    try:
        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        
        if user is None:
            db.close()
            return False, "User not found"
        
        # Soft-delete the user
        user.is_deleted = True
        
        # Soft-delete associated donor profile (if exists)
        donor_profile = db.query(DonorProfile).filter(DonorProfile.user_id == user_id).first()
        if donor_profile:
            donor_profile.is_deleted = True
        
        # Soft-delete associated proposal submissions
        proposals = db.query(ProposalSubmission).filter(ProposalSubmission.user_id == user_id).all()
        for proposal in proposals:
            proposal.is_deleted = True
        
        db.commit()
        db.close()
        
        return True, "Account has been deactivated"
    except Exception as e:
        return False, f"Error deactivating account: {str(e)}"


def reactivate_user(user_id):
    """
    Reactivate a soft-deleted user account and their associated profiles.
    Sets is_deleted=False on user, their donor_profile, and proposal_submissions.
    
    Args:
        user_id (int): User ID
        
    Returns:
        tuple: (success: bool, message: str)
    """
    from helpers.db import DonorProfile, ProposalSubmission
    
    try:
        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        
        if user is None:
            db.close()
            return False, "User not found"
        
        # Reactivate the user
        user.is_deleted = False
        
        # Reactivate associated donor profile (if exists)
        donor_profile = db.query(DonorProfile).filter(DonorProfile.user_id == user_id).first()
        if donor_profile:
            donor_profile.is_deleted = False
        
        # Reactivate associated proposal submissions
        proposals = db.query(ProposalSubmission).filter(ProposalSubmission.user_id == user_id).all()
        for proposal in proposals:
            proposal.is_deleted = False
        
        db.commit()
        db.close()
        
        return True, "Account has been reactivated"
    except Exception as e:
        return False, f"Error reactivating account: {str(e)}"


def is_user_deleted(user_id=None):
    """
    Check if a user account is soft-deleted.
    
    Args:
        user_id (int, optional): User ID. If None, uses current logged-in user.
        
    Returns:
        bool: True if user is soft-deleted, False otherwise
    """
    if user_id is None:
        user_id = get_current_user_id()
    
    if user_id is None:
        return False
    
    try:
        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        db.close()
        
        if user:
            return user.is_deleted
        return False
    except Exception:
        return False
