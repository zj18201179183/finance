from django.urls import path,include
from django.conf.urls.static import static
from django.conf import settings
from . import views

urlpatterns = [
    path('', views.VoucherView.as_view()),
    path('voucher/check/', views.VoucherView.as_view()),
]
