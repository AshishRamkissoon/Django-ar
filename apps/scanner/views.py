import base64
import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.core.paginator import Paginator
from . import services
from .models import ScanSession

logger = logging.getLogger("apps.scanner")

MAX_IMAGE_BYTES = 5_000_000  # 5 MB Base64 limit


@login_required
@require_POST
def scan_view(request):
    image_b64 = request.POST.get("image", "").strip()

    # Input validation
    if not image_b64:
        return render(request, "scanner/partials/error.html",
                      {"message": "No image received."}, status=400)

    if len(image_b64) > MAX_IMAGE_BYTES:
        return render(request, "scanner/partials/error.html",
                      {"message": "Image too large. Please try again."}, status=400)

    try:
        decoded = base64.b64decode(image_b64)
        if not decoded.startswith(b'\xff\xd8'):  # JPEG magic bytes
            raise ValueError("Not a JPEG")
    except Exception:
        return render(request, "scanner/partials/error.html",
                      {"message": "Invalid image format. Please use JPEG."}, status=400)

    try:
        result = services.scan_object(request.user, image_b64)
    except ValueError as e:
        return render(request, "scanner/partials/error.html",
                      {"message": str(e)}, status=400)
    except RuntimeError as e:
        logger.error("Scan error for user %s: %s", request.user.email, e)
        return render(request, "scanner/partials/error.html",
                      {"message": "Scan failed. Please try again."}, status=500)

    return render(request, "scanner/partials/result.html", result)


@login_required
def history_view(request):
    scans = ScanSession.objects.filter(user=request.user)
    paginator = Paginator(scans, 10)
    page = paginator.get_page(request.GET.get("page", 1))
    return render(request, "scanner/history.html", {"page": page})
