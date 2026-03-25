"""API views for analytics endpoints."""

from rest_framework.response import Response
from rest_framework.views import APIView

from .services.analytics_service import AnalyticsService


class DashboardView(APIView):
    """Return analytics dashboard data."""

    def get(self, request):
        service = AnalyticsService()
        data = service.get_dashboard()
        return Response(data)
