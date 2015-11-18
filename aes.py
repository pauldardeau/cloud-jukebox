_encryption_support = False


try:
    from Crypto.Cipher import AES
    import struct
    _encryption_support = True
except ImportError:
    _encryption_support = False


def is_available():
    return _encryption_support


class AESBlockEncryption:
    def __init__(self, key_size_bytes, encrypt_key, iv):
        self.key = encrypt_key  # 32 bytes for AES-256
        self.iv = iv  # must be block_size bytes long (16 bytes)
        self.mode = AES.MODE_CBC  # Cipher-Block Chaining
        self.keySizeBytes = key_size_bytes  # AES-256
        self.ivLength = 16  # initialization vector length

        if self.key is not None:
            key_length = len(self.key)
            if key_length == 0:
                raise Exception('encryption key cannot be empty')
            else:
                if key_length > self.keySizeBytes:
                    # substring (shorten) it
                    self.key = self.key[0:self.keySizeBytes]
                elif key_length < self.keySizeBytes:
                    # pad it
                    self.key = self.key.ljust(self.keySizeBytes, '#')
                else:
                    # already the required length
                    pass
        else:
            raise Exception('encryption key must be provided')

        if self.iv is not None:
            iv_length = len(self.iv)
            if iv_length == 0:
                self.iv = None
            else:
                if iv_length > self.ivLength:
                    # substring (shorten) it
                    self.iv = self.iv[0:self.ivLength]
                elif iv_length < self.ivLength:
                    # pad it
                    self.iv = self.iv.ljust(self.ivLength, '@')
                else:
                    # already the required length
                    pass

    def encrypt(self, plain_text):
        # the string to encrypt must be a multiple of 16
        num_extra_chars = len(plain_text) % 16
        if num_extra_chars > 0:
            padded_text = plain_text + "".ljust(16 - num_extra_chars, ' ')
        else:
            padded_text = plain_text
        aes_cipher = AES.new(self.key, self.mode, self.iv)
        aes_cipher.key_size = self.keySizeBytes
        return aes_cipher.encrypt(padded_text)

    def decrypt(self, cipher_text):
        aes_cipher = AES.new(self.key, self.mode, self.iv)
        aes_cipher.key_size = self.keySizeBytes
        return aes_cipher.decrypt(cipher_text).rstrip()
