"""
Authentication module for user login and registration.
"""
import streamlit as st
from helpers.db import get_db, User


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


def login(username, password):
    """
    Authenticate a user with username and password.
    
    Args:
        username (str): Username
        password (str): Plain text password
        
    Returns:
        tuple: (success: bool, message: str, user: User or None)
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
        
        # Set user in session state
        st.session_state.user_id = user.id
        st.session_state.username = user.username
        st.session_state.user_type = user.user_type
        
        return True, "Login successful", user
    except Exception as e:
        return False, f"Error during login: {str(e)}", None


def register(username, email, password, confirm_password, user_type="representative"):
    """
    Register a new user.
    
    Args:
        username (str): Username
        email (str): Email address
        password (str): Plain text password
        confirm_password (str): Password confirmation
        user_type (str): User type ("representative" or "donor")
        
    Returns:
        tuple: (success: bool, message: str, user: User or None)
    """
    # Validation
    if not username or not email or not password:
        return False, "All fields are required", None
    
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
        
        # Create new user
        user = User(username=username, email=email, account_tier="free", user_type=user_type)
        user.set_password(password)
        
        db.add(user)
        db.commit()
        db.refresh(user)
        db.close()
        
        # Automatically log in the new user
        st.session_state.user_id = user.id
        st.session_state.username = user.username
        st.session_state.user_type = user.user_type
        
        return True, "Registration successful! You are now logged in.", user
    except Exception as e:
        return False, f"Error during registration: {str(e)}", None


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



