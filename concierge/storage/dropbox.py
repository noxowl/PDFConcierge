import os.path

import dropbox
from tqdm import tqdm
from concierge.storage import Storage


class DropboxStorage(Storage):
    @classmethod
    def is_available(cls, storage_type):
        return storage_type == 'dropbox'

    def __init__(self, storage_type, storage_token):
        super().__init__(storage_type, storage_token)
        self.provider = dropbox.Dropbox(self.token)
        self.chunk_size = 4 * 1024 * 1024

    def connected(self):
        payload = 'ping'
        echo = self.provider.check_user(payload)
        if echo.result != payload:
            raise ConnectionError
        else:
            pass

    def upload(self, file, file_path):
        size = os.path.getsize(file)
        with open(file, 'rb') as f:
            if size <= self.chunk_size:
                self.provider.files_upload(
                    f.read(),
                    file_path
                )
            else:
                with tqdm(total=size) as progress:
                    upload_session = self.provider.files_upload_session_start(
                        f.read(),
                        file_path
                    )
                    progress.update(self.chunk_size)
                    cursor = dropbox.dropbox_client.files.UploadSessionCursor(
                        session_id=upload_session.session_id,
                        offset=f.tell()
                    )
                    upload_commit = dropbox.dropbox_client.files.CommitInfo(
                        path=file_path
                    )
                    while f.tell() < size:
                        if (size - f.tell()) <= self.chunk_size:
                            self.provider.files_upload_session_finish(
                                f.read(self.chunk_size), cursor, upload_commit
                            )
                        else:
                            self.provider.files_upload_session_append_v2(
                                f.read(self.chunk_size),
                                cursor
                            )
                        progress.update(self.chunk_size)

    def fetch_history(self):
        if self.connected():
            self.provider

    def push_history(self):
        pass
