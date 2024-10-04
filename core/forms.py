from django import forms
from core.models import  ProductReview
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget


class ProductReviewForm(forms.ModelForm):
    review = forms.CharField(
        widget=forms.Textarea(attrs={"placeholder": "Write review"})
    )

    class Meta:
        model = ProductReview
        fields = ["review", "rating"]


PAYMENT_CHOICES = (
    ('S', 'Stripe'),
    ('P', 'PayPal')
)


class CheckoutForm(forms.Form):
    shipping_address = forms.CharField(required=False)
    shipping_address2 = forms.CharField(required=False)
    shipping_country = CountryField(blank_label='Choisir un pays').formfield(
        required=False,
        id="id_shipping_country",
        widget=CountrySelectWidget(attrs={
            'class': 'form-select',
        }))
    shipping_zip = forms.CharField(required=False)

    billing_address = forms.CharField(required=False)
    billing_address2 = forms.CharField(required=False)
    billing_country = CountryField(blank_label='Choisir un pays').formfield(
        required=False,
        id="id_billing_country",
        widget=CountrySelectWidget(attrs={
            'class': 'form-select',
        }))
    billing_zip = forms.CharField(required=False)

    same_billing_address = forms.BooleanField(required=False)
    set_default_shipping = forms.BooleanField(required=False)
    use_default_shipping = forms.BooleanField(required=False)
    set_default_billing = forms.BooleanField(required=False)
    use_default_billing = forms.BooleanField(required=False)

    payment_option = forms.ChoiceField(
        widget=forms.RadioSelect, choices=PAYMENT_CHOICES)



class PaymentForm(forms.Form):
    stripeToken = forms.CharField(required=False)
    save = forms.BooleanField(required=False)
    use_default = forms.BooleanField(required=False)

# class ContactForm(forms.ModelForm):
#     class Meta:
#         model = Contact
#         fields = ['number']
#         widgets = {
#             'number': forms.TextInput(attrs={'placeholder': 'Enter your Phone Number Here'}),
#         }
#         labels = {
#             'number': 'Phone Number',
#         }

#     def clean_number(self):
#         number = self.cleaned_data.get('number')
#         # Ensure that the number only contains digits
#         if not number.isdigit():
#             raise forms.ValidationError("Phone number must only contain digits.")
#         return number
