from django.urls import path
from commission import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    #Commission Sale Urls
    path('record-sale/', views.record_sale, name='record_sale'),
    path('commission-report/', views.commission_report, name='commission_report'),
    # path('success/', views.success, name='success'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

