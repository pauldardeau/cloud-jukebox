import unittest

import jukebox_db


class TestJukeboxDB(unittest.TestCase):

    def setUp(self):
        self.options = jukebox_db.JukeboxDB()
        self.options.debug_mode = False
        self.options.use_encryption = False
        self.options.use_compression = False
        self.options.check_data_integrity = False
        self.options.file_cache_count = 3
        self.options.number_songs = 0
        self.options.encryption_key = ""
        self.options.encryption_key_file = ""
        self.options.encryption_iv = ""

    def test_is_open(self):
        self.assertTrue(False)

    def test_open(self):
        self.assertTrue(False)

    def test_close(self):
        self.assertTrue(False)

    def test_create_table(self):
        self.assertTrue(False)

    def test_create_tables(self):
        self.assertTrue(False)

    def test_have_tables(self):
        self.assertTrue(False)

    def test_songs_for_query(self):
        self.assertTrue(False)

    def test_retrieve_song(self):
        self.assertTrue(False)

    def test_insert_song(self):
        self.assertTrue(False)

    def test_update_song(self):
        self.assertTrue(False)

    def test_store_song_metadata(self):
        self.assertTrue(False)

    def test_retrieve_songs(self):
        self.assertTrue(False)

    def test_songs_for_artist(self):
        self.assertTrue(False)

    def test_show_listings(self):
        self.assertTrue(False)

    def test_show_artists(self):
        self.assertTrue(False)

    def test_show_genres(self):
        self.assertTrue(False)

    def test_show_albums(self):
        self.assertTrue(False)