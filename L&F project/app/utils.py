import random
import string
from flask_mail import Message
from app import mail

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(email, otp, purpose):
    subject = 'Email Verification OTP' if purpose == 'verification' else 'Password Reset OTP'
    body = f'Your OTP for {purpose} is: {otp}. This OTP will expire in 10 minutes.'
    
    msg = Message(
        subject=subject,
        sender='your-email@gmail.com',
        recipients=[email],
        body=body
    )
    mail.send(msg) 