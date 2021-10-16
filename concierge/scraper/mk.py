import os

import bs4.element
import requests
import re
import pypandoc
import tempfile
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from concierge.scraper.common import exclude_from_history


class MKDocument:
    def __init__(self, filename, doc):
        self.filename, self.file_extension = os.path.splitext(
            os.path.basename(filename.encode('iso-8859-1').decode('cp949', 'replace')))  # R.I.P Hannakageul
        self.filename = self.filename.replace('.', '')
        self.origin = doc
        with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as tmp:
            tmp.write(self.origin)
            self.temp_path = tmp.name

    def to_kindle_pdf(self):
        pass

    def to_pdf(self):
        pypandoc.convert_file(self.temp_path, format='docx', to='pdf',
                              outputfile='{0}_a4.pdf'.format(self.filename),
                              extra_args=['--data-dir={0}'.format(tempfile.tempdir)])

    def pass_through(self):
        return self._result(self.temp_path)

    def _result(self, filepath):
        return {'path': filepath, 'filename': self.filename, 'file_ext': self.file_extension}

    def convert(self, convert_format) -> list:
        result = []
        if convert_format == 'pass-through':
            result.append(self.pass_through())
        elif convert_format == 'kindle':
            result.append(self.to_kindle_pdf())
        elif convert_format == 'a4':
            result.append(self.to_pdf())
        else:
            result.append(self.to_pdf())
            result.append(self.to_kindle_pdf())
        return result


class MKAudiobook:
    def __init__(self, audio):
        self.origin = audio

    def set_thumbnail(self, image):
        pass


class MkScraper:
    def __init__(self, mk_id: str, mk_pw: str, pdf_format: str, history: dict):
        self.id = mk_id
        self.pw = mk_pw
        self.pdf_format = pdf_format
        self.history = history
        self._mk_digest_url = 'http://digest.mk.co.kr'
        self.mk_digest_index = self._mk_digest_url + '/Main/Index.asp'
        self.mk_digest_new_books = self._mk_digest_url + '/sub/digest/newbooklist.asp'
        self.mk_digest_download = self._mk_digest_url + '/Sub/Digest/DownLoad.asp'
        self.mk_digest_login_url = self._mk_digest_url + '/loginAction.asp'
        self.mk_login_phase_one_url = 'https://member.mk.co.kr/member_login_process.php'
        self.mk_login_phase_two_url = 'https://member.mk.co.kr/mem/v1/action.php'
        self.cookies = requests.Session()
        self._login()

    def _login(self):
        self.__login_phase_one()
        self.__login_phase_two()
        self.__login_phase_three()

    def __login_phase_one(self):
        r = requests.post(self.mk_login_phase_one_url,
                          data={'user_id': self.id, 'password': self.pw,
                                'successUrl': self.mk_digest_login_url})

    def __login_phase_two(self):
        r = requests.post(self.mk_login_phase_two_url,
                          data={'id': self.id, 'pw': self.pw, 'c': 'login_action',
                                'successUrl': self.mk_digest_login_url})
        self.cookies = r.cookies

    def __login_phase_three(self):
        r = requests.get(self.mk_digest_index, cookies=self.cookies)
        r.cookies.update(self.cookies)
        self.cookies = r.cookies
        r = requests.get(self.mk_digest_login_url, cookies=self.cookies)
        r.cookies.update(self.cookies)
        self.cookies = r.cookies

    def _digest_new_book_scrap(self) -> list:
        contents = self._fetch_new_book_page(self.mk_digest_new_books)
        last_page = int(parse_qs(urlparse(contents.find_all('a')[-1].get('href')).query)['page'][0])
        new_books = self._extract_book_data(contents)
        for i in range(1, last_page):
            contents = self._fetch_new_book_page('{0}?Type=T&page={1}'.format(self.mk_digest_new_books, i + 1))
            new_books += self._extract_book_data(contents)
        return new_books

    def _fetch_new_book_page(self, url):
        r = requests.get(url, cookies=self.cookies)
        parse = BeautifulSoup(r.content, features='html.parser').find('div', class_='bodybox')
        return parse

    def _extract_book_data(self, contents: bs4.element.Tag):
        books = []
        raw_books = contents.find_all('span', class_='booktitle')
        for raw in raw_books:
            books.append(parse_qs(urlparse(raw.parent.get('href')).query)['book_sno'][0])
        return books

    def _download_book(self, book_id: str) -> MKDocument:
        if self.pdf_format == 'pass-through':
            r = requests.post(self.mk_digest_download,
                              data={'book_sno': book_id, 'book_type': 'pdf'}, cookies=self.cookies,
                              headers={'referer': self.mk_digest_new_books})
        else:
            r = requests.post(self.mk_digest_download,
                              data={'book_sno': book_id, 'book_type': 'doc'}, cookies=self.cookies,
                              headers={'referer': self.mk_digest_new_books})
        if r.status_code == 200:
            return MKDocument(re.findall("filename=(.+)", r.headers.get('Content-Disposition'))[0], r.content)
        else:
            raise ConnectionError

    def _digest_new_audiobook_scrap(self) -> list:
        pass

    def _download_audiobook(self, audiobook_id: str) -> MKAudiobook:
        pass

    def execute(self) -> dict:
        result = {'book': [], 'audiobook': []}
        book_task = self._digest_new_book_scrap()
        for task in exclude_from_history(book_task, self.history['book']):
            try:
                book = self._download_book(task)
                result['book'] += book.convert(self.pdf_format)
                self.history['book'].append(task)
            except ConnectionError:
                continue
        # audiobook_task = self._digest_new_audiobook_scrap()
        # for task in exclude_from_history(audiobook_task, self.history['audiobook']):
        #     try:
        #         audiobook = self._download_audiobook(task)
        #         self.history['audiobook'].add(task)
        #     except ConnectionError:
        #         continue
        return result
