from telegram_quote_bot.config import sp_user_id
from telegram_quote_bot.db_query import insert, query, insert_multiple
from telegram_quote_bot.utils import go_sleep
import spotipy
import logging
logger = logging.getLogger('TeleBot')


def get_spotify_playlist_url(playlist_id):
    platform_url = 'https://open.spotify.com/user/' + sp_user_id + '/playlist/'
    complete_url = platform_url + playlist_id
    return complete_url


def get_client():
    client_credentials_manager = spotipy.oauth2.SpotifyClientCredentials()
    return spotipy.Spotify(client_credentials_manager=client_credentials_manager)


class SpotifyHandler():
    def __init__(self, token=None):
        self.client = spotipy.Spotify(auth=token)
        self.keys = []
        self.next_page_indicator = None
        self.keys.append('name')
        self.next_page_indicator = 'next'
        self.playlist_id = None

    def get_online_playlists(self):
        response = self.client.user_playlists(sp_user_id)
        my_list = response['items']
        count = 1
        while len(my_list) < response['total'] \
                and self.next_page_indicator in response and response[self.next_page_indicator] is not None:
            go_sleep(2)
            response = self.client.user_playlists(sp_user_id, 50, count * 50)
            count += 1
            if len(response['items']) > 0:
                my_list += response['items']

        return my_list

    def add_playlist_ids_to_db_cache(self, playlists):
        insert("""DELETE FROM "cache" WHERE platform = 'spotify';""")
        insert_text = """INSERT INTO "cache" (playlist_title, playlist_id) VALUES %s;"""
        insert_args = []
        for playlist in playlists:
            insert_args.append((playlist[self.keys[0]], playlist['id']))
        insert_multiple(insert_text, insert_args)

    def update_playlist_cache(self):
        self.client = get_client()
        my_online_pls = self.get_online_playlists()
        old_cache_result = query("""SELECT COUNT(*) FROM "cache" WHERE platform = 'spotify';""")
        no_of_pl_in_old_cache = old_cache_result[0][0]
        self.add_playlist_ids_to_db_cache(my_online_pls)
        if no_of_pl_in_old_cache < len(my_online_pls):
            logger.debug("len of sp online pls: {}".format(len(my_online_pls)))
            logger.debug("no of pls in old cache: {}".format(no_of_pl_in_old_cache))
            newest_fiehe = query("""SELECT playlist_title, playlist_id FROM "cache"
                                    WHERE playlist_title LIKE '%Fiehe%' ORDER BY date DESC LIMIT 1;""")
            insert("""UPDATE "jobs" SET msg_text = %s WHERE interval = 'on fiehe pl';""",
                   (get_spotify_playlist_url(newest_fiehe[0][1]),))
