# coding: utf-8
__author__ = 'rik91'

import common
import bencode, hashlib
from bs4 import BeautifulSoup
from quasar import provider

# this read the settings
settings = common.Settings()
# define the browser
browser = common.Browser()
# create the filters
filters = common.Filtering()

# login
username = provider.ADDON.getSetting('username')  # username
password = provider.ADDON.getSetting('password')  # passsword
resp_login = provider.POST('%s/auth' % settings.value["url_address"], params={}, headers={}, data='username=' + username + '&password=' + password)
try:
    token = resp_login.json()['token']
    provider.log.info('token : %s' % token)
except:
    provider.notify(message=resp_login.json()['error'], header=None, time=5000, image='')

def extract_torrents(data):
    sint = common.ignore_exception(ValueError)(int)
    results = []
    cont = 0
    if data is not None:
        filters.information()  # print filters settings
        links = data['torrents']
        for link in links:
            name = link['name']  # name
            magnet = '%s/torrents/download/%s' % (settings.value["url_address"], link['id'])  # magnet
            fsize = int(link['size'])/1000000 # size
            if fsize > 1000:
                size = "%0.2f Go" % (fsize/1000.00)
            else:
                size = "%0.2f Mo" % fsize
            seeds = link['seeders']  # seeds
            peers = link['leechers']  # peers
            # infohash
            metainfo = bencode.bdecode(provider.GET(magnet, params={}, headers={'Authorization': token}, data=None).data)
            info_hash = hashlib.sha1(bencode.bencode(metainfo['info'])).hexdigest()
            trackers = [metainfo["announce"]]
            if filters.verify(name, size):
                cont += 1
                results.append({"name": name.strip(),
                                "uri": magnet,
                                "info_hash": info_hash,
                                "is_private" : True,
                                "trackers" : trackers,
                                "size": size.strip(),
                                "seeds": sint(seeds),
                                "peers": sint(peers),
                                "language": settings.value.get("language", "fr"),
                                "provider": settings.name,
                                "icon": settings.icon,
                                })  # return the torrent
                if cont >= int(settings.value.get("max_magnets", 10)):  # limit magnets
                    break
            else:
                provider.log.warning(filters.reason)
    provider.log.info('>>>>>>' + str(cont) + ' torrents sent to Quasar<<<<<<<')
    return results


def search(query):
    info = {"query": query,
            "type": "general"}
    return search_general(info)


def search_general(info):
    category = {"movie": 0, "show": 433, "anime": 637, "general" : 0}
    info["extra"] = settings.value.get("extra", "")  # add the extra information
    if not "query_filter" in info:
        info["query_filter"] = ""
    query = filters.type_filtering(info, '-')  # check type filter and set-up filters.title
    url_search = "%s/torrents/search/%s&?limit=10&cid=%s%s" % (settings.value["url_address"], query, category[info["type"]], info["query_filter"])
    provider.log.info(url_search)
    data = provider.GET(url_search, params={}, headers={'Authorization': token}, data=None)
    return extract_torrents(data.json())


def search_movie(info):
    info["type"] = "movie"
    query = common.translator(info['imdb_id'], 'fr', False)  # Just title
    info["query"] = query + ' ' + str(info['year'])
    return search_general(info)


def search_episode(info):
    if info['absolute_number'] == 0:
        info["type"] = "show"
        info["query_filter"] = ""
        if(info['season']):
            if info['season'] < 25  or 27 < info['season'] < 31 :
                real_s = int(info['season']) + 967
            if info['season'] == 25 :
                real_s = 994
            if 25 < info['season'] < 28 :
                real_s = int(info['season']) + 966
            info["query_filter"] += '&term[45][]=%s' % real_s
        if(info['episode']):
            if info['episode'] < 9 :
                real_ep = int(info['episode']) + 936
            if 8 < info['episode'] < 31 :
                real_ep = int(info['episode']) + 937
            if 30 < info['episode'] < 61 :
                real_ep = int(info['episode']) + 1057
            info["query_filter"] += '&term[46][]=%s' % real_ep
        info["query"] = info['title'].encode('utf-8')  # define query
    else:
        info["type"] = "anime"
        info["query"] = info['title'].encode('utf-8') + ' %02d' % info['absolute_number']  # define query anime
    return search_general(info)


def search_season(info):
    info["type"] = "show"
    info["query_filter"]= "&term[46][]=936"
    if(info['season']):
        if info['season'] < 25  or 27 < info['season'] < 31 :
            real_s = int(info['season']) + 967
        if info['season'] == 25 :
            real_s = 994
        if 25 < info['season'] < 28 :
            real_s = int(info['season']) + 966
        info["query_filter"] += '&term[45][]=%s' % real_s
    info["query"] = info['title'].encode('utf-8')  # define query
    return search_general(info)

# This registers your module for use
provider.register(search, search_movie, search_episode, search_season)

del settings
del browser
del filters
