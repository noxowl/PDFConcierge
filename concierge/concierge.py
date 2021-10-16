import os
import sys
from .storage import Storage, LocalStorage
from .scraper import MkScraper

conflict_mode = {
    'add': 'add',
    'overwrite': 'overwrite',
    'update': 'update'
}

pdf_format = {
    'a4': 'a4',
    'kindle': 'kindle',
    'all': 'all',
    'pass-through': 'pass-through'
}


def is_true(value) -> bool:
    return value.lower() == 'true' if value else False


def when_conflict_mode(condition) -> str:
    try:
        return conflict_mode[condition]
    except KeyError:
        return conflict_mode['overwrite']


def pdf_format_mode(mode) -> str:
    try:
        return pdf_format[mode]
    except KeyError:
        return pdf_format['pass-through']


class PDFConcierge:
    def __init__(self):
        self.storage = None
        self.local_storage = None
        self.mk_scraper = None
        self.allow_local_backup = is_true(os.environ.get('PDFC_ALLOW_LOCAL_BACKUP'))
        self.when_conflict = when_conflict_mode(os.environ.get('PDFC_WHEN_CONFLICT'))
        self.pdf_format = pdf_format_mode(os.environ.get('PDFC_PDF_FORMAT'))
        self.use_history = is_true(os.environ.get('PDFC_USE_HISTORY'))
        # self.history_reference = os.environ.get('PDFC_HISTORY_REFERENCE')
        self.storage_type = os.environ.get('PDFC_STORAGE')
        self.storage_token = os.environ.get('PDFC_CLOUD_TOKEN')
        self.mk_id = os.environ.get('PDFC_MK_ID')
        self.mk_pw = os.environ.get('PDFC_MK_PW')

    def initialize(self):
        self.storage = self._set_storage()
        if self.allow_local_backup and self.storage.type != 'local':
            self.local_storage = LocalStorage('local', '')
        if self.use_history:
            self.storage.fetch_history()
        if self.mk_id:
            try:
                self.storage.history['mk']
            except KeyError:
                self.storage.history.update({'mk': {'book': [], 'audiobook': []}})
            mk_history = self.storage.history['mk']
            self.mk_scraper = MkScraper(mk_id=self.mk_id, mk_pw=self.mk_pw,
                                        pdf_format=self.pdf_format, history=mk_history)

    def _set_storage(self):
        for cls in Storage.__subclasses__():
            if cls.is_available(self.storage_type):
                return cls(storage_type=self.storage_type, storage_token=self.storage_token)
        raise ValueError

    def execute(self):
        self.initialize()
        if self.mk_scraper:
            files = self.mk_scraper.execute()
            for k, v in files.items():
                for f in v:
                    self.storage.upload(f, k)
            self.storage.history['mk'] = self.mk_scraper.history
        self.storage.push_history()
        sys.exit()


app = PDFConcierge()
