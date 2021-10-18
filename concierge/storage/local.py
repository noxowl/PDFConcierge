import os.path
import shutil
from pathlib import Path

from concierge.storage import Storage


class LocalStorage(Storage):
    @classmethod
    def is_available(cls, storage_type):
        return storage_type == 'local'

    def __init__(self, storage_type, storage_token):
        super().__init__(storage_type, storage_token)
        self.provider = Path(Path(os.path.dirname(__file__)).parents[1])
        self.upload_path = Path(self.provider, 'downloads')
        self.history_path = Path(self.provider, 'history.yml')

    def connected(self):
        try:
            os.makedirs(self.upload_path)
        except FileExistsError:
            return True
        return False

    def upload(self, file_result, filetype):
        if self.connected() and self._upload_path_safety_check(filetype, file_result['category']):
            shutil.move(Path(file_result['path']),
                        Path(self.upload_path, filetype, file_result['category'], '{0}{1}'
                             .format(file_result['filename'], file_result['file_ext']))
                        )

    def _history_file_safety_check(self):
        if not os.path.isfile(self.history_path):
            with open(self.history_path, 'w'):
                pass

    def _upload_path_safety_check(self, upload_path, category):
        try:
            os.makedirs(Path(self.upload_path, upload_path, category))
        except FileExistsError:
            return True
        return False

    def fetch_history(self):
        if self.connected():
            self._history_file_safety_check()
            self.read_history(self.history_path)

    def push_history(self):
        if self.connected():
            with open(self.history_path, 'w') as f:
                f.write(self.dump_history())
