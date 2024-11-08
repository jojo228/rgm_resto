from django.contrib import admin
from core.models import (
    CartOrderProducts,
    Payment,
    Product,
    Category,
    CartOrder,
    ProductImages,
    ProductReview,
    wishlist_model,
    Address,
    Contact,
    Event,
    Catalogue,
    CatalogueCategory
)


class ProductImagesAdmin(admin.TabularInline):
    model = ProductImages


class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImagesAdmin]
    list_editable = ["title", "price"]
    list_display = [
        "user",
        "title",
        "product_image",
        "price",
        "category",
        "pid",
    ]


class CategoryAdmin(admin.ModelAdmin):
    list_display = ["title", "category_image"]


class CartOrderAdmin(admin.ModelAdmin):
    list_editable = ["paid_status",  "sku"]
    list_display = [
        "user",
        "price",
        "paid_status",
        "order_date",
        "sku",
    ]


class CartOrderProductsAdmin(admin.ModelAdmin):
    list_display = ["user","order", "item", "order_image", "qty", "price", "total"]


class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ["user", "product", "review", "rating"]


class wishlistAdmin(admin.ModelAdmin):
    list_display = ["user", "product", "date"]


class PaymentAdmin(admin.ModelAdmin):
    list_display = ["order", "transaction_id", "amount", "status"]


class AddressAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'street_address',
        'apartment_address',
        'country',
        'zip',
        'ville',
        'whatsapp',
        'default'
    ]
    list_filter = ['default', 'ville', 'country', 'whatsapp']
    search_fields = ['user', 'street_address', 'apartment_address', 'zip']


admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(CartOrder, CartOrderAdmin)
admin.site.register(CartOrderProducts, CartOrderProductsAdmin)
admin.site.register(ProductReview, ProductReviewAdmin)
admin.site.register(wishlist_model, wishlistAdmin)
admin.site.register(Address, AddressAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Contact)
admin.site.register(Event)
admin.site.register(Catalogue)
admin.site.register(CatalogueCategory)
