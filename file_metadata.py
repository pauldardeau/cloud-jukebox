class FileMetadata(object):

    def __init__(self):
        self.file_uid = ""
        self.file_name = ""
        self.origin_file_size = 0
        self.stored_file_size = 0
        self.pad_char_count = 0
        self.file_time = ""
        self.md5_hash = ""
        self.compressed = 0
        self.encrypted = 0
        self.container_name = ""
        self.object_name = ""

    def __eq__(self, other):
        return self.file_uid == other.file_uid and \
               self.file_name == other.file_name and \
               self.origin_file_size == other.origin_file_size and \
               self.stored_file_size == other.stored_file_size and \
               self.pad_char_count == other.pad_char_count and \
               self.file_time == other.file_time and \
               self.md5_hash == other.md5_hash and \
               self.compressed == other.compressed and \
               self.encrypted == other.encrypted and \
               self.container_name == other.container_name and \
               self.object_name == other.object_name

    def from_dictionary(self, dictionary, prefix=None):
        if dictionary is not None:
            if prefix is None:
                prefix = ""
            if prefix + "file_uid" in dictionary:
                self.file_uid = dictionary[prefix + "file_uid"]
            if prefix + "file_name" in dictionary:
                self.file_name = dictionary[prefix + "file_name"]
            if prefix + "origin_file_size" in dictionary:
                self.origin_file_size = dictionary[prefix + "origin_file_size"]
            if prefix + "stored_file_size" in dictionary:
                self.stored_file_size = dictionary[prefix + "stored_file_size"]
            if prefix + "pad_char_count" in dictionary:
                self.pad_char_count = dictionary[prefix + "pad_char_count"]
            if prefix + "file_time" in dictionary:
                self.file_time = dictionary[prefix + "file_time"]
            if prefix + "md5_hash" in dictionary:
                self.md5_hash = dictionary[prefix + "md5_hash"]
            if prefix + "compressed" in dictionary:
                self.compressed = dictionary[prefix + "compressed"]
            if prefix + "encrypted" in dictionary:
                self.encrypted = dictionary[prefix + "encrypted"]
            if prefix + "container_name" in dictionary:
                self.container_name = dictionary[prefix + "container_name"]
            if prefix + "object_name" in dictionary:
                self.object_name = dictionary[prefix + "object_name"]

    def to_dictionary(self, prefix=None):
        d = {}
        if prefix is None:
            prefix = ""
        d[prefix + "file_uid"] = self.file_uid
        d[prefix + "file_name"] = self.file_name
        d[prefix + "origin_file_size"] = self.origin_file_size
        d[prefix + "stored_file_size"] = self.stored_file_size
        d[prefix + "pad_char_count"] = self.pad_char_count
        d[prefix + "file_time"] = self.file_time
        d[prefix + "md5_hash"] = self.md5_hash
        d[prefix + "compressed"] = self.compressed
        d[prefix + "encrypted"] = self.encrypted
        d[prefix + "container_name"] = self.container_name
        d[prefix + "object_name"] = self.object_name
        return d
