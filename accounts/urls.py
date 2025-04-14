from django.urls import path, include
from . import views

urlpatterns = [
    path('login', views.login, name="login"),
    path('register', views.register, name="register"),
    path('logout', views.logout, name="logout"),
    path("Terms-and-conditions", views.tnc, name="tnc"),

    path('check_username_availability/', views.check_username_availability, name='check_username_availability'),
    path('check_mobile_availability/', views.check_mobile_availability, name='check_mobile_availability'),

    # path('reset_password', views.reset_password, name="reset_password"),
] 
