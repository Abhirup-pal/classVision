import smtplib
import ssl
from email.message import EmailMessage
import os
from dotenv import load_dotenv


def send_email(email_receiver,password) :

    load_dotenv()
    
    # Define email sender and receiver
    email_sender = os.getenv("EMAIL_SENDER")
    email_password = os.getenv("EMAIL_PASSWORD")


    # Set the subject and body of the email
    subject = 'Login to the ClassVision portal'
    body = f"""
    You can now login to the classVision portal using the following credentials :


    Email id : {email_receiver}
    Password : {password}


    Note : This is a temporary password. You are advised to change it immediately after logging in by clicking the "Update password" link in the navbar/menu
    """

    em = EmailMessage()
    em['From'] = "Class vision admin"
    em['To'] = email_receiver
    em['Subject'] = subject
    em.set_content(body)

    # Add SSL (layer of security)
    context = ssl.create_default_context()

    # Log in and send the email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465 , context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.sendmail(email_sender, email_receiver, em.as_string())