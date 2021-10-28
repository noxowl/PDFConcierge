import os
import bs4.element
import eyed3.id3
import requests
import re
import eyed3
import tempfile
from bs4 import BeautifulSoup
from tqdm import tqdm
from urllib.parse import urlparse, parse_qs
from multiprocessing import Pool

from concierge.logger import get_logger
from concierge.scraper.common import exclude_from_history


def title_normalizer(title) -> str:
    return title.replace('.', '').replace('/', '-').replace(',', '')\
        .replace('\\', '').replace('|', '').replace(':', '-').replace("\"", "")


class MKDocument:
    def __init__(self, book_id, filename, category, doc, convert_format):
        """
        this class will refactored.

        :param book_id:
        :param filename:
        :param category:
        :param doc:
        :param convert_format:
        """
        self.type = 'book'
        self.id = book_id
        self.category = category
        self.format = convert_format
        self.filename, self.file_extension = os.path.splitext(
            os.path.basename(filename.encode('iso-8859-1').decode('cp949', 'replace')))  # R.I.P Hannakageul
        self.filename = title_normalizer(self.filename)
        self.title = self.filename
        with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as tmp:
            tmp.write(doc)
            self.temp_path = tmp.name

    def to_kindle_pdf(self):
        pass

    def to_pdf(self):
        pass

    def pass_through(self):
        return self._result(self.temp_path)

    def _result(self, filepath):
        return {'path': filepath, 'category': self.category,
                'filename': self.filename, 'file_ext': self.file_extension}

    def convert(self) -> list:
        result = []
        if self.format == 'pass-through':
            result.append(self.pass_through())
        elif self.format == 'kindle':
            result.append(self.to_kindle_pdf())
        elif self.format == 'a4':
            result.append(self.to_pdf())
        else:
            result.append(self.to_pdf())
            result.append(self.to_kindle_pdf())
        return result


class MKAudiobook:
    def __init__(self, audiobook_id, metadata, category, audio):
        """
        this class will refactored.

        :param audiobook_id:
        :param metadata:
        :param category:
        :param audio:
        """
        self.type = 'audiobook'
        self.id = audiobook_id
        self.category = category
        self.title = metadata['title']
        self.author = metadata['author']
        self.publisher = metadata['publisher']
        if metadata['thumb']:
            self.thumb = metadata['thumb']
        else:
            self.thumb = None
        with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as tmp:
            tmp.write(audio)
            self.temp_path = tmp.name

    def _set_id3(self):
        id3_tag = eyed3.load(self.temp_path)
        id3_tag.initTag(eyed3.id3.tag.ID3_V2)
        id3_tag.tag.title = self.title
        id3_tag.tag.artist = 'BOOKCOSMOS'
        id3_tag.tag.album = 'BOOKCOSMOS'
        id3_tag.tag.genre = 'Audiobook'
        id3_tag.tag.comments.set(
            '{0} - {1}\nMK_Bookdigest ID: {2}'.format(self.author, self.publisher, self.id))
        if self.thumb:
            id3_tag.tag.images.set(eyed3.id3.frames.ImageFrame.FRONT_COVER, self.thumb, 'image/gif')
        id3_tag.tag.save()

    def _result(self, filepath):
        return {'path': filepath, 'category': self.category, 'filename': self.title, 'file_ext': '.mp3'}

    def convert(self) -> dict:
        self._set_id3()
        return self._result(self.temp_path)


class MkScraper:
    def __init__(self, mk_id: str, mk_pw: str, pdf_format: str, history: dict):
        """
        This class will refactored.

        :param mk_id:
        :param mk_pw:
        :param pdf_format:
        :param history:
        """
        self.logger = get_logger(__name__)
        self.id = mk_id
        self.pw = mk_pw
        self.pdf_format = pdf_format
        self.history = history
        self.result = {'book': [], 'audiobook': []}
        self._mk_digest_url = 'http://digest.mk.co.kr'
        self.mk_digest_index = self._mk_digest_url + '/Main/Index.asp'
        self.mk_digest_new_books = self._mk_digest_url + '/sub/digest/newbooklist.asp'
        self.mk_digest_books_index = self._mk_digest_url + '/sub/digest/index.asp'
        self.mk_digest_books = self._mk_digest_url + '/sub/digest/classlist.asp'
        self.mk_digest_download = self._mk_digest_url + '/Sub/Digest/DownLoad.asp'
        self.mk_digest_audiobook_index = self._mk_digest_url + '/sub/audio/index.asp'
        self.mk_digest_audiobooks = self._mk_digest_url + '/sub/audio/classlist.asp'
        self.mk_digest_audiobook_download = 'https://www.bcaudio.co.kr/audio/{0}.mp3'
        self.mk_digest_book_detail = self._mk_digest_url + '/Sub/Digest/GuideBook.asp?book_sno={0}'
        self.mk_digest_book_thumb = self._mk_digest_url + '/book_img/{0}.gif'
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

    def _parse_book_metadata(self, content: bytes) -> dict:
        raw_book_info = BeautifulSoup(content, features='html.parser') \
            .find('div', style=re.compile(r'width:420px;height:40px;float:left;'))
        raw_meta = " ".join(raw_book_info.find_all('div')[1].text.split()).split('/')
        title = raw_book_info.find('span').text
        title = title_normalizer(title)
        book_metadata = {
            'title': title,
            'author': raw_meta[0].replace('저자 :', '').strip(),
            'publisher': raw_meta[1].replace('출판사 :', '').strip(),
            'thumb': None
        }
        return book_metadata

    def _digest_book_scrap(self, url) -> list:
        contents = self._fetch_book_page(url)
        try:
            last_page = int(
                parse_qs(
                    urlparse(contents.find_all('a')[-1].get('href')).query
                )['page'][0])
        except KeyError:
            last_page = 1
        books = self._extract_book_data(contents)
        if last_page > 1:
            for i in range(1, last_page):
                _u = requests.PreparedRequest()
                _u.prepare_url(url, {'Type': 'T', 'page': i + 1})
                contents = self._fetch_book_page(_u.url)
                books += self._extract_book_data(contents)
        return books

    def _digest_all_book_scrap(self) -> dict:
        self.logger.info('scrap all books...')
        books = {}
        categories = self._fetch_book_categories()
        for name, code in categories.items():
            self.logger.info('scrap from {0}...'.format(name))
            books.update({
                name: self._digest_book_scrap('{0}?code={1}'.format(self.mk_digest_books, code))
            })
            self.logger.info('{0} - {1}'.format(name, len(books[name])))
        return books

    def _fetch_book_categories(self) -> dict:
        self.logger.info('fetch categories...')
        categories = {}
        r = requests.get(self.mk_digest_books_index, cookies=self.cookies)
        raw_categories = BeautifulSoup(r.content, features='html.parser') \
            .find('div', style=re.compile(r"background: url\(/images/sub/digest_leftmntitle_02.gif\) repeat-y")) \
            .find_all('a')
        for c in tqdm(raw_categories):
            try:
                categories[c.find('span').contents[0].strip().replace('/', '・')] = \
                    parse_qs(urlparse(c.get('href')).query)['code'][0]
            except KeyError:
                continue
        return categories

    def _fetch_book_page(self, url):
        r = requests.get(url, cookies=self.cookies)
        parse = BeautifulSoup(r.content, features='html.parser').find('div', class_='bodybox')
        return parse

    def _extract_book_data(self, contents: bs4.element.Tag):
        books = []
        raw_books = contents.find_all('span', class_='booktitle')
        for raw in tqdm(raw_books):
            books.append(parse_qs(urlparse(raw.parent.get('href')).query)['book_sno'][0])
        return books

    def _download_book(self, category: str, book_id: str, convert_format: str) -> MKDocument:
        self.logger.info('download {0} - {1}'.format(category, book_id))
        if self.pdf_format == 'pass-through':
            r = requests.post(self.mk_digest_download,
                              data={'book_sno': book_id, 'book_type': 'pdf'}, cookies=self.cookies,
                              headers={'referer': self.mk_digest_new_books})
        else:
            r = requests.post(self.mk_digest_download,
                              data={'book_sno': book_id, 'book_type': 'doc'}, cookies=self.cookies,
                              headers={'referer': self.mk_digest_new_books})
        return MKDocument(book_id=book_id,
                          filename=re.findall("filename=(.+)", r.headers.get('Content-Disposition'))[0],
                          category=category, doc=r.content, convert_format=convert_format)

    def _digest_new_audiobook_scrap(self) -> dict:
        contents = self._fetch_new_audiobook_page(self.mk_digest_audiobook_index)
        new_audiobooks = self._extract_audiobook_id(contents)
        return {'신간': new_audiobooks}

    def _digest_all_audiobook_scrap(self) -> dict:
        self.logger.info('scrap all audiobooks...')
        audiobooks = {}
        categories = self._fetch_audiobook_categories()
        for name, code in tqdm(categories.items()):
            self.logger.info('scrap from {0}...'.format(name))
            audiobooks.update({
                name: self._digest_book_scrap('{0}?gubun={1}'.format(self.mk_digest_audiobooks, code))
            })
        return audiobooks

    def _fetch_audiobook_categories(self) -> dict:
        self.logger.info('fetch categories...')
        categories = {}
        r = requests.get(self.mk_digest_audiobook_index, cookies=self.cookies)
        raw_categories = BeautifulSoup(r.content, features='html.parser') \
            .find('div', style=re.compile(r"background: url\(/images/sub/digest_leftmntitle_02.gif\) repeat-y")) \
            .find_all('a')
        for c in tqdm(raw_categories):
            try:
                categories[c.find('span').contents[0].strip().replace('/', '・')] = \
                    parse_qs(urlparse(c.get('href')).query)['gubun'][0]
            except KeyError:
                continue
        return categories

    def _fetch_new_audiobook_page(self, url):
        r = requests.get(url, cookies=self.cookies)
        parse = BeautifulSoup(r.content, features='html.parser') \
            .find_all('img', class_='bookimg')
        return parse

    def _extract_audiobook_id(self, contents: bs4.element.ResultSet):
        audiobooks = []
        for c in tqdm(contents):
            if c.parent.name == 'a':
                audiobooks.append(
                    parse_qs(
                        urlparse(c.parent.get('href')).query
                    )['book_sno'][0])
        return audiobooks

    def _download_audiobook(self, category: str, audiobook_id: str) -> MKAudiobook:
        self.logger.info('download start for {0} - {1}'.format(category, audiobook_id))
        raw_info = requests.get(self.mk_digest_book_detail.format(audiobook_id))
        book_metadata = self._parse_book_metadata(raw_info.content)
        self.logger.info('download metadata for {0} - {1} completed'.format(category, audiobook_id))
        thumb = requests.get(self.mk_digest_book_thumb.format(audiobook_id))
        if thumb.status_code == 200:
            book_metadata['thumb'] = thumb.content
            self.logger.info('download thumbnail for {0} - {1} completed'.format(category, audiobook_id))
        self.logger.info('download audio for {0} - {1}'.format(category, audiobook_id))
        audio = requests.get(self.mk_digest_audiobook_download.format(audiobook_id),
                             headers={'referer': self._mk_digest_url})
        self.logger.info('download done for {0} - {1}'.format(category, audiobook_id))
        return MKAudiobook(audiobook_id=audiobook_id, metadata=book_metadata, audio=audio.content, category=category)

    def _push_to_result(self, payload):
        self.logger.info('push {0} - {1} to result'.format(payload.type, payload.title))
        result = payload.convert()
        if isinstance(result, list):
            self.result[payload.type] += result
        else:
            self.result[payload.type].append(result)
        self.history[payload.type].append(payload.id)

    def _execute_download_books(self, mode):
        pool = Pool(processes=3)
        if mode == 'fetch_new':
            book_task = {'신간': self._digest_book_scrap(self.mk_digest_new_books)}
        else:
            book_task = self._digest_all_book_scrap()
        for category, task in book_task.items():
            filtered_task = exclude_from_history(task, self.history['book'])
            if filtered_task:
                self.logger.info('start fetch book from category {0}...'.format(category))
                for t in filtered_task:
                    self.logger.info('start download book {0}...'.format(t))
                    pool.apply_async(self._download_book, (category, t, self.pdf_format), callback=self._push_to_result)
        pool.close()
        pool.join()

    def _execute_download_audiobooks(self, mode):
        pool = Pool(processes=3)
        if mode == 'fetch_new':
            audiobook_task = self._digest_new_audiobook_scrap()
        else:
            audiobook_task = self._digest_all_audiobook_scrap()
        for category, task in audiobook_task.items():
            filtered_task = exclude_from_history(task, self.history['audiobook'])
            if filtered_task:
                self.logger.info('start fetch audiobook from category {0}...'.format(category))
                for t in filtered_task:
                    self.logger.info('start download audiobook {0}...'.format(t))
                    pool.apply_async(self._download_audiobook, (category, t), callback=self._push_to_result)
        pool.close()
        pool.join()

    def execute(self, mode) -> dict:
        self._execute_download_books(mode)
        self._execute_download_audiobooks(mode)
        return self.result
