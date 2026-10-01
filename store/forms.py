from django import forms
from django.utils.text import slugify
from .models import Product, ShippingAddress


class ProductForm(forms.ModelForm):
    """Form to manage or add new products."""

    class Meta:
        model = Product
        fields = [
            'category', 'name', 'slug', 'brand', 'image', 'description',
            'price', 'stock', 'is_available', 'is_featured',
        ]
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Samsung Galaxy S24'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Leave blank to auto-generate'}),
            'brand': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Samsung'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].required = False

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        name = self.cleaned_data.get('name')
        if not slug and name:
            slug = slugify(name)
        return slug


class CheckoutForm(forms.ModelForm):
    """
    Form to collect checkout shipping info.
    Aligned with the ShippingAddress model instead of Order.
    """
    full_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'John Doe', 'class': 'form-control'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'example@email.com', 'class': 'form-control'})
    )
    phone = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '+254 700 000 000', 'class': 'form-control'})
    )

    class Meta:
        model = ShippingAddress
        fields = ['full_name', 'email', 'phone', 'address', 'city', 'state', 'zipcode']
        widgets = {
            'address': forms.TextInput(attrs={'placeholder': '123 Main St', 'class': 'form-control'}),
            'city': forms.TextInput(attrs={'placeholder': 'Nairobi', 'class': 'form-control'}),
            'state': forms.TextInput(attrs={'placeholder': 'Nairobi County', 'class': 'form-control'}),
            'zipcode': forms.TextInput(attrs={'placeholder': '00100', 'class': 'form-control'}),
        }
