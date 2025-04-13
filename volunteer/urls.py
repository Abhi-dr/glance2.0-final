from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.volunteer_dashboard, name='volunteer_dashboard'),
    path('applications/', views.volunteer_applications, name='volunteer_applications'),
    path('applications/date/<str:date>/', views.volunteer_applications_by_date, name='volunteer_applications_by_date'),
    path('attendance/', views.volunteer_attendance, name='volunteer_attendance'),
    path('mark-attendance/<int:application_id>/<str:status>/', views.mark_attendance, name='mark_attendance'),
    path('change-attendance/<int:attendance_id>/', views.change_attendance, name='change_attendance'),
    path('export-attendance-csv/', views.export_attendance_csv, name='export_attendance_csv'),
] 