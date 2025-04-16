from django.urls import path
from . import views, dataDownload, views_whatsapp

urlpatterns = [
    path("", views.administration, name="administration"),
    path("companies", views.companies, name="companies"),
    path("filter_page", views.filter_page, name="filter_page"),
    path("get_filtered_students", views.get_filtered_students, name="get_filtered_students"),
    path("test_student_data", views.test_student_data, name="test_student_data"),
    
    path("company/<int:id>", views.company, name="company"),
    path("job_details/<str:slug>", views.job_details, name="job_details"),
    path("applications/<str:slug>", views.applications, name="applications"),
    path("all_registrations", views.all_registrations, name="all_registrations"),
    path("all_students", views.all_students, name="all_students"),
    
    path("shortlisted_students", views.shortlisted_students, name="shortlisted_students"),
    path("rejected_students", views.rejected_students, name="rejected_students"),
    path("add_notification", views.add_notification, name="add_notification"),
    path("send_message_to_filtered_students", views.send_message_to_filtered_students, name="send_message_to_filtered_students"),
    
    # WhatsApp Messaging
    path("whatsapp_message", views.whatsapp_message, name="whatsapp_message"),
    path("whatsapp_test", views_whatsapp.whatsapp_test, name="whatsapp_test"),
    path("api_test", views_whatsapp.api_test, name="api_test"),
    path("send_whatsapp_to_filtered_students", views.send_whatsapp_to_filtered_students, name="send_whatsapp_to_filtered_students"),
    path("send_whatsapp_bulk_csv", views.send_whatsapp_bulk_csv, name="send_whatsapp_bulk_csv"),
    path("download_whatsapp_csv_template", views.download_whatsapp_csv_template, name="download_whatsapp_csv_template"),
    
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
    path("export_filtered_students_pdf", dataDownload.export_filtered_students_pdf, name="export_filtered_students_pdf"),
    path("export_filtered_students", dataDownload.export_filtered_students, name="export_filtered_students"),
    path("export_filtered_documents", dataDownload.export_filtered_documents, name="export_filtered_documents"),
    path("export_all_students", dataDownload.export_all_students, name="export_all_students"),
    path("simple_export", dataDownload.simple_export, name="simple_export"),
    path("filtered_export", dataDownload.filtered_export, name="filtered_export"),
]