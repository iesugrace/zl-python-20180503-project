import os

from django.conf import settings


def make_abspath(path):
    return os.path.join(settings.MEDIA_ROOT, path)
