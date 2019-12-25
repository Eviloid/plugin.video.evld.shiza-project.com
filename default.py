#!/usr/bin/python
# -*- coding: utf-8 -*-
# Eviloid, 31.05.2018

import sys, os, cookielib, urllib2, urllib, re, urlparse, json
import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import CommonFunctions

PLUGIN_NAME   = 'SHIZA Project'
BASE_URL = 'http://shiza-project.com'

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'

common = CommonFunctions
common.plugin = PLUGIN_NAME

try:handle = int(sys.argv[1])
except:pass

def xt(x):return xbmc.translatePath(x)

addon = xbmcaddon.Addon(id='plugin.video.evld.shiza-project.com')

Pdir = addon.getAddonInfo('path')
icon = xt(os.path.join(Pdir, 'icon.png'))
fanart = xt(os.path.join(Pdir, 'fanart.jpg'))
fcookies = xt(os.path.join(Pdir, 'cookies.txt'))
cj = cookielib.MozillaCookieJar(fcookies)

xbmcplugin.setContent(handle, 'tvshows')

URL_RE = re.compile(r'^((http[s]?|ftp):\/)?\/?([^:\/\s]+)((\/\w+)*\/)([\w\-\.]?[^#?\s]+)(.*)?(#[\w\-]+)?$')

sections = {
    'all':              BASE_URL,
    'ongoing':          BASE_URL + '/status/ongoing',
    'novelty':          BASE_URL + '/status/novelty',
    'completed':        BASE_URL + '/status/completed',
    'suspended':        BASE_URL + '/status/suspended',
    'top':              BASE_URL + '/releases/top',
    'favorite':         BASE_URL + '/releases/favorite',
    'find':             BASE_URL + '/releases/search',

    'do_login':         BASE_URL + '/accounts/login',
    'view_release':     BASE_URL + '/releases/view',
    'get_torrent':      BASE_URL + '/download/torrents',
}

def find_between(s, first, last):
    start = s.find(first)
    if start < 0:
        return ''
    start += len(first)
    end = s.find(last, start)

    return s[start:end]


def build_next_page(pagination, next_page, params):
    pages = common.parseDOM(pagination[0], 'a')

    for i in pages[::-1]:
        if i.isdigit():
            break
    if i.isdigit():
        if int(i) > next_page - 1:
            params['page'] = next_page
            add_nav(u'Далее > %d из %s' % (next_page, i), params)


def do_login():
    if addon.getSetting('User') == '':
        addon.openSettings()
    else:
        post = {'field-email':addon.getSetting('User'), 'field-password':addon.getSetting('Password')}
        get_html(sections['do_login'], post=post)

        cj.save(fcookies, True, True)
        xbmc.executebuiltin('Container.Refresh')


def checkauth():
    html = get_html(sections['favorite'], noerror=False)
    return isinstance(html, basestring)


def get_html(url, params={}, post={}, noerror=True):
    headers = {'User-Agent':USER_AGENT}

    if post:
        headers['Content-Type'] = 'application/x-www-form-urlencoded'

    html = ''

    try:
        conn = urllib2.urlopen(urllib2.Request('%s?%s' % (url, urllib.urlencode(params)), urllib.urlencode(post), headers))
        html = conn.read()
        conn.close()
    except urllib2.HTTPError, err:
        if not noerror:
            html = err.code

        if err.code == 404:
            xbmc.log('Not found: ' + url.encode('utf-8'), xbmc.LOGWARNING)
        elif err.code == 403:
            xbmc.log('Forbidden: ' + url.encode('utf-8'), xbmc.LOGWARNING)
        else:
            pass

    return html 


def get_sibnet_data(url):
    html = get_html(url)

    res = {'url':'Видео не найдено', 'thumb':''}

    s = re.search(r'<div class=videostatus><p>(.*?)</p>', html)
    if s:
        res['url'] = s.group(1).decode('cp1251')
    else:
        s = re.search(r'player.src\(\[{src: "(.*?)"', html)
        if s:
            res['url'] = 'https://video.sibnet.ru' + s.group(1) + '|referer=' + url

        t = re.search(r'meta property="og:image" content="(.*?)"/>', html)
        if t:
            res['thumb'] = t.group(1)

    return res


def get_vk_data(url):
    html = get_html(url).decode('cp1251')

    res = {'url':'Видео не найдено', 'thumb':''}

    href = common.parseDOM(html, 'a', attrs={'class':'flat_button button_big'}, ret='href')
    if href:
        html = get_html('https:%s' % href[0])

        t = re.search(r'"info":\[.*?,"(.*?)"', html)
        if t:
            res['thumb'] = t.group(1).replace(r'\/', '/')
    else:
        t = common.parseDOM(html, 'div', attrs={'class':'video_box_msg_background'}, ret='style')
        if t:
            s = re.search(r'url\((.*?)\);', t[0])
            if s:
                res['thumb'] = s.group(1)

    s = re.findall(r'"url(\d+)":"(.+?)"', html)
    if s:
        res['url'] = s[-1][1].replace(r'\/', '/')
            
    return res


def get_myvi_data(url):
    res = {'url':'Видео недоступно', 'thumb':''}

    s = re.search(r'embed/html/(.*)', url)
    if s:
        url = 'http://myvi.ru/player/api/Video/Get/' + s.group(1) + '?sig'

        req = urllib2.Request(url)
        req.add_header('User-Agent', USER_AGENT)
        req.add_header('Cookie', 'UniversalUserID=cda9eb54bfb042b3863d2157258dd51e')

        try:
            conn = urllib2.urlopen(req)
            data = conn.read()
            conn.close()

            data = json.loads(data)

            res['thumb'] = 'http:' + data['sprutoData']['playlist'][0]['posterUrl']
            u = data['sprutoData']['playlist'][0]['video'][0]['url']
            res['url'] = u + '|Cookie=UniversalUserID=cda9eb54bfb042b3863d2157258dd51e'
        except:
            pass

    return res


def main_menu():
    auth = checkauth()
    if not auth:
        add_item ('[B]Войти[/B]',   {'mode':'login'},     fanart=fanart)
    add_item ('Все',                {'mode':'all'},       fanart=fanart)
    add_item ('Онгоинги',           {'mode':'ongoing'},   fanart=fanart)
    add_item ('Новинки',            {'mode':'novelty'},   fanart=fanart)
    add_item ('Завершенные',        {'mode':'completed'}, fanart=fanart)
    add_item ('Приостановленные',   {'mode':'suspended'}, fanart=fanart)

    if auth:
        add_item ('Избранные',      {'mode':'favorite'},  fanart=fanart)

    add_item ('Поиск',              {'mode':'find'},      fanart=fanart)

    xbmcplugin.endOfDirectory(handle)


def get_release_info(url):
    info = {'plot':'', 'enabled':True}

    if addon.getSetting('ShowDescriptions') != 'true':
        return info        

    html = get_html(url, noerror=False)

    if html == 404:
        info['plot'] = '[COLOR red]Страница не найдена (404)[/COLOR]'
        info['enabled'] = False
    if html == 403:
        info['plot'] = '[COLOR red]Доступ запрещен (403)[/COLOR]'
        info['enabled'] = False

    if isinstance(html, basestring):
        desc = common.parseDOM(html, 'p', attrs={'class':'desc'})
        if len(desc) <> 0:
            info['plot'] = common.stripTags(common.replaceHTMLCodes(desc[0]).strip())
            if addon.getSetting('ShowAgeRating') == 'true':
                age = common.parseDOM(html, 'span', attrs={'class':'watermark grad-warning'})
                if len(age) <> 0:
                    info['plot'] = '[B][COLOR yellow]%s[/COLOR][/B] %s' % (age[0], info['plot'])
    return info


def sub_menu(params):
    page = int(params.get('page', 1))

    params['page'] = page

    html = get_html(sections[params['mode']], params)

    releases = common.parseDOM(html, 'article', attrs={'class':'grid-card'})

    for release in releases:
        title = common.parseDOM(release, 'img', ret='alt')[0].replace('  ', ' ')
        img = BASE_URL + common.parseDOM(release, 'img', ret='src')[0]
        url = common.parseDOM(release, 'a', attrs={'class':'card-box'},ret='href')[0]

        data = get_release_info(url)

        if not data['enabled']: title = '[COLOR red] %s [/COLOR]' % title

        if addon.getSetting('ShowDescriptions') != 'true':
            status = common.parseDOM(release, 'span', attrs={'class':'relstatus'})
            if len(status) > 0:
                data['plot'] = '[COLOR yellow]%s[/COLOR]\n' % (status[0].strip())
            desc = common.parseDOM(release, 'a', attrs={'class':'card-box'}, ret='title')
            if len(desc) > 0:
                data['plot'] = data['plot'] + common.replaceHTMLCodes(desc[0])

        release_id = URL_RE.match(url).group(6)

        add_item(title, {'mode':'release', 'r':release_id}, fanart=img, banner=img, poster=img, plot=data['plot'])

    pagination = common.parseDOM(html, 'ul', attrs={'class':'pagination pagination-centered'})
    if len(pagination) > 0: build_next_page(pagination, page + 1, params)

    xbmcplugin.endOfDirectory(handle)


def input_text():
    result = ''

    skbd = xbmc.Keyboard()
    skbd.setHeading('Поиск:')
    skbd.doModal()
    if skbd.isConfirmed():
        result = skbd.getText()

    return result


def do_find(params):
    q = params.get('q', '')

    if q == '':
        q = input_text()
        params['q'] = q

    if q == '':
        return

    sub_menu(params)


def sub_release(params):
    html = get_html(sections['view_release'] + '/' + params['r'])

    covers = common.parseDOM(html, 'a', attrs={'class':'release-slider__item'}, ret='href')

    img = ''
    fanart = ''

    if len(covers) > 0:
        img = BASE_URL + covers[0]

        if len(covers) > 1:
            fanart = BASE_URL + covers[1]
        else:
            fanart = img

    if addon.getSetting('HideOnline') == 'false':
        # online if exist
        if len(common.parseDOM(html, 'a', attrs={'data-fancybox':'online'}, ret='href')) > 0:
            plots = common.parseDOM(html, 'a', attrs={'data-fancybox':'online'})
            videos = common.parseDOM(html, 'a', attrs={'data-fancybox':'online'}, ret='href')

            for i, v in enumerate(videos):
                # support sibnet.ru, vk.com and myvi.ru
                if 'sibnet.ru' in v:
                    data = get_sibnet_data(v)
                elif 'vk.com' in v:
                    v = common.replaceHTMLCodes(v)
                    data = get_vk_data(v)
                elif 'myvi.ru' in v:
                    data = get_myvi_data(v)
                    if data['url'][:4] == 'http':
                        data['url'] = v.replace('http', 'myvi')
                else:
                    continue

                title = common.parseDOM(plots[i], 'p')[0]
                url = data['url']
                thumb = data['thumb']

                if url[:4] == 'http' or url[:4] =='myvi':
                    add_item(title, {'mode':'play','r':url}, fanart=fanart, banner=img, thumb=thumb, isFolder=False, isPlayable=True)
                else:
                    title = '[COLOR red] %s [/COLOR]' % title
                    url = '[COLOR red] %s [/COLOR]' % url
                    add_item(title, {}, fanart=fanart, banner=img, poster=img, url='', plot=url, isFolder=False, isPlayable=False)

    # torrents
    plot = common.parseDOM(html, 'ul', attrs={'class':'torrent-title'})
    torrents = common.parseDOM(html, 'a', attrs={'class':'btn btn-torrent grad-success'}, ret='href')

    for i, t in enumerate(torrents):
        url = t
        torrent_id = URL_RE.match(url).group(6)

        content = (common.parseDOM(html, 'div', attrs={'id': torrent_id})[0]).encode('utf-8')
        title = find_between(content, 'Раздел:</b>', '<br')
        title = title + find_between(content, 'Видео', 'Аудио').replace('Видео', '')
        title = title + ' (' + find_between(content, 'Размер:</b>', '<').strip() + ')'
        if title[0] == ':': title = title[1:]
        title = common.stripTags(title)

        authors = [m.start() for m in re.finditer('Автор рипа:', content)]

        if len(authors) > 1:
            info = '[B]Авторы рипов:[/B]\n'
        else:
            info = '[B]Автор рипа:[/B] '
        for a in authors:
            info += common.stripTags(find_between(content[a:], 'Автор рипа:', '<b')) + '\n'

        info = info + '\n' + common.stripTags(plot[i]).replace('\t', '').encode('utf-8')

        add_item(title, {'mode':'series','r':params['r'], 't':torrent_id}, fanart=fanart, banner=img, poster=img, plot=info)

    xbmcplugin.setContent(handle, 'episodes')
    xbmcplugin.endOfDirectory(handle)


def sub_series(params):
    torrent_data = get_html(sections['get_torrent'] + '/' + params['r'] + '/' + params['t'])

    import bencode
    torrent = bencode.bdecode(torrent_data)

    series = {}

    try:
        files = torrent['info'].get('files', None)
        if files == None:
            add_item(torrent['info']['name'], {'mode':'play','r':params['r'],'t':params['t'],'i':0}, fanart=fanart, isPlayable=True, isFolder=False)
        else:
            for i, f in enumerate(files):
                name = f['path'][-1]
                series[i] = name

            if addon.getSetting('SortSeries') == 'true':
                for i in sorted(series, key=series.get):
                    add_item(series[i], {'mode':'play','r':params['r'],'t':params['t'],'i':i}, fanart=fanart, isPlayable=True, isFolder=False)
            else:
                for i in series:
                    add_item(series[i], {'mode':'play','r':params['r'],'t':params['t'],'i':i}, fanart=fanart, isPlayable=True, isFolder=False)
            
        xbmcplugin.setContent(handle, 'files')
        xbmcplugin.endOfDirectory(handle)
    except:
        pass


def sub_play_yatp(url, ind):
    purl = 'plugin://plugin.video.yatp/?action=play&torrent=' + urllib.quote_plus(url) + '&file_index=' + str(ind)
    item = xbmcgui.ListItem(path=purl)
    xbmcplugin.setResolvedUrl(handle, True, item)


def sub_play_tam(url, ind):
	purl ='plugin://plugin.video.tam/?mode=play&url='+ urllib.quote_plus(url) + '&ind=' + str(ind)
	item = xbmcgui.ListItem(path=purl)
	xbmcplugin.setResolvedUrl(handle, True, item)


def sub_play(params):
    if params['r'][:4] == 'http':
        purl = urllib.unquote_plus(params['r'])
        item = xbmcgui.ListItem(path=purl)
        xbmcplugin.setResolvedUrl(handle, True, item)
        return

    if params['r'][:4] == 'myvi':
        url = urllib.unquote_plus(params['r']).replace('myvi', 'http')
        data = get_myvi_data(url)

        item = xbmcgui.ListItem(path=data['url'])
        xbmcplugin.setResolvedUrl(handle, True, item)
        return

    file_id = int(params.get('i', 0))
    uri = sections['get_torrent'] + '/' + params['r'] + '/' + params['t']
    
    torrent = get_html(uri)

    temp_name = os.path.join(xt('special://masterprofile'), 'shiza.torrent')

    temp_file = open(temp_name, "wb")
    temp_file.write(torrent)
    temp_file.close()

    uri = 'file://' + temp_name.replace('\\', '//')

    if addon.getSetting('Engine') == '1':
        sub_play_yatp(uri, file_id)
        return

    if addon.getSetting('Engine') == '2':
        sub_play_tam(uri, file_id)
        return

    #, cwd=os.path.dirname(binary_path)) in torrent2html engine.py

    from torrent2http import State, Engine, MediaType
    progressBar = xbmcgui.DialogProgress()
    from contextlib import closing
    DDir=xt('special://masterprofile')

    progressBar.create('Torrent2Http', 'Запуск')
    # XBMC addon handle
    # handle = ...
    # Playable list item
    # listitem = ...
    # We can know file_id of needed video file on this step, if no, we'll try to detect one.
    # file_id = None
    # Flag will set to True when engine is ready to resolve URL to XBMC
    ready = False
    # Set pre-buffer size to 15Mb. This is a size of file that need to be downloaded before we resolve URL to XMBC 
    pre_buffer_bytes = 15 * 1024 * 1024
    
    engine = Engine(uri, download_path=DDir)
    with closing(engine):
        # Start engine and instruct torrent2http to begin download first file, 
        # so it can start searching and connecting to peers  
        engine.start(file_id)
        progressBar.update(0, 'Torrent2Http', 'Загрузка торрента', "")
        while not xbmc.abortRequested and not ready:
            xbmc.sleep(500)

            if progressBar.iscanceled():
                ready = False
                break

            status = engine.status()
            # Check if there is loading torrent error and raise exception 
            engine.check_torrent_error(status)
            # Trying to detect file_id
            if file_id is None:
                # Get torrent files list, filtered by video file type only
                files = engine.list(media_types=[MediaType.VIDEO])
                # If torrent metadata is not loaded yet then continue
                if files is None:
                    continue
                # Torrent has no video files
                if not files:
                    progressBar.close()
                    break
                # Select first matching file                    
                file_id = files[0].index
                file_status = files[0]
            else:
                # If we've got file_id already, get file status
                file_status = engine.file_status(file_id)
                # If torrent metadata is not loaded yet then continue
                if not file_status:
                    continue
            if status.state == State.DOWNLOADING:
                # Wait until minimum pre_buffer_bytes downloaded before we resolve URL to XBMC
                if file_status.download >= pre_buffer_bytes:
                    ready = True
                    break
                #print file_status
                #downloadedSize = status.total_download / 1024 / 1024
                getDownloadRate = status.download_rate / 1024 * 8
                #getUploadRate = status.upload_rate / 1024 * 8
                getSeeds = status.num_seeds
                
                progressBar.update(100 * file_status.download / pre_buffer_bytes, 'Предварительная буферизация: ' + str(file_status.download / 1024 / 1024) + " MB", "Сиды: " + str(getSeeds), "Скорость: " + str(getDownloadRate)[:4] + ' Mbit/s')
                
            elif status.state in [State.FINISHED, State.SEEDING]:
                #progressBar.update(0, 'T2Http', 'We have already downloaded file', "")
                # We have already downloaded file
                ready = True
                break
            
            # Here you can update pre-buffer progress dialog, for example.
            # Note that State.CHECKING also need waiting until fully finished, so it better to use resume_file option
            # for engine to avoid CHECKING state if possible.
            # ...
        progressBar.update(0)
        progressBar.close()
        if ready:
            # Resolve URL to XBMC
            item = xbmcgui.ListItem(path=file_status.url)
            xbmcplugin.setResolvedUrl(handle, True, item)
            xbmc.sleep(3000)
            # Wait until playing finished or abort requested
            while not xbmc.abortRequested and xbmc.Player().isPlaying():
                xbmc.sleep(500)


def add_nav(title, params={}):
    url = '%s?%s' % (sys.argv[0], urllib.urlencode(params))
    item = xbmcgui.ListItem(title)
    xbmcplugin.addDirectoryItem(handle, url=url, listitem=item, isFolder=True)


def add_item(title, params={}, banner='', fanart='', poster='', thumb='', plot='', isFolder=True, isPlayable=False, url=None):

    if url == None: url = '%s?%s' % (sys.argv[0], urllib.urlencode(params))

    item = xbmcgui.ListItem(common.replaceHTMLCodes(title), iconImage = icon, thumbnailImage = thumb)
    item.setInfo(type='Video', infoLabels={'Title': title, 'Plot': plot})
    if isPlayable:
        item.setProperty('IsPlayable', 'true')
    
    if banner != '':
        item.setArt({'banner': banner})
    if fanart != '':
        item.setArt({'fanart': fanart})
    if poster != '':
        item.setArt({'poster': poster})
    if thumb != '':
        item.setArt({'thumb': thumb})

    xbmcplugin.addDirectoryItem(handle, url=url, listitem=item, isFolder=isFolder)


def get_params():
    param = {}
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]
    return param


try:
    cj.load(fcookies, True, True)
except:
    pass

hr = urllib2.HTTPCookieProcessor(cj)
opener = urllib2.build_opener(hr)
urllib2.install_opener(opener)

#params = common.getParameters(sys.argv[2])
# issue: https://github.com/HenrikDK/xbmc-common-plugin-functions/issues/6
params = get_params()

mode = params.get('mode', '')
page = params.get('page', 1)
q = params.get('q', '')
r = params.get('r', '')
t = params.get('t', '')
i = params.get('i', 0)

if mode == '': main_menu()
elif mode == 'login': do_login()
elif mode == 'favorite': sub_menu({'mode':mode,'page':page})
elif mode == 'find': do_find({'mode':mode,'page':page,'q':q})

elif mode == 'release': sub_release({'mode':mode,'r':r})
elif mode == 'series': sub_series({'mode':mode,'r':r, 't':t})
elif mode == 'play': sub_play({'mode':mode,'r':r,'t':t,'i':i})
elif mode == 'cleancache':
    from tccleaner import TextureCacheCleaner as tcc
    tcc().remove_like('%shiza-project.com/upload/covers/%', True)
    tcc().remove_like('%video.sibnet.ru/upload/cover/%', True)

else:
    sub_menu({'mode':mode, 'page':page})
