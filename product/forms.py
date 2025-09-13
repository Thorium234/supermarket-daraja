from django import forms
from .models import Product, Customer, Order, Shelf


# ---------------- Product & Shelf ---------------- #

class ProductForm(forms.ModelForm):
    """Form for adding/editing products (Cashier/Owner)."""
    class Meta:
        model = Product
        fields = ["name", "description", "barcode", "price", "stock", "shelf"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter product name"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Optional description"}),
            "barcode": forms.TextInput(attrs={"class": "form-control", "placeholder": "Barcode / SKU"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "stock": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "shelf": forms.Select(attrs={"class": "form-select"}),
        }


class ShelfForm(forms.ModelForm):
    """Form for managing shelves in the supermarket."""
    class Meta:
        model = Shelf
        fields = ["name", "location", "capacity"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Shelf Name"}),
            "location": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Aisle 3, Row B"}),
            "capacity": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
        }


# ---------------- Customer ---------------- #

class CustomerForm(forms.ModelForm):
    """Form for customer creation (guest checkout allowed)."""
    class Meta:
        model = Customer
        fields = ["name", "phone_number", "email"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Full Name (optional)"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 0712345678"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email (optional)"}),
        }


# ---------------- Checkout ---------------- #

class CheckoutForm(forms.Form):
    """Form for checkout (customer doesn’t need an account)."""
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter phone number (e.g. 254712345678)",
        }),
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Optional email"}),
    )


# ---------------- Dashboard Filtering ---------------- #

class DateFilterForm(forms.Form):
    """For dashboard filtering: Today / Week / Month."""
    FILTER_CHOICES = [
        ("today", "Today"),
        ("week", "This Week"),
        ("month", "This Month"),
    ]
    filter_by = forms.ChoiceField(
        choices=FILTER_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
