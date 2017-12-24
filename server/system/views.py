from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render


@login_required
@user_passes_test(lambda u: u.is_superuser)
def system_index(request):
    return render(request, 'system_index.html')
