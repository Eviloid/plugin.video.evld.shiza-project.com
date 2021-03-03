# -*- coding: utf-8 -*-

import os, json, time, binascii
from io import BytesIO

import urllib.request as urlrequest
import urllib.parse as urlparse
import urllib.error as urlerror


class Engine(object):

    def __init__(self, host='127.0.0.1', port=8090):
        self.host = host
        self.port = port
        self.success = True
        self.version = None
        self.hash = None
        self._store = False
        self._preload_size = 20
        self._index = 0

        if not self.echo():
            self.success = False
            return

    @property
    def url(self):
        return self._get_url()

    def make_url(self, path):
        return 'http://{0}:{1}{2}'.format(self.host, self.port, path)

    def encode_multipart_formdata(self, data):
        body = BytesIO()
        boundary = binascii.hexlify(os.urandom(16)).decode('utf-8')

        body.write(f'--{boundary}\r\n'.encode('utf-8'))
        body.write(b'Content-Disposition: form-data; name="file"; filename=shiza.torrent\r\n')
        body.write(b'Content-Type: application/octet-stream\r\n')
        body.write(b'\r\n')
        body.write(data)
        body.write(b'\r\n')
        body.write(f'--{boundary}--\r\n'.encode('utf-8'))

        content_type = 'multipart/form-data; boundary=%s' % boundary
        return body.getvalue(), content_type

    def request(self, name, data=None, is_file=False):
        url = self.make_url('/torrent/' + name)

        headers = {'Content-Type':'application/json'}

        if is_file and data:
            data, content_type = self.encode_multipart_formdata(data)
            headers = {'Content-Type':content_type, 'Content-Length':len(data)}
        elif data:
            data = json.dumps(data).encode('utf-8')
        else:
            data = None

        request = urlrequest.Request(url, data, headers=headers)
        conn = urlrequest.urlopen(request)

        result = conn.read()
        conn.close()

        if conn.headers.get_content_charset():
            result = result.decode(conn.headers.get_content_charset())
        return result

    def echo(self):
        try:
            version = urlrequest.urlopen(self.make_url('/echo'), timeout=3.0).read()
            self.version = version.decode('utf-8')
        except urlerror.URLError as e:
            return False
        return True

    def close(self):
        if self._store:
            self.drop()
        else:
            self.rem()

    def stat(self):
        return json.loads(self.request('stat', data={'Hash': self.hash}))

    def list(self):
        return json.loads(self.request('list', data={'Hash': self.hash}))

    def get(self):
        return json.loads(self.request('get', data={'Hash': self.hash}))

    def add(self, url):
        r = self.request('add', data={'Link': url, 'DontSave': not self._store})
        self.hash = r
        return True
        
    def rem(self):
        self.request('rem', data={'Hash': self.hash})

    def drop(self):
        self.request('drop', data={'Hash': self.hash})

    def upload(self, data):
        r = json.loads(self.request('upload', data=data, is_file=True))
        self.hash = r[0]
        return True

    def is_preloading(self):
        try:
            st = self.stat()
            return any(x for x in ['preload', 'info'] if x in st['TorrentStatusString'])
        except KeyError:
            pass
        return False

    def preload(self):
        try:
            preload_url = self._get_url('Preload')
            if preload_url:
                preload_url = preload_url.replace('&preload=true', '&preload={}'.format(self._preload_size)) # 1.77
                preload_url = preload_url.replace('/preload/', '/preload/{}/'.format(self._preload_size)) # 1.76
                conn = urlrequest.urlopen(preload_url, timeout=1.0).read(128)
        except:
            pass

    def start(self, torrent, index=0, preload_size=20, store=False):
        self._index = index
        self._preload_size = preload_size
        self._store = store

        if torrent[:6] == 'magnet':
            self.add(torrent)
            time.sleep(0.5)
        else:
            self.upload(torrent)

        self.preload()

    def status(self):
        st = self.stat()
        try:
            seeders = st['ConnectedSeeders']
            preloaded = st['PreloadedBytes'] / 1024 / 1024
            preload = st['PreloadSize'] / 1024 / 1024
            speed = st['DownloadSpeed'] / 1024 / 1024
        except KeyError:
            return 0, 0, 0, 0
        return seeders, preloaded, preload, speed

    def _get_url(self, mode='Link'):
        try:
            files = self.get()['Files']
        except Exception:
            return None

        for i, f in enumerate(files):
            if i == self._index:
                return self.make_url(f[mode])

