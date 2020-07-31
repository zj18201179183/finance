from django.urls import path,include
from django.conf.urls.static import static
from django.conf import settings
from . import views

urlpatterns = [
    path('', views.VoucherView.as_view()),
    path('check/', views.VoucherCheckView.as_view()),
    path('transfer', views.TransferView.as_view()),
]
