from django.urls import path,include
from django.conf.urls.static import static
from django.conf import settings
from . import views

urlpatterns = [
    path('login/', views.UserAuthView.as_view()),
    path('put/', views.UserAuthView.as_view()),
    path('user/', views.UserViewSet.as_view()),
]
