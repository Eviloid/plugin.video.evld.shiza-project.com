# -*- coding: utf-8 -*-

import xbmc, xbmcaddon, xbmcplugin, xbmcvfs
import os, sys

import http.cookiejar as cookielib

import urllib.request as urlrequest
import urllib.parse as urlparse
import urllib.error as urlerror


import CommonFunctions as common
import router
import utils

PLUGIN_NAME = 'SHIZA Project'

__all__ = ['run']


class Plugin():
    def __init__(self, name=None, addon_id=None):

        if addon_id:
            self._addon = xbmcaddon.Addon(id=addon_id)
        else:
            self._addon = xbmcaddon.Addon()

        self._addon_id = addon_id or self._addon.getAddonInfo('id')
        self._name = name or self._addon.getAddonInfo('name')

        self.icon = self._addon.getAddonInfo('icon')
        self.fanart = self._addon.getAddonInfo('fanart')

        self.addon_data = self._addon.getAddonInfo('profile')
        self.addon_folder = self._addon.getAddonInfo('path')

        self._handle = None
        self._url = ''
        self._params = {}

        self._cookie = None

        self._router = router.Router()

    @property
    def name(self):
        return self._name

    @property
    def addon(self):
        return self._addon

    @property
    def handle(self):
        return self._handle

    @property
    def params(self):
        return self._params

    @property
    def url(self):
        return self._url


    def get_setting(self, key):
        return self.addon.getSetting(key)


    def set_setting(self, key, value):
        self.addon.setSetting(key, value)


    def open_settings(self):
        self.addon.openSettings()


    def _load_cookie(self):
        cookiefile = xbmcvfs.translatePath(os.path.join(self.addon_data, 'fcookie.txt'))
        self._cookie = cookielib.MozillaCookieJar(cookiefile)
        try:
            self._cookie.load()
        except IOError:
            pass

        hr = urlrequest.HTTPCookieProcessor(self._cookie)
        opener = urlrequest.build_opener(hr)
        urlrequest.install_opener(opener)


    def save_cookie(self):
        if self._cookie:
            self._cookie.save()


    def main(self):
        common.plugin   = self.name
        self._url       = sys.argv[0]
        self._handle    = int(sys.argv[1])
        self._params    = utils.get_params(sys.argv[2])

        xbmcplugin.setContent(self.handle, 'tvshows')

        self._load_cookie()
        self._router.route(self)


def run():
    plugin = Plugin(PLUGIN_NAME)
    plugin.main()
