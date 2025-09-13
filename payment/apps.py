from django.apps import AppConfig

class PaymentConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "payment"

    def ready(self):
        import payment.signals  # noqa


import os, sys
from urllib.parse import urlparse
from django.apps import AppConfig
from django.conf import settings

class CommonConfig(AppConfig):
    name = "supermarket.common"
    verbose_name = "Common"

    def ready(self):
        if getattr(settings, "USE_NGROK", False):
            from pyngrok import ngrok
            addrport = urlparse(f"http://{sys.argv[-1]}")
            port = addrport.port if addrport.netloc and addrport.port else "8000"

            public_url = ngrok.connect(port).public_url
            print(f"ngrok tunnel \"{public_url}\" -> \"http://127.0.0.1:{port}\"")
            settings.BASE_URL = public_url
            CommonConfig.init_webhooks(public_url)

    @staticmethod
    def init_webhooks(base_url):
        # TODO: update webhooks with ngrok public URL
        pass


from django.apps import AppConfig
from django.db.models.signals import post_migrate

def create_default_groups(sender, **kwargs):
    from django.contrib.auth.models import Group
    for group_name in ["Cashier", "Owner"]:
        Group.objects.get_or_create(name=group_name)

class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self):
        post_migrate.connect(create_default_groups, sender=self)
