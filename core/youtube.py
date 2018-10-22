import re
import time
from googleapiclient.errors import HttpError
from core.constants import yt_channel_id
from core.dbQuery import insert, query
from core.platform import Platform
from playlists.playlist_tools import get_yt_playlist_id, go_sleep, search_list_by_keyword, yt_playlist_insert, \
    playlists_list_by_channel_id, get_playlist_id, get_client, playlist_items_list_by_playlist_id, yt_api_key


class YouTube(Platform):
    def __init__(self, client = None):
        self.name = 'youtube'
        self.client = client
        self.keys = []
        self.next_page_indicator = None
        self.keys.append('snippet')
        self.keys.append('title')
        self.next_page_indicator = 'nextPageToken'
        self.playlist_id = None

    def create_playlist(self, pl):
        self.playlist_id = get_yt_playlist_id(self.client, pl.title, pl.description)

    def add_to_playlist(self, playlist_item):
        artist = playlist_item[0]
        track = playlist_item[1]
        go_sleep(1)
        result = search_list_by_keyword(self.client, part = 'snippet', maxResults = 1, q = artist + track, type = '')
        video_id = re.findall(r'"videoId": "(\S+)"', result.data)

        if len(video_id) > 0 and video_id[0] not in self.track_uris:
            video_id = video_id[0]
            self.track_uris.append(video_id)
            yt_playlist_insert(video_id, self.client, self.playlist_id)
        else:
            print("YouTube Track not found!")
            self.tracks_not_found += 1

    def get_online_pls(self):
        response = playlists_list_by_channel_id(self.client, part = 'snippet', channelId = yt_channel_id,
                                                maxResults = 50)

        my_list = response['items']

        while self.next_page_indicator in response and response[self.next_page_indicator] is not None:
            go_sleep(1)
            next_page_token = response[self.next_page_indicator]

            try:
                response = playlists_list_by_channel_id(self.client,
                                                        part = 'snippet',
                                                        channelId = yt_channel_id,
                                                        maxResults = 50,
                                                        pageToken = next_page_token)
            except HttpError as e:
                print('An HTTP error {} occurred:\n{}'.format(e.resp.status, e.content))
                print(e)
                go_sleep(5)

            if len(response['items']) > 0:
                my_list += response['items']

        return my_list

    def add_pl_ids_to_db_cache(self, my_list):
        keys = self.keys
        insert("""DELETE FROM CACHE WHERE PLATFORM LIKE 'youtube'""")
        for item in my_list:
            insert("""INSERT INTO CACHE VALUES ('youtube', ?, ?, ?, date('now'))""",
                   (item[keys[0]][keys[1]], item['id'], None))

    def get_rdm_playlist(self, dj = None):
        """
        Send one random playlist from specified DJ and Platform.
        :param self:
        :param dj:
        :return: complete_url
        """
        try:
            time.sleep(0.1)
            playlist_id = get_playlist_id(self, dj, yt_api_key)
            video_id = query("""SELECT VIDEO_ID FROM CACHE
                                WHERE DATE > DATE('NOW', '-1 DAY') 
                                AND PLATFORM LIKE 'youtube' AND PLAYLIST_ID = ? AND VIDEO_ID IS NOT NULL""",
                                (playlist_id,))
            if len(video_id) > 0:
                video_id = video_id[0][0]
            else:
                if self.client is None:
                    self.client = get_client('youtube', yt_api_key)
                video_id = playlist_items_list_by_playlist_id(self.client,
                                                              part = 'snippet,contentDetails',
                                                              maxResults = 1,
                                                              playlistId = playlist_id)
                video_id = video_id['items'][0]['contentDetails']['videoId']
                insert("""UPDATE OR IGNORE CACHE SET VIDEO_ID = ? WHERE PLATFORM LIKE 'youtube' AND PLAYLIST_ID = ?""",
                       (video_id, playlist_id))
            platform_url = 'https://www.youtube.com/watch?v=' + video_id + '&list='
            complete_url = platform_url + playlist_id
            return complete_url
        except HttpError as e:
            print('An HTTP error %d occurred:\n%s' % (e.resp.status, e.content))
        except Exception as e:
            print(e)
