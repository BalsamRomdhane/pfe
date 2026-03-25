"""URL routing for standards app."""

from django.urls import path

from .views import (
    StandardCreateView,
    StandardListView,
    StandardDetailView,
    ControlListCreateView,
    ControlDetailView,
)

urlpatterns = [
    path("create/", StandardCreateView.as_view(), name="standards-create"),
    path("", StandardListView.as_view(), name="standards-list"),
    path("<int:pk>/", StandardDetailView.as_view(), name="standards-detail"),
    path("<int:standard_id>/controls/", ControlListCreateView.as_view(), name="standard-controls"),
    path("<int:standard_id>/controls/<int:pk>/", ControlDetailView.as_view(), name="standard-control-detail"),
]
