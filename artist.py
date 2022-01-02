class Artist(object):
    def __init__(self, artist_uid: str, artist_name: str, artist_description: str = ""):
        self.artist_uid: str = artist_uid
        self.artist_name: str = artist_name
        self.artist_description: str = artist_description
