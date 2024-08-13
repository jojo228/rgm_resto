from datetime import date
from django.shortcuts import redirect, render
from commission.forms import SaleForm
from .models import Customer, Sale, Commission

COMMISSION_RATE = 0.05  # 5% commission rate

def create_sale(customer_id, amount):
    customer = Customer.objects.get(referral_id=customer_id)
    sale = Sale.objects.create(customer=customer, amount=amount, date=date.today())
    
    if customer.referred_by:
        referrer = customer.referred_by
        commission_amount = amount * COMMISSION_RATE
        Commission.objects.create(
            customer=referrer,
            sale=sale,
            commission_amount=commission_amount,
            date=sale.date
        )
    
    return sale


def record_sale(request):
    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            sale = form.save()
            if sale.customer.referred_by:
                Commission.create_commission(sale)
            return redirect('success')
    else:
        form = SaleForm()
    return render(request, 'commission/record_sale.html', {'form': form})


def commission_report(request):
    commissions = Commission.objects.all()
    return render(request, 'commission/commission_report.html', {'commissions': commissions})
