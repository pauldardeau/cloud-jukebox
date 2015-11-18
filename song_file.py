

class SongFile:
    def __init__(self):
        self.uid = ""
        self.artistName = ""
        self.songName = ""
        self.originFileSize = 0
        self.storedFileSize = 0
        self.padCharCount = 0
        self.fileTime = ""
        self.md5 = ""
        self.compressed = 0
        self.encrypted = 0
        self.container = ""
        self.objectName = ""

    def __eq__(self, other):
        return self.uid == other.uid and \
               self.artistName == other.artistName and \
               self.songName == other.songName and \
               self.originFileSize == other.originFileSize and \
               self.storedFileSize == other.storedFileSize and \
               self.padCharCount == other.padCharCount and \
               self.fileTime == other.fileTime and \
               self.md5 == other.md5 and \
               self.compressed == other.compressed and \
               self.encrypted == other.encrypted and \
               self.container == other.container and \
               self.objectName == other.objectName

    def from_dictionary(self, dictionary, prefix):
        if dictionary is not None:
            if prefix is None:
                prefix = ""

            if prefix + "uid" in dictionary:
                self.uid = dictionary[prefix + "uid"]
            if prefix + "artistName" in dictionary:
                self.artistName = dictionary[prefix + "artistName"]
            if prefix + "songName" in dictionary:
                self.songName = dictionary[prefix + "songName"]
            if prefix + "originFileSize" in dictionary:
                self.originFileSize = dictionary[prefix + "originFileSize"]
            if prefix + "storedFileSize" in dictionary:
                self.storedFileSize = dictionary[prefix + "storedFileSize"]
            if prefix + "padCharCount" in dictionary:
                self.padCharCount = dictionary[prefix + "padCharCount"]
            if prefix + "fileTime" in dictionary:
                self.fileTime = dictionary[prefix + "fileTime"]
            if prefix + "md5" in dictionary:
                self.md5 = dictionary[prefix + "md5"]
            if prefix + "compressed" in dictionary:
                self.compressed = dictionary[prefix + "compressed"]
            if prefix + "encrypted" in dictionary:
                self.encrypted = dictionary[prefix + "encrypted"]
            if prefix + "container" in dictionary:
                self.container = dictionary[prefix + "container"]
            if prefix + "objectName" in dictionary:
                self.objectName = dictionary[prefix + "objectName"]

    def to_dictionary(self, prefix):
        d = {}

        if prefix is None:
            prefix = ""

        d[prefix + "uid"] = self.uid
        d[prefix + "artistName"] = self.artistName
        d[prefix + "songName"] = self.songName
        d[prefix + "originFileSize"] = self.originFileSize
        d[prefix + "storedFileSize"] = self.storedFileSize
        d[prefix + "padCharCount"] = self.padCharCount
        d[prefix + "fileTime"] = self.fileTime
        d[prefix + "md5"] = self.md5
        d[prefix + "compressed"] = self.compressed
        d[prefix + "encrypted"] = self.encrypted
        d[prefix + "container"] = self.container
        d[prefix + "objectName"] = self.objectName

        return d

    def get_pad_char_count(self):
        return self.padCharCount

    def set_pad_char_count(self, pad_char_count):
        self.padCharCount = pad_char_count

    def get_uid(self):
        return self.uid

    def set_uid(self, uid):
        self.uid = uid

    def get_artist_name(self):
        return self.artistName

    def set_artist_name(self, artist_name):
        self.artistName = artist_name

    def get_song_name(self):
        return self.songName

    def set_song_name(self, song_name):
        self.songName = song_name

    def get_origin_file_size(self):
        return self.originFileSize

    def set_origin_file_size(self, origin_file_size):
        self.originFileSize = origin_file_size

    def get_stored_file_size(self):
        return self.storedFileSize

    def set_stored_file_size(self, stored_file_size):
        self.storedFileSize = stored_file_size

    def get_file_time(self):
        return self.fileTime

    def set_file_time(self, file_time):
        self.fileTime = file_time

    def get_md5(self):
        return self.md5

    def set_md5(self, md5):
        self.md5 = md5

    def get_compressed(self):
        return self.compressed

    def set_compressed(self, compressed):
        self.compressed = compressed

    def get_encrypted(self):
        return self.encrypted

    def set_encrypted(self, encrypted):
        self.encrypted = encrypted

    def get_container(self):
        return self.container

    def set_container(self, container):
        self.container = container

    def get_object_name(self):
        return self.objectName

    def set_object_name(self, object_name):
        self.objectName = object_name
