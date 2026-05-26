"""
Email utilities for sending notifications and reports.
"""

import os
import smtplib
import logging
import time
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

# SMTP Configuration
SMTP_TIMEOUT = 30  # Increased from 10 to 30 seconds
SMTP_RETRIES = 3   # Number of retry attempts
SMTP_RETRY_DELAY = 2  # Delay between retries in seconds


class EmailConfigurationError(Exception):
    """Raised when email configuration is invalid."""
    pass


class EmailSenderError(Exception):
    """Raised when email sending fails."""
    pass


def validate_email_configuration():
    """
    Validate email configuration and test connection.
    
    Raises:
        EmailConfigurationError: If configuration is invalid or connection fails
    """
    # Get configuration
    origin_email = os.getenv("ORIGIN_EMAIL")
    password = os.getenv("PASSWORD_EMAIL")
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")
    
    # Validate all required variables exist
    if not all([origin_email, password, smtp_server, smtp_port]):
        missing = []
        if not origin_email:
            missing.append("ORIGIN_EMAIL")
        if not password:
            missing.append("PASSWORD_EMAIL")
        if not smtp_server:
            missing.append("SMTP_SERVER")
        if not smtp_port:
            missing.append("SMTP_PORT")
        raise EmailConfigurationError(
            f"Email configuration incomplete. Missing: {', '.join(missing)}"
        )
    
    # Validate email format
    if "@" not in origin_email or "." not in origin_email.split("@")[1]:
        raise EmailConfigurationError(f"Invalid email format: {origin_email}")
    
    # Validate port is numeric
    try:
        port_int = int(smtp_port)
        if not (1 <= port_int <= 65535):
            raise ValueError("Port out of range")
    except ValueError as e:
        raise EmailConfigurationError(f"Invalid SMTP port: {smtp_port}. {str(e)}")
    
    # Test connection
    try:
        log.info(f"Testing SMTP connection to {smtp_server}:{smtp_port}")
        with smtplib.SMTP(smtp_server, int(smtp_port), timeout=SMTP_TIMEOUT) as smtp:
            smtp.starttls()
            smtp.login(origin_email, password)
        log.info("Email configuration validated successfully")
    except smtplib.SMTPAuthenticationError as e:
        raise EmailConfigurationError(f"SMTP authentication failed: {str(e)}")
    except smtplib.SMTPException as e:
        raise EmailConfigurationError(f"SMTP error: {str(e)}")
    except Exception as e:
        raise EmailConfigurationError(f"Failed to connect to SMTP server: {str(e)}")


def _validate_email_address(email: str) -> bool:
    """Validate email address format."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def _send_smtp_message_with_retry(msg: EmailMessage, origin_email: str, password: str, smtp_server: str, smtp_port: str):
    """
    Send SMTP message with retry logic and improved error handling.
    
    Args:
        msg: EmailMessage object to send
        origin_email: Sender email address
        password: SMTP password
        smtp_server: SMTP server address
        smtp_port: SMTP server port
        
    Raises:
        EmailSenderError: If sending fails after all retries
    """
    last_error = None
    
    for attempt in range(SMTP_RETRIES):
        try:
            log.info(f"Attempting to send email (attempt {attempt + 1}/{SMTP_RETRIES})...")
            with smtplib.SMTP(smtp_server, int(smtp_port), timeout=SMTP_TIMEOUT) as smtp:
                smtp.starttls()
                smtp.login(origin_email, password)
                smtp.send_message(msg)
            log.info("Email sent successfully")
            return
        except smtplib.SMTPAuthenticationError as e:
            log.error(f"SMTP authentication failed: {e}")
            raise EmailSenderError(f"SMTP authentication failed: {str(e)}")
        except smtplib.SMTPException as e:
            last_error = e
            log.warning(f"SMTP error on attempt {attempt + 1}: {e}")
            if attempt < SMTP_RETRIES - 1:
                log.info(f"Retrying in {SMTP_RETRY_DELAY} seconds...")
                time.sleep(SMTP_RETRY_DELAY)
        except (OSError, TimeoutError, ConnectionError) as e:
            last_error = e
            log.warning(f"Connection error on attempt {attempt + 1}: {e}")
            if attempt < SMTP_RETRIES - 1:
                log.info(f"Retrying in {SMTP_RETRY_DELAY} seconds...")
                time.sleep(SMTP_RETRY_DELAY)
    
    # All retries exhausted
    error_msg = f"Failed to send email after {SMTP_RETRIES} attempts: {str(last_error)}"
    log.error(error_msg)
    raise EmailSenderError(error_msg)


def send_email_report_less_attachment(attachment_file: str, email_destination: str):
    """
    Send email with attachment.
    
    Args:
        attachment_file: Path to the attachment file
        email_destination: Recipient email address
        
    Raises:
        EmailConfigurationError: If configuration is invalid
        EmailSenderError: If sending fails
        FileNotFoundError: If attachment file not found
    """
    try:
        # Validate configuration
        validate_email_configuration()
        
        # Validate destination email
        if not _validate_email_address(email_destination):
            raise EmailConfigurationError(f"Invalid destination email: {email_destination}")
        
        # Check if file exists
        if not os.path.exists(attachment_file):
            raise FileNotFoundError(f"Attachment file not found: {attachment_file}")
        
        origin_email = os.getenv("ORIGIN_EMAIL")
        password = os.getenv("PASSWORD_EMAIL")
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = os.getenv("SMTP_PORT")
        
        # Double-check that all variables are set (defensive programming)
        if not all([origin_email, password, smtp_server, smtp_port]):
            missing = [var for var, val in [
                ("ORIGIN_EMAIL", origin_email),
                ("PASSWORD_EMAIL", password),
                ("SMTP_SERVER", smtp_server),
                ("SMTP_PORT", smtp_port)
            ] if not val]
            raise EmailConfigurationError(
                f"Email configuration incomplete. Missing: {', '.join(missing)}"
            )
        
        msg = EmailMessage()
        msg["Subject"] = "[SISTEMA QUETO] RELATÓRIO"
        msg["From"] = origin_email
        msg["To"] = email_destination

        with open(attachment_file, "rb") as f:
            filename = os.path.basename(attachment_file)
            msg.add_attachment(f.read(), maintype="application", subtype="octet-stream", filename=filename)

        _send_smtp_message_with_retry(msg, origin_email, password, smtp_server, smtp_port)
        log.info(f"Email sent successfully to {email_destination}")
        
    except EmailConfigurationError as e:
        log.error(f"Email configuration error: {e}")
        raise
    except FileNotFoundError as e:
        log.error(f"File error: {e}")
        raise
    except (smtplib.SMTPException, OSError) as e:
        log.error(f"Failed to send email: {e}")
        raise EmailSenderError(f"Email sending failed: {str(e)}")
    except Exception as e:
        log.error(f"Unexpected error sending email: {e}")
        raise EmailSenderError(f"Unexpected error: {str(e)}")


async def send_email_with_attachments(files_path, email_destination: str):
    """
    Send email with multiple attachments.
    
    Args:
        files_path: List of file paths to attach
        email_destination: Recipient email address
        
    Raises:
        EmailConfigurationError: If configuration is invalid
        EmailSenderError: If sending fails
    """
    try:
        # Validate configuration
        validate_email_configuration()
        
        # Validate destination email
        if not _validate_email_address(email_destination):
            raise EmailConfigurationError(f"Invalid destination email: {email_destination}")
        
        # Validate all files exist
        missing_files = [f for f in files_path if not os.path.exists(f)]
        if missing_files:
            raise FileNotFoundError(f"Some attachment files not found: {missing_files}")
        
        origin_email = os.getenv("ORIGIN_EMAIL")
        password = os.getenv("PASSWORD_EMAIL")
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = os.getenv("SMTP_PORT")
        
        # Double-check that all variables are set (defensive programming)
        if not all([origin_email, password, smtp_server, smtp_port]):
            missing = [var for var, val in [
                ("ORIGIN_EMAIL", origin_email),
                ("PASSWORD_EMAIL", password),
                ("SMTP_SERVER", smtp_server),
                ("SMTP_PORT", smtp_port)
            ] if not val]
            raise EmailConfigurationError(
                f"Email configuration incomplete. Missing: {', '.join(missing)}"
            )

        msg = EmailMessage()
        msg["Subject"] = "Relatório de Evento e Áudio Capturado"
        msg["From"] = origin_email
        msg["To"] = email_destination
        msg.set_content("Segue em anexo o relatório e o áudio do evento detectado.")

        for path in files_path:
            try:
                with open(path, "rb") as f:
                    file_content = f.read()
                    file_name = os.path.basename(path)
                    msg.add_attachment(
                        file_content, 
                        maintype="application", 
                        subtype="octet-stream", 
                        filename=file_name
                    )
                log.info(f"Attached file: {file_name}")
            except IOError as e:
                log.error(f"Error reading attachment {path}: {e}")
                raise EmailSenderError(f"Failed to read attachment {path}: {str(e)}")

        _send_smtp_message_with_retry(msg, origin_email, password, smtp_server, smtp_port)
        log.info(f"Email with {len(files_path)} attachments sent to {email_destination}")
        
    except EmailConfigurationError as e:
        log.error(f"Email configuration error: {e}")
        raise
    except FileNotFoundError as e:
        log.error(f"File error: {e}")
        raise
    except (smtplib.SMTPException, OSError) as e:
        log.error(f"Failed to send email: {e}")
        raise EmailSenderError(f"Email sending failed: {str(e)}")
    except Exception as e:
        log.error(f"Unexpected error sending email: {e}")
        raise EmailSenderError(f"Unexpected error: {str(e)}")


# Backward compatibility with old naming convention
sendEmailWithAttachments = send_email_with_attachments
sendEmailReportLessAttachment = send_email_report_less_attachment
