from concierge.uploader import Uploader


class DropboxUploader(Uploader):
    @classmethod
    def is_available(cls, uploader_type):
        return uploader_type == 'dropbox'
