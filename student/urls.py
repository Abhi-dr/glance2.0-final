from django.urls import path, include
from . import views, profile

urlpatterns = [
    path('home', views.home, name="student"),
    path("my_applications", views.my_applications, name="my_applications"),
    path("job/<str:slug>", views.job_details, name="student_job_details"),
    path("applied_job/<str:slug>", views.applied_job, name="applied_job"),
    
    path("upload_documents", views.upload_resume, name="upload_resume"),
    path("all_jobs", views.all_jobs, name="all_jobs"),
    
    path("confirm_application/<str:slug>", views.confirm_application, name="confirm_application"),
    path("apply_job/<str:slug>", views.apply_job, name="apply_job"),
    path("withdraw_application/<str:slug>", views.withdraw_application, name="withdraw_application"),
    path("withdraw_application_by_id/<int:app_id>", views.withdraw_application_by_id, name="withdraw_application_by_id"),
    
    path('notifications', views.notifications, name='notifications'),    
    path("support", views.support, name="support"),

]

urlpatterns += [
    path("my_profile", profile.my_profile, name="my_profile"),
    path("edit_profile", profile.edit_profile, name="edit_profile"),
    path('upload_profile', profile.upload_profile, name='upload_profile'),
]

