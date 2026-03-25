"""URL configuration for the compliance platform."""

from django.contrib import admin
from django.urls import include, path

from apps.ui import views as ui_views
from apps.compliance.views import ATCNameValidationView

urlpatterns = [
    path("favicon.ico", ui_views.favicon),
    path("admin/", admin.site.urls),
    path("", include("apps.ui.urls")),
    path("api/documents/", include("apps.documents.urls")),
    path("api/standards/", include("apps.standards.urls")),
    path("api/compliance/", include("apps.compliance.urls")),
    path("api/analytics/", include("apps.analytics.urls")),

    # ATC filename validation API (explicit route required)
    path("api/atc/validate-name/", ATCNameValidationView.as_view(), name="atc-validate-name"),
]
