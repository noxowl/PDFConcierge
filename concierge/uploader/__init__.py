

class Uploader(object):
    def __init__(self, uploader_type):
        self.uploader_type = uploader_type


from .local import LocalUploader
from .dropbox import DropboxUploader
