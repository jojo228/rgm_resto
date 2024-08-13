from django.db import models
from decimal import Decimal

class Customer(models.Model):
    referral_id = models.CharField(max_length=10, unique=True)
    referred_by = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='referrals')

    def __str__(self):
        return f"Customer (Referral ID: {self.referral_id})"

class Sale(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.05'))  # Default 5%

    def __str__(self):
        return f"Sale for {self.customer.referral_id} on {self.date} for ${self.amount}"

    def calculate_commission(self):
        return self.amount * self.commission_rate

class Commission(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()

    def __str__(self):
        return f"Commission for {self.customer.referral_id} on {self.sale.date} of ${self.commission_amount}"

    @classmethod
    def create_commission(cls, sale):
        commission_amount = sale.calculate_commission()
        if sale.customer.referred_by:
            commission = cls(
                customer=sale.customer.referred_by,
                sale=sale,
                commission_amount=commission_amount,
                date=sale.date
            )
            commission.save()
        return commission
