import yaml


class Storage(object):
    def __init__(self, storage_type, storage_token):
        self.type = storage_type
        self.token = storage_token
        self.chunk_size = 0
        self.history = {}
        self.history_path = None
        self.upload_path = None
        self.provider = None

    def connected(self):
        pass

    def upload(self, file, path):
        pass

    def fetch_history(self):
        pass

    def push_history(self):
        pass

    def read_history(self, history_file):
        with open(history_file, 'r') as stream:
            h = yaml.load(stream, Loader=yaml.Loader)
            self.history = h if h else {}

    def dump_history(self):
        return yaml.dump(self.history)


from .local import LocalStorage
from .dropbox import DropboxStorage
