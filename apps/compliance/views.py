"""API views for running compliance audits."""

import json

from rest_framework import status
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.compliance.services.compliance_service import ComplianceService
from apps.documents.models import Document
from apps.standards.models import Standard

from .serializers import AuditResultSerializer

from services.langgraph_workflow import LangGraphAuditWorkflow

from rest_framework.permissions import AllowAny


class ComplianceAuditView(APIView):
    """Run a compliance audit against one or more documents."""

    permission_classes = [AllowAny]

    def post(self, request):
        document_ids = request.data.get("document_ids", [])
        standard_id = request.data.get("standard_id")

        if not document_ids or not standard_id:
            return Response(
                {"detail": "document_ids and standard_id are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        standard = Standard.objects.filter(id=standard_id).first()
        if not standard:
            return Response({"detail": "Standard not found."}, status=status.HTTP_404_NOT_FOUND)

        documents = list(Document.objects.filter(id__in=document_ids))
        if not documents:
            return Response({"detail": "No documents found."}, status=status.HTTP_404_NOT_FOUND)

        service = ComplianceService()
        results = []
        for document in documents:
            # Persist the standard association on the document so it is visible in the Documents table.
            if document.standard_id != standard.id:
                document.standard = standard
                document.save(update_fields=["standard"])

            audit_result = service.run_audit(document, standard)
            results.append(AuditResultSerializer(audit_result).data)

        return Response({"results": results})


class ComplianceAuditGraphView(APIView):
    """Run a compliance audit using the LangGraph workflow."""

    permission_classes = [AllowAny]

    def post(self, request):
        document_ids = request.data.get("document_ids", [])
        standard_id = request.data.get("standard_id")

        if not document_ids or not standard_id:
            return Response(
                {"detail": "document_ids and standard_id are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        standard = Standard.objects.filter(id=standard_id).first()
        if not standard:
            return Response({"detail": "Standard not found."}, status=status.HTTP_404_NOT_FOUND)

        documents = list(Document.objects.filter(id__in=document_ids))
        if not documents:
            return Response({"detail": "No documents found."}, status=status.HTTP_404_NOT_FOUND)

        workflow = LangGraphAuditWorkflow()
        results = []

        for document in documents:
            if document.standard_id != standard.id:
                document.standard = standard
                document.save(update_fields=["standard"])

            report = workflow.run(document, standard)
            results.append(report)

        return Response({"results": results})


class AuditResultListView(APIView):
    """List audit results in the system."""

    # When requested from the UI (fetch/AJAX), we want JSON by default.
    # The HTML view remains available for direct browser access.
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = "api_results.html"

    def get(self, request):
        queryset = AuditResultSerializer.Meta.model.objects.all().order_by("-created_at")
        
        # Filter by document_id if provided
        document_id = request.query_params.get('document_id')
        if document_id:
            queryset = queryset.filter(document_id=document_id)
        
        serializer = AuditResultSerializer(queryset, many=True)

        # If the request accepts HTML, render a human-friendly view.
        if request.accepted_renderer.format == "html":
            return Response(
                {"payload": json.dumps(serializer.data, indent=2, ensure_ascii=False)},
                template_name=self.template_name,
            )

        return Response(serializer.data)


class ComplianceChatView(APIView):
    """Simple compliance chat endpoint."""

    permission_classes = [AllowAny]

    def get(self, request):
        # Make the endpoint friendly when opened in a browser.
        return Response(
            {
                "message": "POST a JSON payload like {\"message\": \"Hello\"} to this endpoint to receive a response.",
            }
        )

    def post(self, request):
        message = request.data.get("message", "")
        reply = (
            "I am a compliance assistant. "
            "For document questions, upload your document and run an audit, then ask about the results."
        )
        if message:
            # Minimal heuristic response
            if "audit" in message.lower():
                reply = "Run a compliance audit first, then view the results page for score and violations."
            elif "standard" in message.lower():
                reply = "Standards can be created in Standards Manager. Use it to define controls."
            elif "risk" in message.lower():
                reply = "Risks are derived from violations and missing controls. Check the audit results."

        return Response({"reply": reply})


class ATCNameValidationView(APIView):
    """API endpoint for validating ATC document filename conventions."""

    permission_classes = [AllowAny]

    def post(self, request):
        from services.document_name_validator import validate_filename
        from apps.compliance.models import ATCNameValidation

        filename = request.data.get("filename")
        result = validate_filename(filename)

        # Log validation for analytics
        try:
            ATCNameValidation.objects.create(
                filename=result.get("filename") or "",
                status=result.get("status") or "NON_COMPLIANT",
                reason=result.get("reason") or "",
            )
        except Exception:
            # Do not fail the API if persistence fails.
            pass

        return Response(result)
