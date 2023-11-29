# -*- coding: utf-8 -*-

import xbmc, xbmcgui, xbmcplugin, xbmcvfs
import sys, os
import urllib.parse as urlparse


from scraper import ShizaScraper, ScraperException
import utils

class Router():
    def __init__(self):
        self._plugin = None
        self._params = {}
        self._hide_online = True
        self.routes = self._get_routes()

    def _get_routes(self):
        routes = {
            None: self._main_menu,
            'login': self._login,
            'release': self._show_release,
            'search': self._search,
            'info': self._show_info,
            'play': self._play,
            'radio': self._radio,
            'home': self._home,
            'cleancache': self._cleancache,
        }
        return routes

    def _add_item(self, title, params={}, arts={}, plot='', isFolder=False, isPlayable=False, url=None, info={}):
        if url is None:
            url = '%s?%s' % (self._plugin.url, urlparse.urlencode(params))

        item = xbmcgui.ListItem(title)
        info.update({'title':title, 'plot':plot})
        item.setInfo(type='video', infoLabels=info)

        item.setArt(arts)

        if isPlayable:
            item.setProperty('isPlayable', 'true')
            item.setProperty('mediatype', 'video')

        xbmcplugin.addDirectoryItem(self._plugin.handle, url=url, listitem=item, isFolder=isFolder)

    def _login(self):
        scraper = ShizaScraper()

        login = self._plugin.get_setting('User')
        password = self._plugin.get_setting('Password')

        if login:
            scraper.login(login, password)
            self._plugin.save_cookie()
            xbmcplugin.endOfDirectory(self._plugin.handle, False)
            xbmc.executebuiltin('Container.Refresh')
        else:
            self._plugin.open_settings()

    def _main_menu(self):
        scraper = ShizaScraper()
        auth = scraper.check_auth()

        if not auth:
            self._add_item('[B]Войти[/B]',   {'mode':'login'},     arts={'fanart':self._plugin.fanart}, isFolder=True)

        self._add_item('Все',                {'mode':'all'},       arts={'fanart':self._plugin.fanart, 'icon':self._plugin.icon}, isFolder=True)
        self._add_item('Онгоинги',           {'mode':'ongoing'},   arts={'fanart':self._plugin.fanart, 'icon':self._plugin.icon}, isFolder=True)
        self._add_item('В работе',           {'mode':'workin'},    arts={'fanart':self._plugin.fanart, 'icon':self._plugin.icon}, isFolder=True)
        self._add_item('Завершенные',        {'mode':'completed'}, arts={'fanart':self._plugin.fanart, 'icon':self._plugin.icon}, isFolder=True)
        self._add_item('Радио Shiza-Project', {'mode':'radio'},    arts={'fanart':self._plugin.fanart, 'thumb':self._plugin.icon}, isPlayable=True, info={'watched':'False'})
        self._add_item('Поиск',              {'mode':'search'},    arts={'fanart':self._plugin.fanart, 'icon':'DefaultAddonsSearch.png'}, isFolder=True)
        xbmcplugin.endOfDirectory(self._plugin.handle, True)

    def _sub_menu(self):
        scraper = ShizaScraper(after=self._params.get('after'), query=self._params.get('query'))
        mode = self._params.get('mode')

        if mode == 'all':
            items = scraper.get_all()
        elif mode == 'ongoing':
            items = scraper.get_ongoing()
        elif mode == 'workin':
            items = scraper.get_workin()
        elif mode == 'completed':
            items = scraper.get_completed()
        elif mode == 'favorite':
            items = scraper.get_favorite()
        elif mode == 'search':
            xbmcplugin.setPluginCategory(self._plugin.handle, category='Search')
            items = scraper.get_all()
        else:
            items = {}

        for item in items:
            title = item.get('title', '')
            image = item.get('img')
            plot  = item.get('plot', '')
            id    = item.get('url')
            self._add_item(title, {'mode':'release', 'id':id}, arts={'fanart':image, 'banner':image, 'poster':image}, plot=plot, isFolder=True)

        if scraper.after:
            arts={'fanart':self._plugin.fanart}

            self._params['after'] = scraper.after
            self._params['page'] = int(self._params.get('page', 1)) + 1
            self._add_item('Далее > {0} из {1}'.format(self._params['page'], scraper.total_page), params=self._params, arts=arts, isFolder=True)

            if self._params['page'] > 3:
                arts.update({'icon': 'DefaultFolderBack.png'})
                self._add_item('<< В начало', params={'mode':'home'}, arts=arts)

        xbmcplugin.endOfDirectory(self._plugin.handle, True)

    def _show_release(self):
        scraper = ShizaScraper(hide_online=self._hide_online)
        items = scraper.get_release(self._params.get('id'))

        for item in items:
            title  = item.get('title', '')
            image  = item.get('img')
            thumb  = item.get('thumb')
            fanart = item.get('fanart') if item.get('fanart') else self._plugin.fanart
            plot   = item.get('plot', '')
            url    = item.get('url')
            id     = item.get('id')
            type   = item.get('type')

            if type == 'info':
                self._add_item(title, {'mode':'info'}, arts={'fanart':fanart, 'banner':fanart, 'poster':image}, plot=plot)
                xbmcgui.Window(10000).setProperty('SHIZA_PLOT', u"{}".format(plot))

            elif type == 'online':
                self._add_item(title, {'mode':'play', 'url':url}, arts={'fanart':fanart, 'banner':fanart, 'thumb':thumb}, isPlayable=True)

            elif type == 'offline':
                self._add_item(title, {}, arts={'fanart':fanart, 'icon':self._plugin.icon}, plot=plot)

        xbmcplugin.setContent(self._plugin.handle, 'episodes')
        xbmcplugin.endOfDirectory(self._plugin.handle, True)

    def _search(self):
        keywords = self._params.get('query')

        if not keywords:
            kbd = xbmc.Keyboard('', 'Поиск:')
            kbd.doModal()
            if kbd.isConfirmed():
                keywords = kbd.getText()

        if keywords:
            self._params['query'] = keywords
            self._sub_menu()

    def _play(self):
        url = self._params.get('url') # online
        if url:
            url = utils.get_online_video_url(url)

        if url:
            item = xbmcgui.ListItem(path=url)
            xbmcplugin.setResolvedUrl(self._plugin.handle, True, item)

    def _radio(self):
        item = xbmcgui.ListItem(path='https://radio.shiza-project.com/ara-ara')
        xbmcplugin.setResolvedUrl(self._plugin.handle, True, item)

    def _home(self):
        xbmc.executebuiltin('Container.Update({}, replace)'.format(self._plugin.url))
        xbmcplugin.endOfDirectory(self._plugin.handle, True, True)

    def _show_info(self):
        info = xbmcgui.Window(10000).getProperty('SHIZA_PLOT')
        utils.open_info_window('Описание', info)

    def _cleancache(self):
        utils.clean_cache()


    def route(self, plugin):
        self._plugin = plugin
        self._hide_online = plugin.get_setting('HideOnline') == 'true'

        for key, value in plugin.params.items():
            self._params[key] = urlparse.unquote_plus(value)

        route = self.routes.get(plugin.params.get('mode'))
        if route:
            return route()

        return self._sub_menu()
