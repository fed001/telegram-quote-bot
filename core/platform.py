import re
from core.constants import sp_user_id
from core.dbQuery import query, insert
from playlists.playlist_tools import get_dates


class Platform(object):
    """
    Encapsulate data about the used Music Platform, Spotify or YouTube.
    """
    def __init__(self):
        self.online_pls = None
        self.online_dates = None
        self.missing_dates = None
        self.tracks_not_found = None
        self.track_uris = None
        self.found_quota = None

    def update_pls(self, dj):
        """
        Update DJ Playlists on Spotify & YouTube to be in sync with contents in the database.
        """
        my_online_pls = self.get_online_pls()
        self.add_pl_ids_to_db_cache(my_online_pls)
        self.online_pls = query("""SELECT DISTINCT PLAYLIST_TITLE FROM CACHE WHERE PLAYLIST_TITLE LIKE '%{}%'
                            AND PLATFORM LIKE ?;""".format(dj), (self.name,))
        self.online_dates = []
        self.missing_dates = []

        for online_pl in self.online_pls:
            if len(re.findall('\d', online_pl[0])) > 5:
                my_date = re.findall('\d\d\d\d-*\d\d-*\d\d', online_pl[0])
                if len(my_date) > 0:
                    my_date = my_date[0]
                    my_date = my_date.replace('-', '')
                    self.online_dates.append(my_date)

        offline_pls = query("""SELECT DISTINCT DATE FROM MUSIC WHERE DJ LIKE ?;""", (dj, ))
        offline_dates = []

        for offline_pl in offline_pls:
            offline_dates.append(offline_pl[0])

        for offline_date in offline_dates:
            if offline_date not in self.online_dates:
                self.missing_dates.append(offline_date)

        for missing_date in self.missing_dates:
            self.dj_set(dj, missing_date)

    def pl_queue(self):
        """
        Create Playlists that were collected in database table PLAYLIST.
        """
        pl_keys = query("""SELECT DISTINCT KEY FROM PLAYLIST;""")
        i = 0
        no_of_keys = len(pl_keys)
        step_size = round(100 * 1 / no_of_keys, 0)

        for pl_key in pl_keys:
            pl_key = pl_key[0]
            pl = Playlist()
            pl.playlist = query("""SELECT ARTIST, TRACK, PL_TITLE, PL_DESCRIPTION FROM PLAYLIST WHERE KEY = ?""",
                                (pl_key,))
            pl.title = pl.playlist[0][2]
            pl.description = pl.playlist[0][3]
            percentage = round(100 * float(i) / no_of_keys, 0)
            j = 1
            self.create_and_insert_online(pl, percentage, j, step_size)
            insert("""DELETE FROM PLAYLIST WHERE KEY = ?;""", (pl_key,))
            i += 1

        print("Playlist Queue done.")

    def dj_set(self, dj, input_date, input_date_operator = 'exact'):
        """
        Reproduce DJ's Playlist on Platform.
        """
        date_rows = get_dates(dj, input_date, input_date_operator)
        i = 0
        no_of_keys = len(date_rows)
        step_size = round(100 * 1 / no_of_keys, 0)

        for date_row in date_rows:
            date = date_row[0]
            formatted_date = '{}-{}-{}'.format(date[:4], date[4:6], date[6:])
            pl = Playlist()
            print("Working on Playlist of {}...".format(formatted_date))
            pl.playlist = query("""SELECT ARTIST, TRACK, DATE FROM MUSIC WHERE DJ LIKE ? AND DATE = ?""", (dj, date,))
            pl.title = "{} ".format(dj) + formatted_date
            pl.description = "{} Playlist of {}".format(dj.title(), formatted_date)
            percentage = round(100 * float(i) / no_of_keys, 0)
            j = 1
            self.create_and_insert_online(pl, percentage, j, step_size)
            i += 1

        print("Done with input date {}.".format(input_date))

    def artist_charts(self, dj, artist):
        """
        Create Playlist about Artist played by DJ.
        """
        artist4db = '%{}%'.format(artist)
        pl = Playlist()
        pl.playlist = query("""SELECT DISTINCT ARTIST, TRACK FROM MUSIC
                               WHERE DJ LIKE ? AND ARTIST LIKE ? ;""", (dj, artist4db))
        pl.title = "{} x {}".format(dj, artist.title())
        pl.description = "{} introducing {}".format(dj, artist.title())
        no_of_keys = 1
        step_size = round(100 * 1 / no_of_keys, 0)
        i = 0
        percentage = round(100 * float(i) / no_of_keys, 0)
        j = 1
        self.create_and_insert_online(pl, percentage, j, step_size)

    def charts(self, dj, order, date, limit = 100, threshhold = 1):
        """
        Create 'Best of'-Playlists.
        """
        year4db = '%{}%'.format(date)

        if order == 'descending':
            mini_label = 'Favorites'
        else:
            mini_label = 'Flop'

        pl = Playlist()
        pl.playlist = query("""SELECT ARTIST, TRACK, DATE, COUNT (*) C FROM MUSIC
                               WHERE DJ LIKE ? AND DATE LIKE ? GROUP BY ARTIST, TRACK HAVING C > ?
                               ORDER BY C DESC LIMIT ?;""", (dj, year4db, int(threshhold), limit))

        if date == '%':
            pl.title = "{} {}".format(dj, mini_label)
        else:
            label = '{} {}'.format(mini_label, limit)
            pl.title = "{} {} [{}]".format(dj, label, date)

        pl.description = "{} Favorite Tracks".format(dj)
        no_of_keys = 1
        step_size = round(100 * 1 / no_of_keys, 0)
        percentage = round(100 * float(0) / no_of_keys, 0)
        j = 1
        self.create_and_insert_online(pl, percentage, j, step_size)

    def create_and_insert_online(self, pl, percentage, j, step_size):
        """
        Create Playlist on Online Platform & insert Tracks.
        """
        pl_length = len(pl.playlist)
        print("Length of Playlist: {}".format(pl_length))
        self.create_playlist(pl)
        self.tracks_not_found = 0
        self.track_uris = []

        for pl_item in pl.playlist:
            self.add_to_playlist(pl_item)
            added = round(percentage + step_size * float(j) / pl_length, 0)
            print ("{}% added.".format(added))
            j += 1

        if pl_length:
            self.found_quota = 100.0 - round(100.0 * self.tracks_not_found / pl_length, 1)
            print("{} {} Track(s) found ({}% of Playlist).".format(
                pl_length - self.tracks_not_found, self.name.title(), self.found_quota))

        if self.name == 'spotify':
            if len(self.track_uris) > 0:
                results = self.client.user_playlist_add_tracks(sp_user_id, self.playlist_id, self.track_uris)
            else:
                print('Empty Spotify Playlist! Skipping...')
                return


class Playlist(object):
    """
    Encapsulate data about a playlist that should be added to Online Platform.
    """
    def __init__(self, title = None, description = None, playlist = None):
        self.title = title
        self.description = description
        self.playlist = playlist
