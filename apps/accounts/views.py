from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import APIKeyForm


@login_required
def profile(request):
    profile = request.user.profile
    if request.method == "POST":
        form = APIKeyForm(request.POST)
        if form.is_valid():
            profile.set_api_key(form.cleaned_data["api_key"])
            profile.save()
            messages.success(request, "API key saved successfully.")
            return redirect("profile")
    else:
        form = APIKeyForm()

    return render(request, "accounts/profile.html", {
        "form": form,
        "has_key": profile.has_api_key(),
        "scan_count": profile.scan_count,
    })
