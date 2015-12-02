import unittest

import jukebox_db


class TestJukeboxDB(unittest.TestCase):

    def setUp(self):
        self.mdb_file_path = 'test_jukebox_db.sqlite3'
        self.jb_db = jukebox_db.JukeboxDB(self.mdb_file_path)
        self.jb_db.open()
        self.jb_db.create_tables()

    def tearDown(self):
        self.jb_db.close()
        # TODO: delete file

    def test_is_open(self):
        self.assertTrue(self.jb_db.is_open())
        self.jb_db.close()
        self.assertFalse(self.jb_db.is_open())

    def test_open(self):
        self.jb_db.close()
        self.assertTrue(self.jb_db.open())

    def test_close(self):
        self.assertTrue(self.jb_db.close())
        self.assertFalse(self.jb_db.close())

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
