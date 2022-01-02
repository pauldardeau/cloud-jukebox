from typing import List

import song_metadata


class Playlist(object):
    def __init__(self, playlist_uid: str, playlist_name: str, playlist_description: str = ""):
        self.playlist_uid: str = playlist_uid
        self.playlist_name: str = playlist_name
        self.playlist_description: str = playlist_description
        self.songs: List[song_metadata.SongMetadata] = []
