# -*- coding: utf-8 -*-

import re, json

from urllib.error import HTTPError

import api
import utils


class ScraperException(Exception):
    pass

class ShizaScraper():
    def __init__(self, after=None, query=None, hide_online=True):
        self._hide_online = hide_online
        self._after = after
        self._query = query
        self._total_page = 0
        self._json = None

    @property
    def after(self):
        return self._after

    @property
    def total_page(self):
        return self._total_page

    @classmethod
    def fetch(self, url, params={}, post={}, headers={}):
        return utils.get_html(url, params, post, headers)


    def check_auth(self):
        return True


    def login(self, login, password):
        pass


    def _check_pagination(self):
        data = self._json['data'].get('releases', self._json['data'].get('collections'))
        page_info = data['pageInfo']

        self._total_page = data.get('totalCount', 0) // api.ITEMS_PER_PAGE + 1

        if page_info['hasNextPage']:
            self._after = page_info['endCursor']
        else:
            self._after = ''


    def _parse_releases(self):
        items = []

        releases = self._json['data']['releases']

        for release in releases['edges']:
            node = release['node']
            title = node['name']

            announcement = ''

            if node['announcement']:
                announcement = node['announcement']
            elif node['episodesAired']:
                announcement = 'Добавлена {:02d} серия'.format(node['episodesAired'])

            original = node['originalName']
            genres = api.get_genres(node['genres'])

            plot = f'[COLOR yellow]{announcement}[/COLOR]\n\n[COLOR gray]{original}[/COLOR]'
            if genres:
                plot = f'{plot}\n\nЖанры: [COLOR ff137ddc]{genres}[/COLOR]'

            if node['season']:
                plot = f'{plot}\n\nСезон: [COLOR ff137ddc]{api.get_season(node)}[/COLOR]'

            id = node['id']
            img = api.get_poster(node)

            url = node['slug']
            items.append({'title':title, 'url':url, 'img':img, 'plot':plot, 'id':id})

        return items


    def _parse_release(self):
        items = []

        release = self._json['data']['release']

        plot = utils.clean_text(release['description'])
        mpaa = release.get('rating', '')
        if mpaa:
            plot = f'[B][COLOR yellow]{api.mpaa_rus(mpaa)}[/COLOR][/B] {plot}'

        fanart = release['cover']['original']['url'] if release['cover'] else ''
        img = api.get_poster(release)

        items.append({'title':'Описание', 'img':img, 'fanart':fanart, 'plot':plot, 'type':'info'})

        # online
        if not self._hide_online:

            # trailer
            if release['videos']:
                data = utils.parse_online_videos([v['embedUrl'] for v in release['videos']])
                if data:
                    url = data['url']
                    thumb = data['thumb']
                    video = data['embed']

                    if url[:4] == 'http':
                        items.append({'title':'Трейлер', 'thumb':thumb, 'fanart':fanart, 'url':video, 'type':'online'})

            for episode in release['episodes']:
                title = f'{episode["number"]}. {episode["name"]}'

                if episode['videos']:
                    data = utils.parse_online_videos([v['embedUrl'] for v in episode['videos']])
                    if not data:
                        continue

                    url = data['url']
                    thumb = data['thumb']
                    video = data['embed']

                    if url[:4] == 'http':
                        items.append({'title':title, 'thumb':thumb, 'fanart':fanart, 'url':video, 'type':'online'})
                    else:
                        title = f'[COLOR red]{title}[/COLOR]'
                        url = f'[COLOR red]{url}[/COLOR]'
                        items.append({'title':title, 'thumb':img, 'fanart':fanart, 'plot':url, 'type':'offline'})

        return items


    def get_all(self):
        query = api.get_all_query(self.after, self._query)
        answer = ShizaScraper.fetch(api.BASE_API_URL, post=query)
        self._json = json.loads(answer)
        self._check_pagination()
        return self._parse_releases()


    def get_ongoing(self):
        query = api.get_ongoing_query(self.after)
        answer = ShizaScraper.fetch(api.BASE_API_URL, post=query)
        self._json = json.loads(answer)
        self._check_pagination()
        return self._parse_releases()


    def get_workin(self):
        query = api.get_workin_query(self.after)
        answer = ShizaScraper.fetch(api.BASE_API_URL, post=query)
        self._json = json.loads(answer)
        self._check_pagination()
        return self._parse_releases()


    def get_completed(self):
        query = api.get_completed_query(self.after)
        answer = ShizaScraper.fetch(api.BASE_API_URL, post=query)
        self._json = json.loads(answer)
        self._check_pagination()
        return self._parse_releases()


    def get_favorite(self):
        return []


    def get_release(self, id):
        query = api.get_release_query(id)
        answer = ShizaScraper.fetch(api.BASE_API_URL, post=query)
        self._json = json.loads(answer)
        return self._parse_release()
