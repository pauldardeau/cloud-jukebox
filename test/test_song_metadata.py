import unittest

import song_metadata
import file_metadata


class TestSongMetadata(unittest.TestCase):

    def setUp(self):
        self.fm = None
        self.artist_uid = ""
        self.artist_name = ""  # keep temporarily until artist_uid is hooked up to artist table
        self.album_uid = None
        self.song_name = ""

        self.sm = song_metadata.SongMetadata()
        self.sm.fm = file_metadata.FileMetadata()
        self.sm.fm.file_uid = "some_file_uid"
        self.sm.fm.file_name = "some_file_name"
        self.sm.fm.origin_file_size = 1024
        self.sm.fm.stored_file_size = 512
        self.sm.fm.pad_char_count = 5
        self.sm.fm.file_time = "some_file_time"
        self.sm.fm.md5_hash = "asdf"
        self.sm.fm.compressed = 0
        self.sm.fm.encrypted = 1
        self.sm.fm.container_name = "some_container_name"
        self.sm.fm.object_name = "some_object_name"
        self.sm.artist_uid = "some_artist_uid"
        self.sm.artist_name = "some_artist_name"
        self.sm.album_uid = "some_album_uid"
        self.sm.song_name = "some_song_name"

    def test_eq(self):
        sm2 = song_metadata.SongMetadata()
        sm2.fm = file_metadata.FileMetadata()
        sm2.fm.file_uid = "some_file_uid"
        sm2.fm.file_name = "some_file_name"
        sm2.fm.origin_file_size = 1024
        sm2.fm.stored_file_size = 512
        sm2.fm.pad_char_count = 5
        sm2.fm.file_time = "some_file_time"
        sm2.fm.md5_hash = "asdf"
        sm2.fm.compressed = 0
        sm2.fm.encrypted = 1
        sm2.fm.container_name = "some_container_name"
        sm2.fm.object_name = "some_object_name"
        sm2.artist_uid = "some_artist_uid"
        sm2.artist_name = "some_artist_name"
        sm2.album_uid = "some_album_uid"
        sm2.song_name = "some_song_name"
        self.assertEqual(self.sm, sm2)
        sm2.album_uid = "a_new_album_uid"
        self.assertNotEqual(self.sm, sm2)
