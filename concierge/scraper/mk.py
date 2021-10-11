import requests


class MkScraper:
    def __init__(self, mk_id, mk_pw):
        self.id = mk_id
        self.pw = mk_pw
        self._mk_digest_url = 'http://digest.mk.co.kr'
        self.mk_digest_index = self._mk_digest_url + '/Main/Index.asp'
        self.mk_digest_new_books = self._mk_digest_url + '/sub/digest/newbooklist.asp'
        self.mk_digest_download = self._mk_digest_url + '/Sub/Digest/DownLoad.asp'
        self.mk_digest_login_url = self._mk_digest_url + '/loginAction.asp'
        self.mk_login_phase_one_url = 'https://member.mk.co.kr/member_login_process.php'
        self.mk_login_phase_two_url = 'https://member.mk.co.kr/mem/v1/action.php'
        self.cookies = requests.Session()
        self._login()
        self._digest_new_book_scrap()

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

    def _digest_new_book_scrap(self):
        r = requests.get(self.mk_digest_new_books, cookies=self.cookies)
        print(r.content)

    def _download_book(self, book_id: str):
        r = requests.post(self.mk_digest_download,
                          data={'book_sno': book_id, 'book_type': 'doc'}, cookies=self.cookies,
                          headers={'referer': self.mk_digest_new_books})
        print(r.content)


class MKDocConverter:
    def __init__(self, doc):
        pass

    def to_kindle_pdf(self):
        pass

    def to_pdf(self):
        pass
