"""URL routing for the compliance app."""

from django.urls import path

from .views import (
    ComplianceAuditGraphView,
    ComplianceAuditView,
    AuditResultListView,
    ComplianceChatView,
    ATCNameValidationView,
)

urlpatterns = [
    path("audit/", ComplianceAuditView.as_view(), name="compliance-audit"),
    path("audit/graph/", ComplianceAuditGraphView.as_view(), name="compliance-audit-graph"),
    path("results/", AuditResultListView.as_view(), name="audit-results"),
    path("chat/", ComplianceChatView.as_view(), name="compliance-chat"),

    # ATC naming validation
    path("atc/validate-name/", ATCNameValidationView.as_view(), name="atc-validate-name"),
]
