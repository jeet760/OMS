from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import random, string

class SMTPMail:
    def __init__(self, to_emails, regn_no, regd_name, href_url, type_of_mail, email_otp):
        self.to_emails = to_emails
        self.body = regn_no
        self.regd_name = regd_name
        self.href_url = href_url
        self.type_of_mail = type_of_mail
        self.email_otp = email_otp


    def __str__(self):
        return f"SMTP Email to: {', '.join(self.to_emails)}"

    def send_email(self):
        try:
            approved = True if self.type_of_mail == 'approval' else False
            html_content = render_to_string('activation-mail.html',context={'uid':self.body, 'regd_name':self.regd_name, 'href_url':self.href_url, 'email_otp':self.email_otp, 'approved':approved})
            text_content = strip_tags(html_content)

            email = EmailMultiAlternatives(
                subject='Account Activation',
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=self.to_emails
            )
            email.attach_alternative(html_content, "text/html")
            email.send()

            print('✅ Email sent successfully!')
            return True
        except Exception as ex:
            print("❌ Error:", ex)
            return False


class OTPGeneration:
    def __init__(self, length=6):
        try:
            characters = string.ascii_uppercase + string.digits
            self.otp = ''.join(random.choices(characters, k=length))
        except Exception as ex:
            print(type(ex).__name__)
            self.otp = 'EE00EE'  # fallback OTP
    
    def __str__(self):
        return self.otp


