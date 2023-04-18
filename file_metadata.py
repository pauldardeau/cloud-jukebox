from typing import Dict

COMPRESSED       = "compressed"
CONTAINER_NAME   = "container_name"
ENCRYPTED        = "encrypted"
FILE_NAME        = "file_name"
FILE_TIME        = "file_time"
FILE_UID         = "file_uid"
MD5_HASH         = "md5_hash"
OBJECT_NAME      = "object_name"
ORIGIN_FILE_SIZE = "origin_file_size"
PAD_CHAR_COUNT   = "pad_char_count"
STORED_FILE_SIZE = "stored_file_size"

class FileMetadata(object):

    def __init__(self):
        self.file_uid: str = ""
        self.file_name: str = ""
        self.origin_file_size: int = 0
        self.stored_file_size: int = 0
        self.pad_char_count: int = 0
        self.file_time: str = ""
        self.md5_hash: str = ""
        self.compressed: int = 0
        self.encrypted: int = 0
        self.container_name: str = ""
        self.object_name: str = ""

    def __eq__(self, other: 'FileMetadata') -> bool:
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

    def from_dictionary(self, dictionary: Dict[str, object], prefix: str = ""):
        if dictionary is not None:
            if prefix + FILE_UID in dictionary:
                self.file_uid = dictionary[prefix + FILE_UID]
            if prefix + FILE_NAME in dictionary:
                self.file_name = dictionary[prefix + FILE_NAME]
            if prefix + ORIGIN_FILE_SIZE in dictionary:
                self.origin_file_size = dictionary[prefix + ORIGIN_FILE_SIZE]
            if prefix + STORED_FILE_SIZE in dictionary:
                self.stored_file_size = dictionary[prefix + STORED_FILE_SIZE]
            if prefix + PAD_CHAR_COUNT in dictionary:
                self.pad_char_count = dictionary[prefix + PAD_CHAR_COUNT]
            if prefix + FILE_TIME in dictionary:
                self.file_time = dictionary[prefix + FILE_TIME]
            if prefix + MD5_HASH in dictionary:
                self.md5_hash = dictionary[prefix + MD5_HASH]
            if prefix + COMPRESSED in dictionary:
                self.compressed = dictionary[prefix + COMPRESSED]
            if prefix + ENCRYPTED in dictionary:
                self.encrypted = dictionary[prefix + ENCRYPTED]
            if prefix + CONTAINER_NAME in dictionary:
                self.container_name = dictionary[prefix + CONTAINER_NAME]
            if prefix + OBJECT_NAME in dictionary:
                self.object_name = dictionary[prefix + OBJECT_NAME]

    def to_dictionary(self, prefix: str = "") -> Dict[str, object]:
        d = {prefix + FILE_UID: self.file_uid,
             prefix + FILE_NAME: self.file_name,
             prefix + ORIGIN_FILE_SIZE: self.origin_file_size,
             prefix + STORED_FILE_SIZE: self.stored_file_size,
             prefix + PAD_CHAR_COUNT: self.pad_char_count,
             prefix + FILE_TIME: self.file_time,
             prefix + MD5_HASH: self.md5_hash,
             prefix + COMPRESSED: self.compressed,
             prefix + ENCRYPTED: self.encrypted,
             prefix + CONTAINER_NAME: self.container_name,
             prefix + OBJECT_NAME: self.object_name}
        return d
