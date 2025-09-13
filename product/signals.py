# product/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.sites.models import Site
from django.urls import reverse
from .models import Order
import requests
import socket


def get_base_url():
    """
    Dynamically get base URL depending on environment.
    - If running under ngrok (or production), use the domain.
    - Else default to localhost:8000 for dev.
    """
    try:
        current_site = Site.objects.get_current()
        domain = current_site.domain
        if "ngrok" in domain:
            return f"https://{domain}"
        return f"http://{socket.gethostname()}:8000"
    except Exception:
        return "http://127.0.0.1:8000"

# product/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.sites.models import Site
from django.urls import reverse
from .models import Order
import requests

@receiver(post_save, sender=Order)
def send_receipt_message(sender, instance, created, **kwargs):
    # Only fire when order status changes to PAID
    if not created and instance.status == "PAID":
        phone = instance.customer.phone_number

        # Build receipt link dynamically (works for ngrok + prod)
        current_site = Site.objects.get_current()
        base_url = f"http://{current_site.domain}"
        receipt_link = base_url + reverse("receipt", args=[instance.id])

        # Example: Africa’s Talking SMS
        url = "https://api.africastalking.com/version1/messaging"
        headers = {
            "apiKey": "YOUR_API_KEY",
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        payload = {
            "username": "YOUR_USERNAME",
            "to": phone,
            "message": f"✅ Your order #{instance.id} has been PAID.\nDownload receipt: {receipt_link}",
        }

        try:
            response = requests.post(url, headers=headers, data=payload, timeout=10)
            print("SMS response:", response.json())
        except Exception as e:
            print("❌ SMS sending failed:", e)

        # Optional: Twilio WhatsApp sandbox
        # from twilio.rest import Client
        # client = Client("TWILIO_SID", "TWILIO_AUTH_TOKEN")
        # client.messages.create(
        #     from_="whatsapp:+14155238886",
        #     body=f"✅ Your order #{instance.id} has been PAID.\nReceipt: {receipt_link}",
        #     to=f"whatsapp:{phone}"
        # )
