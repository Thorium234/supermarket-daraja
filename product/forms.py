from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import password_validators_help_texts
from .models import Product, Customer, Order, Shelf


# ---------------- Product & Shelf ---------------- #

class ProductForm(forms.ModelForm):
    """Form for adding/editing products (Cashier/Owner)."""
    class Meta:
        model = Product
        fields = ["name", "description", "image", "category", "barcode", "price", "stock", "shelf"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter product name"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Optional description"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "barcode": forms.TextInput(attrs={"class": "form-control", "placeholder": "Barcode / SKU"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "stock": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "shelf": forms.Select(attrs={"class": "form-select"}),
        }


class ShelfForm(forms.ModelForm):
    """Form for managing shelves in the supermarket."""
    class Meta:
        model = Shelf
        fields = ["name", "location", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Shelf Name"}),
            "location": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Aisle 3, Row B"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Optional shelf description"}),
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


class CustomerRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={"class": "form-control"}))
    last_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"class": "form-control"}))
    phone_number = forms.CharField(max_length=15, required=True, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "07XXXXXXXX"}))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email", "phone_number", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"class": "form-control"})
        self.fields["password1"].widget.attrs.update({"class": "form-control", "id": "id_password1"})
        self.fields["password2"].widget.attrs.update({"class": "form-control", "id": "id_password2"})
        self.password_help_texts = password_validators_help_texts()

    def clean_phone_number(self):
        phone = "".join(ch for ch in self.cleaned_data["phone_number"] if ch.isdigit())
        if phone.startswith("0"):
            phone = "254" + phone[1:]
        elif phone.startswith("7") and len(phone) == 9:
            phone = "254" + phone
        if not (phone.startswith("254") and len(phone) == 12):
            raise forms.ValidationError("Enter a valid Kenyan phone number.")
        return phone
