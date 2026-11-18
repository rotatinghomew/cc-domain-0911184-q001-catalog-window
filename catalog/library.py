import json
import sqlite3


class Library:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS observations(
                region TEXT, source_id TEXT, revision INTEGER, payload TEXT,
                PRIMARY KEY(region,source_id,revision));
            CREATE TABLE IF NOT EXISTS titles(
                region TEXT, source_id TEXT, revision INTEGER, title TEXT,
                active INTEGER, PRIMARY KEY(region,source_id));
        ''')

    def apply(self, region, record):
        if not record.get('id') or not isinstance(record.get('revision'), int):
            raise ValueError('source identity and integer revision are required')
        raw = json.dumps(record, sort_keys=True, ensure_ascii=False)
        with self.db:
            previous = self.db.execute(
                'SELECT payload FROM observations WHERE region=? AND source_id=? AND revision=?',
                (region, record['id'], record['revision']),
            ).fetchone()
            if previous and previous['payload'] != raw:
                raise ValueError('conflicting content at the same revision')
            self.db.execute('INSERT OR IGNORE INTO observations VALUES(?,?,?,?)',
                            (region, record['id'], record['revision'], raw))
            old = self.db.execute('SELECT revision FROM titles WHERE region=? AND source_id=?',
                                  (region, record['id'])).fetchone()
            if old is None or record['revision'] > old['revision']:
                self.db.execute('INSERT OR REPLACE INTO titles VALUES(?,?,?,?,?)',
                                (region, record['id'], record['revision'], record['title'],
                                 int(not record.get('deleted', False))))

    def rows(self, region):
        return [dict(row) for row in self.db.execute(
            'SELECT * FROM titles WHERE region=? ORDER BY source_id', (region,))]

    def close(self):
        self.db.close()
