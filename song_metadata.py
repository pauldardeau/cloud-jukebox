import file_metadata


class SongMetadata:

    def __init__(self):
        self.fm = None
        self.artist_uid = ""
        self.artist_name = ""  # keep temporarily until artist_uid is hooked up to artist table
        self.album_uid = None
        self.song_name = ""

    def __eq__(self, other):
        return self.fm == other.fm and \
               self.artist_uid == other.artist_uid and \
               self.artist_name == other.artist_name and \
               self.album_uid == other.album_uid and \
               self.song_name == other.song_name

    def from_dictionary(self, dictionary, prefix):
        if dictionary is not None:
            if prefix is None:
                prefix = ""
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

    def to_dictionary(self, prefix):
        d = {}
        if prefix is None:
            prefix = ""
        d[prefix + "fm"] = self.fm.to_dictionary(prefix)
        d[prefix + "artist_uid"] = self.artist_uid
        d[prefix + "artist_name"] = self.artist_name
        d[prefix + "album_uid"] = self.album_uid
        d[prefix + "song_name"] = self.song_name
        return d
