class Album(object):
    def __init__(self, album_uid, album_name, artist_uid, genre_uid=None, album_description=None):
        self.album_uid = album_uid
        self.album_name = album_name
        self.artist_uid = artist_uid
        self.genre_uid = genre_uid
        self.album_description = album_description
