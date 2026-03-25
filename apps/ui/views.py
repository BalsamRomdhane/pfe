"""Views rendering the frontend SPA pages."""

import base64

from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie


@ensure_csrf_cookie
def dashboard(request):
    return render(request, "dashboard.html")


@ensure_csrf_cookie
def upload(request):
    return render(request, "upload.html")


@ensure_csrf_cookie
def audit_results(request):
    return render(request, "audit_results.html")


@ensure_csrf_cookie
def analytics(request):
    return render(request, "analytics.html")


@ensure_csrf_cookie
def standards(request):
    return render(request, "standards.html")


@ensure_csrf_cookie
def documents(request):
    return render(request, "documents.html")


@ensure_csrf_cookie
def chat(request):
    return render(request, "chat.html")


@ensure_csrf_cookie
def atc_validator(request):
    return render(request, "atc_validator.html")


def favicon(request):
    """Serve a small favicon to prevent 404 noise."""

    # A 1x1 transparent PNG (base64-encoded) to satisfy browser favicon requests.
    favicon_png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8Xw8AAsMBgX1Lj2cAAAAASUVORK5CYII="
    )
    return HttpResponse(favicon_png, content_type="image/png")
