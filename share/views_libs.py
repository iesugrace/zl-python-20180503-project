from django.conf import settings

from .models import DirectoryFile, File


def create_directory(name, owner):
    fo = DirectoryFile.objects.create()
    dir = File.objects.create(name=name, owner=owner, is_regular=False)
    dir.link(fo)
    return dir


def get_session_id(request):
    name = settings.SESSION_COOKIE_NAME
    sid = request.COOKIES.get(name)
    if sid is None:
        request.session.create()
        sid = request.session.session_key
    return sid


def get_session_data(request, key, sid=None):
    if sid is None:
        sid = get_session_id(request)
    return request.session.get(sid, {}).get(key)


def set_session_data(request, key, data, sid=None):
    if sid is None:
        sid = get_session_id(request)
    sdata = request.session.get(sid, {})
    sdata[key] = data
    request.session[sid] = sdata


def share_approved(request, file):
    approved_shares = get_session_data(request, 'shares') or []
    for share, _ in file.shares():
        if share.pk in approved_shares:
            approved = True
            break
    else:
        approved = False
    return approved


def permission_ok(request, file):
    return (request.user.is_authenticated() or file.shared_to_all()
            or (file.shared_with_code() and share_approved(request, file)))
