from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render

from rating.utils import transliterate_name


@login_required
@user_passes_test(lambda u: u.is_superuser)
def system_index(request):
    return render(request, 'system_index.html')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def transliterate_text(request):
    text = ''
    if request.POST.get('text'):
        text = transliterate_name(request.POST.get('text'))
    return render(request, 'transliterate.html', {'text': text})
