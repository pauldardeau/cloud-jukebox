from typing import Dict

import file_metadata
import typing


class SongMetadata:

    def __init__(self):
        self.fm: typing.Optional[file_metadata.FileMetadata] = None
        self.artist_uid: str = ""
        self.artist_name: str = ""  # keep temporarily until artist_uid is hooked up to artist table
        self.album_uid: str = ""
        self.song_name: str = ""

    def __eq__(self, other: 'SongMetadata') -> bool:
        return self.fm == other.fm and \
               self.artist_uid == other.artist_uid and \
               self.artist_name == other.artist_name and \
               self.album_uid == other.album_uid and \
               self.song_name == other.song_name

    def from_dictionary(self, dictionary: Dict[str, object], prefix: str = ""):
        if dictionary is not None:
            self.fm = file_metadata.FileMetadata()
            self.fm.from_dictionary(dictionary, prefix)
            if prefix + "artist_uid" in dictionary:
                self.artist_uid = dictionary[prefix + "artist_uid"]
            if prefix + "artist_name" in dictionary:
                self.artist_name = dictionary[prefix + "artist_name"]
            if prefix + "album_uid" in dictionary:
                self.album_uid = dictionary[prefix + "album_uid"]
            if prefix + "song_name" in dictionary:
                self.song_name = dictionary[prefix + "song_name"]

    def to_dictionary(self, prefix: str = "") -> Dict[str, object]:
        d = {prefix + "fm": self.fm.to_dictionary(prefix),
             prefix + "artist_uid": self.artist_uid,
             prefix + "artist_name": self.artist_name,
             prefix + "album_uid": self.album_uid,
             prefix + "song_name": self.song_name}
        return d
