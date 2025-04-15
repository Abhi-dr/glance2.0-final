from django.urls import path
from . import views, api_views
from django.contrib.auth.decorators import login_required, user_passes_test
from .api_views import StudentsDataTablesView

urlpatterns = [
    path('login', views.login, name="login"),
    path('register', views.register, name="register"),
    path('logout', views.logout, name="logout"),
    path("Terms-and-conditions", views.tnc, name="tnc"),

    path('check_username_availability/', views.check_username_availability, name='check_username_availability'),
    path('check_mobile_availability/', views.check_mobile_availability, name='check_mobile_availability'),
    # path('reset_password', views.reset_password, name="reset_password"),
    
    # Secure API endpoints with login_required and staff_member_required
    path('api/datatables/students/', 
        login_required(user_passes_test(lambda u: u.is_staff)(StudentsDataTablesView.as_view())), 
        name='datatables_students'
    ),
] 
