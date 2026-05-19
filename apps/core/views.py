from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


def landing(request):
    if request.user.is_authenticated:
        return redirect("ar_view")
    return render(request, "core/landing.html")


@login_required
def ar_view(request):
    return render(request, "scanner/ar_view.html")
