"""URL routing for the documents app."""

from django.urls import path

from .views import DocumentUploadView, DocumentBulkUploadView, DocumentDetailView, DocumentListView

urlpatterns = [
    path("upload/", DocumentUploadView.as_view(), name="document-upload"),
    path("bulk-upload/", DocumentBulkUploadView.as_view(), name="document-bulk-upload"),
    path("<int:pk>/", DocumentDetailView.as_view(), name="document-detail"),
    path("", DocumentListView.as_view(), name="document-list"),
]
