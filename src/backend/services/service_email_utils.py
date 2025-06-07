import os
import smtplib

from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

def enviar_email_relatorio(arquivo: str, destinatario: str):

    msg = EmailMessage()
    msg["Subject"] = "[Queto] Relatório Gerado"
    msg["From"] = os.getenv("EMAIL_ORIGEM")
    msg["To"] = destinatario

    with open(arquivo, "rb") as f:
        msg.add_attachment(f.read(), maintype="text", subtype="plain", filename=arquivo)

    with smtplib.SMTP(os.getenv("SMTP_SERVIDOR"), int(os.getenv("SMTP_PORTA"))) as smtp:
        smtp.starttls()
        smtp.login(os.getenv("EMAIL_ORIGEM"), os.getenv("EMAIL_SENHA"))
        smtp.send_message(msg)

async def enviar_email_com_anexos(caminhos_arquivos, destinatario: str):
    
    servidor = os.getenv("SMTP_SERVIDOR")
    porta = os.getenv("SMTP_PORTA")

    if not servidor or not porta:
        raise ValueError("Configurações de e-mail não definidas corretamente.")

    mensagem = EmailMessage()
    mensagem["Subject"] = "Relatório de Evento e Áudio Capturado"
    mensagem["From"] = os.getenv("EMAIL_ORIGEM")
    mensagem["To"] = destinatario
    mensagem.set_content("Segue em anexo o relatório e o áudio do evento detectado.")

    for caminho in caminhos_arquivos:
        with open(caminho, "rb") as f:
            conteudo = f.read()
            nome_arquivo = os.path.basename(caminho)
            mensagem.add_attachment(conteudo, maintype="application", subtype="octet-stream", filename=nome_arquivo)

    with smtplib.SMTP(servidor, int(porta)) as smtp:
        smtp.starttls()
        smtp.login(os.getenv("EMAIL_ORIGEM"), os.getenv("EMAIL_SENHA"))
        smtp.send_message(mensagem)

