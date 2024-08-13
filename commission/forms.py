from django import forms
from .models import Sale, Customer

class SaleForm(forms.ModelForm):
    customer_referral_id = forms.CharField(max_length=10, label='Referral ID')

    class Meta:
        model = Sale
        fields = ['amount', 'date', 'commission_rate']

    def save(self, commit=True):
        referral_id = self.cleaned_data.get('customer_referral_id')
        customer = Customer.objects.get(referral_id=referral_id)
        sale = super().save(commit=False)
        sale.customer = customer
        if commit:
            sale.save()
        return sale
