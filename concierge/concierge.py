import os
import pathlib
import sys

from .logger import get_logger
from .storage import Storage, LocalStorage
from .scraper import MkScraper

concierge_mode = {
    'new': 'fetch_new',
    'all': 'fetch_all'
}

pdf_format = {
    'a4': 'a4',
    'kindle': 'kindle',
    'all': 'all',
    'pass-through': 'pass-through'
}


def is_true(value) -> bool:
    return value.lower() == 'true' if value else False


def concierge_execute_mode(mode) -> str:
    try:
        return concierge_mode[mode]
    except KeyError:
        return concierge_mode['new']


def pdf_format_mode(mode) -> str:
    try:
        return pdf_format[mode]
    except KeyError:
        return pdf_format['pass-through']


class PDFConcierge:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.storage = None
        self.local_storage = None
        self.mk_scraper = None
        self.history_hash = None
        self.mode = concierge_execute_mode(os.environ.get('PDFC_MODE'))
        self.allow_local_backup = is_true(os.environ.get('PDFC_ALLOW_LOCAL_BACKUP'))
        self.pdf_format = pdf_format_mode(os.environ.get('PDFC_PDF_FORMAT'))
        self.use_history = is_true(os.environ.get('PDFC_USE_HISTORY'))
        # self.history_reference = os.environ.get('PDFC_HISTORY_REFERENCE')
        self.storage_type = os.environ.get('PDFC_STORAGE')
        self.storage_token = os.environ.get('PDFC_CLOUD_TOKEN')
        self.mk_id = os.environ.get('PDFC_MK_ID')
        self.mk_pw = os.environ.get('PDFC_MK_PW')

    def initialize(self):
        self.storage = self._set_storage()
        self.logger.info('storage type "{0}" initialized.'.format(self.storage.type))
        if self.allow_local_backup and self.storage.type != 'local':
            self.local_storage = LocalStorage('local', '')
        if self.use_history:
            self.storage.fetch_history()
            self.logger.info('history data fetched.')
        if self.mk_id:
            self.logger.info('mk digest initializing...')
            try:
                self.storage.history['mk']
            except KeyError:
                self.storage.history.update({'mk': {'book': [], 'audiobook': []}})
            mk_history = self.storage.history['mk']
            self.mk_scraper = MkScraper(mk_id=self.mk_id, mk_pw=self.mk_pw,
                                        pdf_format=self.pdf_format, history=mk_history)
            self.logger.info('mk digest initialized.')
        self.history_hash = self._make_history_hash()

    def _make_history_hash(self):
        try:
            return hash(tuple(frozenset(sorted(self.storage.history.items()))))
        except TypeError:
            return hash(tuple(frozenset({}.items())))

    def _history_hash_unmatched(self) -> bool:
        return self.history_hash != self._make_history_hash()

    def _set_storage(self):
        for cls in Storage.__subclasses__():
            if cls.is_available(self.storage_type):
                return cls(storage_type=self.storage_type, storage_token=self.storage_token)
        raise ValueError

    def _upload_to_storage(self, files):
        for category, v in files.items():
            for file_result in v:
                self.storage.upload(file_result, category)
                if self.local_storage:
                    self.logger.info('upload to local backup...')
                    self.local_storage.upload(file_result, category)
                else:
                    try:
                        os.remove(pathlib.Path(file_result['path']))
                    except OSError:
                        pass

    def _send_notice(self):
        pass

    def execute(self):
        self.initialize()
        if self.mk_scraper:
            self.logger.info('fetch from mk digest...')
            files = self.mk_scraper.execute(self.mode)
            self._upload_to_storage(files)
            self.storage.history['mk'] = self.mk_scraper.history
            self.logger.info('fetch from mk digest done.')
        self.logger.info('all task done. update history data.')
        self.storage.push_history()
        if self._history_hash_unmatched():
            self.logger.info('history hash unmatched. send notice.')
            self._send_notice()
        sys.exit()


app = PDFConcierge()
