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
        self.suppress_metadata_download = False

    def validate_options(self):
        if self.file_cache_count < 0:
            print("error: file cache count must be non-negative integer value")
            return False

        if len(self.encryption_key_file) > 0 and not os.path.isfile(self.encryption_key_file):
            print("error: encryption key file doesn't exist '%s'" % self.encryption_key_file)
            return False

        if self.use_encryption:
            if not aes.is_available():
                print("""encryption support not available. please install Crypto.Cipher for
                      encryption support (pycrypto-2.6.1)""")
                return False

            if len(self.encryption_key) == 0 and len(self.encryption_key_file) == 0:
                print("error: encryption key or encryption key file is required for encryption")
                return False

        return True
