from typing import Dict


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

    def to_dictionary(self, prefix: str = "") -> Dict[str, object]:
        d = {prefix + "file_uid": self.file_uid,
             prefix + "file_name": self.file_name,
             prefix + "origin_file_size": self.origin_file_size,
             prefix + "stored_file_size": self.stored_file_size,
             prefix + "pad_char_count": self.pad_char_count,
             prefix + "file_time": self.file_time,
             prefix + "md5_hash": self.md5_hash,
             prefix + "compressed": self.compressed,
             prefix + "encrypted": self.encrypted,
             prefix + "container_name": self.container_name,
             prefix + "object_name": self.object_name}
        return d
