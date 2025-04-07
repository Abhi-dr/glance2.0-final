from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path("alumni_registration/", views.alumni_registration, name="alumni_registration"),
]

