from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render

from utils.general import transliterate_name


@login_required
@user_passes_test(lambda u: u.is_superuser)
def system_index(request):
    return render(request, "system_index.html")


@login_required
@user_passes_test(lambda u: u.is_superuser)
def transliterate_text(request):
    original_text = ""
    transliterated_text = ""

    if request.POST.get("text"):
        original_text = request.POST.get("text")
        transliterated_text = transliterate_name(original_text)

    return render(
        request, "transliterate.html", {"original_text": original_text, "transliterated_text": transliterated_text}
    )
