"""URL routes for the frontend UI pages."""

from django.urls import path

from .views import (
    analytics,
    audit_results,
    atc_validator,
    chat,
    dashboard,
    documents,
    standards,
    upload,
)

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('upload/', upload, name='upload'),
    # Alias for backwards compatibility: templates or code may refer to either name.
    path('audit-results/', audit_results, name='audit_results'),
    path('audit-results/', audit_results, name='audit-results'),
    path('analytics/', analytics, name='analytics'),
    path('standards/', standards, name='standards'),
    path('documents/', documents, name='documents'),
    path('chat/', chat, name='chat'),
    path('atc-validator/', atc_validator, name='atc-validator'),
]
