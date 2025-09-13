# payment/tasks.py
import logging
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

# ---------------- EMAIL TASK ---------------- #
@shared_task(bind=True, max_retries=3, default_retry_delay=60)  
def send_email_task(self, subject, message, recipient_email):
    """
    Send an email with retry (3 times, 1 min apart).
    """
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient_email],
            fail_silently=False,
        )
        logger.info("📧 Email sent to %s", recipient_email)
    except Exception as exc:
        logger.error("❌ Email sending failed to %s: %s", recipient_email, exc)
        raise self.retry(exc=exc)  # retry after delay


# ---------------- SMS TASK ---------------- #
@shared_task(bind=True, max_retries=3, default_retry_delay=30)  
def send_sms_task(self, phone, message):
    """
    Send SMS with retry (3 times, 30s apart).
    Replace with your actual SMS provider API.
    """
    try:
        # TODO: Replace with Africa’s Talking / Twilio / Safaricom SMS API
        logger.info("📲 Sending SMS to %s: %s", phone, message)

        # Simulated SMS API call
        success = True  # change this to API response check
        if not success:
            raise Exception("SMS gateway error")

        logger.info("✅ SMS delivered to %s", phone)

    except Exception as exc:
        logger.error("❌ SMS sending failed to %s: %s", phone, exc)
        raise self.retry(exc=exc)  # retry after delay
