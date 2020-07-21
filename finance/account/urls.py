from django.urls import path,include
from django.conf.urls.static import static
from django.conf import settings
from . import views

urlpatterns = [
    path('detail/', views.AccountDetailView.as_view()),
    path('all/', views.AllAccountView.as_view()),
    path('subject/balance/', views.SubjectAccountView.as_view()),
]
