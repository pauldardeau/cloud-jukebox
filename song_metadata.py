from typing import Dict

import file_metadata
import typing


PROP_ALBUM_UID   = "album_uid"
PROP_ARTIST_NAME = "artist_name"
PROP_ARTIST_UID  = "artist_uid"
PROP_FM          = "fm"
PROP_SONG_NAME   = "song_name"

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
            if prefix + PROP_ARTIST_UID in dictionary:
                self.artist_uid = dictionary[prefix + PROP_ARTIST_UID]
            if prefix + PROP_ARTIST_NAME in dictionary:
                self.artist_name = dictionary[prefix + PROP_ARTIST_NAME]
            if prefix + PROP_ALBUM_UID in dictionary:
                self.album_uid = dictionary[prefix + PROP_ALBUM_UID]
            if prefix + PROP_SONG_NAME in dictionary:
                self.song_name = dictionary[prefix + PROP_SONG_NAME]

    def to_dictionary(self, prefix: str = "") -> Dict[str, object]:
        d = {prefix + PROP_FM: self.fm.to_dictionary(prefix),
             prefix + PROP_ARTIST_UID: self.artist_uid,
             prefix + PROP_ARTIST_NAME: self.artist_name,
             prefix + PROP_ALBUM_UID: self.album_uid,
             prefix + PROP_SONG_NAME: self.song_name}
        return d
