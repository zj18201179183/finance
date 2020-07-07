from django.urls import path,include
from . import views

urlpatterns = [
    path('login/', views.UserAuthView.as_view()),
    path('user/', views.UserViewSet.as_view()),
]
