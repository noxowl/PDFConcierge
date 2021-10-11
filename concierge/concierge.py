import os
import sys
from .uploader import Uploader, LocalUploader
from .scraper import MkScraper


def is_true(value) -> bool:
    return value.lower() == 'true' if value else False


class PDFConcierge:
    def __init__(self):
        self.uploader = None
        self.local_uploader = None
        self.mk_scraper = None
        self.allow_local_backup = is_true(os.environ.get('PDFC_ALLOW_LOCAL_BACKUP'))
        self.when_conflict = os.environ.get('PDFC_WHEN_CONFLICT')
        self.use_history = is_true(os.environ.get('PDFC_USE_HISTORY'))
        self.history_reference = os.environ.get('PDFC_HISTORY_REFERENCE')
        self.upload_to = os.environ.get('PDFC_UPLOAD_TO')
        self.cloud_token = os.environ.get('PDFC_CLOUD_TOKEN')
        self.mk_id = os.environ.get('PDFC_MK_ID')
        self.mk_pw = os.environ.get('PDFC_MK_PW')

    def initialize(self):
        self.uploader = self._create_uploader()
        if self.allow_local_backup:
            self.local_uploader = LocalUploader('local')
        if self.mk_id:
            self.mk_scraper = MkScraper(mk_id=self.mk_id, mk_pw=self.mk_pw)

    def _create_uploader(self):
        for cls in Uploader.__subclasses__():
            if cls.is_available(self.upload_to):
                return cls(self.upload_to)
        raise ValueError

    def execute(self):
        self.initialize()
        sys.exit()


app = PDFConcierge()
