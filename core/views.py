import json
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import View
from regex import E
import uuid
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator
from requests import session
import requests
from core.models import (
    CatalogueCategory,
    Event,
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
from core.forms import CheckoutForm, ContactForm, ProductReviewForm
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
    # Get all categories that have at least one product, then select a product from each
    categories_with_products = Category.objects.annotate(product_count=Count('category')).filter(product_count__gt=0)

    # Now retrieve one product from each category
    products = []

    for category in categories_with_products:
        # Get one product from each category
        product = Product.objects.filter(category=category).first()
        if product:
            products.append(product)
    patisserie = Product.objects.filter(category=1).count()
    cuisine = Product.objects.filter(category=2).count()
    fast_food = Product.objects.filter(category=3).count()
    autre = Product.objects.filter(category=4).count()
    events = Event.objects.all().order_by('-created_at')[:6]

    return render(request, "index.html", locals())



def product_list_view(request):
    # Fetch all products and order them by id
    products = Product.objects.all().order_by("-id")

    # Set up pagination (6 products per page in this example)
    paginator = Paginator(products, 9)
    
    # Get the current page number from the request
    page_number = request.GET.get('page')

    # Get the products for the current page
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,  # Pass the page object to the template
    }

    return render(request, "all-food.html", context)



def category_list_view(request):
    categories = Category.objects.all()

    context = {"categories": categories}
    return render(request, "category-list.html", context)


def catalogue_list(request):
    categories = CatalogueCategory.objects.prefetch_related('catalogue_set').all()
    context = {
        'categories': categories
    }
    return render(request, "catalogue.html", context)


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
            cleaned_price = item["price"].replace(',', '').replace('f', '').strip()
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

            if "cart_data_obj" in self.request.session:
                for p_id, item in self.request.session["cart_data_obj"].items():
                    cleaned_price = item["price"].replace(',', '').replace('f', '').strip()
                    total_amount += int(item["qty"]) * float(cleaned_price)

                cart_data = self.request.session.get("cart_data_obj", {})
                totalcartitems = len(cart_data)

                order = CartOrder.objects.filter(user=self.request.user, ordered=False).first()
                form = CheckoutForm()

                context = {
                    'form': form,
                    'order': order,
                    'DISPLAY_COUPON_FORM': True,
                    "cart_data": cart_data,
                    "totalcartitems": totalcartitems,
                    "cart_total_amount": total_amount,
                }

                shipping_address_qs = Address.objects.filter(
                    user=self.request.user,
                    default=True
                )
                if shipping_address_qs.exists():
                    context.update({'default_shipping_address': shipping_address_qs[0]})

                return render(self.request, "checkout.html", context)

        except ObjectDoesNotExist:
            messages.info(self.request, "You do not have an active order")
            return redirect("core:checkout")

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        total_amount = 0

        shipping_address = self.request.POST.get('shipping_address')
        shipping_address2 = self.request.POST.get('shipping_address2')
        shipping_country = self.request.POST.get('id_shipping_country')
        shipping_zip = self.request.POST.get('shipping_zip')
        ville = self.request.POST.get('ville')
        whatsapp = self.request.POST.get('whatsapp')
        use_default_shipping = self.request.POST.get('use_default_shipping')
        set_default_shipping = self.request.POST.get('set_default_shipping')

        try:
            # Calculate total amount
            for p_id, item in self.request.session["cart_data_obj"].items():
                cleaned_price = item["price"].replace(',', '').replace('f', '').strip()
                total_amount += int(item["qty"]) * float(cleaned_price)

            order, created = CartOrder.objects.get_or_create(
                user=self.request.user,
                ordered=False,
                defaults={'price': total_amount}
            )

            # Create CartOrderProducts for each item in the cart
            for p_id, item in self.request.session["cart_data_obj"].items():
                cleaned_price = item["price"].replace(',', '').replace('f', '').strip()

                # Check if CartOrderProduct for the same item already exists for this order
                product_exists = CartOrderProducts.objects.filter(
                    order=order,
                    item=item["title"]
                ).exists()

                if not product_exists:
                    CartOrderProducts.objects.create(
                        user=self.request.user,
                        order=order,
                        item=item["title"],
                        image=item["image"],
                        qty=item["qty"],
                        price=float(cleaned_price),
                        total=int(item["qty"]) * float(cleaned_price),
                    )

            if form.is_valid():
                use_default_shipping = form.cleaned_data.get('use_default_shipping')
                if use_default_shipping:
                    shipping_address_qs = Address.objects.filter(
                        user=self.request.user,
                        default=True
                    )
                    if shipping_address_qs.exists():
                        order.shipping_address = shipping_address_qs[0]
                    else:
                        messages.info(self.request, "No default shipping address available")
                        return redirect('core:checkout')
                else:
                    shipping_address1 = form.cleaned_data.get('shipping_address')
                    shipping_address2 = form.cleaned_data.get('shipping_address2')
                    shipping_country = form.cleaned_data.get('id_shipping_country')
                    shipping_zip = form.cleaned_data.get('shipping_zip')
                    ville = form.cleaned_data.get('ville')
                    whatsapp = form.cleaned_data.get('whatsapp')

                    if is_valid_form([shipping_address1, shipping_address2, shipping_country, shipping_zip, ville, whatsapp]):
                        shipping_address = Address(
                            user=self.request.user,
                            street_address=shipping_address1,
                            apartment_address=shipping_address2,
                            country=shipping_country,
                            zip=shipping_zip,
                            ville=ville,
                            whatsapp=whatsapp,
                        )
                        shipping_address.save()
                        order.shipping_address = shipping_address

                        set_default_shipping = form.cleaned_data.get('set_default_shipping')
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()
                    else:
                        messages.info(self.request, "Please fill in the required shipping address fields")
                        return redirect('core:checkout')

                order.save()
                return redirect('core:checkout')

        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order.")
            return redirect("core:orders")

        


@method_decorator(csrf_exempt, name='dispatch')
class PaymentInitializationView(View):
    def post(self, request, *args, **kwargs):
        try:
            # Récupérer les données du formulaire
            data = request.POST
            shipping_address = data.get('shipping_address')
            shipping_address2 = data.get('shipping_address2')
            shipping_country = data.get('shipping_country')
            shipping_zip = data.get('shipping_zip')
            
            use_default_shipping = data.get('use_default_shipping') == 'true'
            set_default_shipping = data.get('set_default_shipping') == 'true'
            
            payment_option = data.get('payment_option')

            # Vous pouvez ajouter ici la logique pour sauvegarder ces informations dans votre base de données si nécessaire

            # Calculer le montant total du panier
            cart_data = request.session.get('cart_data_obj', {})
            total_amount = sum(int(item['qty']) * float(item['price']) for item in cart_data.values())

            if total_amount <= 0:
                return JsonResponse({'error': 'Le montant total doit être supérieur à zéro.'}, status=400)

            # Get or create an active CartOrder for the user
            order, created = CartOrder.objects.get_or_create(
                user=request.user,
                ordered=False,
                defaults={'price': total_amount}
            )
            
            # Update the order price if it was retrieved and not created
            if not created:
                order.price = total_amount
                order.save()

            # Retrieve the order SKU
            order_sku = order.sku

            # Générer un identifiant unique pour la transaction
            transaction_id = str(uuid.uuid4())

            # Préparer les données pour l'API CinetPay
            cinetpay_data = {
                'apikey': settings.CINETPAY_API_KEY,
                'site_id': settings.CINETPAY_SITE_ID,
                'transaction_id': transaction_id,
                'amount': str(total_amount),
                'currency': 'XOF',
                'channels': 'ALL',
                'description': 'Paiement de commande',
                'return_url': request.build_absolute_uri('/payment/return/'),
                'notify_url': request.build_absolute_uri('/payment/notify/'),
                'metadata': json.dumps({'session_id': request.session.session_key}), 
                'customer_id': request.user.id if request.user.is_authenticated else 'Anonymous',
                'customer_name': request.user.username if request.user.is_authenticated else 'Anonymous',
                'customer_surname': request.user.username if request.user.is_authenticated else 'Anonymous',
                'customer_email': request.user.email if request.user.is_authenticated else 'anonymous@example.com',
                'customer_phone_number': '00000000',  # Remplacez par un numéro valide si disponible
                'customer_address': shipping_address,
                'customer_city': 'Lome',
                'customer_state': 'Lome',
                'customer_country': 'TG',
                'customer_zip_code': shipping_zip,
                
            }
            print("data are :", cinetpay_data)

            # Envoyer la requête à CinetPay
            response = requests.post(
                'https://api-checkout.cinetpay.com/v2/payment',
                json=cinetpay_data
            )

            response_data = response.json()

            if response.status_code == 200 and response_data.get('code') == '201':
                payment_url = response_data['data']['payment_url']
                # Vous pouvez sauvegarder les détails de la transaction ici si nécessaire
                payment = Payment.objects.update_or_create(
                    transaction_id=transaction_id,
                    defaults={
                        'order': order,
                        'amount': total_amount,
                        'status': "PENDING",
                    }
        )
                return JsonResponse({'payment_url': payment_url})
            else:
                error_message = response_data.get('description', 'Une erreur est survenue lors de l\'initialisation du paiement.')
                return JsonResponse({'error': error_message}, status=400)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)



@csrf_exempt
def payment_notify(request):
    if request.method == 'POST':
        try:
            # Charger les données envoyées par CinetPay
            data = json.loads(request.body)

            # Extraire les données importantes
            transaction_id = data.get('cpm_trans_id')

            # Vérifier que les données nécessaires sont présentes
            if not transaction_id is None:
                return JsonResponse({'error': 'Missing transaction data.'}, status=400)

            # Requête de vérification à l'API de CinetPay pour confirmer le statut
            verification_url = "https://api-checkout.cinetpay.com/v2/payment/check"
            verification_data = {
                "apikey": settings.CINETPAY_API_KEY,
                "site_id": settings.CINETPAY_SITE_ID,
                "transaction_id": transaction_id,
            }
            response = requests.post(verification_url, json=verification_data)
            verification_result = response.json()

            # Validation du statut de la transaction auprès de CinetPay
            confirmed_status = verification_result.get('code')
            amount = verification_result.get('amount')

            # Vérifier si le paiement existe dans la base de données
            try:
                payment = Payment.objects.get(transaction_id=transaction_id)
            except Payment.DoesNotExist:
                return JsonResponse({'error': 'Transaction not found.'}, status=404)

            # Mise à jour du statut en fonction du statut confirmé
            if confirmed_status == '00':  # Code de succès de CinetPay
                payment.status = 'COMPLETED'
                payment.order.ordered = True
                payment.order.paid_status = True
                payment.order.save()

                # Mise à jour des produits dans la commande
                CartOrderProducts.objects.filter(order=payment.order).update(ordered=True)
            else:
                payment.status = 'FAILED'

            # Sauvegarde de la mise à jour
            payment.save()

            return JsonResponse({'status': 'success'})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)



@method_decorator(csrf_exempt, name='dispatch')
class PaymentReturnView(View):
    def post(self, request, *args, **kwargs):
        # Récupérer les paramètres `transaction_id` et `token` envoyés par CinetPay
        transaction_id = request.POST.get('transaction_id')
        token = request.POST.get('token')  # Optionnel si nécessaire pour d'autres vérifications

        # Vérifier si le `transaction_id` est fourni
        if not transaction_id:
            return render(request, 'payment_return.html', {'payment_status': 'Transaction ID missing.'})

        # Chercher le paiement correspondant
        try:
            payment = Payment.objects.get(transaction_id=transaction_id)
        except Payment.DoesNotExist:
            return render(request, 'payment_return.html', {'payment_status': 'Payment not found.'})

        # Déterminer le statut du paiement pour afficher le message approprié
        if payment.status == 'COMPLETED':
            payment_status = "Votre paiement a été effectué avec succès."
        elif payment.status == 'FAILED':
            payment_status = "Votre paiement a échoué. Veuillez réessayer ou contacter le support."
        else:
            payment_status = "Le paiement est en attente. Veuillez réessayer."

        # Rendre la page de retour avec le statut du paiement
        return render(request, 'payment_return.html', {'payment_status': payment_status})






@login_required
def customer_dashboard(request):
    orders_list = CartOrder.objects.filter(user=request.user).order_by("-id")
    orders_count = CartOrder.objects.filter(user=request.user).count()
    address = Address.objects.filter(user=request.user, default=True).last()

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
        "orders_count": orders_count,
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


def event(request):
    events = Event.objects.all().order_by('-created_at')
    paginator = Paginator(events, 6)  # Show 6 events per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'events': page_obj,
    }
    return render(request, 'event.html', context)

# Detail view for a single event
def event_detail_view(request, pk):
    event = get_object_or_404(Event, pk=pk)
    last_events = Event.objects.all().order_by('-created_at')[:6]
    context = {
        'event': event,
        'last_events': last_events,
    }
    return render(request, 'event-detail.html', context)


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


def trust_safety(request):
    return render(request, "trust-safety.html")


def privacy_policy(request):
    return render(request, "privacy-policy.html")


def terms_of_service(request):
    return render(request, "terms-service.html")


def register_phone(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('core:success')  # Redirect to a success page or the same page with a success message
    else:
        form = ContactForm()
    return render(request, 'index.html', {'form': form})


def success(request):
    return render(request, 'success.html')
