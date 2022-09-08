# -*- coding: utf-8 -*-

import time, re, json
import urllib.request as urlrequest
import urllib.parse as urlparse
import xbmc, xbmcgui

import CommonFunctions as common

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'

def get_html(url, params={}, post={}, headers={}):
    headers['User-Agent'] = USER_AGENT
    headers['Accept-Encoding'] = 'gzip, identity'

    if params:
        url = '{0}?{1}'.format(url, urlparse.urlencode(params))

    if post:
        if isinstance(post, dict):
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            request = urlrequest.Request(url, urlparse.urlencode(post).encode('utf-8'), headers=headers)
        else:
            headers['Content-Type'] = 'application/json'
            request = urlrequest.Request(url, post.encode('utf-8'), headers=headers)
    else:
        request = urlrequest.Request(url, headers=headers)

    conn = urlrequest.urlopen(request)

    data = conn.read()

    if conn.headers.get('Content-Encoding', '') == 'gzip':
        import zlib
        data = zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(data)

    if conn.headers.get_content_charset():
        data = data.decode(conn.headers.get_content_charset())

    conn.close()
    return data


def get_params(argv):
    param = {}
    paramstring = argv
    if len(paramstring) >= 2:
        params = argv
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


def clean_text(txt):
    return common.stripTags(common.replaceHTMLCodes(txt)) if txt else ''


def open_info_window(title, content, timeout=1):
    if content:
        window_id = 10147
        control_label = 1
        control_textbox = 5

        xbmc.executebuiltin("ActivateWindow({})".format(window_id))
        w = xbmcgui.Window(window_id)

        # Wait for window to open
        start_time = time.time()
        while (not xbmc.getCondVisibility("Window.IsVisible({})".format(window_id)) and
                time.time() - start_time < timeout):
            xbmc.sleep(50)

        w.getControl(control_label).setLabel(title)
        w.getControl(control_textbox).setText(content)


def _parse_myvi(url):
    result = {'url':'Видео недоступно', 'thumb':''}

    s = re.search(r'embed/html/(.*)', url)
    if s:
        url = 'http://myvi.ru/player/api/Video/Get/' + s.group(1) + '?sig'
        try:
            headers = {'Cookie':'UniversalUserID=cda9eb54bfb042b3863d2157258dd51e'}
            
            data = get_html(url, headers=headers)
            data = json.loads(data)

            result['thumb'] = 'http:' + data['sprutoData']['playlist'][0]['posterUrl']
            u = data['sprutoData']['playlist'][0]['video'][0]['url']
            result['url'] = u  + '|Cookie=UniversalUserID=cda9eb54bfb042b3863d2157258dd51e'
        except:
            pass

    return result


def _parse_sibnet(url):
    html = get_html(url)

    result = {'url':'Видео недоступно', 'thumb':''}

    try:
        s = re.search(r'<div class=videostatus><p>(.*?)</p>', html)
        if s:
            result['url'] = s.group(1).decode('cp1251')
        else:
            s = re.search(r'player.src\(\[{src: "(.*?)"', html)
            if s:
                result['url'] = 'https://video.sibnet.ru' + s.group(1) + '|referer=' + url

            t = re.search(r'meta property="og:image" content="(.*?)"/>', html)
            if t:
                result['thumb'] = t.group(1)
    except:
        pass

    return result


def _parse_vk(url):
    html = get_html(url)

    result = {'url':'Видео недоступно', 'thumb':''}

    try:
        href = common.parseDOM(html, 'a', attrs={'class':'flat_button button_big'}, ret='href')
        if href:
            html = get_html(re.sub(r'^//', 'https://', href[0]))

            t = re.search(r'"info":\[.*?,"(.*?)"', html)
            if t:
                result['thumb'] = t.group(1).replace(r'\/', '/')
        else:
            t = common.parseDOM(html, 'div', attrs={'class':'video_box_msg_background'}, ret='style')
            if t:
                s = re.search(r'url\((.*?)\);', t[0])
                if s:
                    result['thumb'] = s.group(1)

        s = re.findall(r'"url(\d+)":"(.+?)"', html)
        if s:
            result['url'] = s[-1][1].replace(r'\/', '/')
    except:
        pass
            
    return result


def _parse_kodik(url, info_only=True):
    result = {'url':'Видео недоступно', 'thumb':''}

    try:

        html = get_html(url)

        if info_only:
            s = re.search(r'nails = \[(".*?")\]', html)
            if s:
                thumbs = s.group(1).split(',')
                result['url'] = '//'
                result['thumb'] =  thumbs[0].strip(' "')

        else:
            s = re.search(r"data-code='(//.*?)'", html)
            if s:
                url = s.group(1)    

            video_type, video_id, video_hash = url.split('/')[3:6]
            payload = {'type':video_type, 'id':video_id, 'hash':video_hash}

            html = get_html('https://kodik.info/gvi', post=payload, headers={'Referer':'https://shiza-project.com/'})
            data = json.loads(html)

            import base64
            result['url'] = base64.standard_b64decode(data['links']['720'][0]['src'][::-1] + '===').decode('utf-8')


        result['thumb'] = re.sub(r'^//', 'https://', result['thumb'])
        result['url'] = re.sub(r'^//', 'https://', result['url'])
    except:
        pass

    return result


def parse_online_videos(urls):
    result = {'embed':'', 'url':'Видео недоступно', 'thumb':''}

    for url in urls:
        # fix url
        s = re.search(r'(.*?)"', url)
        if s:
            url = s.group(1)

        if 'sibnet.ru' in url:
            result.update(_parse_sibnet(url))
        elif 'vk.com' in url:
            result.update(_parse_vk(url))
        elif 'myvi.ru' in url:
            result.update(_parse_myvi(url))
        elif any(x in url for x in ['kodik', 'aniqit', 'anivod']):
            result.update(_parse_kodik(url))

        if result.get('url', '')[:4] == 'http':
            result['embed'] = url
            break

    return result


def get_online_video_url(url):
    data = {}

    if url:
        url = common.replaceHTMLCodes(url)
        if 'sibnet.ru' in url:
            data = _parse_sibnet(url)
        elif 'vk.com' in url:
            data = _parse_vk(url)
        elif 'myvi.ru' in url:
            data = _parse_myvi(url)
        elif any(x in url for x in ['kodik', 'aniqit', 'anivod']):
            data = _parse_kodik(url, False)

    url = data.get('url', '')
    if url[:4] == 'http':
        return url

    return None


def clean_cache():
    from tccleaner import TextureCacheCleaner as tcc
    tcc().remove_like('%shiza-project.com/upload/covers/%', True)
    tcc().remove_like('%video.sibnet.ru/upload/cover/%', True)


class BencodeException(Exception):
    pass

def bdecode(data):
    _decimal_match = re.compile(r'\d')

    def _dechunk(chunks):
        item = chunks.pop()

        if item == 'd': 
            item = chunks.pop()
            hash = {}
            while item != 'e':
                chunks.append(item)
                key = _dechunk(chunks)
                hash[key] = _dechunk(chunks)
                item = chunks.pop()
            return hash
        elif item == 'l':
            item = chunks.pop()
            list = []
            while item != 'e':
                chunks.append(item)
                list.append(_dechunk(chunks))
                item = chunks.pop()
            return list
        elif item == 'i':
            item = chunks.pop()
            num = ''
            while item != 'e':
                num  += item
                item = chunks.pop()
            return int(num)
        elif _decimal_match.search(item):
            num = ''
            while _decimal_match.search(item):
                num += item
                item = chunks.pop()
            line = ''
            for i in range(int(num)):
                line += chunks.pop()
            return line
        raise BencodeException('Invalid torrent file')

    chunks = []
    for item in list(data):
        chunks.append(chr(item))
    chunks.reverse()

    root = _dechunk(chunks)
    return root
