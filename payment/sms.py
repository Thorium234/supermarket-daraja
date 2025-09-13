import africastalking
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Initialize Africa's Talking client
africastalking.initialize(
    settings.AFRICASTALKING_USERNAME,
    settings.AFRICASTALKING_API_KEY
)
sms = africastalking.SMS

def send_sms(phone_number, message):
    """
    Send an SMS via Africa's Talking
    """
    try:
        response = sms.send(message, [str(phone_number)])
        logger.info("📲 SMS sent to %s: %s", phone_number, response)
        return True, response
    except Exception as e:
        logger.error("❌ Failed to send SMS to %s: %s", phone_number, e)
        return False, str(e)
