import unittest

import jukebox_options


class TestJukeboxOptions(unittest.TestCase):

    def setUp(self):
        self.options = jukebox_options.JukeboxOptions()
        self.options.debug_mode = False
        self.options.use_encryption = False
        self.options.use_compression = False
        self.options.check_data_integrity = False
        self.options.file_cache_count = 3
        self.options.number_songs = 0
        self.options.encryption_key = ""
        self.options.encryption_key_file = ""
        self.options.encryption_iv = ""

    def test_validate_options(self):
        self.assertTrue(self.options)

    def test_negative_file_cache_count(self):
        self.options.file_cache_count = -3
        self.assertFalse(self.options.validate_options())

    def test_invalid_key_file(self):
        self.options.encryption_key_file = "aslkj43rouvnzdiufh2rkn13"
        self.assertFalse(self.options.validate_options())
