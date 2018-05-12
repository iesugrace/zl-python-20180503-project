from .models import DirectoryFile, File


def create_directory(name, owner):
    fo = DirectoryFile.objects.create()
    dir = File.objects.create(name=name, owner=owner, is_regular=False)
    dir.link(fo)
    return dir
