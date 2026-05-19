import os
import smtplib
from email.message import EmailMessage
from pathlib import Path


def send_pdf_email(pdf_path: str, drive_link: str):
    recipients = os.environ["MAIL_TO"].split(",")

    msg = EmailMessage()
    msg["Subject"] = os.getenv("MAIL_SUBJECT", "Weekly Automotive Brief")
    msg["From"] = os.environ["SMTP_USER"]
    msg["To"] = os.environ["SMTP_USER"]
    msg["Bcc"] = ", ".join(recipients)

    msg.set_content(
        f"""Buongiorno,

in allegato il Weekly Automotive Brief.



"""
    )

    path = Path(pdf_path)
    msg.add_attachment(
        path.read_bytes(),
        maintype="application",
        subtype="pdf",
        filename=path.name,
    )

    with smtplib.SMTP_SSL(os.environ["SMTP_HOST"], int(os.getenv("SMTP_PORT", "465"))) as smtp:
        smtp.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
        smtp.send_message(msg)