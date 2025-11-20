import stripe
import streamlit as st
import os

stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]


def get_app_url():
    """
    Determine the correct app URL based on the environment.
    Returns the URL that should be used for Stripe redirects.
    """
    # First, check if APP_URL is explicitly set in secrets
    if "APP_URL" in st.secrets:
        return st.secrets["APP_URL"]
    
    # Check if we're running locally vs on Streamlit Cloud
    # Streamlit Cloud sets STREAMLIT_SHARING_MODE to "SHARED"
    is_cloud = os.environ.get("STREAMLIT_SHARING_MODE") == "SHARED"
    
    if not is_cloud:
        # Running locally - use localhost
        # Note: The default Streamlit port is 8501
        # You can override this by setting LOCAL_APP_URL in secrets
        local_url = st.secrets.get("LOCAL_APP_URL", "http://localhost:8501")
        return local_url
    
    # Running on Streamlit Cloud - use production URL
    return "https://nonprofit-tinder.streamlit.app"


def create_checkout_session(user):
    """
    Create a Stripe checkout session for upgrading to premium.
    
    Args:
        user: User object from the database
        
    Returns:
        str: Checkout session URL
    """
    # Get the app URL based on environment
    app_url = get_app_url()
    
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{
            "price": st.secrets["STRIPE_PRICE_ID"],
            "quantity": 1,
        }],
        customer_email=user.email,
        success_url=f"{app_url}/?checkout=success",
        cancel_url=f"{app_url}/?checkout=cancel",
        metadata={
            "user_id": str(user.id),  # Store user ID for webhook processing
        },
    )
    return session.url
