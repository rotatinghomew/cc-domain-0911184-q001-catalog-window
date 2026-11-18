import json
import tempfile
from pathlib import Path
from catalog.fixture import serve
from catalog.library import Library
from catalog.source import CatalogSource
from catalog.traversal import collect


def main():
    with tempfile.TemporaryDirectory() as directory, serve() as (url, state):
        library = Library(Path(directory) / 'catalog.sqlite3')
        report = collect(CatalogSource(url), library, 'east')
        print(json.dumps({'scan': report, 'titles': library.rows('east')}, ensure_ascii=False))
        library.close()


if __name__ == '__main__':
    main()
