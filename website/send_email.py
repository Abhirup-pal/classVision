import os
import smtplib
import ssl
from email.message import EmailMessage


def send_email(reciever,password) :

    # Define email sender and receiver
    


    ##### MUST BE CHANGED before deploy
    email_sender = 'abhiruppal2804@gmail.com'
    email_password = "wmgiemnsoyizlspw"
    #####

    email_receiver = reciever

    # Set the subject and body of the email
    subject = 'Login to the ClassVision portal'
    body = f"""
    Hello,
    You can now login to the classVision portal using the following credentials :
    Email id : {reciever}
    Password : {password}
    """

    em = EmailMessage()
    em['From'] = email_sender
    em['To'] = email_receiver
    em['Subject'] = subject
    em.set_content(body)

    # Add SSL (layer of security)
    context = ssl.create_default_context()

    # Log in and send the email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.sendmail(email_sender, email_receiver, em.as_string())