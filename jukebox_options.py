import os.path
import aes


class JukeboxOptions:
    def __init__(self):
        self.debug_mode = False
        self.use_encryption = False
        self.use_compression = False
        self.check_data_integrity = False
        self.file_cache_count = 3
        self.number_songs = 0
        self.encryption_key = ""
        self.encryption_key_file = ""
        self.encryption_iv = ""

    def validate_options(self):
        if self.file_cache_count < 0:
            print "error: file cache count must be non-negative integer value"
            return False

        if len(self.encryption_key_file) > 0 and not os.path.isfile(self.encryption_key_file):
            print "error: encryption key file doesn't exist '%s'" % self.encryption_key_file
            return False

        if self.use_encryption:
            if not aes.is_available():
                print """encryption support not available. please install Crypto.Cipher for
                      encryption support (pycrypto-2.6.1)"""
                return False

            if len(self.encryption_key) == 0 and len(self.encryption_key_file) == 0:
                print "error: encryption key or encryption key file is required for encryption"
                return False

        return True

    def get_check_data_integrity(self):
        return self.check_data_integrity

    def set_check_data_integrity(self, check_data_integrity):
        self.check_data_integrity = check_data_integrity

    def get_debug_mode(self):
        return self.debug_mode

    def set_debug_mode(self, debug_mode):
        self.debug_mode = debug_mode

    def get_use_encryption(self):
        return self.use_encryption

    def set_use_encryption(self, use_encryption):
        self.use_encryption = use_encryption

    def get_use_compression(self):
        return self.use_compression

    def set_use_compression(self, use_compression):
        self.use_compression = use_compression

    def get_encryption_key(self):
        return self.encryption_key

    def set_encryption_key(self, encryption_key):
        self.encryption_key = encryption_key

    def get_encryption_key_file(self):
        return self.encryption_key_file

    def set_encryption_key_file(self, encryption_key_file):
        self.encryption_key_file = encryption_key_file

    def get_encryption_iv(self):
        return self.encryption_iv

    def set_encryption_iv(self, encryption_iv):
        self.encryption_iv = encryption_iv

    def get_file_cache_count(self):
        return self.file_cache_count

    def set_file_cache_count(self, file_cache_count):
        self.file_cache_count = file_cache_count
