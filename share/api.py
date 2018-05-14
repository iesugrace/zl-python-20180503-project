from django.contrib import auth
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


@csrf_exempt
@require_POST
def login(request):
    username = request.POST.get('username')
    password = request.POST.get('password')
    user = auth.authenticate(username=username, password=password)
    if user is not None and user.is_active:
        auth.login(request, user)
        data = {'status': True}
    else:
        data = {'status': False}
    return JsonResponse(data)


def logout(request):
    auth.logout(request)
    data = {'status': False}
    return JsonResponse(data)


