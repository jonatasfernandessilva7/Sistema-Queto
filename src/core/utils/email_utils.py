"""
Email utilities for sending notifications and reports.
"""

import os
import smtplib
import logging
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)


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
        with smtplib.SMTP(smtp_server, int(smtp_port), timeout=10) as smtp:
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
        
        msg = EmailMessage()
        msg["Subject"] = "[SISTEMA QUETO] RELATÓRIO"
        msg["From"] = origin_email
        msg["To"] = email_destination

        with open(attachment_file, "rb") as f:
            filename = os.path.basename(attachment_file)
            msg.add_attachment(f.read(), maintype="application", subtype="octet-stream", filename=filename)

        with smtplib.SMTP(smtp_server, int(smtp_port), timeout=10) as smtp:
            smtp.starttls()
            smtp.login(origin_email, password)
            smtp.send_message(msg)
        
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

        with smtplib.SMTP(smtp_server, int(smtp_port), timeout=10) as smtp:
            smtp.starttls()
            smtp.login(origin_email, password)
            smtp.send_message(msg)
        
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
