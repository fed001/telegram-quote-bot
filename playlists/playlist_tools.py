# Set DEVELOPER_KEY to the API key value from the APIs & auth > Registered apps
# tab of
#   https://cloud.google.com/console
# Please ensure that you have enabled the YouTube Data API for your project.
import os
import random
import re
import urllib
from time import sleep
import flask
import spotipy
import spotipy.util as util  # Don't remove
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from core.dbQuery import query

yt_api_key = None
if 'YOUTUBE_DEVELOPER_API_KEY' in locals():
    yt_api_key = os.environ['YOUTUBE_DEVELOPER_API_KEY']

YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'


def get_dates(dj, input_date, input_date_operator):
    if input_date_operator == 'exact':
        results = query("""SELECT DISTINCT DATE FROM MUSIC WHERE DJ = ? AND DATE LIKE ?""",
                        (dj.title(), '%{}%'.format(input_date),))
    elif input_date_operator == 'newer':
        results = query("""SELECT DISTINCT DATE FROM MUSIC WHERE DJ = ? AND DATE >= ?""",
                        (dj.title(), '{}'.format(input_date),))
    elif input_date_operator == 'older':
        results = query("""SELECT DISTINCT DATE FROM MUSIC WHERE DJ = ? AND DATE <= ?""",
                        (dj.title(), '{}'.format(input_date),))
    results_len = len(results)
    print("Found {} Playlists in the database.".format(results_len))
    return results


def get_video_id(video_url):
    start_pos = re.search(r'watch\?v=', video_url)

    if not start_pos:
        start_pos = re.search(r'youtu.be/', video_url).end()

    return video_url[start_pos:]


def yt_playlist_insert(video_id, client, playlist_id):
    if video_id:
        try:
            answer = playlist_items_insert(client,
                                           {'snippet.playlistId': playlist_id,
                                            'snippet.resourceId.kind': 'youtube#video',
                                            'snippet.resourceId.videoId': video_id,
                                            'snippet.position': ''},
                                           part = 'snippet',
                                           onBehalfOfContentOwner = '')
        except Exception as e:
            print(e)
        print answer


def playlists_insert(client, properties, **kwargs):
    resource = build_resource(properties)
    kwargs = remove_empty_kwargs(**kwargs)
    response = client.playlists().insert(body = resource, **kwargs).execute()

    return response


def playlist_items_list_by_playlist_id(client, **kwargs):
    kwargs = remove_empty_kwargs(**kwargs)
    response = client.playlistItems().list(**kwargs).execute()

    return response


def playlists_list_by_channel_id(yt_client, **kwargs):
    kwargs = remove_empty_kwargs(**kwargs)
    response = yt_client.playlists().list(**kwargs).execute()

    return response


def get_yt_playlist_id(client, playlist_title, playlist_description):
    playlists_insert_response = client.playlists().insert(
        part = "snippet,status",
        body = dict(snippet = dict(title = playlist_title,
                                   description = playlist_description),
                    status = dict(privacyStatus = "public"))).execute()

    return playlists_insert_response["id"]


def playlist_items_insert(client, properties, **kwargs):
    resource = build_resource(properties)
    kwargs = remove_empty_kwargs(**kwargs)
    response = client.playlistItems().insert(body = resource, **kwargs).execute()

    return print_response(response)


def search_list_by_keyword(client, **kwargs):
    kwargs = remove_empty_kwargs(**kwargs)
    response = client.search().list(**kwargs).execute()

    return print_response(response)


def print_response(response):
    if response:
        return flask.jsonify(**response)
    else:
        return ('This request does not return a response. For these samples, ' +
                'this is generally true for requests that delete resources, ' +
                'such as <code>playlists.delete()</code>, but it is also ' +
                'true for some other methods, such as <code>videos.rate()</code>.')


def build_resource(properties):
    resource = {}
    for p in properties:
        # Given a key like "snippet.title", split into "snippet" and "title", where
        # "snippet" will be an object and "title" will be a property in that object.
        prop_array = p.split('.')
        ref = resource
        for pa in range(0, len(prop_array)):
            is_array = False
            key = prop_array[pa]

            # For properties that have array values, convert a name like
            # "snippet.tags[]" to snippet.tags, and set a flag to handle
            # the value as an array.
            if key[-2:] == '[]':
                key = key[0:len(key) - 2:]
                is_array = True

            if pa == (len(prop_array) - 1):
                # Leave properties without values out of inserted resource.
                if properties[p]:
                    if is_array:
                        ref[key] = properties[p].split(',')
                    else:
                        ref[key] = properties[p]
            elif key not in ref:
                # For example, the property is "snippet.title", but the resource does
                # not yet have a "snippet" object. Create the snippet object here.
                # Setting "ref = ref[key]" means that in the next time through the
                # "for pa in range ..." loop, we will be setting a property in the
                # resource's "snippet" object.
                ref[key] = {}
                ref = ref[key]
            else:
                # For example, the property is "snippet.description", and the resource
                # already has a "snippet" object.
                ref = ref[key]
    return resource


def remove_empty_kwargs(**kwargs):
    good_kwargs = {}
    if kwargs is not None:
        for key, value in kwargs.iteritems():
            if value:
                good_kwargs[key] = value
    return good_kwargs


def get_1st_yt_url(artist, track, yt_key):
    try:
        youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey = yt_key)

        # Call the search.list method to retrieve results matching the specified query term.
        search_response = youtube.search().list(q = artist + ' ' + track,
                                                part = 'id,snippet',
                                                maxResults = 1).execute()

        videos = []

        # Add each result to the appropriate list, and then display the lists of
        # matching videos, channels, and playlists.
        for search_result in search_response.get('items', []):
            if search_result['id']['kind'] == 'youtube#video':
                videos.append('%s' % (search_result['id']['videoId']))

        if len(videos) > 0:
            video_id = videos[0]
            str_video_link = 'https://youtu.be/' + video_id
        else:
            print('Nothing found on YouTube for: ' + artist + ' - ' + track)
            return ''

        return str_video_link
    except HttpError, e:
        print('An HTTP error %d occurred:\n%s' % (e.resp.status, e.content))


def cache_entries_exist(api):
    row_exists = query("""SELECT EXISTS(SELECT 1 FROM CACHE WHERE DATE > DATE('now', '-1 day')
                        AND PLATFORM LIKE ?);""", (api, ))
    if row_exists[0][0]:
        return True
    else:
        return False


def get_cache_entries(api, dj):
    if dj is None:
        rows = query("""SELECT PLAYLIST_ID FROM CACHE
                        WHERE DATE > DATE('now', '-1 day') AND PLATFORM LIKE ?
                        ORDER BY RANDOM() LIMIT 1;""", (api, ))
    else:
        rows = query("""SELECT PLAYLIST_ID FROM CACHE
                    WHERE DATE > DATE('now', '-1 day') AND PLATFORM LIKE ? AND PLAYLIST_TITLE LIKE ?
                    ORDER BY RANDOM() LIMIT 1;""", (api, '%{}%'.format(dj)))
    if len(rows) > 0:
        return rows[0][0]


def get_client(api, yt_key):
    if api == 'youtube':
        client = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey = yt_key)
    elif api == 'spotify':
        client_credentials_manager = spotipy.oauth2.SpotifyClientCredentials()
        client = spotipy.Spotify(client_credentials_manager = client_credentials_manager)

    return client


def get_playlist_id(api_obj, dj, yt_key = None):
    if cache_entries_exist(api_obj.name):
        playlist_id = get_cache_entries(api_obj.name, dj)
        api_obj.client = None
    else:
        api_obj.client = get_client(api_obj.name, yt_key)
        my_online_pls = api_obj.get_online_pls()
        api_obj.add_pl_ids_to_db_cache(my_online_pls)
        my_online_dj_pls = []
        if dj is None:
            for my_online_pl in my_online_pls:
                if len(api_obj.keys) >= 1:
                    my_online_dj_pls.append(my_online_pl)
        else:
            #TODO clean up here
            for my_online_pl in my_online_pls:
                if len(api_obj.keys) > 1 and dj in my_online_pl[api_obj.keys[0]][api_obj.keys[1]].lower():
                    my_online_dj_pls.append(my_online_pl)
                elif len(api_obj.keys) == 1 and dj in my_online_pl[api_obj.keys[0]].lower():
                    my_online_dj_pls.append(my_online_pl)

        playlist_id = my_online_dj_pls[random.randint(0, len(my_online_dj_pls) - 1)]['id']

    return playlist_id


def go_sleep(limit):
    print("Sleeping {} second(s)...".format(limit))
    seconds = random.randint(1, limit)
    sleep(seconds)


user_agent_win_firefox = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11'
user_agent_win_chrome = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Chrome/61.0.3163'
user_agent_linux_chrome = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'


class MyOpener(urllib.FancyURLopener):
    version = user_agent_win_chrome
