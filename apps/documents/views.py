"""Views for document ingestion and processing."""

import math

from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Document
from .serializers import DocumentSerializer
from .services.document_processor import DocumentProcessor


@method_decorator(csrf_exempt, name='dispatch')
class DocumentUploadView(APIView):
    """Upload a single document and trigger processing."""

    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        import logging
        from .services.ocr_service import extract_text_from_file
        from services.chunking_service import _normalize_text

        logger = logging.getLogger(__name__)
        file_obj = request.FILES.get("file")
        standard_id = request.data.get("standard")

        if not file_obj:
            return Response({"detail": "File is required."}, status=status.HTTP_400_BAD_REQUEST)

        document = Document.objects.create(file=file_obj, standard_id=standard_id)

        # Extract text immediately after upload
        file_path = document.file.path
        raw_text = extract_text_from_file(file_path)
        logger.info("[UPLOAD] Extracted raw text length: %d", len(raw_text) if raw_text else 0)
        logger.info("[UPLOAD] Extracted text preview: %s", (raw_text or "")[:1000])

        cleaned_text = _normalize_text(raw_text)
        logger.info("[UPLOAD] Cleaned text length: %d", len(cleaned_text) if cleaned_text else 0)
        logger.info("[UPLOAD] Cleaned text preview: %s", (cleaned_text or "")[:1000])

        # Store extracted text in the model
        document.extracted_text = cleaned_text
        document.save(update_fields=["extracted_text"])

        # Optionally, trigger downstream processing (can be deferred)
        processor = DocumentProcessor()
        processor.process(document)

        serializer = DocumentSerializer(document)
        # Return extracted_text in the response for preview/debug
        data = serializer.data
        data["extracted_text"] = cleaned_text
        return Response(data, status=status.HTTP_201_CREATED)


class DocumentBulkUploadView(APIView):
    """Upload multiple documents in a single request."""

    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        files = request.FILES.getlist("files")
        standard_id = request.data.get("standard")

        if not files:
            return Response({"detail": "At least one file must be provided."}, status=status.HTTP_400_BAD_REQUEST)

        created_documents = []
        processor = DocumentProcessor()

        for f in files:
            document = Document.objects.create(file=f, standard_id=standard_id)
            processor.process(document)
            created_documents.append(document)

        serializer = DocumentSerializer(created_documents, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DocumentDetailView(APIView):
    """Retrieve or delete a document."""

    # Allow deleting documents without requiring authentication (used for dev/demo).
    # If you need auth, replace with a proper permission class (e.g., IsAuthenticated).
    permission_classes = [AllowAny]

    def delete(self, request, pk):
        try:
            document = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            return Response({"detail": "Document not found."}, status=status.HTTP_404_NOT_FOUND)

        processor = DocumentProcessor()
        processor.delete_document(document)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DocumentListView(APIView):
    """List uploaded documents."""

    def get(self, request):
        queryset = Document.objects.order_by("-uploaded_at").all()

        standard_id = request.GET.get("standard")
        search = (request.GET.get("search") or "").strip()

        if standard_id:
            queryset = queryset.filter(standard_id=standard_id)

        if search:
            queryset = queryset.filter(
                Q(file__icontains=search)
                | Q(text__icontains=search)
                | Q(standard__name__icontains=search)
            )

        try:
            page = int(request.GET.get("page", 1))
        except (TypeError, ValueError):
            page = 1

        try:
            page_size = int(request.GET.get("page_size", 20))
        except (TypeError, ValueError):
            page_size = 20

        total = queryset.count()
        total_pages = max(1, math.ceil(total / page_size)) if page_size else 1

        if page < 1:
            page = 1
        if page > total_pages:
            page = total_pages

        if page_size:
            start = (page - 1) * page_size
            end = start + page_size
            queryset = queryset[start:end]

        serializer = DocumentSerializer(queryset, many=True)
        return Response(
            {
                "results": serializer.data,
                "page": page,
                "total_pages": total_pages,
                "total": total,
            }
        )
