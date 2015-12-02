import unittest

from jukebox import Jukebox
from jukebox_options import JukeboxOptions
from memory_storage_system import MemoryStorageSystem
from song_metadata import SongMetadata


class TestJukebox(unittest.TestCase):

    def setUp(self):
        self.jb_options = JukeboxOptions()
        self.ss = MemoryStorageSystem()
        self.jb = Jukebox(self.jb_options, self.ss)
        song_metadata = SongMetadata()
        self.jb.add_song(song_metadata, '')
        self.jb.add_song(song_metadata, '')
        self.jb.add_song(song_metadata, '')
        self.jb.add_song(song_metadata, '')
        self.jb.add_song(song_metadata, '')
        self.jb.add_song(song_metadata, '')

    def test_artist_and_song_from_file_name(self):
        self.assertTrue(False)

    def test_artist_from_file_name(self):
        self.assertEqual('Cream', self.jb.artist_from_file_name('Cream--Badge.mp3'))
        self.assertEqual('ZZ-Top', self.jb.artist_from_file_name('ZZ-Top--Just-Got-Paid-Today.mp3'))

    def test_song_from_file_name(self):
        self.assertEqual('Badge', self.jb.artist_from_file_name('Cream--Badge.mp3'))
        self.assertEqual('Just-Got-Paid-Today', self.jb.artist_from_file_name('ZZ-Top--Just-Got-Paid-Today.mp3'))

    def test_store_song_metadata(self):
        self.assertTrue(False)

    def test_import_songs(self):
        self.assertTrue(False)

    def test_song_path_in_playlist(self):
        self.assertTrue(False)

    def test_check_file_integrity(self):
        self.assertTrue(False)

    def test_batch_download_start(self):
        self.assertTrue(False)

    def test_batch_download_complete(self):
        self.assertTrue(False)

    def test_download_song(self):
        self.assertTrue(False)

    def test_play_song(self):
        self.assertTrue(False)

    def test_download_songs(self):
        self.assertTrue(False)

    def test_play_songs(self):
        self.assertTrue(False)

    def test_show_list_containers(self):
        self.assertTrue(False)

    def test_show_listings(self):
        self.assertTrue(False)

    def test_show_artists(self):
        self.assertTrue(False)
