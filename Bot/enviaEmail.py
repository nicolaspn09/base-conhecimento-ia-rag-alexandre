import os
import base64
import mimetypes
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GmailSender:
    """
    Envia e-mails usando a API do Gmail com autenticação OAuth 2.0.
    """
    SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

    def __init__(self, credentials_path: str = "/home/codigos_airflow/livros/Bot/credentials.json", token_path: str = "/home/codigos_airflow/livros/Bot/token.json"):
        # A lógica do __init__ continua exatamente a mesma...
        self.creds = None
        if os.path.exists(token_path):
            self.creds = Credentials.from_authorized_user_file(token_path, self.SCOPES)
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, self.SCOPES)
                self.creds = flow.run_local_server(port=0)
            with open(token_path, "w") as token:
                token.write(self.creds.to_json())
        self.service = build("gmail", "v1", credentials=self.creds)

    # ALTERAÇÃO PRINCIPAL AQUI
    def send_email(self, to: list[str], subject: str, body: str, attachment_path: str = None):
        """
        Cria e envia um e-mail para uma lista de destinatários.

        Args:
            to (list[str]): Lista de e-mails dos destinatários.
            subject (str): Assunto do e-mail.
            body (str): Corpo do e-mail em texto.
            attachment_path (str, optional): Caminho para o arquivo a ser anexado.
        """
        try:
            message = MIMEMultipart()
            # AQUI ESTÁ A MUDANÇA: Juntamos a lista em uma única string
            message["to"] = ", ".join(to)
            message["subject"] = subject
            message.attach(MIMEText(body, "plain"))

            # A lógica de anexo continua a mesma...
            if attachment_path:
                content_type, encoding = mimetypes.guess_type(attachment_path)
                main_type, sub_type = content_type.split("/", 1)
                with open(attachment_path, "rb") as fp:
                    if main_type == "image":
                        msg_attachment = MIMEImage(fp.read(), _subtype=sub_type)
                    else:
                        from email.mime.base import MIMEBase
                        from email import encoders
                        msg_attachment = MIMEBase(main_type, sub_type)
                        msg_attachment.set_payload(fp.read())
                        encoders.encode_base64(msg_attachment)
                
                filename = os.path.basename(attachment_path)
                msg_attachment.add_header("Content-Disposition", "attachment", filename=filename)
                message.attach(msg_attachment)

            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            create_message = {"raw": encoded_message}

            send_message = (
                self.service.users().messages().send(userId="me", body=create_message).execute()
            )
            print(f"E-mail enviado com sucesso para {', '.join(to)}! Message ID: {send_message['id']}")

        except HttpError as error:
            print(f"Ocorreu um erro ao enviar o e-mail: {error}")
        except Exception as e:
            print(f"Ocorreu um erro inesperado: {e}")


if __name__ == "__main__":
    gmail_sender = GmailSender()
    destinatario = ["nicolaspn09@gmail.com"]

    gmail_sender.send_email(
    to=destinatario,
    subject=f"""Instagram - Livro Teste""",
    body=f"""Olá!\n\nSegue a proposta para a geração do post para o livro"""
    )