class Genre(object):
    def __init__(self, genre_uid: str, genre_name: str, genre_description: str = ""):
        self.genre_uid: str = genre_uid
        self.genre_name: str = genre_name
        self.genre_description: str = genre_description
