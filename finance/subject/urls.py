from django.urls import path,include
from django.conf.urls.static import static
from django.conf import settings
from . import views

urlpatterns = [
    path('', views.SubjectView.as_view()),
    path('setofaccount', views.SetOfAccountsView.as_view()),
    path('setmoney', views.SetSubjectMoneyView.as_view()),
    path('assist', views.AssisView.as_view()),
]
