class Album(object):
    def __init__(self, album_uid: str, album_name: str, artist_uid: str, genre_uid: str = "",
                 album_description: str = ""):
        self.album_uid: str = album_uid
        self.album_name: str = album_name
        self.artist_uid: str = artist_uid
        self.genre_uid: str = genre_uid
        self.album_description: str = album_description
