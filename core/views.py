import json
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import View
from regex import E
from requests import session
import requests
from taggit.models import Tag
from core.models import (
    Payment,
    Product,
    Category,
    CartOrder,
    CartOrderProducts,
    ProductImages,
    ProductReview,
    wishlist_model,
    Address,
)
from userauths.models import ContactUs, Profile
from core.forms import CheckoutForm, ProductReviewForm
from django.template.loader import render_to_string
from django.contrib import messages

from django.urls import reverse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

import calendar
from django.db.models import Count, Avg
from django.db.models.functions import ExtractMonth
from django.core import serializers


def index(request):
    # bannanas = Product.objects.all().order_by("-id")
    products = Product.objects.all().order_by("-id")   

    return render(request, "index.html", locals())


def product_list_view(request):
    products = Product.objects.all().order_by("-id")
    tags = Tag.objects.all().order_by("-id")[:6]

    context = {
        "products": products,
        "tags": tags,
    }

    return render(request, "all-food.html", context)


def category_list_view(request):
    categories = Category.objects.all()

    context = {"categories": categories}
    return render(request, "category-list.html", context)


def category_product_list__view(request, cid):
    category = Category.objects.get(cid=cid)  # food, Cosmetics
    products = Product.objects.filter(product_status="published", category=category)

    context = {
        "category": category,
        "products": products,
    }
    return render(request, "category-product-list.html", context)





def product_detail_view(request, pid):
    product = Product.objects.get(pid=pid)
    # product = get_object_or_404(Product, pid=pid)
    products = Product.objects.filter(category=product.category).exclude(pid=pid)

    # Getting all reviews related to a product
    reviews = ProductReview.objects.filter(product=product).order_by("-date")

    # Getting average review
    average_rating = ProductReview.objects.filter(product=product).aggregate(
        rating=Avg("rating")
    )

    # Product Review form
    review_form = ProductReviewForm()

    make_review = True

    if request.user.is_authenticated:
        # address = Address.objects.get(status=True, user=request.user)
        user_review_count = ProductReview.objects.filter(
            user=request.user, product=product
        ).count()

        if user_review_count > 0:
            make_review = False

    address = "Login To Continue"

    p_image = product.p_images.all()

    context = {
        "p": product,
        "address": address,
        "make_review": make_review,
        "review_form": review_form,
        "p_image": p_image,
        "average_rating": average_rating,
        "reviews": reviews,
        "products": products,
    }

    return render(request, "foods-details.html", context)


def tag_list(request, tag_slug=None):
    products = Product.objects.all().order_by("-id")

    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        products = products.filter(tags__in=[tag])

    context = {"products": products, "tag": tag}

    return render(request, "tag.html", context)


def ajax_add_review(request, pid):
    product = Product.objects.get(pk=pid)
    user = request.user

    review = ProductReview.objects.create(
        user=user,
        product=product,
        review=request.POST["review"],
        rating=request.POST["rating"],
    )

    context = {
        "user": user.username,
        "review": request.POST["review"],
        "rating": request.POST["rating"],
    }

    average_reviews = ProductReview.objects.filter(product=product).aggregate(
        rating=Avg("rating")
    )

    return JsonResponse(
        {"bool": True, "context": context, "average_reviews": average_reviews}
    )


def search_view(request):
    query = request.GET.get("q")

    products = Product.objects.filter(title__icontains=query).order_by("-date")

    context = {
        "products": products,
        "query": query,
    }
    return render(request, "search.html", context)


def filter_product(request):
    categories = request.GET.getlist("category[]")

    min_price = request.GET["min_price"]
    max_price = request.GET["max_price"]

    products = (
        Product.objects.all().order_by("-id").distinct()
    )

    products = products.filter(price__gte=min_price)
    products = products.filter(price__lte=max_price)

    if len(categories) > 0:
        products = products.filter(category__id__in=categories).distinct()

    data = render_to_string("async/product-list.html", {"products": products})
    return JsonResponse({"data": data})


def add_to_cart(request):
    cart_product = {}

    cart_product[str(request.GET["id"])] = {
        "title": request.GET["title"],
        "qty": request.GET["qty"],
        "price": request.GET["price"],
        "image": request.GET["image"],
        "pid": request.GET["pid"],
    }

    if "cart_data_obj" in request.session:
        if str(request.GET["id"]) in request.session["cart_data_obj"]:
            cart_data = request.session["cart_data_obj"]
            cart_data[str(request.GET["id"])]["qty"] = int(
                cart_product[str(request.GET["id"])]["qty"]
            )
            cart_data.update(cart_data)
            request.session["cart_data_obj"] = cart_data
        else:
            cart_data = request.session["cart_data_obj"]
            cart_data.update(cart_product)
            request.session["cart_data_obj"] = cart_data

    else:
        request.session["cart_data_obj"] = cart_product
    return JsonResponse(
        {
            "data": request.session["cart_data_obj"],
            "totalcartitems": len(request.session["cart_data_obj"]),
        }
    )


def cart_view(request):
    cart_total_amount = 0
    if "cart_data_obj" in request.session:
        for p_id, item in request.session["cart_data_obj"].items():
            cart_total_amount += int(item["qty"]) * float(item["price"])
        return render(
            request,
            "shopping-cart.html",
            {
                "cart_data": request.session["cart_data_obj"],
                "totalcartitems": len(request.session["cart_data_obj"]),
                "cart_total_amount": cart_total_amount,
            },
        )
    else:
        messages.warning(request, "Your cart is empty")
        return redirect("core:index")


def delete_cart_item(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")

        if "cart_data_obj" in request.session:
            cart_data = request.session.get("cart_data_obj", {})

            if product_id in cart_data:
                del cart_data[product_id]
                request.session["cart_data_obj"] = cart_data
                request.session.modified = True  # Mark the session as modified

                return JsonResponse({"success": True})

        return JsonResponse({"success": False, "error": "Product not found in cart"})

    return JsonResponse({"success": False, "error": "Invalid request method"})

import logging


def update_cart(request):
    if request.method == "POST":
        product_id = request.POST.get("id")
        product_qty = request.POST.get("qty")

        # Debugging: Print received data
        print(f"Received update_cart request: product_id={product_id}, product_qty={product_qty}")

        if "cart_data_obj" in request.session:
            cart_data = request.session["cart_data_obj"]
            print("Current cart_data_obj keys:", list(cart_data.keys()))

            # Ensure product_id is a string
            product_id = str(product_id)
            print(f"Formatted product_id (as string): {product_id}")

            if product_id in cart_data:
                try:
                    # Convert product_qty to integer
                    new_qty = int(product_qty)
                    cart_data[product_id]["qty"] = new_qty
                    request.session["cart_data_obj"] = cart_data
                    request.session.modified = True

                    # Debugging: Confirm update
                    print(f"Updated cart_data_obj: {request.session['cart_data_obj']}")
                except ValueError:
                    print(f"Invalid quantity value: {product_qty}")
            else:
                print(f"Product_id {product_id} not found in cart_data_obj")
        else:
            print("No cart_data_obj in session")

        # Calculate cart total
        cart_total_amount = 0
        if "cart_data_obj" in request.session:
            for p_id, item in request.session["cart_data_obj"].items():
                try:
                    qty = int(item["qty"])
                    price = float(item["price"])
                    cart_total_amount += qty * price
                except (ValueError, KeyError):
                    print(f"Invalid item data: {item}")
        print(f"Calculated cart_total_amount: {cart_total_amount}")

        # Render updated cart list
        context = render_to_string(
            "async/cart-list.html",
            {
                "cart_data": request.session["cart_data_obj"],
                "totalcartitems": len(request.session["cart_data_obj"]),
                "cart_total_amount": cart_total_amount,
            },
        )

        return JsonResponse(
            {
                "data": context,
                "totalcartitems": len(request.session["cart_data_obj"]),
            }
        )
    else:
        return JsonResponse({"success": False, "error": "Invalid request method"})

def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid


class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            cart_total_amount = 0
            total_amount = 0

            # Checking if cart_data_obj session exists
            if "cart_data_obj" in self.request.session:
                # Getting total amount for Paypal Amount
                for p_id, item in self.request.session["cart_data_obj"].items():
                    total_amount += int(item["qty"]) * float(item["price"])
            

                # Calculate cart total amount and total items
                cart_data = self.request.session.get("cart_data_obj", {})
                cart_total_amount = sum(int(item["qty"]) * float(item["price"]) for item in cart_data.values())
                totalcartitems = len(cart_data)

                order = CartOrder.objects.create(user=self.request.user, ordered=False, price=cart_total_amount)
                form = CheckoutForm()

                # Getting total amount for The Cart
                for p_id, item in self.request.session["cart_data_obj"].items():
                    cart_total_amount += int(item["qty"]) * float(item["price"])

                    cart_order_products = CartOrderProducts.objects.create(
                        user=self.request.user,
                        order=order,
                        # invoice_no="INVOICE_NO-" + str(order.id),  # INVOICE_NO-5,
                        item=item["title"],
                        image=item["image"],
                        qty=item["qty"],
                        price=item["price"],
                        total=float(item["qty"]) * float(item["price"]),
                    )

                context = {
                    'form': form,
                    'order': order,
                    'DISPLAY_COUPON_FORM': True,  # Assuming you have a coupon form
                    "cart_data": cart_data,
                    "totalcartitems": totalcartitems,
                    "cart_total_amount": cart_total_amount,
                }

                # Get default shipping address
                shipping_address_qs = Address.objects.filter(
                    user=self.request.user,
                    address_type='S',
                    default=True
                )
                if shipping_address_qs.exists():
                    context.update({'default_shipping_address': shipping_address_qs[0]})

                # Get default billing address
                billing_address_qs = Address.objects.filter(
                    user=self.request.user,
                    address_type='B',
                    default=True
                )
                if billing_address_qs.exists():
                    context.update({'default_billing_address': billing_address_qs[0]})

                return render(self.request, "checkout.html", context)

        except ObjectDoesNotExist:
            messages.info(self.request, "You do not have an active order")
            return redirect("core:checkout")

    def post(self, *args, **kwargs):

        shipping_address = self.request.POST.get('shipping_address')
        shipping_address2 = self.request.POST.get('shipping_address2')
        shipping_country = self.request.POST.get('shipping_country')
        shipping_zip = self.request.POST.get('shipping_zip')
        billing_address = self.request.POST.get('billing_address')
        billing_address2 = self.request.POST.get('billing_address2')
        billing_country = self.request.POST.get('billing_country')
        billing_zip = self.request.POST.get('billing_zip')
        same_billing_address = self.request.POST.get('same_billing_address')
        use_default_shipping = self.request.POST.get('use_default_shipping')
        set_default_shipping = self.request.POST.get('set_default_shipping')
        use_default_billing = self.request.POST.get('use_default_billing')
        set_default_billing = self.request.POST.get('set_default_billing')



        form = CheckoutForm(self.request.POST or None)
        try:
            order = CartOrder.objects.filter(user=self.request.user, ordered=False).first()
            if form.is_valid():
                # Calculate cart total amount and total items
                cart_data = self.request.session.get("cart_data_obj", {})
                cart_total_amount = sum(int(item["qty"]) * float(item["price"]) for item in cart_data.values())
                totalcartitems = len(cart_data)



                # Shipping Address Handling
                use_default_shipping = form.cleaned_data.get('use_default_shipping')
                if use_default_shipping:
                    shipping_address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='S',
                        default=True
                    )
                    if shipping_address_qs.exists():
                        shipping_address = shipping_address_qs[0]
                        order.shipping_address = shipping_address
                        order.save()
                    else:
                        messages.info(self.request, "No default shipping address available")
                        return redirect('core:checkout')
                else:
                    shipping_address1 = form.cleaned_data.get('shipping_address')
                    shipping_address2 = form.cleaned_data.get('shipping_address2')
                    shipping_country = form.cleaned_data.get('shipping_country')
                    shipping_zip = form.cleaned_data.get('shipping_zip')

                    if is_valid_form([shipping_address1, shipping_country, shipping_zip]):
                        shipping_address = Address(
                            user=self.request.user,
                            street_address=shipping_address1,
                            apartment_address=shipping_address2,
                            country=shipping_country,
                            zip=shipping_zip,
                            address_type='S'
                        )
                        shipping_address.save()
                        order.shipping_address = shipping_address
                        # order.save()

                        set_default_shipping = form.cleaned_data.get('set_default_shipping')
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()
                    else:
                        messages.info(self.request, "Please fill in the required shipping address fields")

                # Billing Address Handling
                use_default_billing = form.cleaned_data.get('use_default_billing')
                same_billing_address = form.cleaned_data.get('same_billing_address')

                if same_billing_address:
                    billing_address = shipping_address
                    billing_address.pk = None  # Create a new instance
                    billing_address.save()
                    billing_address.address_type = 'B'
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()

                elif use_default_billing:
                    billing_address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='B',
                        default=True
                    )
                    if billing_address_qs.exists():
                        billing_address = billing_address_qs[0]
                        order.billing_address = billing_address
                        order.save()
                    else:
                        messages.info(self.request, "No default billing address available")
                        return redirect('core:checkout')
                else:
                    billing_address1 = form.cleaned_data.get('billing_address')
                    billing_address2 = form.cleaned_data.get('billing_address2')
                    billing_country = form.cleaned_data.get('billing_country')
                    billing_zip = form.cleaned_data.get('billing_zip')

                    if is_valid_form([billing_address1, billing_country, billing_zip]):
                        billing_address = Address(
                            user=self.request.user,
                            street_address=billing_address1,
                            apartment_address=billing_address2,
                            country=billing_country,
                            zip=billing_zip,
                            address_type='B'
                        )
                        billing_address.save()
                        order.billing_address = billing_address
                        order.save()

                        set_default_billing = form.cleaned_data.get('set_default_billing')
                        if set_default_billing:
                            billing_address.default = True
                            billing_address.save()
                    else:
                        messages.info(self.request, "Please fill in the required billing address fields")

                # Intégration de CinetPay
                transaction_id = f"order_{order.id}"
                amount = cart_total_amount
                data = {
                    "apikey": settings.CINETPAY_API_KEY,
                    "site_id": settings.CINETPAY_SITE_ID,
                    "transaction_id": transaction_id,
                    "amount": amount,
                    "currency": "XOF",
                    "description": f"Payment for order {order.id}",
                    "return_url": self.request.build_absolute_uri('/payment/success/'),
                    "cancel_url": self.request.build_absolute_uri('/payment/fail/'),
                    "notify_url": self.request.build_absolute_uri('/payment/notify/'),
                    "customer_name": self.request.user.username,
                    "customer_email": self.request.user.email,
                    "customer_phone_number": "0000000000",
                    'order_id': '12233',
                }
                print(data)

                # Appel à l'API CinetPay pour initialiser le paiement
                response = requests.post("https://api.cinetpay.com/v1/payment", data=data)
                response.raise_for_status()  # Lève une exception pour les erreurs HTTP

                # Vérifier la réponse
                response_data = response.json()
                print(response_data)  # Affiche la réponse pour vérification

                if response.status_code == 200:
                    payment_data = response.json()
                    payment_url = payment_data['data']['payment_url']

                    # Enregistrer le paiement dans la base de données
                    Payment.objects.create(
                        user=self.request.user,
                        order=order,
                        transaction_id=transaction_id,
                        amount=amount,
                        status='pending'
                    )

                    return JsonResponse({'payment_url': payment_url})
                else:
                    messages.error(self.request, "Erreur lors de l'initialisation du paiement.")
                    return redirect('core:checkout')

            return redirect('core:checkout')

        except ObjectDoesNotExist:
            messages.warning(self.request, "Vous n'avez pas de commande active.")
            return redirect("core:orders")




@csrf_exempt
def cinetpay_notify(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            transaction_id = data.get('transaction_id')
            status = data.get('status')
            payment = Payment.objects.get(transaction_id=transaction_id)

            if status == '00':
                # Paiement réussi
                payment.status = 'COMPLETED'
                payment.order.ordered = True  # Marquer la commande comme complète
                payment.order.save()
            else:
                # Paiement échoué
                payment.status = 'FAILED'
            
            payment.save()
            return JsonResponse({'status': 'success'}, status=200)

        except Payment.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Payment not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
    

def payment_success(request):
    messages.success(request, "Votre paiement a été effectué avec succès.")
    return render(request, 'payment_success.html')

def payment_fail(request):
    messages.error(request, "Votre paiement a échoué.")
    return render(request, 'payment_fail.html')


@login_required
def customer_dashboard(request):
    orders_list = CartOrder.objects.filter(user=request.user).order_by("-id")
    address = Address.objects.filter(user=request.user)

    orders = (
        CartOrder.objects.annotate(month=ExtractMonth("order_date"))
        .values("month")
        .annotate(count=Count("id"))
        .values("month", "count")
    )
    month = []
    total_orders = []

    for i in orders:
        month.append(calendar.month_name[i["month"]])
        total_orders.append(i["count"])

    if request.method == "POST":
        address = request.POST.get("address")
        mobile = request.POST.get("mobile")

        new_address = Address.objects.create(
            user=request.user,
            address=address,
            mobile=mobile,
        )
        messages.success(request, "Address Added Successfully.")
        return redirect("core:dashboard")
    else:
        print("Error")

    user_profile = Profile.objects.get(user=request.user)
    print("user profile is: #########################", user_profile)

    context = {
        "user_profile": user_profile,
        "orders": orders,
        "orders_list": orders_list,
        "address": address,
        "month": month,
        "total_orders": total_orders,
    }
    return render(request, "dashboard.html", context)


@login_required
def customer_orders(request):
    orders_list = CartOrder.objects.filter(user=request.user).order_by("-id")
    address = Address.objects.filter(user=request.user)

    orders = (
        CartOrder.objects.annotate(month=ExtractMonth("order_date"))
        .values("month")
        .annotate(count=Count("id"))
        .values("month", "count")
    )
    month = []
    total_orders = []

    for i in orders:
        month.append(calendar.month_name[i["month"]])
        total_orders.append(i["count"])

    if request.method == "POST":
        address = request.POST.get("address")
        mobile = request.POST.get("mobile")

        new_address = Address.objects.create(
            user=request.user,
            address=address,
            mobile=mobile,
        )
        messages.success(request, "Address Added Successfully.")
        return redirect("core:dashboard")
    else:
        print("Error")

    user_profile = Profile.objects.get(user=request.user)
    print("user profile is: #########################", user_profile)

    context = {
        "user_profile": user_profile,
        "orders": orders,
        "orders_list": orders_list,
        "address": address,
        "month": month,
        "total_orders": total_orders,
    }
    return render(request, "dashboard-orders.html", context)


def order_detail(request, id):
    order = CartOrder.objects.get(user=request.user, id=id)
    order_items = CartOrderProducts.objects.filter(order=order)

    context = {
        "order_items": order_items,
    }
    return render(request, "order-detail.html", context)




def make_address_default(request):
    id = request.GET["id"]
    Address.objects.update(status=False)
    Address.objects.filter(id=id).update(status=True)
    return JsonResponse({"boolean": True})


@login_required
def wishlist_view(request):
    wishlist = wishlist_model.objects.all()
    context = {"w": wishlist}
    return render(request, "wishlist.html", context)

    # w


def add_to_wishlist(request):
    product_id = request.GET["id"]
    product = Product.objects.get(id=product_id)
    print("product id isssssssssssss:" + product_id)

    context = {}

    wishlist_count = wishlist_model.objects.filter(
        product=product, user=request.user
    ).count()
    print(wishlist_count)

    if wishlist_count > 0:
        context = {"bool": True}
    else:
        new_wishlist = wishlist_model.objects.create(
            user=request.user,
            product=product,
        )
        context = {"bool": True}

    return JsonResponse(context)



def remove_wishlist(request):
    pid = request.GET["id"]
    wishlist = wishlist_model.objects.filter(user=request.user)
    wishlist_d = wishlist_model.objects.get(id=pid)
    delete_product = wishlist_d.delete()

    context = {"bool": True, "w": wishlist}
    wishlist_json = serializers.serialize("json", wishlist)
    t = render_to_string("async/wishlist-list.html", context)
    return JsonResponse({"data": t, "w": wishlist_json})


# Other Pages
def contact(request):
    return render(request, "contact.html")


def ajax_contact_form(request):
    full_name = request.GET["full_name"]
    email = request.GET["email"]
    phone = request.GET["phone"]
    subject = request.GET["subject"]
    message = request.GET["message"]

    contact = ContactUs.objects.create(
        full_name=full_name,
        email=email,
        phone=phone,
        subject=subject,
        message=message,
    )

    data = {"bool": True, "message": "Message Sent Successfully"}

    return JsonResponse({"data": data})


def blog(request):
    return render(request, "blog.html")


def about_us(request):
    return render(request, "about.html")


def purchase_guide(request):
    return render(request, "purchase_guide.html")


def privacy_policy(request):
    return render(request, "privacy_policy.html")


def terms_of_service(request):
    return render(request, "terms_of_service.html")
