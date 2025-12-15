"""
Reset Password page for users with a valid reset token.
"""
import streamlit as st
from helpers.auth import verify_password_reset_token, reset_password_with_token


def render_reset_password_page(token: str):
    """
    Render the reset password page where users can set a new password.
    Uses session state to prevent re-processing the same token.
    
    Args:
        token (str): The password reset token from the URL
    """
    # Track which tokens we've already validated to prevent re-validation
    if "validated_reset_tokens" not in st.session_state:
        st.session_state.validated_reset_tokens = set()
    
    # Track reset success to show appropriate message
    if "reset_password_success" not in st.session_state:
        st.session_state.reset_password_success = False
    
    st.title("🔑 Reset Your Password")
    
    # If password was already reset successfully in this session
    if st.session_state.reset_password_success:
        st.success("✅ Your password has been reset successfully!")
        st.info("You can now log in with your new password.")
        
        if st.button("Go to Login", type="primary", use_container_width=True):
            # Clear the success flag and all reset-related session state
            st.session_state.reset_password_success = False
            if "validated_reset_tokens" in st.session_state:
                del st.session_state.validated_reset_tokens
            if "processed_reset_tokens" in st.session_state:
                del st.session_state.processed_reset_tokens
            if "reset_token_username" in st.session_state:
                del st.session_state.reset_token_username
            st.session_state.page = "login"
            st.rerun()
        
        return
    
    # Validate token only if we haven't validated it before in this session
    if token not in st.session_state.validated_reset_tokens:
        # First time seeing this token - validate it
        valid, message, user = verify_password_reset_token(token)
        
        if not valid or user is None:
            st.error(f"❌ {message}")
            
            if st.button("Request New Reset Link", type="primary", use_container_width=True):
                st.session_state.page = "forgot_password"
                st.rerun()
            
            if st.button("← Back to Login", use_container_width=True):
                st.session_state.page = "login"
                st.rerun()
            
            return
        
        # Token is valid - add to validated set and store user info
        st.session_state.validated_reset_tokens.add(token)
        st.session_state.reset_token_username = user.username
    
    # Show the password reset form
    username = st.session_state.get("reset_token_username", "")
    
    if username:
        st.write(f"Setting new password for: **{username}**")
    
    with st.form("reset_password_form"):
        new_password = st.text_input(
            "New Password",
            type="password",
            key="new_password",
            help="Must be at least 6 characters"
        )
        confirm_password = st.text_input(
            "Confirm New Password",
            type="password",
            key="confirm_password"
        )
        submit = st.form_submit_button("Reset Password", type="primary", use_container_width=True)
        
        if submit:
            if not new_password or not confirm_password:
                st.error("Please fill in both password fields")
            elif new_password != confirm_password:
                st.error("Passwords do not match")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters long")
            else:
                # Reset the password
                success, message = reset_password_with_token(token, new_password, confirm_password)
                
                if success:
                    # Mark token as processed to prevent re-validation
                    if "processed_reset_tokens" not in st.session_state:
                        st.session_state.processed_reset_tokens = set()
                    st.session_state.processed_reset_tokens.add(token)
                    
                    # Mark as successful and clear token from validated set
                    st.session_state.reset_password_success = True
                    if "reset_token_username" in st.session_state:
                        del st.session_state.reset_token_username
                    st.rerun()
                else:
                    st.error(message)
    
    st.markdown("---")
    
    # Back to login button
    if st.button("← Back to Login", use_container_width=True):
        if "reset_token_username" in st.session_state:
            del st.session_state.reset_token_username
        if "validated_reset_tokens" in st.session_state:
            del st.session_state.validated_reset_tokens
        if "processed_reset_tokens" in st.session_state:
            del st.session_state.processed_reset_tokens
        st.session_state.page = "login"
        st.rerun()

