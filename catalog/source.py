import json
from urllib.parse import urlencode
from urllib.request import urlopen


class CatalogSource:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')

    def pages(self, region):
        cursor = ''
        visited = set()
        while True:
            if cursor in visited:
                raise ValueError('source returned a cursor cycle')
            visited.add(cursor)
            query = urlencode({'region': region, 'cursor': cursor})
            with urlopen(self.base_url + '/catalog?' + query, timeout=5) as response:
                page = json.load(response)
            if page['region'] != region:
                raise ValueError('source region mismatch')
            yield page
            cursor = page.get('next')
            if cursor is None:
                break
