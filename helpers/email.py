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
            "host": st.secrets.get("GMAIL_SMTP_HOST", "smtp.gmail.com"),
            "port": int(st.secrets.get("GMAIL_SMTP_PORT", 465)),
            "user": st.secrets.get("GMAIL_SMTP_USER"),
            "password": st.secrets.get("GMAIL_SMTP_PASS"),
            "from_email": st.secrets.get("GMAIL_EMAIL_FROM"),
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


def send_password_reset_email(to_email: str, username: str, token: str) -> tuple[bool, str]:
    """
    Send a password reset email to a user.
    
    Args:
        to_email (str): Recipient email address
        username (str): Username for personalization
        token (str): Password reset token
        
    Returns:
        tuple: (success: bool, message: str)
    """
    config = get_smtp_config()
    
    if not config or not config["user"] or not config["password"]:
        return False, "Email service not configured. Please contact support."
    
    app_url = get_app_url()
    reset_link = f"{app_url}/?page=reset_password&token={token}"
    
    # Create message
    message = MIMEMultipart("alternative")
    message["Subject"] = "Reset your password - Tinder for Non-Profits"
    message["From"] = config["from_email"]
    message["To"] = to_email
    
    # Plain text version
    text = f"""
Hello {username},

You requested to reset your password for Tinder for Non-Profits.

Click the link below to reset your password:

{reset_link}

This link will expire in 1 hour.

If you did not request a password reset, please ignore this email and your password will remain unchanged.

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
                        <td style="padding: 40px 40px 20px; text-align: center; background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); border-radius: 12px 12px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 700;">🔐 Password Reset</h1>
                        </td>
                    </tr>
                    
                    <!-- Body -->
                    <tr>
                        <td style="padding: 40px;">
                            <h2 style="margin: 0 0 20px; color: #1f2937; font-size: 24px; font-weight: 600;">Hi {username},</h2>
                            <p style="margin: 0 0 20px; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                You requested to reset your password for Tinder for Non-Profits. Click the button below to create a new password:
                            </p>
                            
                            <!-- CTA Button -->
                            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td align="center" style="padding: 20px 0;">
                                        <a href="{reset_link}" style="display: inline-block; padding: 16px 32px; background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: #ffffff; text-decoration: none; font-size: 16px; font-weight: 600; border-radius: 8px; box-shadow: 0 4px 14px rgba(245, 158, 11, 0.4);">
                                            🔑 Reset My Password
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="margin: 20px 0 0; color: #6b7280; font-size: 14px; line-height: 1.6;">
                                <strong>Note:</strong> This link will expire in 1 hour.
                            </p>
                            
                            <p style="margin: 20px 0 0; color: #6b7280; font-size: 14px; line-height: 1.6;">
                                If the button doesn't work, copy and paste this link into your browser:
                            </p>
                            <p style="margin: 10px 0 0; color: #f59e0b; font-size: 12px; word-break: break-all;">
                                {reset_link}
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 40px 40px; text-align: center; border-top: 1px solid #e5e7eb;">
                            <p style="margin: 0; color: #9ca3af; font-size: 12px;">
                                If you did not request a password reset, you can safely ignore this email.
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
        
        return True, "Password reset email sent successfully"
    except smtplib.SMTPAuthenticationError:
        return False, "Email authentication failed. Please contact support."
    except smtplib.SMTPRecipientsRefused:
        return False, "Invalid email address. Please check and try again."
    except smtplib.SMTPException as e:
        return False, f"Failed to send email: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error sending email: {str(e)}"


def send_username_reminder_email(to_email: str, username: str) -> tuple[bool, str]:
    """
    Send a username reminder email to a user.
    
    Args:
        to_email (str): Recipient email address
        username (str): The user's username
        
    Returns:
        tuple: (success: bool, message: str)
    """
    config = get_smtp_config()
    
    if not config or not config["user"] or not config["password"]:
        return False, "Email service not configured. Please contact support."
    
    app_url = get_app_url()
    
    # Create message
    message = MIMEMultipart("alternative")
    message["Subject"] = "Your username - Tinder for Non-Profits"
    message["From"] = config["from_email"]
    message["To"] = to_email
    
    # Plain text version
    text = f"""
Hello,

You requested your username for Tinder for Non-Profits.

Your username is: {username}

You can use this to log in at: {app_url}

If you did not request this, you can safely ignore this email.

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
                        <td style="padding: 40px 40px 20px; text-align: center; background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); border-radius: 12px 12px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 700;">👤 Username Reminder</h1>
                        </td>
                    </tr>
                    
                    <!-- Body -->
                    <tr>
                        <td style="padding: 40px;">
                            <h2 style="margin: 0 0 20px; color: #1f2937; font-size: 24px; font-weight: 600;">Hi there!</h2>
                            <p style="margin: 0 0 20px; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                You requested your username for Tinder for Non-Profits.
                            </p>
                            
                            <!-- Username Display -->
                            <div style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); border: 2px solid #3b82f6; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0;">
                                <p style="margin: 0 0 10px; color: #1e40af; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Your Username</p>
                                <p style="margin: 0; color: #1f2937; font-size: 24px; font-weight: 700;">{username}</p>
                            </div>
                            
                            <p style="margin: 20px 0 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                You can use this username to log in at:
                            </p>
                            <p style="margin: 10px 0 0;">
                                <a href="{app_url}" style="color: #3b82f6; text-decoration: none; font-weight: 600;">{app_url}</a>
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
        
        return True, "Username reminder email sent successfully"
    except smtplib.SMTPAuthenticationError:
        return False, "Email authentication failed. Please contact support."
    except smtplib.SMTPRecipientsRefused:
        return False, "Invalid email address. Please check and try again."
    except smtplib.SMTPException as e:
        return False, f"Failed to send email: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error sending email: {str(e)}"
