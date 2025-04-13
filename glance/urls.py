from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('mClk3W)$t=/', admin.site.urls),

    path('', include("home.urls")),
    path('accounts/', include("accounts.urls")),
    path('student/', include("student.urls")),
    path("administration/", include("administration.urls")),
    path('volunteer/', include('volunteer.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# handle 404
 
handler404 = "accounts.views.page_not_found_view"