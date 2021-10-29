import bs4
import os.path
import pdfkit
import requests
import tempfile
import urllib.parse
from bs4 import BeautifulSoup
from requests_html import HTMLSession
from multiprocessing import Pool
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

from concierge.logger import get_logger
from concierge.scraper.common import template_path, template_loader


@dataclass
class AsahiEditorialFigure:
    image: bytes
    caption: str


class AsahiEditorial:
    def __init__(self, url: str, article_id: str, article_date: datetime.date,
                 title: str, body: list, figure: AsahiEditorialFigure):
        self.logger = get_logger(__name__)
        self.type = 'editorial'
        self.lang = 'ja'
        self.url = url
        self.id = article_id
        self.date = article_date
        self.title = title
        self.body = body
        self.figure = figure
        self.template_path = template_path
        self.template = template_loader.get_template('asahi-editorial.html')
        self.temp_image = tempfile.NamedTemporaryFile()
        if self.figure.image:
            self.temp_image.write(self.figure.image)
        self.temp_html = self._render_html()
        self.temp_output = tempfile.NamedTemporaryFile(mode='w+b', delete=False)

    def _render_html(self):
        return self.template.render(
            template_path=self.template_path,
            lang=self.lang,
            title=self.title,
            reference_url=self.url,
            article_id=self.id,
            date=self.date,
            article=self.body,
            figure_img=self.temp_image.name,
            figure_cap=self.figure.caption
        )

    def _render_us_letter(self):
        """
        Render US Letter PDF from html
        (for Fujitsu QAUDERNO)

        :return:
        """
        render_options = {
            'page-size': 'Letter',
            'margin-top': '0.4in',
            'margin-right': '0.4in',
            'margin-bottom': '0.4in',
            'margin-left': '0.4in',
            'encoding': "UTF-8",
            'no-outline': None,
            'enable-local-file-access': None
        }
        self.temp_output.write(pdfkit.from_string(self.temp_html, output_path=False, options=render_options))
        self.temp_output.close()

    def develop(self):
        self.logger.info('develop editorial...')
        self._render_us_letter()
        return {'path': self.temp_output.name, 'category': 'asahi', 'filename': self.title, 'file_ext': '.pdf'}

    def clear(self):
        self.temp_image.close()


def _extract_article_id(url: str) -> str:
    """

    :param url:
    :return:
    """
    _path = urllib.parse.urlparse(url).path
    editorial_id, extension = os.path.splitext(os.path.basename(_path))
    return editorial_id


class AsahiScraper:
    def __init__(self, pdf_format: str):
        self.logger = get_logger(__name__)
        self.pdf_format = pdf_format
        self.timezone = timezone(timedelta(hours=+9), 'JST')
        self.today = datetime.now(tz=self.timezone)
        self._result = {'editorial': []}
        self._asahi_news_url = 'https://www.asahi.com'
        self.asahi_editorials_url = self._asahi_news_url + '/rensai/list.html?id=16'

    def _fetch_editorial_list(self) -> list:
        """
        Fetch editorial list by current date.

        :return: List of editorial article path.
        """
        editorials = []
        r = HTMLSession().get(self.asahi_editorials_url)
        r.html.render(timeout=30000)
        soup = BeautifulSoup(r.html.raw_html, "html.parser")
        for article in soup.find('ul', class_='PageList').find_all('span', class_='Time'):
            if datetime.strptime(article.text, '%Y年%m月%d日　%H時%M分').date() == self.today.date():
                article_link = article.parent.parent.parent.parent.get('href')
                if article_link:
                    editorials.append(article_link)
        return editorials

    def _fetch_editorial_page(self, url: str) -> bs4.element.Tag:
        """

        :param url: Url for fetch.
        :return:
        """
        r = requests.get(url)
        parse = BeautifulSoup(r.content, features='html.parser').find('main')
        return parse

    def _extract_editorial_title(self, contents: bs4.element.Tag) -> str:
        """

        :param contents:
        :return:
        """
        headers = contents.find('h1')
        return headers.text

    def _extract_editorial_figure(self, contents: bs4.element.Tag) -> AsahiEditorialFigure:
        """

        :param contents:
        :return:
        """
        image = b''
        figure = contents.find('figure')
        caption = figure.find('figcaption').text
        image_url = figure.find('img').get('src')
        if image_url.startswith('//'):
            image_url = 'https:' + image_url
        try:
            r = requests.get(image_url)
            if r.ok:
                image = r.content
        except ConnectionError:
            pass
        return AsahiEditorialFigure(image=image, caption=caption)

    def _extract_editorial_body(self, contents: bs4.element.Tag) -> list:
        """

        :param contents:
        :return:
        """
        body = []
        content = contents.find_all('p')
        for p in content:
            if p.text and not p.text.endswith('分'):
                body.append(p.text)
        return body

    def _fetch_editorial(self, url: str) -> AsahiEditorial:
        """

        :param url:
        :return:
        """
        self.logger.info('fetch editorial...')
        url = self._asahi_news_url + url
        article_id = _extract_article_id(url)
        contents = self._fetch_editorial_page(url)
        title = self._extract_editorial_title(contents)
        figure = self._extract_editorial_figure(contents)
        body = self._extract_editorial_body(contents)
        return AsahiEditorial(url=url, article_id=article_id, article_date=self.today.date(),
                              title=title, body=body, figure=figure)

    def _push_to_result(self, payload) -> None:
        """

        :param payload:
        :return:
        """
        self.logger.info('push to result article {0}'.format(payload.id))
        result = payload.develop()
        if result:
            self._result[payload.type].append(result)
        payload.clear()

    def download_editorials(self) -> dict:
        """

        :return:
        """
        self.logger.info('download editorials from Asahi...')
        articles = self._fetch_editorial_list()
        if articles:
            for a in articles:
                self._push_to_result(self._fetch_editorial(a))
            print(self._result)
        return self._result
