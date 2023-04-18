# ******************************************************************************
# Cloud jukebox
# Copyright Paul Dardeau, SwampBits LLC, 2014
# BSD license -- see LICENSE file for details
#
# (1) create a directory for the jukebox (e.g., ~/jukebox)
#
# This cloud jukebox uses an abstract object storage system.
# (2) copy this source file to $JUKEBOX
# (3) create subdirectory for song imports (e.g., mkdir $JUKEBOX/song-import)
# (4) create subdirectory for song-play (e.g., mkdir $JUKEBOX/song-play)
#
# Song file naming convention:
#
# The-Artist-Name--Album-Name--The-Song-Name.ext
#       |         |       |           |       |
#       |         |       |           |       |----  file extension (e.g., 'mp3')
#       |         |       |           |
#       |         |       |           |---- name of the song (' ' replaced with '-')
#       |         |       |
#       |         |       |---- name of the album (' ' replaced with '-')
#       |         |
#       |         |---- double dashes to separate the artist name and song name
#       |
#       |---- artist name (' ' replaced with '-')
#
# For example, the MP3 version of the song 'Under My Thumb' from artist 'The
# Rolling Stones' from the album 'Aftermath' should be named:
#
#   The-Rolling-Stones--Aftermath--Under-My-Thumb.mp3
#
# first time use (or when new songs are added):
# (1) copy one or more song files to $JUKEBOX/song-import
# (2) import songs with command: 'python jukebox_main.py import-songs'
#
# show song listings:
# python jukebox_main.py list-songs
#
# play songs:
# python jukebox_main.py play
#
# ******************************************************************************

import datetime
import logging

from typing import List, Tuple

import sys
import time
import random
from subprocess import Popen
import jukebox_db
import file_metadata
import song_metadata
import song_downloader
import storage_system
import utils
import json
import typing

if utils.os_is_posix():
    import signal


DOWNLOAD_EXTENSION = ".download"
ALBUM_CONTAINER = "albums"
ALBUM_ART_CONTAINER = "album-art"
METADATA_CONTAINER = "music-metadata"
PLAYLIST_CONTAINER = "playlists"
SONG_CONTAINER_SUFFIX = "-artist-songs"
ALBUM_ART_IMPORT_DIR = "album-art-import"
PLAYLIST_IMPORT_DIR = "playlist-import"
SONG_IMPORT_DIR = "song-import"
SONG_PLAY_DIR = "song-play"
DEFAULT_DB_FILE_NAME = "jukebox_db.sqlite3"
JUKEBOX_PID_FILE_NAME = "jukebox.pid"

g_jukebox_instance: typing.Optional['Jukebox'] = None

def signal_handler(signum: int, frame):
    if signum == signal.SIGUSR1:
        if g_jukebox_instance is not None:
            g_jukebox_instance.toggle_pause_play()
    elif signum == signal.SIGUSR2:
        if g_jukebox_instance is not None:
            g_jukebox_instance.advance_to_next_song()


def install_signal_handlers():
    if utils.os_is_posix():
        signal.signal(signal.SIGUSR1, signal_handler)
        signal.signal(signal.SIGUSR2, signal_handler)


class Jukebox:
    def __init__(self, jb_options, storage_sys, debug_print: bool = False):
        global g_jukebox_instance
        g_jukebox_instance = self
        self.jukebox_options = jb_options
        self.storage_system = storage_sys
        self.debug_print = debug_print
        self.jukebox_db: typing.Optional[jukebox_db.JukeboxDB] = None
        self.current_dir = utils.get_current_directory()
        self.song_import_dir = utils.path_join(self.current_dir, SONG_IMPORT_DIR)
        self.playlist_import_dir = utils.path_join(self.current_dir, PLAYLIST_IMPORT_DIR)
        self.song_play_dir = utils.path_join(self.current_dir, SONG_PLAY_DIR)
        self.album_art_import_dir = utils.path_join(self.current_dir, ALBUM_ART_IMPORT_DIR)
        self.download_extension = DOWNLOAD_EXTENSION
        self.metadata_db_file = DEFAULT_DB_FILE_NAME
        self.metadata_container = METADATA_CONTAINER
        self.playlist_container = PLAYLIST_CONTAINER
        self.album_art_container = ALBUM_ART_CONTAINER
        self.song_list: List[song_metadata.SongMetadata] = []
        self.number_songs = 0
        self.song_index = -1
        self.audio_player_command_args = []
        self.audio_player_popen = None
        self.song_play_length_seconds = 20
        self.cumulative_download_bytes = 0
        self.cumulative_download_time = 0
        self.exit_requested = False
        self.is_paused = False
        self.song_start_time = 0
        self.song_seconds_offset = 0

        if jb_options is not None and jb_options.debug_mode:
            self.debug_print = True

        if self.debug_print:
            logging.debug("self.current_dir = '%s'" % self.current_dir)
            logging.debug("self.song_import_dir = '%s'" % self.song_import_dir)
            logging.debug("self.song_play_dir = '%s'" % self.song_play_dir)

    def __enter__(self):
        # look for stored metadata in the storage system
        if self.storage_system is not None and \
           self.storage_system.has_container(self.metadata_container) and \
           not self.jukebox_options.suppress_metadata_download:

            # metadata container exists, retrieve container listing
            container_contents = self.storage_system.list_container_contents(self.metadata_container)

            # does our metadata DB file exist in the metadata container?
            if container_contents is not None and self.metadata_db_file in container_contents:
                # download it
                metadata_db_file_path = self.get_metadata_db_file_path()
                download_file = metadata_db_file_path + ".download"
                if self.storage_system.get_object(self.metadata_container, self.metadata_db_file, download_file) > 0:
                    # have an existing metadata DB file?
                    if utils.file_exists(metadata_db_file_path):
                        logging.debug("deleting existing metadata DB file")
                        utils.delete_file(metadata_db_file_path)
                    # rename downloaded file
                    logging.debug("renaming '%s' to '%s'" % (download_file, metadata_db_file_path))
                    utils.rename_file(download_file, metadata_db_file_path)
                else:
                    logging.error("unable to retrieve metadata DB file")
            else:
                logging.error("no metadata DB file in metadata container")
        else:
            logging.error("no metadata container in storage system")

        self.jukebox_db = jukebox_db.JukeboxDB(self.get_metadata_db_file_path())
        if not self.jukebox_db.open():
            logging.error("unable to connect to database")
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if self.jukebox_db is not None:
            if self.jukebox_db.is_open():
                self.jukebox_db.close()
            self.jukebox_db = None

    def toggle_pause_play(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            print("paused")
            if self.audio_player_popen is not None:
                # capture current song position (seconds into song)
                self.audio_player_popen.terminate()
        else:
            print("resuming play")

    def advance_to_next_song(self):
        print("advancing to next song")
        if self.audio_player_popen is not None:
            self.audio_player_popen.terminate()

    def get_metadata_db_file_path(self) -> str:
        return utils.path_join(self.current_dir, self.metadata_db_file)

    @staticmethod
    def decode_value(encoded_value: str) -> str:
        return encoded_value.replace('-', ' ')

    @staticmethod
    def encode_value(value: str) -> str:
        return value.replace(' ', '-')

    def components_from_file_name(self, file_name: str):  # -> typing.Optional[List[str, str, str]]:
        if len(file_name) == 0:
            return None
        pos_extension = file_name.find('.')
        if pos_extension > -1:
            base_file_name = file_name[0:pos_extension]
        else:
            base_file_name = file_name
        components = base_file_name.split('--')
        if len(components) == 3:
            return [self.decode_value(components[0]),
                    self.decode_value(components[1]),
                    self.decode_value(components[2])]
        else:
            return None

    def artist_from_file_name(self, file_name: str) -> typing.Optional[str]:
        if len(file_name) > 0:
            components = self.components_from_file_name(file_name)
            if components is not None and len(components) == 3:
                return components[0]
        return None

    def album_from_file_name(self, file_name: str) -> typing.Optional[str]:
        if len(file_name) > 0:
            components = self.components_from_file_name(file_name)
            if components is not None and len(components) == 3:
                return components[1]
        return None

    def song_from_file_name(self, file_name: str) -> typing.Optional[str]:
        if len(file_name) > 0:
            components = self.components_from_file_name(file_name)
            if components is not None and len(components) == 3:
                return components[2]
        return None

    def store_song_metadata(self, fs_song: song_metadata.SongMetadata) -> bool:
        db_song = self.jukebox_db.retrieve_song(fs_song.fm.file_uid)
        if db_song is not None:
            if fs_song != db_song:
                return self.jukebox_db.update_song(fs_song)
            else:
                return True  # no insert or update needed (already up-to-date)
        else:
            # song is not in the database, insert it
            return self.jukebox_db.insert_song(fs_song)

    def store_song_playlist(self, file_name: str, file_contents: str) -> bool:
        pl = json.loads(file_contents)
        if 'name' in pl.keys():
            pl_name = pl['name']
            pl_uid = file_name
            return self.jukebox_db.insert_playlist(pl_uid, pl_name)
        else:
            return False

    def container_suffix(self) -> str:
        return ""

    def object_file_suffix(self) -> str:
        return ""

    def container_for_song(self, song_uid: str) -> typing.Optional[str]:
        if song_uid is None or len(song_uid) == 0:
            return None
        container_suffix = "-artist-songs" + self.container_suffix()

        artist = self.artist_from_file_name(song_uid)
        if artist.startswith('A '):
            artist_letter = artist[2:3]
        elif artist.startswith('The '):
            artist_letter = artist[4:5]
        else:
            artist_letter = artist[0:1]

        return artist_letter.lower() + container_suffix

    def import_songs(self):
        if self.jukebox_db is not None and self.jukebox_db.is_open():
            dir_listing = utils.list_files_in_directory(self.song_import_dir)
            num_entries = float(len(dir_listing))
            progressbar_chars = 0.0
            progressbar_width = 40
            progress_chars_per_iteration = progressbar_width / num_entries
            progressbar_char = '#'
            bar_chars = 0

            if not self.debug_print:
                # setup progressbar
                sys.stdout.write("[%s]" % (" " * progressbar_width))
                sys.stdout.flush()
                sys.stdout.write("\b" * (progressbar_width + 1))  # return to start of line, after '['

            cumulative_upload_time = 0
            cumulative_upload_bytes = 0
            file_import_count = 0

            for listing_entry in dir_listing:
                full_path = utils.path_join(self.song_import_dir, listing_entry)
                # ignore it if it's not a file
                if utils.path_is_file(full_path):
                    file_name = listing_entry
                    extension = utils.path_split_ext(full_path)[1]
                    if extension:
                        file_size = utils.get_file_size(full_path)
                        artist = self.artist_from_file_name(file_name)
                        album = self.album_from_file_name(file_name)
                        song = self.song_from_file_name(file_name)
                        if file_size > 0 and artist is not None and album is not None and song is not None:
                            object_name = file_name + self.object_file_suffix()
                            fs_song = song_metadata.SongMetadata()
                            fs_song.fm = file_metadata.FileMetadata()
                            fs_song.fm.file_uid = object_name
                            fs_song.album_uid = None
                            fs_song.fm.origin_file_size = file_size
                            fs_song.fm.file_time = datetime.datetime.fromtimestamp(utils.path_get_mtime(full_path))
                            fs_song.artist_name = artist
                            fs_song.song_name = song
                            fs_song.fm.md5_hash = utils.md5_for_file(full_path)
                            fs_song.fm.compressed = 0
                            fs_song.fm.encrypted = 0
                            fs_song.fm.object_name = object_name
                            fs_song.fm.pad_char_count = 0

                            fs_song.fm.container_name = self.container_for_song(file_name)

                            # read file contents
                            file_read = False
                            file_contents = None

                            try:
                                with open(full_path, 'rb') as content_file:
                                    file_contents = content_file.read()
                                file_read = True
                            except IOError:
                                logging.error("unable to read file %s" % full_path)

                            if file_read and file_contents is not None:
                                # now that we have the data that will be stored, set the file size for
                                # what's being stored
                                fs_song.fm.stored_file_size = len(file_contents)
                                start_upload_time = time.time()

                                # store song file to storage system
                                if self.storage_system.put_object(fs_song.fm.container_name,
                                                                  fs_song.fm.object_name,
                                                                  file_contents):
                                    end_upload_time = time.time()
                                    upload_elapsed_time = end_upload_time - start_upload_time
                                    cumulative_upload_time += upload_elapsed_time
                                    cumulative_upload_bytes += len(file_contents)

                                    # store song metadata in local database
                                    if not self.store_song_metadata(fs_song):
                                        # we stored the song to the storage system, but were unable to store
                                        # the metadata in the local database. we need to delete the song
                                        # from the storage system since we won't have any way to access it
                                        # since we can't store the song metadata locally.
                                        logging.error("unable to store metadata, deleting obj '%s'" % fs_song.fm.object_name)
                                              
                                        self.storage_system.delete_object(fs_song.fm.container_name,
                                                                          fs_song.fm.object_name)
                                    else:
                                        file_import_count += 1
                                else:
                                    logging.error("unable to upload '%s' to '%s'" % (fs_song.fm.object_name,
                                                                                    fs_song.fm.container_name))

                if not self.debug_print:
                    progressbar_chars += progress_chars_per_iteration
                    if int(progressbar_chars) > bar_chars:
                        num_new_chars = int(progressbar_chars) - bar_chars
                        if num_new_chars > 0:
                            # update progress bar
                            for j in iter(range(num_new_chars)):
                                sys.stdout.write(progressbar_char)
                            sys.stdout.flush()
                            bar_chars += num_new_chars

            if not self.debug_print:
                # if we haven't filled up the progress bar, fill it now
                if bar_chars < progressbar_width:
                    num_new_chars = progressbar_width - bar_chars
                    for j in iter(range(num_new_chars)):
                        sys.stdout.write(progressbar_char)
                    sys.stdout.flush()
                sys.stdout.write("\n")

            if file_import_count > 0:
                self.upload_metadata_db()

            print("%s song files imported" % file_import_count)

            if cumulative_upload_time > 0:
                cumulative_upload_kb = cumulative_upload_bytes / 1000.0
                print("average upload throughput = %s KB/sec" % (int(cumulative_upload_kb / cumulative_upload_time)))

    def song_path_in_playlist(self, song: song_metadata.SongMetadata) -> str:
        return utils.path_join(self.song_play_dir, song.fm.file_uid)

    def check_file_integrity(self, song: song_metadata.SongMetadata) -> bool:
        file_integrity_passed = True

        if self.jukebox_options is not None and self.jukebox_options.check_data_integrity:
            file_path = self.song_path_in_playlist(song)
            if utils.file_exists(file_path):
                logging.debug("checking integrity for %s" % song.fm.file_uid)

                if song.fm is not None:
                    playlist_md5 = utils.md5_for_file(file_path)
                    if playlist_md5 == song.fm.md5_hash:
                        logging.debug("integrity check SUCCESS")
                        file_integrity_passed = True
                    else:
                        logging.error("file integrity check failed: %s" % song.fm.file_uid)
                        file_integrity_passed = False
            else:
                # file doesn't exist
                logging.error("file doesn't exist")
                file_integrity_passed = False
        else:
            logging.debug("file integrity bypassed, no jukebox options or check integrity not turned on")

        return file_integrity_passed

    def batch_download_start(self):
        self.cumulative_download_bytes = 0
        self.cumulative_download_time = 0

    def batch_download_complete(self):
        if not self.exit_requested:
            if self.cumulative_download_time > 0:
                cumulative_download_kb = self.cumulative_download_bytes / 1000.0
                print("average download throughput = %s KB/sec" % (
                    int(cumulative_download_kb / self.cumulative_download_time)))
            self.cumulative_download_bytes = 0
            self.cumulative_download_time = 0

    def download_song(self, song: song_metadata.SongMetadata) -> bool:
        if self.exit_requested:
            return False

        if song is not None:
            file_path = self.song_path_in_playlist(song)
            download_start_time = time.time()
            song_bytes_retrieved = self.storage_system.retrieve_file(song.fm, self.song_play_dir)
            if self.exit_requested:
                return False

            if self.debug_print:
                print("bytes retrieved: %s" % song_bytes_retrieved)

            if song_bytes_retrieved > 0:
                download_end_time = time.time()
                download_elapsed_time = download_end_time - download_start_time
                self.cumulative_download_time += download_elapsed_time
                self.cumulative_download_bytes += song_bytes_retrieved

                # are we checking data integrity?
                # if so, verify that the storage system retrieved the same length that has been stored
                if self.jukebox_options is not None and self.jukebox_options.check_data_integrity:
                    logging.debug("verifying data integrity")

                    if song_bytes_retrieved != song.fm.stored_file_size:
                        logging.error("data integrity check failed for '%s'" % file_path)
                        return False

                if self.check_file_integrity(song):
                    return True
                else:
                    # we retrieved the file, but it failed our integrity check
                    # if file exists, remove it
                    if utils.file_exists(file_path):
                        utils.delete_file(file_path)

        return False

    def play_song(self, song: song_metadata.SongMetadata):
        song_file_path = self.song_path_in_playlist(song)
        if utils.file_exists(song_file_path):
            print("playing %s" % song.fm.file_uid)

            if self.audio_player_command_args:
                cmd_args = self.audio_player_command_args[:]
                cmd_args.append(song_file_path)
                exit_code = -1
                started_audio_player = False
                try:
                    audio_player_proc = Popen(cmd_args)
                    if audio_player_proc is not None:
                        started_audio_player = True
                        self.song_start_time = time.time()
                        self.audio_player_popen = audio_player_proc
                        exit_code = audio_player_proc.wait()
                        self.audio_player_popen = None
                except OSError:
                    # audio player not available
                    self.audio_player_command_args = []
                    self.audio_player_popen = None
                    exit_code = -1

                # if the audio player failed or is not present, just sleep
                # for the length of time that audio would be played
                if not started_audio_player and exit_code != 0:
                    time.sleep(self.song_play_length_seconds)
            else:
                # we don't know about an audio player, so simulate a
                # song being played by sleeping
                time.sleep(self.song_play_length_seconds)

            if not self.is_paused:
                # delete the song file from the play list directory
                utils.delete_file(song_file_path)
        else:
            logging.info("song file doesn't exist: '%s'" % song_file_path)
            with open("404.txt", "a+") as f:
                f.write("%s\n" % song_file_path)

    def download_songs(self):
        # scan the play list directory to see if we need to download more songs
        dir_listing = utils.list_files_in_directory(self.song_play_dir)
        song_file_count = 0
        for listing_entry in dir_listing:
            full_path = utils.path_join(self.song_play_dir, listing_entry)
            extension = utils.path_split_ext(full_path)[1]
            if extension and extension != self.download_extension:
                song_file_count += 1

        file_cache_count = self.jukebox_options.file_cache_count

        if song_file_count < file_cache_count:
            dl_songs = []
            # start looking at the next song in the list
            check_index = self.song_index + 1
            for j in iter(range(self.number_songs)):
                if check_index >= self.number_songs:
                    check_index = 0
                if check_index != self.song_index:
                    si = self.song_list[check_index]
                    file_path = self.song_path_in_playlist(si)
                    if not utils.file_exists(file_path):
                        dl_songs.append(si)
                        if len(dl_songs) >= file_cache_count:
                            break
                check_index += 1

            if dl_songs:
                download_thread = song_downloader.SongDownloader(self, dl_songs)
                download_thread.start()

    def play_songs(self, shuffle: bool = False, artist: str = "", album: str = "", file_format: str = ""):
        song_list = self.jukebox_db.retrieve_songs(artist, album, file_format)
        self.play_song_list(song_list, shuffle)

    def play_song_list(self, song_list, shuffle):
        self.song_list = song_list
        if self.song_list is not None:
            self.number_songs = len(self.song_list)

            if self.number_songs == 0:
                print("no songs in jukebox")
                sys.exit(0)

            # does play list directory exist?
            if not utils.directory_exists(self.song_play_dir):
                logging.debug("song-play directory does not exist, creating it")
                utils.create_directory(self.song_play_dir)
            else:
                # play list directory exists, delete any files in it
                logging.debug("deleting existing files in song-play directory")
                utils.delete_files_in_directory(self.song_play_dir)

            self.song_index = 0
            install_signal_handlers()

            if sys.platform == "darwin":
                self.audio_player_command_args = ["afplay"]
                # self.audio_player_command_args.extend(["-t", str(self.song_play_length_seconds)])
            elif utils.os_is_posix():
                self.audio_player_command_args = ["mplayer", "-novideo", "-nolirc", "-really-quiet"]
                # self.audio_player_command_args.extend(["-endpos", str(self.song_play_length_seconds)])
            elif sys.platform == "win32":
                # we really need command-line support for /play and /close arguments. unfortunately,
                # this support used to be available in the built-in Windows Media Player, but is
                # no longer present.
                # self.audio_player_command_args = ["C:\Program Files\Windows Media Player\wmplayer.exe"]
                self.audio_player_command_args = ["C:\\Program Files\\MPC-HC\\mpc-hc64.exe",
                                                  "/play", "/close", "/minimized"]
            else:
                self.audio_player_command_args = []

            print("downloading first song...")

            if shuffle:
                self.song_list = random.sample(self.song_list, len(self.song_list))

            try:
                if self.download_song(self.song_list[0]):
                    print("first song downloaded. starting playing now.")
                    with open("jukebox.pid", "w") as f:
                        f.write('%d\n' % utils.get_process_id())
                    while True:
                        if not self.exit_requested:
                            if not self.is_paused:
                                self.download_songs()
                                self.play_song(self.song_list[self.song_index])
                            if not self.is_paused:
                                self.song_index += 1
                                if self.song_index >= self.number_songs:
                                    self.song_index = 0
                            else:
                                time.sleep(1)
                        else:
                            break
                    utils.delete_file("jukebox.pid")
                else:
                    print("error: unable to download songs")
                    sys.exit(1)
            except KeyboardInterrupt:
                print("\nexiting jukebox")
                utils.delete_file("jukebox.pid")
                self.exit_requested = True

    def show_list_containers(self):
        if self.storage_system is not None:
            if self.storage_system.list_containers is not None:
                for container_name in self.storage_system.list_containers:
                    print(container_name)

    def show_listings(self):
        if self.jukebox_db is not None:
            self.jukebox_db.show_listings()

    def show_artists(self):
        if self.jukebox_db is not None:
            self.jukebox_db.show_artists()

    def show_genres(self):
        if self.jukebox_db is not None:
            self.jukebox_db.show_genres()

    def show_albums(self):
        if self.jukebox_db is not None:
            self.jukebox_db.show_albums()

    def read_file_contents(self, file_path: str) -> Tuple[bool, str]:
        file_read = False
        file_contents = None

        try:
            with open(file_path, 'r') as content_file:
                file_contents = content_file.read()
                file_read = True
        except IOError:
            logging.error("unable to read file %s" % file_path)

        return file_read, file_contents

    def upload_metadata_db(self) -> bool:
        metadata_db_upload = False
        if not self.storage_system.has_container(self.metadata_container):
            have_metadata_container = self.storage_system.create_container(self.metadata_container)
        else:
            have_metadata_container = True

        if have_metadata_container:
            logging.debug("uploading metadata db file to storage system")

            self.jukebox_db.close()
            self.jukebox_db = None

            db_file_contents = ''
            with open(self.get_metadata_db_file_path(), 'rb') as db_file:
                db_file_contents = db_file.read()

            metadata_db_upload = self.storage_system.put_object(self.metadata_container,
                                                                self.metadata_db_file,
                                                                db_file_contents)

            if metadata_db_upload:
                logging.debug("metadata db file uploaded")
            else:
                logging.error("unable to upload metadata db file")

        return metadata_db_upload

    def import_playlists(self):
        if self.jukebox_db is not None and self.jukebox_db.is_open():
            file_import_count = 0
            dir_listing = utils.list_files_in_directory(self.playlist_import_dir)
            if len(dir_listing) == 0:
                print("no playlists found")
                return

            if not self.storage_system.has_container(self.playlist_container):
                have_container = self.storage_system.create_container(self.playlist_container)
            else:
                have_container = True

            if not have_container:
                logging.error("unable to create container for playlists. unable to import")
                return

            for listing_entry in dir_listing:
                full_path = utils.path_join(self.playlist_import_dir, listing_entry)
                object_name = listing_entry
                file_read, file_contents = self.read_file_contents(full_path)
                if file_read and file_contents is not None:
                    if self.storage_system.put_object(self.playlist_container,
                                                      object_name,
                                                      file_contents):
                        logging.debug("put of playlist succeeded")
                        if not self.store_song_playlist(object_name, file_contents):
                            logging.error("storing of playlist to db failed")
                            self.storage_system.delete_object(self.playlist_container,
                                                              object_name)
                        else:
                            logging.debug("storing of playlist succeeded")
                            file_import_count += 1

            if file_import_count > 0:
                print("%d playlists imported" % file_import_count)
                # upload metadata DB file
                self.upload_metadata_db()
            else:
                print("no files imported")

    def show_playlists(self):
        if self.jukebox_db is not None:
            self.jukebox_db.show_playlists()

    def show_playlist(self, playlist):
        bucket_name = "cj-playlists"
        object_name = "%s.json" % Jukebox.encode_value(playlist)
        download_file = object_name
        if self.storage_system.get_object(bucket_name,
                                          object_name,
                                          download_file) > 0:
            try:
                with open(download_file, 'rb') as content_file:
                    file_contents = content_file.read()
                file_read = True
            except IOError:
                logging.error("unable to read file %s" % download_file)
                file_read = False
            if file_read:
                pl = json.loads(file_contents)
                if pl is not None:
                    if "songs" in pl:
                        list_song_dicts = pl["songs"]
                        for song_dict in list_song_dicts:
                            artist_name = song_dict["artist"]
                            if "'" in artist_name:
                                artist_name = artist_name.replace("'", "")
                            artist = Jukebox.encode_value(artist_name)
                            album_name = song_dict["album"]
                            if "'" in album_name:
                                album_name = album_name.replace("'", "")
                            album = Jukebox.encode_value(album_name)
                            song_name = song_dict["song"]
                            if "'" in song_name:
                                song_name = song_name.replace("'", "")
                            song = Jukebox.encode_value(song_name)
                            base_object_name = "%s--%s--%s" % (artist, album, song)
                            print(base_object_name)
        else:
            logging.error("unable to retrieve %s" % object_name)

    def play_playlist(self, playlist):
        bucket_name = "cj-playlists"
        object_name = "%s.json" % Jukebox.encode_value(playlist)
        download_file = object_name
        if self.storage_system.get_object(bucket_name,
                                          object_name,
                                          download_file) > 0:
            try:
                with open(download_file, 'rb') as content_file:
                    file_contents = content_file.read()
                file_read = True
            except IOError:
                logging.error("unable to read file %s" % download_file)
                file_read = False
            if file_read:
                pl = json.loads(file_contents)
                if pl is not None:
                    if "songs" in pl:
                        song_list = []
                        list_song_dicts = pl["songs"]
                        for song_dict in list_song_dicts:
                            artist_name = song_dict["artist"]
                            if "'" in artist_name:
                                artist_name = artist_name.replace("'", "")
                            artist = Jukebox.encode_value(artist_name)
                            album_name = song_dict["album"]
                            if "'" in album_name:
                                album_name = album_name.replace("'", "")
                            album = Jukebox.encode_value(album_name)
                            song_name = song_dict["song"]
                            if "'" in song_name:
                                song_name = song_name.replace("'", "")
                            song = Jukebox.encode_value(song_name)
                            base_object_name = "%s--%s--%s" % (artist, album, song)
                            ext_list = [".flac", ".m4a", ".mp3"]
                            for ext in ext_list:
                                object_name = base_object_name + ext
                                db_song = self.jukebox_db.retrieve_song(object_name)
                                if db_song is not None:
                                    song_list.append(db_song)
                                    break
                            else:
                                logging.error("No song file for %s" % base_object_name)
                        self.play_song_list(song_list, False)
        else:
            logging.error("unable to retrieve %s" % object_name)

    def play_album(self, artist, album):
        bucket_name = "cj-albums"
        object_name = "%s--%s.json" % (Jukebox.encode_value(artist), Jukebox.encode_value(album))
        download_file = object_name
        if self.storage_system.get_object(bucket_name,
                                          object_name,
                                          download_file) > 0:
            try:
                with open(download_file, 'rb') as content_file:
                    file_contents = content_file.read()
                file_read = True
            except IOError:
                logging.error("unable to read file %s" % download_file)
                file_read = False
            if file_read:
                pl = json.loads(file_contents)
                if pl is not None:
                    if "tracks" in pl:
                        song_list = []
                        list_song_dicts = pl["tracks"]
                        for song_dict in list_song_dicts:
                            if not "object" in song_dict:
                                logging.error("missing 'object' in %s" % repr(song_dict))
                                continue
                            base_object_name = song_dict["object"]
                            pos_dot = base_object_name.find(".")
                            if pos_dot > 0:
                                base_object_name = base_object_name[0:pos_dot]
                            ext_list = [".flac", ".m4a", ".mp3"]
                            for ext in ext_list:
                                object_name = base_object_name + ext
                                db_song = self.jukebox_db.retrieve_song(object_name)
                                if db_song is not None:
                                    song_list.append(db_song)
                                    break
                            else:
                                logging.error("No song file for %s" % base_object_name)
                        self.play_song_list(song_list, False)
        else:
            logging.error("unable to retrieve %s" % object_name)

    def delete_song(self, song_uid: str, upload_metadata: bool = True) -> bool:
        is_deleted = False
        if len(song_uid) > 0:
            db_deleted = self.jukebox_db.delete_song(song_uid)
            container = self.container_for_song(song_uid)
            ss_deleted = False
            if container is not None and len(container) > 0:
                ss_deleted = self.storage_system.delete_object(container, song_uid)
            if db_deleted and upload_metadata:
                self.upload_metadata_db()
            is_deleted = db_deleted or ss_deleted

        return is_deleted

    def delete_artist(self, artist: str) -> bool:
        is_deleted = False
        if len(artist) > 0:
            song_list = self.jukebox_db.retrieve_songs(artist)
            if song_list is not None:
                if len(song_list) == 0:
                    print("no songs in jukebox")
                    sys.exit(0)
                else:
                    for song in song_list:
                        if not self.delete_song(song.fm.object_name, False):
                            logging.error("deleting song '%s'" % song.fm.object_name)
                            sys.exit(1)
                    self.upload_metadata_db()
                    is_deleted = True
            else:
                print("no songs in jukebox")
                sys.exit(0)

        return is_deleted

    def delete_album(self, album):
        pos_double_dash = album.find("--")
        if pos_double_dash > -1:
            artist = album[0:pos_double_dash]
            album_name = album[pos_double_dash+2:]
            list_album_songs = self.jukebox_db.retrieve_songs(artist, album_name)
            if list_album_songs is not None and len(list_album_songs) > 0:
                num_songs_deleted = 0
                for song in list_album_songs:
                    print("%s %s" % (song.fm.container_name, song.fm.object_name))
                    # delete each song audio file
                    if self.storage_system.delete_object(song.fm.container_name, song.fm.object_name):
                        num_songs_deleted += 1
                        # delete song metadata
                        self.jukebox_db.delete_song(song.fm.object_name)
                    else:
                        logging.error("unable to delete song %s" % song.fm.object_name)
                        #TODO: delete song metadata if we got 404
                if num_songs_deleted > 0:
                    # upload metadata db
                    self.upload_metadata_db()
                    return True
            else:
                print("no songs found for artist='%s' album name='%s'" % (artist, album_name))
        else:
            print("specify album with 'the-artist--the-song-name' format")
        return False

    def delete_playlist(self, playlist_name: str) -> bool:
        is_deleted = False
        object_name = self.jukebox_db.get_playlist(playlist_name)
        if object_name is not None and len(object_name) > 0:
            db_deleted = self.jukebox_db.delete_playlist(playlist_name)
            if db_deleted:
                print("container='%s', object='%s'" % (self.playlist_container, object_name))
                if self.storage_system.delete_object(self.playlist_container, object_name):
                    is_deleted = True
                else:
                    logging.error("object delete failed")
            else:
                logging.error("database delete failed")
            if is_deleted:
                self.upload_metadata_db()
            else:
                logging.error("delete of playlist failed")
        else:
            logging.error("invalid playlist name")

        return is_deleted

    def import_album_art(self):
        if self.jukebox_db is not None and self.jukebox_db.is_open():
            file_import_count = 0
            dir_listing = utils.list_files_in_directory(self.album_art_import_dir)
            if len(dir_listing) == 0:
                logging.info("no album art found")
                return

            if not self.storage_system.has_container(self.album_art_container):
                have_container = self.storage_system.create_container(self.album_art_container)
            else:
                have_container = True

            if not have_container:
                logging.error("unable to create container for album art. unable to import")
                return

            for listing_entry in dir_listing:
                full_path = utils.path_join(self.album_art_import_dir, listing_entry)
                object_name = listing_entry
                file_read, file_contents = self.read_file_contents(full_path)
                if file_read and file_contents is not None:
                    if self.storage_system.put_object(self.album_art_container,
                                                      object_name,
                                                      file_contents):
                        file_import_count += 1

            if file_import_count > 0:
                print("%d album art files imported" % file_import_count)
            else:
                print("no files imported")


def initialize_storage_system(storage_sys: storage_system.StorageSystem):
    # create the containers that will hold songs
    artist_song_chars = "0123456789abcdefghijklmnopqrstuvwxyz"

    for ch in artist_song_chars:
        container_name = "%c%s" % (ch, SONG_CONTAINER_SUFFIX)
        if not storage_sys.create_container(container_name):
            print("error: unable to create container '%s'" % container_name)
            return False

    # create the other (non-song) containers
    container_names = [METADATA_CONTAINER, ALBUM_ART_CONTAINER, ALBUM_CONTAINER, PLAYLIST_CONTAINER]

    for container_name in container_names:
        if not storage_sys.create_container(container_name):
            print("error: unable to create container '%s'" % container_name)
            return False

    # delete metadata DB file if present
    if utils.file_exists(DEFAULT_DB_FILE_NAME):
        utils.delete_file(DEFAULT_DB_FILE_NAME)

    return True
