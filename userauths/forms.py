from django import forms
from django.contrib.auth.forms import UserCreationForm
from userauths.models import User, Profile


class UserRegisterForm(UserCreationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={"placeholder": "Nom d'utilisateur", "class": "form-control"})
    )
    email = forms.EmailField(widget=forms.EmailInput(attrs={"placeholder": "Email", "class": "form-control"}))
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Mot de passe", "class": "form-control"})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Confirmer Mot de passe", "class": "form-control"})
    )

    class Meta:
        model = User
        fields = ["username", "email"]


class OTPForm(forms.Form):
    otp = forms.CharField(max_length=6)  # Assuming your OTP is 6 digits


class ProfileForm(forms.ModelForm):
    full_name = forms.CharField(
        widget=forms.TextInput(attrs={"placeholder": "Full Name"})
    )
    bio = forms.CharField(widget=forms.TextInput(attrs={"placeholder": "Bio", "class": "form-control"}))
    phone = forms.CharField(widget=forms.TextInput(attrs={"placeholder": "Phone", "class": "form-control"}))

    class Meta:
        model = Profile
        fields = ["full_name", "image", "bio", "phone"]

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Votre nom'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Votre email'}),
            'tel': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Votre téléphone'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Votre message'}),
        }
