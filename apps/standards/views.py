"""API views for standards management."""

from rest_framework import generics, permissions

from .models import Standard, Control
from .serializers import StandardSerializer, ControlSerializer


class StandardCreateView(generics.CreateAPIView):
    """Create a new compliance standard."""

    queryset = Standard.objects.all()
    serializer_class = StandardSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        standard = serializer.save()

        controls_data = request.data.get('controls', [])
        for control_data in controls_data:
            Control.objects.create(standard=standard, **control_data)

        serializer = self.get_serializer(standard)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class StandardListView(generics.ListAPIView):
    """List all compliance standards."""

    queryset = Standard.objects.all()
    serializer_class = StandardSerializer
    permission_classes = [permissions.AllowAny]


class StandardDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a compliance standard."""

    queryset = Standard.objects.all()
    serializer_class = StandardSerializer
    permission_classes = [permissions.AllowAny]


class ControlListCreateView(generics.ListCreateAPIView):
    """List and create controls for a given standard."""

    serializer_class = ControlSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        standard_id = self.kwargs.get("standard_id")
        return Control.objects.filter(standard_id=standard_id)

    def perform_create(self, serializer):
        standard_id = self.kwargs.get("standard_id")
        serializer.save(standard_id=standard_id)


class ControlDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a control."""

    queryset = Control.objects.all()
    serializer_class = ControlSerializer
    permission_classes = [permissions.AllowAny]
