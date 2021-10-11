from concierge.uploader import Uploader


class LocalUploader(Uploader):
    @classmethod
    def is_available(cls, uploader_type):
        return uploader_type == 'local'
