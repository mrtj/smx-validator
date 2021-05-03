import os
import json
import csv
from collections import defaultdict
from urllib.parse import urlparse

import s3fs

class S3Wrapper:

    content_type_map = defaultdict(
        lambda: 'application/octet-stream', 
        {
            '.html': 'text/html',
            '.csv': 'text/csv',
            '.txt': 'text/plain',
            '.json': 'application/json'
        }
    )

    @staticmethod
    def parse_url(s3_url):
        ''' Parses a s3://bucket/key style url into a (bucket, key) tuple. '''
        up = urlparse(s3_url)
        path = up.path[1:] if up.path.startswith('/') else up.path
        return up.netloc, path

    @staticmethod
    def get_filename(s3_url):
        up = urlparse(url)
        basename = os.path.basename(parsed.path)
        filename, _ = os.path.splitext(basename)
        return filename

    def __init__(self, save_prefix=None):
        self.s3 = s3fs.S3FileSystem(anon=False)
        self.save_prefix = save_prefix

    def _get_path(self, filename=None, target_path=None):
        if not target_path and not (self.save_prefix and filename):
            raise ValueError('Either target_path or both S3Wrapper.save_prefix '
                             'and filename must be specified')
        return target_path if target_path else \
            os.path.join(self.save_prefix, filename)

    def save(self, contents, filename=None, target_path=None):
        path = self._get_path(filename=filename, target_path=target_path)
        _, ext = os.path.splitext(filename or target_path)
        content_type = S3Wrapper.content_type_map[ext]
        with self.s3.open(path, 'w', ContentType=content_type) as f:
            f.write(contents)
        return path

    def list_recursive(self, absolute_path):
        for (dirpath, dirnames, filenames) in self.s3.walk(absolute_path):
            for filename in filenames:
                yield 's3://' + os.path.join(dirpath, filename)

    def load_str(self, absolute_path, encoding='utf-8'):
        with self.s3.open(absolute_path) as f:
            data = f.read().decode(encoding=encoding)
        return data

    def load_bytes(self, absolute_path):
        with self.s3.open(absolute_path) as f:
            data = f.read()
        return data

    def load_json(self, absolute_path):
        with self.s3.open(absolute_path) as f:
            data = json.load(f)
        return data

    def load_lines(self, absolute_path):
        with self.s3.open(absolute_path) as f:
            for line in f:
                yield line

    def load_json_lines(self, absolute_path):
        for line in self.load_lines(absolute_path):
            yield json.loads(line)

    def url(self, path, **kwargs):
        return self.s3.url(path, **kwargs)
