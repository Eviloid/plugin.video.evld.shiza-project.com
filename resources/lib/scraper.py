# -*- coding: utf-8 -*-

import xbmc
import re, json

from urllib.error import HTTPError

import CommonFunctions as common
import utils

BASE_URL = 'http://shiza-project.com'


class ScraperException(Exception):
    pass

class ShizaScraper():
    def __init__(self, page=None, query=None, hide_online=True):
        self.page = int(page or 1)
        self._query = query
        self._hide_online = hide_online

        self._total_page = 0
        self._html = ''

    @property
    def total_page(self):
        return self._total_page
    
    @classmethod
    def fetch(self, url, params={}, post={}, headers={}):
        return utils.get_html(url, params, post, headers)


    def check_auth(self):
        try:
            ShizaScraper.fetch('{}/releases/favorite'.format(BASE_URL))
        except HTTPError as e:
            if e.code == 403:
                return False
            else:
                raise ScraperException('Ошибка соединения')
        return True


    def login(self, login, password):
        post = {'field-email':login, 'field-password':password}
        ShizaScraper.fetch('{}/accounts/login'.format(BASE_URL), post=post)


    def _check_pagination(self):
        self._total_page = 0

        pagination = common.parseDOM(self._html, 'ul', attrs={'class':'pagination pagination-centered'})
        if pagination:
            pages = common.parseDOM(pagination[0], 'a')

            for i in pages[::-1]:
                if i.isdigit():
                    break
            if i.isdigit():
                self._total_page = int(i)


    def _parse_releases(self):
        items = []

        releases = common.parseDOM(self._html, 'article', attrs={'class':'grid-card'})

        for release in releases:
            title = common.parseDOM(release, 'img', ret='alt')[0].replace('  ', ' ')
            title = common.replaceHTMLCodes(title)

            img = BASE_URL + common.parseDOM(release, 'img', ret='src')[0]
            url = common.parseDOM(release, 'a', attrs={'class':'card-box'}, ret='href')[0]
            id = url.split('/')[-1]

            status = common.parseDOM(release, 'span', attrs={'class':'relstatus'})
            if status:
                plot = u'[COLOR yellow]{}[/COLOR]\n'.format(status[0].strip())
            desc = common.parseDOM(release, 'a', attrs={'class':'card-box'}, ret='title')
            if desc:
                plot = plot + common.replaceHTMLCodes(desc[0])

            items.append({'title':title, 'url':url, 'img':img, 'plot':plot, 'id':id})
        return items


    def _parse_release(self):
        items = []

        covers = common.parseDOM(self._html, 'a', attrs={'class':'release-slider__item'}, ret='href')
        img = ''
        fanart = ''

        if covers:
            img = BASE_URL + covers[0]

            if len(covers) > 1:
                fanart = BASE_URL + covers[1]
            else:
                fanart = img

        # описание
        desc = common.parseDOM(self._html, 'div', attrs={'class':'desc'})
        if desc:
            plot = common.stripTags(common.replaceHTMLCodes(desc[0]).strip())
            age = common.parseDOM(self._html, 'span', attrs={'class':'watermark grad-warning'})
            if age:
                plot = u'[B][COLOR yellow]{0}[/COLOR][/B] {1}'.format(age[0], plot)

        items.append({'title':'Описание', 'img':img, 'fanart':fanart, 'plot':plot, 'type':'info'})

        # online
        if not self._hide_online:
            videos = common.parseDOM(self._html, 'a', attrs={'data-fancybox':'online'}, ret='href')
            if videos:
                plots = common.parseDOM(self._html, 'a', attrs={'data-fancybox':'online'})

                for i, v in enumerate(videos):
                    data = utils.parse_online_videos(v)
                    if not data:
                        continue

                    title = common.parseDOM(plots[i], 'p')[0]
                    url = data['url']
                    thumb = data['thumb']

                    if url[:4] == 'http':
                        items.append({'title':title, 'thumb':thumb, 'fanart':fanart, 'url':v, 'type':'online'})
                    else:
                        title = u'[COLOR red] {} [/COLOR]'.format(title)
                        url = u'[COLOR red] {} [/COLOR]'.format(url)
                        items.append({'title':title, 'thumb':img, 'fanart':fanart, 'plot':url, 'type':'offline'})

        # torrents
        titles = common.parseDOM(self._html, 'a', attrs={'data-toggle':'tab'})
        tabs = common.parseDOM(self._html, 'a', attrs={'data-toggle':'tab'}, ret='href')

        container = common.parseDOM(self._html, 'div', attrs={'class':'tab-content'})

        for i, t in enumerate(tabs):
            info = common.stripTags(titles[i]).replace('\t', '').strip()

            torrent = common.parseDOM(container, 'div', attrs={'id':t[1:]})
            url =  common.parseDOM(torrent, 'a', attrs={'class':'button--success button--big button--fluid'}, ret='href')

            if url:
                id = url[0].split('/')[-1]

                content = (common.parseDOM(container, 'div', attrs={'id': id})[0])

                title = utils.find_between(content, 'Видео', 'Аудио').replace('Видео', '')
                title = title + ' (' + utils.find_between(content, 'Размер:</b>', '<').strip() + ')'
                if title[0] == ':': title = title[1:]
                title = info + ', ' + common.stripTags(title)

                info = '[COLOR=yellow]{}[/COLOR]'.format(info)

                authors = [m.start() for m in re.finditer(r'Автор рипа:', content)]

                if len(authors) > 1:
                    info = '{}\n[B]Авторы рипов:[/B]\n'.format(info)
                else:
                    info = '{}\n[B]Автор рипа:[/B] '.format(info)
                for a in authors:
                    info = '{0}{1}\n'.format(info, common.stripTags(utils.find_between(content[a:], 'Автор рипа:', '<b')))

                counters = common.parseDOM(torrent, 'div', attrs={'class': 'torrent-counter'})[0]
                info = '{0}\n {1}'.format(info, re.sub(r' +', ' ', common.stripTags(counters).strip()))

                items.append({'title':title, 'img':img, 'fanart':fanart, 'plot':info, 'id':id, 'type':'torrent'})

        return items


    def get_torrent(self, release_id, torrent_id):
        return ShizaScraper.fetch('{0}/download/torrents/{1}/{2}'.format(BASE_URL, release_id, torrent_id))


    def get_torrent_items(self, release_id, torrent_id):

        torrent_data = self.get_torrent(release_id, torrent_id)

        data = utils.bdecode(torrent_data)

        items = []

        files = data['info'].get('files', None)

        if files == None:
            title = '{0} ({1:.0f} MB)'.format(data['info']['name'], data['info']['length'] / 1024 // 1024)
            items.append({'title':title, 'id':0})
        else:
            for i, f in enumerate(files):
                title = '{0} ({1:.0f} MB)'.format(f['path'][-1], f['length'] / 1024 // 1024)
                items.append({'title':title, 'id':i})
            items = sorted(items, key=lambda x: x['title'])

        return items


    def get_all(self):
        self._html = ShizaScraper.fetch(BASE_URL, {'page':self.page})
        self._check_pagination()
        return self._parse_releases()


    def find_all(self):
        query = self._query

        self._html = ShizaScraper.fetch('{}/releases/search'.format(BASE_URL), {'page':self.page, 'q':query})
        self._check_pagination()
        return self._parse_releases()


    def get_ongoing(self):
        self._html = ShizaScraper.fetch('{}/status/ongoing'.format(BASE_URL), {'page':self.page})
        self._check_pagination()
        return self._parse_releases()


    def get_novelty(self):
        self._html = ShizaScraper.fetch('{}/status/novelty'.format(BASE_URL), {'page':self.page})
        self._check_pagination()
        return self._parse_releases()


    def get_completed(self):
        self._html = ShizaScraper.fetch('{}/status/completed'.format(BASE_URL), {'page':self.page})
        self._check_pagination()
        return self._parse_releases()


    def get_suspended(self):
        self._html = ShizaScraper.fetch('{}/status/suspended'.format(BASE_URL), {'page':self.page})
        self._check_pagination()
        return self._parse_releases()


    def get_favorite(self):
        self._html = ShizaScraper.fetch('{}/releases/favorite'.format(BASE_URL), {'page':self.page})
        self._check_pagination()
        return self._parse_releases()


    def get_release(self, id):
        self._html = ShizaScraper.fetch('{0}/releases/view/{1}'.format(BASE_URL, id))
        return self._parse_release()

