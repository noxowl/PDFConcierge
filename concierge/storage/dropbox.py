import os.path
import tempfile

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
        self.write_mode = dropbox.dropbox_client.files.WriteMode.overwrite

    def connected(self):
        payload = 'ping'
        echo = self.provider.check_user(payload)
        if echo.result != payload:
            self.logger.info('dropbox connection failed.')
            raise ConnectionError
        else:
            self.logger.info('dropbox connection success.')
            return True

    def upload(self, file_result, filetype):
        size = os.path.getsize(file_result['path'])
        with open(file_result['path'], 'rb') as f:
            if size <= self.chunk_size:
                self.logger.info(
                    self.provider.files_upload(
                        f=f.read(),
                        path='/{0}/{1}/{2}{3}'.format(
                            filetype, file_result['category'],
                            file_result['filename'], file_result['file_ext']
                        ),
                        mode=self.write_mode
                    )
                )
            else:
                with tqdm(total=size) as progress:
                    upload_session = self.provider.files_upload_session_start(
                        f=f.read(self.chunk_size),
                    )
                    progress.update(self.chunk_size)
                    cursor = dropbox.dropbox_client.files.UploadSessionCursor(
                        session_id=upload_session.session_id,
                        offset=f.tell()
                    )
                    upload_commit = dropbox.dropbox_client.files.CommitInfo(
                        path='/{0}/{1}/{2}{3}'.format(
                            filetype, file_result['category'],
                            file_result['filename'], file_result['file_ext']
                        ),
                        mode=self.write_mode
                    )
                    while f.tell() < size:
                        if (size - f.tell()) <= self.chunk_size:
                            self.logger.info(
                                self.provider.files_upload_session_finish(
                                    f.read(self.chunk_size), cursor, upload_commit
                                )
                            )
                            break
                        else:
                            self.provider.files_upload_session_append_v2(
                                f.read(self.chunk_size),
                                cursor
                            )
                            cursor.offset = f.tell()
                        progress.update(self.chunk_size)

    def fetch_history(self):
        if self.connected():
            self.logger.info('fetch history from dropbox...')
            try:
                meta, r = self.provider.files_download('/data/history.yml')
                h = tempfile.NamedTemporaryFile()
                h.write(r.content)
                h.flush()
                self.read_history(h.name)
                h.close()
            except dropbox.exceptions.ApiError:
                return None

    def push_history(self):
        if self.connected():
            payload = self.dump_history()
            self.provider.files_upload(f=payload.encode('utf-8'), path='/data/history.yml',
                                       mode=dropbox.dropbox_client.files.WriteMode.overwrite)
