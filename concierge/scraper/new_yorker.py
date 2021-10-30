import bs4
import os.path
import pdfkit
import requests
import tempfile
import feedparser
import urllib.parse
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

from concierge.logger import get_logger
from concierge.scraper.common import Figure, template_path, template_loader, title_normalizer, render_option_us_letter


class NewYorkerEditorial:
    def __init__(self, url: str, article_id: str, article_date: datetime.date,
                 title: str, body: list, figure: Figure):
        self.logger = get_logger(__name__)
        self.type = 'editorial'
        self.lang = 'en'
        self.url = url
        self.id = article_id
        self.date = article_date
        self.title = title.strip()
        self.filename = '{1}_{0}'.format(title_normalizer(self.title).lower().replace(' ', '-'), self.date)
        self.body = body
        self.figure = figure
        self.template_path = template_path
        self.template = template_loader.get_template('new-yorker-editorial.html')
        self.temp_output = tempfile.NamedTemporaryFile(mode='w+b', delete=False)
        self.temp_image = tempfile.NamedTemporaryFile()
        if self.figure.image:
            self.temp_image.write(self.figure.image)
        self.temp_html = self._render_html()

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
        self.temp_output.write(pdfkit.from_string(self.temp_html, output_path=False, options=render_option_us_letter))
        self.temp_output.close()

    def develop(self):
        self.logger.info('develop editorial...')
        self._render_us_letter()
        return {'path': self.temp_output.name, 'category': 'new-yorker', 'filename': self.filename, 'file_ext': '.pdf'}

    def clear(self):
        self.temp_image.close()


def _extract_article_id(url: str) -> str:
    """

    :param url:
    :return:
    """
    _path = urllib.parse.urlparse(url).path
    article_id = os.path.basename(_path)
    return article_id


class NewYorkerScraper:
    def __init__(self, pdf_format: str):
        self.logger = get_logger(__name__)
        self.pdf_format = pdf_format
        self.timezone = timezone(timedelta(hours=-4), 'EDT')
        self.today = datetime.now(tz=self.timezone)
        self._result = {'editorial': []}
        self.new_yorker_feed_url = 'https://www.newyorker.com/feed/news/daily-comment'

    def _fetch_editorial_list(self) -> list:
        """
        Fetch editorial list by current date.

        :return: List of editorial article path.
        """
        editorials = []
        feed = feedparser.parse(self.new_yorker_feed_url)
        for f in feed['entries']:
            if datetime(*f['published_parsed'][:6], tzinfo=timezone.utc).astimezone(self.timezone).date()\
                    == self.today.date():
                editorials.append(f['link'])
        return editorials

    def _fetch_editorial_page(self, url: str) -> bs4.element.Tag:
        """

        :param url: Url for fetch.
        :return:
        """
        r = requests.get(url)
        parse = BeautifulSoup(r.content, features='html.parser').find('article')
        return parse

    def _extract_editorial_title(self, contents: bs4.element.Tag) -> str:
        """

        :param contents:
        :return:
        """
        headers = contents.find('h1')
        return headers.text

    def _extract_editorial_figure(self, contents: bs4.element.Tag) -> Figure:
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
        return Figure(image=image, caption=caption)

    def _extract_editorial_body(self, contents: bs4.element.Tag) -> list:
        """

        :param contents:
        :return:
        """
        body = []
        content = contents.find_all('p')
        for p in content:
            if p.text and not p.parent.attrs['class'][0] == 'scrap-modal-comp':
                body.append(p.text)
        return body

    def _fetch_editorial(self, url: str) -> NewYorkerEditorial:
        """

        :param url:
        :return:
        """
        self.logger.info('fetch editorial...')
        article_id = _extract_article_id(url)
        contents = self._fetch_editorial_page(url)
        title = self._extract_editorial_title(contents)
        body = self._extract_editorial_body(contents)
        figure = self._extract_editorial_figure(contents)
        return NewYorkerEditorial(url=url, article_id=article_id, article_date=self.today.date(),
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
        self.logger.info('download editorials from New Yorker...')
        articles = self._fetch_editorial_list()
        if articles:
            for a in articles:
                self._push_to_result(self._fetch_editorial(a))
        return self._result


