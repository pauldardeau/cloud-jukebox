

class SongFile:
    def __init__(self):
        self.uid = ""
        self.artist_name = ""
        self.song_name = ""
        self.origin_file_size = 0
        self.stored_file_size = 0
        self.pad_char_count = 0
        self.file_time = ""
        self.md5 = ""
        self.compressed = 0
        self.encrypted = 0
        self.container = ""
        self.object_name = ""

    def __eq__(self, other):
        return self.uid == other.uid and \
               self.artist_name == other.artist_name and \
               self.song_name == other.song_name and \
               self.origin_file_size == other.origin_file_size and \
               self.stored_file_size == other.stored_file_size and \
               self.pad_char_count == other.pad_char_count and \
               self.file_time == other.file_time and \
               self.md5 == other.md5 and \
               self.compressed == other.compressed and \
               self.encrypted == other.encrypted and \
               self.container == other.container and \
               self.object_name == other.object_name

    def from_dictionary(self, dictionary, prefix):
        if dictionary is not None:
            if prefix is None:
                prefix = ""

            if prefix + "uid" in dictionary:
                self.uid = dictionary[prefix + "uid"]
            if prefix + "artist_name" in dictionary:
                self.artist_name = dictionary[prefix + "artist_name"]
            if prefix + "song_name" in dictionary:
                self.song_name = dictionary[prefix + "song_name"]
            if prefix + "origin_file_size" in dictionary:
                self.origin_file_size = dictionary[prefix + "origin_file_size"]
            if prefix + "stored_file_size" in dictionary:
                self.stored_file_size = dictionary[prefix + "stored_file_size"]
            if prefix + "pad_char_count" in dictionary:
                self.pad_char_count = dictionary[prefix + "pad_char_count"]
            if prefix + "file_time" in dictionary:
                self.file_time = dictionary[prefix + "file_time"]
            if prefix + "md5" in dictionary:
                self.md5 = dictionary[prefix + "md5"]
            if prefix + "compressed" in dictionary:
                self.compressed = dictionary[prefix + "compressed"]
            if prefix + "encrypted" in dictionary:
                self.encrypted = dictionary[prefix + "encrypted"]
            if prefix + "container" in dictionary:
                self.container = dictionary[prefix + "container"]
            if prefix + "object_name" in dictionary:
                self.object_name = dictionary[prefix + "object_name"]

    def to_dictionary(self, prefix):
        d = {}

        if prefix is None:
            prefix = ""

        d[prefix + "uid"] = self.uid
        d[prefix + "artist_name"] = self.artist_name
        d[prefix + "song_name"] = self.song_name
        d[prefix + "origin_file_size"] = self.origin_file_size
        d[prefix + "stored_file_size"] = self.stored_file_size
        d[prefix + "pad_char_count"] = self.pad_char_count
        d[prefix + "file_time"] = self.file_time
        d[prefix + "md5"] = self.md5
        d[prefix + "compressed"] = self.compressed
        d[prefix + "encrypted"] = self.encrypted
        d[prefix + "container"] = self.container
        d[prefix + "object_name"] = self.object_name

        return d

