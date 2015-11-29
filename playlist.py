class Playlist(object):
    def __init__(self, playlist_uid, playlist_name, playlist_description=None):
        self.playlist_uid = playlist_uid
        self.playlist_name = playlist_name
        self.playlist_description = playlist_description
        self.songs = []
