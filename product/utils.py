from django.contrib.auth.models import Group

def is_cashier_or_owner(user):
    """
    Check if a user is authenticated and belongs to 'Cashier' or 'Owner' group.
    Superusers are always allowed.
    """
    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    return user.groups.filter(name__in=["Cashier", "Owner"]).exists()
