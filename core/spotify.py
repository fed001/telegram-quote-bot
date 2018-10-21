import time
from googleapiclient.errors import HttpError
from core.constants import sp_user_id
from core.dbQuery import insert
from core.platform import Platform
from playlists.playlist_tools import go_sleep, get_playlist_id


class Spotify(Platform):
    def __init__(self, client = None):
        self.name = 'spotify'
        self.client = client
        self.keys = []
        self.next_page_indicator = None
        self.keys.append('name')
        self.next_page_indicator = 'next'
        self.playlist_id = None

    def create_playlist(self, pl):
        playlists = self.client.user_playlist_create(sp_user_id, pl.title)
        self.playlist_id = playlists['id']

    def add_to_playlist(self, playlist_item):
        artist = playlist_item[0]
        track = playlist_item[1]
        results = self.client.search(q = '{} - {}'.format(artist, track), limit = 1)
        if results['tracks']['items'] and results['tracks']['items'][0]['uri'] not in self.track_uris:
            current_result = results['tracks']['items'][0]['uri']
            self.track_uris.append(current_result)
        else:
            print("Spotify Track not found!")
            self.tracks_not_found += 1

    def get_online_pls(self):
        response = self.client.user_playlists(sp_user_id)
        my_list = response['items']

        while len(my_list) < response['total'] \
                and self.next_page_indicator in response and response[self.next_page_indicator] is not None:
            go_sleep(1)
            response = self.client.user_playlists(sp_user_id, 50, 50)
            if len(response['items']) > 0:
                my_list += response['items']

        return my_list

    def add_pl_ids_to_db_cache(self, my_list):
        keys = self.keys
        insert("""DELETE FROM CACHE WHERE PLATFORM LIKE 'spotify'""")
        for item in my_list:
            insert("""INSERT INTO CACHE VALUES ('spotify', ?, ?, ?, date('now'))""",
                   (item[keys[0]], item['id'], None))

    def get_rdm_playlist(self, dj = None):
        """
        Send one random playlist from specified DJ and Platform.
        :param self:
        :param dj:
        :return: complete_url
        """
        try:
            time.sleep(0.1)
            playlist_id = get_playlist_id(self, dj)
            platform_url = 'https://open.spotify.com/user/' + sp_user_id + '/playlist/'
            complete_url = platform_url + playlist_id
            return complete_url
        except HttpError, e:
            print('An HTTP error %d occurred:\n%s' % (e.resp.status, e.content))
        except Exception as e:
            print(e)
