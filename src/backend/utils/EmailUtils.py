import os
import smtplib

from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

def sendEmailReportLessAttachment(attachmentFile: str, emailDestination: str):

    msg = EmailMessage()
    msg["Subject"] = "[SISTEMA QUETO] RELATÓRIO"
    msg["From"] = os.getenv("ORIGIN_EMAIL")
    msg["To"] = emailDestination

    with open(attachmentFile, "rb") as f:
        msg.add_attachment(f.read(), maintype="text", subtype="plain", filename=attachmentFile)

    with smtplib.SMTP(os.getenv("SMTP_SERVER"), int(os.getenv("SMTP_PORT"))) as smtp:
        smtp.starttls()
        smtp.login(os.getenv("ORIGIN_EMAIL"), os.getenv("PASSWORD_EMAIL"))
        smtp.send_message(msg)

async def sendEmailWithAttachments(filesPath, emailDestination: str):
    
    server = os.getenv("SMTP_SERVER")
    port = os.getenv("SMTP_PORT")

    if not server or not port:
        raise ValueError("Configurações de e-mail não definidas corretamente.")

    msg = EmailMessage()
    msg["Subject"] = "Relatório de Evento e Áudio Capturado"
    msg["From"] = os.getenv("ORIGIN_EMAIL")
    msg["To"] = emailDestination
    msg.set_content("Segue em anexo o relatório e o áudio do evento detectado.")

    for path in filesPath:
        with open(path, "rb") as f:
            fileContent = f.read()
            fileName = os.path.basename(path)
            msg.add_attachment(fileContent, maintype="application", subtype="octet-stream", filename=fileName)

    with smtplib.SMTP(server, int(port)) as smtp:
        smtp.starttls()
        smtp.login(os.getenv("ORIGIN_EMAIL"), os.getenv("PASSWORD_EMAIL"))
        smtp.send_message(msg)

