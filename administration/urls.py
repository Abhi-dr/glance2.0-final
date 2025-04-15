from django.urls import path
from . import views, dataDownload

urlpatterns = [
    path("", views.administration, name="administration"),
    path("companies", views.companies, name="companies"),
    path("filter_page", views.filter_page, name="filter_page"),
    
    path("company/<int:id>", views.company, name="company"),
    path("job_details/<str:slug>", views.job_details, name="job_details"),
    path("applications/<str:slug>", views.applications, name="applications"),
    path("all_registrations", views.all_registrations, name="all_registrations"),
    path("all_students", views.all_students, name="all_students"),
    
    path("shortlisted_students", views.shortlisted_students, name="shortlisted_students"),
    path("rejected_students", views.rejected_students, name="rejected_students"),
    path("add_notification", views.add_notification, name="add_notification"),
    
    # ======================== Applications Toggles ========================
    
    path("accept_application/<int:id>", views.accept_application, name="accept_application"),
    path("reject_application/<int:id>", views.reject_application, name="reject_application"),
    path("change_to_pending/<int:id>", views.change_to_pending, name="change_to_pending"),
    
    # ======================== Company / Job Modifications ========================
    
    path("add_company", views.add_company, name="add_company"),
    path("add_job/<int:id>", views.add_job, name="add_job"),
    
    path("export_unapplied_students_csv", dataDownload.export_unapplied_students_csv, name="export_unapplied_students_csv"),
    path("export_company_applications_summary_csv", dataDownload.export_company_applications_summary_csv, name="export_company_applications_summary_csv"),
    path("export_uneligible_students", dataDownload.export_uneligible_students, name="export_uneligible_students"),
    path("export_job_applications_csv/<int:job_id>", dataDownload.export_job_applications_csv, name="export_job_applications_csv"),
    path("download_job_resumes/<int:job_id>", dataDownload.download_job_resumes, name="download_job_resumes"),
    path("download_resumes", dataDownload.download_resumes, name="download_resumes"),

]