# -*- coding: utf-8 -*-

import xbmc, xbmcgui, xbmcplugin
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
            'torrent': self._show_torrent,
            'cleancache': self._cleancache,
        }
        return routes

    def _add_item(self, title, params={}, arts={}, plot='', isFolder=False, isPlayable=False, url=None):
        if url is None:
            url = '%s?%s' % (self._plugin.url, urlparse.urlencode(params))

        item = xbmcgui.ListItem(title)
        item.setInfo(type='video', infoLabels={'title':title, 'plot':plot})

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
        self._add_item('Новинки',            {'mode':'novelty'},   arts={'fanart':self._plugin.fanart, 'icon':self._plugin.icon}, isFolder=True)
        self._add_item('Завершенные',        {'mode':'completed'}, arts={'fanart':self._plugin.fanart, 'icon':self._plugin.icon}, isFolder=True)
        self._add_item('Приостановленные',   {'mode':'suspended'}, arts={'fanart':self._plugin.fanart, 'icon':self._plugin.icon}, isFolder=True)

        if auth:
            self._add_item('Избранные',      {'mode':'favorite'},  arts={'fanart':self._plugin.fanart, 'icon':self._plugin.icon}, isFolder=True)

        self._add_item('Поиск',              {'mode':'search'},    arts={'fanart':self._plugin.fanart, 'icon':'DefaultAddonsSearch.png'}, isFolder=True)
        xbmcplugin.endOfDirectory(self._plugin.handle, True)

    def _sub_menu(self):
        scraper = ShizaScraper(page=self._params.get('page'), query=self._params.get('query'))
        mode = self._params.get('mode')

        if mode == 'all':
            items = scraper.get_all()
        elif mode == 'ongoing':
            items = scraper.get_ongoing()
        elif mode == 'novelty':
            items = scraper.get_novelty()
        elif mode == 'completed':
            items = scraper.get_completed()
        elif mode == 'suspended':
            items = scraper.get_suspended()
        elif mode == 'favorite':
            items = scraper.get_favorite()
        elif mode == 'search':
            items = scraper.find_all()
        else:
            items = {}

        for item in items:
            title = item.get('title', '')
            image = item.get('img')
            plot  = item.get('plot', '')
            id    = item.get('id')
            self._add_item(title, {'mode':'release', 'id':id}, arts={'fanart':image, 'banner':image, 'poster':image}, plot=plot, isFolder=True)

        if scraper.total_page > 0:
            if scraper.total_page >= scraper.page + 1:
                self._params['page'] = scraper.page + 1
                self._add_item('Далее > {0} из {1}'.format(scraper.page + 1, scraper.total_page), params=self._params, isFolder=True)

        xbmcplugin.endOfDirectory(self._plugin.handle, True)

    def _show_release(self):
        scraper = ShizaScraper(hide_online=self._hide_online)
        items = scraper.get_release(self._params.get('id'))

        for item in items:
            title  = item.get('title', '')
            image  = item.get('img')
            thumb  = item.get('thumb')
            fanart = item.get('fanart')
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
                self._add_item(title, {}, arts={'fanart':fanart, 'banner':fanart, 'poster':image}, plot=plot)

            elif type == 'torrent':
                self._add_item(title, {'mode':'torrent', 'release':self._params.get('id'), 'id':id}, arts={'fanart':fanart, 'banner':fanart, 'poster':image}, plot=plot, isFolder=True)

        xbmcplugin.setContent(self._plugin.handle, 'episodes')
        xbmcplugin.endOfDirectory(self._plugin.handle, True)

    def _show_torrent(self):
        scraper = ShizaScraper()

        release_id = self._params.get('release')
        torrent_id = self._params.get('id')

        items = scraper.get_torrent_items(release_id, torrent_id)

        for i, item in enumerate(items):
            self._add_item(item['title'], {'mode':'play', 'release': release_id, 'id':torrent_id, 'index':i, 'oindex':item['id']}, arts={'fanart':self._plugin.fanart, 'icon':self._plugin.icon}, isPlayable=True)

        xbmcplugin.setContent(self._plugin.handle, 'files')
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
        else:
            release_id = self._params.get('release')
            torrent_id = self._params.get('id')
            index = int(self._params.get('index', 0))
            oindex = int(self._params.get('oindex', 0))
            preload_size = int(self._plugin.get_setting('Preload'))

            torrent = ShizaScraper().get_torrent(release_id, torrent_id)

            import player

            if self._plugin.get_setting('Engine') == '0':
                player.play_ts(self._plugin.handle, preload_size, self._plugin.get_setting('TSHost'), self._plugin.get_setting('TSPort'), torrent, index)
            else:
                temp_name = os.path.join(xbmc.translatePath('special://masterprofile'), 'ani.torrent')

                temp_file = open(temp_name.decode('utf-8') if sys.platform == 'win32' else temp_name, "wb")
                temp_file.write(torrent)
                temp_file.close()

                if self._plugin.get_setting('Engine') == '2':
                    url ='plugin://plugin.video.elementum/play?uri='+ urlparse.quote_plus(temp_name) + '&index={0}&oindex={1}'.format(index, oindex)
                else:
                    uri = 'file:///' + temp_name.replace('\\', '/')

                player.play_t2h(self._plugin.handle, preload_size, uri, oindex)


        if url:
            item = xbmcgui.ListItem(path=url)
            xbmcplugin.setResolvedUrl(self._plugin.handle, True, item)
        
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
