"""
Email module for sending verification and notification emails.
Uses SMTP with SSL for secure email delivery.
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st


def get_smtp_config():
    """
    Get SMTP configuration from Streamlit secrets.
    
    Returns:
        dict: SMTP configuration or None if not configured
    """
    try:
        return {
            "host": st.secrets.get("SMTP_HOST", "smtp.gmail.com"),
            "port": int(st.secrets.get("SMTP_PORT", 465)),
            "user": st.secrets.get("SMTP_USER"),
            "password": st.secrets.get("SMTP_PASS"),
            "from_email": st.secrets.get("EMAIL_FROM"),
        }
    except Exception:
        return None


def get_app_url():
    """
    Get the application URL from secrets or use a default.
    
    Returns:
        str: The application base URL
    """
    # Try to get from secrets, otherwise use a sensible default
    return st.secrets.get("APP_URL", "https://nonprofittinder.streamlit.app")


def send_verification_email(to_email: str, username: str, token: str) -> tuple[bool, str]:
    """
    Send a verification email to a user.
    
    Args:
        to_email (str): Recipient email address
        username (str): Username for personalization
        token (str): Verification token
        
    Returns:
        tuple: (success: bool, message: str)
    """
    config = get_smtp_config()
    
    if not config or not config["user"] or not config["password"]:
        return False, "Email service not configured. Please contact support."
    
    app_url = get_app_url()
    verification_link = f"{app_url}/?page=verify&token={token}"
    
    # Create message
    message = MIMEMultipart("alternative")
    message["Subject"] = "Verify your email - Tinder for Non-Profits"
    message["From"] = config["from_email"]
    message["To"] = to_email
    
    # Plain text version
    text = f"""
Hello {username},

Welcome to Tinder for Non-Profits!

Please verify your email address by clicking the link below:

{verification_link}

This link will expire in 2 hours.

If you did not create an account, please ignore this email.

Best regards,
The Tinder for Non-Profits Team
"""
    
    # HTML version
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td align="center" style="padding: 40px 0;">
                <table role="presentation" style="width: 100%; max-width: 600px; border-collapse: collapse; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 20px; text-align: center; background: linear-gradient(135deg, #10b981 0%, #059669 100%); border-radius: 12px 12px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 700;">💚 Tinder for Non-Profits</h1>
                        </td>
                    </tr>
                    
                    <!-- Body -->
                    <tr>
                        <td style="padding: 40px;">
                            <h2 style="margin: 0 0 20px; color: #1f2937; font-size: 24px; font-weight: 600;">Welcome, {username}!</h2>
                            <p style="margin: 0 0 20px; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                Thank you for joining Tinder for Non-Profits. To get started, please verify your email address by clicking the button below:
                            </p>
                            
                            <!-- CTA Button -->
                            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td align="center" style="padding: 20px 0;">
                                        <a href="{verification_link}" style="display: inline-block; padding: 16px 32px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: #ffffff; text-decoration: none; font-size: 16px; font-weight: 600; border-radius: 8px; box-shadow: 0 4px 14px rgba(16, 185, 129, 0.4);">
                                            ✓ Verify My Email
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="margin: 20px 0 0; color: #6b7280; font-size: 14px; line-height: 1.6;">
                                <strong>Note:</strong> This link will expire in 2 hours.
                            </p>
                            
                            <p style="margin: 20px 0 0; color: #6b7280; font-size: 14px; line-height: 1.6;">
                                If the button doesn't work, copy and paste this link into your browser:
                            </p>
                            <p style="margin: 10px 0 0; color: #10b981; font-size: 12px; word-break: break-all;">
                                {verification_link}
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 40px 40px; text-align: center; border-top: 1px solid #e5e7eb;">
                            <p style="margin: 0; color: #9ca3af; font-size: 12px;">
                                If you did not create an account, you can safely ignore this email.
                            </p>
                            <p style="margin: 10px 0 0; color: #9ca3af; font-size: 12px;">
                                © 2025 Tinder for Non-Profits. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    
    # Attach parts
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    message.attach(part1)
    message.attach(part2)
    
    try:
        # Create secure SSL context
        context = ssl.create_default_context()
        
        # Connect using SSL (port 465)
        with smtplib.SMTP_SSL(config["host"], config["port"], context=context) as server:
            server.login(config["user"], config["password"])
            server.sendmail(config["from_email"], to_email, message.as_string())
        
        return True, "Verification email sent successfully"
    except smtplib.SMTPAuthenticationError:
        return False, "Email authentication failed. Please contact support."
    except smtplib.SMTPRecipientsRefused:
        return False, "Invalid email address. Please check and try again."
    except smtplib.SMTPException as e:
        return False, f"Failed to send email: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error sending email: {str(e)}"


def send_verification_resent_email(to_email: str, username: str, token: str, attempts_remaining: int) -> tuple[bool, str]:
    """
    Send a resent verification email with attempt count.
    
    Args:
        to_email (str): Recipient email address
        username (str): Username for personalization
        token (str): New verification token
        attempts_remaining (int): Number of resend attempts remaining
        
    Returns:
        tuple: (success: bool, message: str)
    """
    config = get_smtp_config()
    
    if not config or not config["user"] or not config["password"]:
        return False, "Email service not configured. Please contact support."
    
    app_url = get_app_url()
    verification_link = f"{app_url}/?page=verify&token={token}"
    
    # Create message
    message = MIMEMultipart("alternative")
    message["Subject"] = "Your new verification link - Tinder for Non-Profits"
    message["From"] = config["from_email"]
    message["To"] = to_email
    
    # Plain text version
    text = f"""
Hello {username},

Here's your new verification link:

{verification_link}

This link will expire in 2 hours.

You have {attempts_remaining} resend attempt(s) remaining.

If you did not request this, please ignore this email.

Best regards,
The Tinder for Non-Profits Team
"""
    
    # HTML version (similar to above but with resend context)
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td align="center" style="padding: 40px 0;">
                <table role="presentation" style="width: 100%; max-width: 600px; border-collapse: collapse; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 20px; text-align: center; background: linear-gradient(135deg, #10b981 0%, #059669 100%); border-radius: 12px 12px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 700;">💚 Tinder for Non-Profits</h1>
                        </td>
                    </tr>
                    
                    <!-- Body -->
                    <tr>
                        <td style="padding: 40px;">
                            <h2 style="margin: 0 0 20px; color: #1f2937; font-size: 24px; font-weight: 600;">New Verification Link</h2>
                            <p style="margin: 0 0 20px; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                Hi {username}, here's your new verification link:
                            </p>
                            
                            <!-- CTA Button -->
                            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td align="center" style="padding: 20px 0;">
                                        <a href="{verification_link}" style="display: inline-block; padding: 16px 32px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: #ffffff; text-decoration: none; font-size: 16px; font-weight: 600; border-radius: 8px; box-shadow: 0 4px 14px rgba(16, 185, 129, 0.4);">
                                            ✓ Verify My Email
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="margin: 20px 0 0; color: #6b7280; font-size: 14px; line-height: 1.6;">
                                <strong>Note:</strong> This link will expire in 2 hours.
                            </p>
                            
                            <p style="margin: 20px 0 0; color: #f59e0b; font-size: 14px; line-height: 1.6;">
                                ⚠️ You have <strong>{attempts_remaining}</strong> resend attempt(s) remaining.
                            </p>
                            
                            <p style="margin: 20px 0 0; color: #6b7280; font-size: 14px; line-height: 1.6;">
                                If the button doesn't work, copy and paste this link into your browser:
                            </p>
                            <p style="margin: 10px 0 0; color: #10b981; font-size: 12px; word-break: break-all;">
                                {verification_link}
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 40px 40px; text-align: center; border-top: 1px solid #e5e7eb;">
                            <p style="margin: 0; color: #9ca3af; font-size: 12px;">
                                If you did not request this, you can safely ignore this email.
                            </p>
                            <p style="margin: 10px 0 0; color: #9ca3af; font-size: 12px;">
                                © 2025 Tinder for Non-Profits. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    
    # Attach parts
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    message.attach(part1)
    message.attach(part2)
    
    try:
        # Create secure SSL context
        context = ssl.create_default_context()
        
        # Connect using SSL (port 465)
        with smtplib.SMTP_SSL(config["host"], config["port"], context=context) as server:
            server.login(config["user"], config["password"])
            server.sendmail(config["from_email"], to_email, message.as_string())
        
        return True, "New verification email sent successfully"
    except smtplib.SMTPAuthenticationError:
        return False, "Email authentication failed. Please contact support."
    except smtplib.SMTPRecipientsRefused:
        return False, "Invalid email address. Please check and try again."
    except smtplib.SMTPException as e:
        return False, f"Failed to send email: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error sending email: {str(e)}"

