import json
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen
from catalog.fixture import serve
from catalog.library import Library
from catalog.source import CatalogSource
from catalog.traversal import collect


class CatalogTests(unittest.TestCase):
    def test_end_to_end_and_reopen(self):
        with tempfile.TemporaryDirectory() as folder, serve() as (url, state):
            path = Path(folder) / 'catalog.db'
            book = Library(path)
            result = collect(CatalogSource(url), book, 'east')
            self.assertEqual(result['pages'], 2)
            self.assertEqual(len(book.rows('east')), 3)
            collect(CatalogSource(url), book, 'east')
            self.assertEqual(book.db.execute('SELECT count(*) FROM observations').fetchone()[0], 3)
            book.close()
            reopened = Library(path)
            self.assertEqual(len(reopened.rows('east')), 3)
            reopened.close()

    def test_revision_and_region(self):
        book = Library(':memory:')
        for revision, title in [(3, '新版'), (1, '旧版')]:
            book.apply('east', {'id': 'a', 'revision': revision, 'title': title})
        book.apply('west', {'id': 'a', 'revision': 1, 'title': '另一作品'})
        self.assertEqual(book.rows('east')[0]['title'], '新版')
        self.assertEqual(book.rows('west')[0]['title'], '另一作品')
        book.close()

    def test_conflicting_revision(self):
        book = Library(':memory:')
        book.apply('east', {'id': 'a', 'revision': 1, 'title': '甲'})
        with self.assertRaises(ValueError):
            book.apply('east', {'id': 'a', 'revision': 1, 'title': '乙'})
        self.assertEqual(book.rows('east')[0]['title'], '甲')
        book.close()

    def test_window_is_stable_and_expires(self):
        with serve() as (url, state):
            with urlopen(url + '/window?region=east') as response:
                token = json.load(response)['window']
            state.records.insert(0, {'id': 'new', 'revision': 1, 'title': '新作'})
            with urlopen(url + '/catalog?region=east&window=' + token) as response:
                page = json.load(response)
            self.assertEqual(page['items'][0]['id'], 'series-a')
            state.expired.add(token)
            with self.assertRaises(HTTPError) as error:
                urlopen(url + '/catalog?window=' + token)
            self.assertEqual(error.exception.code, 410)

    def test_window_cursor_cannot_cross(self):
        with serve() as (url, state):
            with urlopen(url + '/window') as response:
                token = json.load(response)['window']
            with self.assertRaises(HTTPError) as error:
                urlopen(url + '/catalog?window=' + token + '&cursor=other:2')
            self.assertEqual(error.exception.code, 409)
