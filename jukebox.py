# ******************************************************************************
# Cloud jukebox
# Copyright Paul Dardeau, SwampBits LLC, 2014
# BSD license -- see LICENSE file for details
#
# (1) create a directory for the jukebox (e.g., ~/jukebox)
#
# This cloud jukebox uses an abstract object storage system.
# (2) copy this source file to $JUKEBOX
# (3) create subdirectory for song imports (e.g., mkdir $JUKEBOX/import)
# (4) create subdirectory for playlist (e.g., mkdir $JUKEBOX/playlist)
#
# Song file naming convention:
#
# The-Artist-Name--The-Song-Name.ext
#       |         |       |       |
#       |         |       |       |----  file extension (e.g., 'mp3')
#       |         |       |
#       |         |       |---- name of the song with ' ' replaced with '-'
#       |         |
#       |         |---- double dashes to separate the artist name and song name
#       |
#       |---- artist name with ' ' replaced with '-'
#
# For example, the MP3 version of the song 'Under My Thumb' from artist 'The
# Rolling Stones' should be named:
#
#   The-Rolling-Stones--Under-My-Thumb.mp3
#
# first time use (or when new songs are added):
# (1) copy one or more song files to $JUKEBOX/import
# (2) import songs with command: 'python jukebox.py import'
#
# show song listings:
# python jukebox.py list-songs
#
# play songs:
# python jukebox.py play
#
# ******************************************************************************

import datetime
import hashlib
import optparse
import os
import os.path
import sys
import time
import zlib
from subprocess import Popen
import aes
import jukebox_options
import jukebox_db
import s3
import swift
import song_file
import song_downloader


class Jukebox:
    def __init__(self, jb_options, storage_sys, debug_print=False):

        self.jukebox_options = jb_options
        self.storage_system = storage_sys
        self.debug_print = debug_print
        self.jukebox_db = None
        self.current_dir = os.getcwd()
        self.import_dir = os.path.join(self.current_dir, 'import')
        self.playlist_dir = os.path.join(self.current_dir, 'playlist')
        self.download_extension = ".download"
        self.metadata_db_file = 'jukebox_db.sqlite3'
        self.metadata_container = 'music-metadata'
        self.song_list = []
        self.number_songs = 0
        self.song_index = -1
        self.audio_player_command_args = []
        self.song_play_length_seconds = 20
        self.cumulative_download_bytes = 0
        self.cumulative_download_time = 0

        if jb_options is not None and jb_options.debug_mode:
            self.debug_print = True

        if self.debug_print:
            print("self.current_dir = '%s'" % self.current_dir)
            print("self.import_dir = '%s'" % self.import_dir)
            print("self.playlist_dir = '%s'" % self.playlist_dir)

    def __enter__(self):
        # look for stored metadata in the storage system
        if self.storage_system is not None and self.storage_system.has_container(self.metadata_container):
            # metadata container exists, retrieve container listing
            container_contents = self.storage_system.list_container_contents(self.metadata_container)

            # does our metadata DB file exist in the metadata container?
            if container_contents is not None and self.metadata_db_file in container_contents:
                # download it
                metadata_db_file_path = self.get_metadata_db_file_path()
                download_file = metadata_db_file_path + ".download"
                if self.storage_system.retrieve_file(self.metadata_container, self.metadata_db_file, download_file) > 0:
                    # have an existing metadata DB file?
                    if os.path.exists(metadata_db_file_path):
                        if self.debug_print:
                            print("deleting existing metadata DB file")
                        os.remove(metadata_db_file_path)
                    # rename downloaded file
                    if self.debug_print:
                        print("renaming '%s' to '%s'" % (download_file, metadata_db_file_path))
                    os.rename(download_file, metadata_db_file_path)
                else:
                    if self.debug_print:
                        print("error: unable to retrieve metadata DB file")
            else:
                if self.debug_print:
                    print("no metadata DB file in metadata container")
        else:
            if self.debug_print:
                print("no metadata container in storage system")

        self.jukebox_db = jukebox_db.JukeboxDB(self.get_metadata_db_file_path())
        if not self.jukebox_db.open():
            print("unable to connect to database")
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if self.jukebox_db is not None:
            if self.jukebox_db.is_open():
                self.jukebox_db.close()
            self.jukebox_db = None

    def get_metadata_db_file_path(self):
        return os.path.join(self.current_dir, self.metadata_db_file)

    @staticmethod
    def unencode_value(encoded_value):
        return encoded_value.replace('-', ' ')

    def artist_and_song_from_file_name(self, file_name):
        pos_extension = file_name.find('.')
        if pos_extension > -1:
            base_file_name = file_name[0:pos_extension]
        else:
            base_file_name = file_name

        components = base_file_name.split('--')
        if len(components) == 2:
            encoded_artist = components[0]
            encoded_song = components[1]
            return [self.unencode_value(encoded_artist), self.unencode_value(encoded_song)]
        else:
            return None

    def artist_from_file_name(self, file_name):
        if (file_name is not None) and (len(file_name) > 0):
            components = self.artist_and_song_from_file_name(file_name)
            if components is not None and len(components) == 2:
                return components[0]
        return None

    def song_from_file_name(self, file_name):
        if (file_name is not None) and (len(file_name) > 0):
            components = self.artist_and_song_from_file_name(file_name)
            if len(components) == 2:
                return components[1]
        return None

    @staticmethod
    def md5_for_file(path_to_file):
        with open(path_to_file, mode='rb') as f:
            d = hashlib.md5()
            for buf in f.read(4096):
                d.update(buf)
        return d.hexdigest()

    def store_song_metadata(self, fs_song):
        db_song = self.jukebox_db.retrieve_song(fs_song.uid)
        if db_song is not None:
            if fs_song != db_song:
                return self.jukebox_db.update_song(fs_song)
            else:
                return True  # no insert or update needed (already up-to-date)
        else:
            # song is not in the database, insert it
            return self.jukebox_db.insert_song(fs_song)

    def get_encryptor(self):
        # key_block_size = 16  # AES-128
        # key_block_size = 24  # AES-192
        key_block_size = 32  # AES-256
        return aes.AESBlockEncryption(key_block_size, self.jukebox_options.encryption_key,
                                      self.jukebox_options.encryption_iv)

    def import_songs(self):
        if self.jukebox_db is not None and self.jukebox_db.is_open():
            dir_listing = os.listdir(self.import_dir)
            num_entries = float(len(dir_listing))
            progressbar_chars = 0.0
            progressbar_width = 40
            progresschars_per_iteration = progressbar_width / num_entries
            progressbar_char = '#'
            bar_chars = 0

            if not self.debug_print:
                # setup progressbar
                sys.stdout.write("[%s]" % (" " * progressbar_width))
                sys.stdout.flush()
                sys.stdout.write("\b" * (progressbar_width + 1))  # return to start of line, after '['

            encrypting = False
            compressing = False
            encryption = None

            if self.jukebox_options is not None:
                encrypting = self.jukebox_options.use_encryption
                compressing = self.jukebox_options.use_compression
                if encrypting:
                    encryption = self.get_encryptor()

            container_suffix = "-artist-songs"
            appended_file_ext = ""

            if encrypting and compressing:
                container_suffix += "-ez"
                appended_file_ext = ".egz"
            elif encrypting:
                container_suffix += "-e"
                appended_file_ext = ".e"
            elif compressing:
                container_suffix += "-z"
                appended_file_ext = ".gz"

            cumulative_upload_time = 0
            cumulative_upload_bytes = 0
            file_import_count = 0

            for listing_entry in dir_listing:
                full_path = os.path.join(self.import_dir, listing_entry)

                # ignore it if it's not a file
                if os.path.isfile(full_path):
                    file_name = listing_entry
                    extension = os.path.splitext(full_path)[1]
                    if len(extension) > 0:
                        file_size = os.path.getsize(full_path)
                        artist = self.artist_from_file_name(file_name)
                        if file_size > 0 and artist is not None:
                            object_name = file_name + appended_file_ext
                            fs_song = song_file.SongFile()
                            fs_song.uid = object_name
                            fs_song.origin_file_size = file_size
                            fs_song.file_time = datetime.datetime.fromtimestamp(os.path.getmtime(full_path))
                            fs_song.artist_name = artist
                            fs_song.song_name = self.song_from_file_name(file_name)
                            fs_song.md5 = self.md5_for_file(full_path)
                            fs_song.compressed = self.jukebox_options.use_compression
                            fs_song.encrypted = self.jukebox_options.use_encryption
                            fs_song.object_name = object_name
                            fs_song.pad_char_count = 0

                            # get first letter of artist name, ignoring 'A ' and 'The '
                            if artist.startswith('A '):
                                artist_letter = artist[2:3]
                            elif artist.startswith('The '):
                                artist_letter = artist[4:5]
                            else:
                                artist_letter = artist[0:1]

                            container = artist_letter.lower() + container_suffix
                            fs_song.container = container

                            # read file contents
                            file_read = False
                            file_contents = None

                            try:
                                with open(full_path, 'r') as content_file:
                                    file_contents = content_file.read()
                                file_read = True
                            except IOError:
                                print("error: unable to read file %s" % full_path)

                            if file_read and file_contents is not None:
                                if len(file_contents) > 0:
                                    # for general purposes, it might be useful or helpful to have
                                    # a minimum size for compressing
                                    if compressing:
                                        if self.debug_print:
                                            print("compressing file")

                                        compressed_contents = zlib.compress(file_contents, 9)
                                        file_contents = compressed_contents

                                    if encrypting:
                                        if self.debug_print:
                                            print("encrypting file")

                                        # the length of the data to encrypt must be a multiple of 16
                                        num_extra_chars = len(file_contents) % 16
                                        if num_extra_chars > 0:
                                            if self.debug_print:
                                                print("padding file for encryption")
                                            num_pad_chars = 16 - num_extra_chars
                                            file_contents += "".ljust(num_pad_chars, ' ')
                                            fs_song.pad_char_count = num_pad_chars

                                        cipher_text = encryption.encrypt(file_contents)
                                        file_contents = cipher_text

                                # now that we have the data that will be stored, set the file size for
                                # what's being stored
                                fs_song.stored_file_size = len(file_contents)

                                start_upload_time = time.time()

                                # store song file to storage system
                                if self.storage_system.store_song_file(fs_song, file_contents):

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
                                        self.storage_system.delete_song_file(fs_song)
                                    else:
                                        file_import_count += 1

                if not self.debug_print:
                    progressbar_chars += progresschars_per_iteration
                    if int(progressbar_chars) > bar_chars:
                        num_new_chars = int(progressbar_chars) - bar_chars

                        if num_new_chars > 0:
                            # update progress bar
                            for j in xrange(num_new_chars):
                                sys.stdout.write(progressbar_char)
                            sys.stdout.flush()
                            bar_chars += num_new_chars

            if not self.debug_print:
                # if we haven't filled up the progress bar, fill it now
                if bar_chars < progressbar_width:
                    num_new_chars = progressbar_width - bar_chars
                    for j in xrange(num_new_chars):
                        sys.stdout.write(progressbar_char)
                    sys.stdout.flush()

                sys.stdout.write("\n")

            if file_import_count > 0:
                if not self.storage_system.has_container(self.metadata_container):
                    have_metadata_container = self.storage_system.create_container(self.metadata_container)
                else:
                    have_metadata_container = True

                if have_metadata_container:
                    if self.debug_print:
                        print("uploading metadata db file to storage system")

                    self.jukebox_db.close()
                    self.jukebox_db = None

                    metadata_db_upload = self.storage_system.add_file_from_path(self.metadata_container,
                                                                                self.metadata_db_file,
                                                                                self.get_metadata_db_file_path())

                    if self.debug_print:
                        if metadata_db_upload:
                            print("metadata db file uploaded")
                        else:
                            print("unable to upload metadata db file")

            print("%s song files imported" % file_import_count)

            if cumulative_upload_time > 0:
                cumulative_upload_kb = cumulative_upload_bytes / 1000.0
                print("average upload throughput = %s KB/sec" % (int(cumulative_upload_kb / cumulative_upload_time)))

    def song_path_in_playlist(self, song):
        return os.path.join(self.playlist_dir, song.uid)

    def check_file_integrity(self, song):
        file_integrity_passed = True

        if self.jukebox_options is not None and self.jukebox_options.check_data_integrity:
            file_path = self.song_path_in_playlist(song)
            if os.path.exists(file_path):
                if self.debug_print:
                    print("checking integrity for %s" % song.uid)

                playlist_md5 = self.md5_for_file(file_path)
                if playlist_md5 == song.md5:
                    if self.debug_print:
                        print("integrity check SUCCESS")

                    file_integrity_passed = True
                else:
                    print("file integrity check failed: %s" % song.uid)
                    file_integrity_passed = False
            else:
                # file doesn't exist
                print("file doesn't exist")
                file_integrity_passed = False
        else:
            if self.debug_print:
                print("file integrity bypassed, no jukebox options or check integrity not turned on")

        return file_integrity_passed

    def batch_download_start(self):
        self.cumulative_download_bytes = 0
        self.cumulative_download_time = 0

    def batch_download_complete(self):
        if self.cumulative_download_time > 0:
            cumulative_download_kb = self.cumulative_download_bytes / 1000.0
            print("average download throughput = %s KB/sec" % (
                int(cumulative_download_kb / self.cumulative_download_time)))
        self.cumulative_download_bytes = 0
        self.cumulative_download_time = 0

    def download_song(self, song):
        if song is not None:
            file_path = self.song_path_in_playlist(song)
            download_start_time = time.time()
            song_bytes_retrieved = self.storage_system.retrieve_song_file(song, self.playlist_dir)

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
                    if self.debug_print:
                        print("verifying data integrity")

                    if song_bytes_retrieved != song.stored_file_size:
                        print("error: data integrity check failed for '%s'" % file_path)
                        return False

                # is it encrypted? if so, unencrypt it
                encrypted = song.encrypted
                compressed = song.compressed

                if encrypted or compressed:
                    try:
                        with open(file_path, 'rb') as content_file:
                            storage_file_contents = content_file.read()
                    except IOError:
                        print("error: unable to read file %s" % file_path)
                        return False

                    file_contents = storage_file_contents

                    if encrypted:
                        encryption = self.get_encryptor()
                        file_contents = encryption.decrypt(file_contents)

                    if compressed:
                        file_contents = zlib.decompress(file_contents)

                    # re-write out the uncompressed, unencrypted file contents
                    try:
                        with open(file_path, 'wb') as content_file:
                            content_file.write(file_contents)
                    except IOError:
                        print("error: unable to write unencrypted/uncompressed file '%s'" % file_path)
                        return False

                if self.check_file_integrity(song):
                    return True
                else:
                    # we retrieved the file, but it failed our integrity check
                    # if file exists, remove it
                    if os.path.exists(file_path):
                        os.remove(file_path)

        return False

    def play_song(self, song_file_path):
        if os.path.exists(song_file_path):
            print("playing %s" % song_file_path)

            if len(self.audio_player_command_args) > 0:
                cmd_args = self.audio_player_command_args[:]
                cmd_args.append(song_file_path)
                exit_code = -1
                try:
                    audio_player_proc = Popen(cmd_args)
                    if audio_player_proc is not None:
                        exit_code = audio_player_proc.wait()
                except OSError:
                    # audio player not available
                    self.audio_player_command_args = []
                    exit_code = -1

                # if the audio player failed or is not present, just sleep
                # for the length of time that audio would be played
                if exit_code != 0:
                    time.sleep(self.song_play_length_seconds)
            else:
                # we don't know about an audio player, so simulate a
                # song being played by sleeping
                time.sleep(self.song_play_length_seconds)

            # delete the song file from the play list directory
            os.remove(song_file_path)
        else:
            print("song file doesn't exist: '%s'" % song_file_path)

    def download_songs(self):
        # scan the play list directory to see if we need to download more songs
        dir_listing = os.listdir(self.playlist_dir)
        song_file_count = 0
        for listing_entry in dir_listing:
            full_path = os.path.join(self.playlist_dir, listing_entry)
            if os.path.isfile(full_path):
                extension = os.path.splitext(full_path)[1]
                if len(extension) > 0 and extension != self.download_extension:
                    song_file_count += 1

        file_cache_count = self.jukebox_options.file_cache_count

        if song_file_count < file_cache_count:
            dl_songs = []
            # start looking at the next song in the list
            check_index = self.song_index + 1
            for j in xrange(self.number_songs):
                if check_index >= self.number_songs:
                    check_index = 0

                if check_index != self.song_index:
                    si = self.song_list[check_index]
                    file_path = self.song_path_in_playlist(si)
                    if not os.path.exists(file_path):
                        dl_songs.append(si)
                        if len(dl_songs) >= file_cache_count:
                            break

                check_index += 1

            if len(dl_songs) > 0:
                download_thread = song_downloader.SongDownloader(self, dl_songs)
                download_thread.start()

    def play_songs(self):
        self.song_list = self.jukebox_db.retrieve_songs()
        if self.song_list is not None:
            self.number_songs = len(self.song_list)

            if self.number_songs == 0:
                print("no songs in jukebox")
                sys.exit(0)

            # does play list directory exist?
            if not os.path.exists(self.playlist_dir):
                if self.debug_print:
                    print("playlist directory does not exist, creating it")
                os.makedirs(self.playlist_dir)
            else:
                # play list directory exists, delete any files in it
                if self.debug_print:
                    print("deleting existing files in playlist directory")

                for theFile in os.listdir(self.playlist_dir):
                    file_path = os.path.join(self.playlist_dir, theFile)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                    except OSError:
                        pass

            self.song_index = 0

            if sys.platform == "darwin":
                self.audio_player_command_args = ["afplay"]
                self.audio_player_command_args.extend(["-t", str(self.song_play_length_seconds)])
            elif os.name == "posix":
                self.audio_player_command_args = ["mplayer", "-nolirc", "-really-quiet"]
                self.audio_player_command_args.extend(["-endpos", str(self.song_play_length_seconds)])
            elif sys.platform == "win32":
                # we really need command-line support for /play and /close arguments. unfortunately,
                # this support used to be available in the built-in windows media player, but is
                # no longer present.
                #self.audio_player_command_args = ["C:\Program Files\Windows Media Player\wmplayer.exe"]
                self.audio_player_command_args = ["C:\Program Files\MPC-HC\mpc-hc64.exe", "/play", "/close"]
            else:
                self.audio_player_command_args = []

            print("downloading first song...")

            if self.download_song(self.song_list[0]):
                print("first song downloaded. starting playing now.")

                while True:
                    self.download_songs()
                    self.play_song(self.song_path_in_playlist(self.song_list[self.song_index]))

                    self.song_index += 1
                    if self.song_index >= self.number_songs:
                        self.song_index = 0

            else:
                print("error: unable to download songs")
                sys.exit(1)

    def show_list_containers(self):
        if self.storage_system is not None:
            if self.storage_system.list_containers is not None:
                for container_name in self.storage_system.list_containers:
                    print(container_name)

    def show_listings(self):
        if self.jukebox_db is not None:
            self.jukebox_db.show_listings()


def show_usage():
    print('Usage: python jukebox.py [options] <command>')
    print('')
    print('Options:')
    print('\t--debug                                - run in debug mode')
    print('\t--file-cache-count <positive integer>  - specify number of songs to buffer in cache')
    print('\t--integrity-checks                     - check file integrity after download')
    print('\t--compress                             - use gzip compression')
    print('\t--encrypt                              - encrypt file contents')
    print('\t--key <encryption_key>                 - specify encryption key')
    print('\t--keyfile <keyfile_path>               - specify path to file containing encryption key')
    print('\t--storage <storage type>               - specifies storage system type (s3 or swift)')
    print('')
    print('Commands:')
    print('\thelp            - show this help message')
    print('\timport          - import all new songs in import subdirectory')
    print('\tlist-songs      - show listing of all available songs')
    print('\tlist-containers - show listing of all available storage containers')
    print('\tplay            - start playing songs')
    print('\tusage           - show this help message')
    print('')


def connect_storage_system(system_name, credentials, prefix, in_debug_mode=False):
    if system_name == "swift":
        if not swift.is_available():
            print("error: swift is not supported on this system. please install swiftclient first.")
            sys.exit(1)

        swift_auth_host = ""
        swift_account = ""
        swift_user = ""
        swift_password = ""
        if "swift_auth_host" in credentials:
            swift_auth_host = credentials["swift_auth_host"]
        if "swift_account" in credentials:
            swift_account = credentials["swift_account"]
        if "swift_user" in credentials:
            swift_user = credentials["swift_user"]
        if "swift_password" in credentials:
            swift_password = credentials["swift_password"]

        if in_debug_mode:
            print("swift_auth_host='%s'" % swift_auth_host)
            print("swift_account='%s'" % swift_account)
            print("swift_user='%s'" % swift_user)
            print("swift_password='%s'" % swift_password)

        if len(swift_account) == 0 or len(swift_user) == 0 or len(swift_password) == 0:
            print("""error: no swift credentials given. please specify swift_account,
                  swift_user, and swift_password in """ + creds_file)
            sys.exit(1)

        return swift.SwiftStorageSystem(swift_auth_host,
                                        swift_account,
                                        swift_user,
                                        swift_password,
                                        debug_mode)
    elif system_name == "s3":
        if not s3.is_available():
            print("error: s3 is not supported on this system. please install boto (s3 client) first.")
            sys.exit(1)

        aws_access_key = ""
        aws_secret_key = ""
        if "aws_access_key" in credentials:
            aws_access_key = credentials["aws_access_key"]
        if "aws_secret_key" in credentials:
            aws_secret_key = credentials["aws_secret_key"]

        if in_debug_mode:
            print("aws_access_key='%s'" % aws_access_key)
            print("aws_secret_key='%s'" % aws_secret_key)

        if len(aws_access_key) == 0 or len(aws_secret_key) == 0:
            print("""error: no s3 credentials given. please specify aws_access_key
                  and aws_secret_key in credentials file""")
            sys.exit(1)
        else:
            return s3.S3StorageSystem(aws_access_key,
                                      aws_secret_key,
                                      prefix,
                                      debug_mode)
    else:
        return None


if __name__ == '__main__':
    debug_mode = False
    swift_system = "swift"
    s3_system = "s3"
    storage_type = swift_system

    optKeyDebug = "debug"
    optKeyFileCacheCount = "fileCacheCount"
    optKeyIntegrityChecks = "integrityChecks"
    optKeyCompression = "compression"
    optKeyEncryption = "encrypt"
    optKeyEncryptionKey = "encryption_key"
    optKeyEncryptionKeyFile = "encryptionKeyFile"
    optKeyStorageType = "storageType"

    opt_parser = optparse.OptionParser()
    opt_parser.add_option("--debug", action="store_true", dest=optKeyDebug)
    opt_parser.add_option("--file-cache-count", action="store", type="int", dest=optKeyFileCacheCount)
    opt_parser.add_option("--integrity-checks", action="store_true", dest=optKeyIntegrityChecks)
    opt_parser.add_option("--compress", action="store_true", dest=optKeyCompression)
    opt_parser.add_option("--encrypt", action="store_true", dest=optKeyEncryption)
    opt_parser.add_option("--key", action="store", type="string", dest=optKeyEncryptionKey)
    opt_parser.add_option("--keyfile", action="store", type="string", dest=optKeyEncryptionKeyFile)
    opt_parser.add_option("--storage", action="store", type="string", dest=optKeyStorageType)

    opt, args = opt_parser.parse_args()
    stem_var = "opt."
    optValDebug = eval(stem_var + optKeyDebug)
    optValFileCacheCount = eval(stem_var + optKeyFileCacheCount)
    optValIntegrityChecks = eval(stem_var + optKeyIntegrityChecks)
    optValCompression = eval(stem_var + optKeyCompression)
    optValEncryption = eval(stem_var + optKeyEncryption)
    optValEncryptionKey = eval(stem_var + optKeyEncryptionKey)
    optValEncryptionKeyFile = eval(stem_var + optKeyEncryptionKeyFile)
    optValStorageType = eval(stem_var + optKeyStorageType)

    options = jukebox_options.JukeboxOptions()

    if optValDebug is not None:
        debug_mode = True
        options.debug_mode = optValDebug

    if optValFileCacheCount is not None:
        if debug_mode:
            print("setting file cache count=" + repr(optValFileCacheCount))
        options.file_cache_count = optValFileCacheCount

    if optValIntegrityChecks is not None:
        if debug_mode:
            print("setting integrity checks on")
        options.check_data_integrity = optValIntegrityChecks

    if optValCompression is not None:
        if debug_mode:
            print("setting compression on")
        options.use_compression = optValCompression

    if optValEncryption is not None:
        if debug_mode:
            print("setting encryption on")
        options.use_encryption = optValEncryption

    if optValEncryptionKey is not None:
        if debug_mode:
            print("setting encryption key='%s'" % optValEncryptionKey)
        options.encryption_key = optValEncryptionKey

    if optValEncryptionKeyFile is not None:
        if debug_mode:
            print("reading encryption key file='%s'" % optValEncryptionKeyFile)
        encryption_key = ''

        try:
            with open(optValEncryptionKeyFile, 'rt') as key_file:
                encryption_key = key_file.read().strip()
        except IOError:
            print("error: unable to read key file '%s'" % optValEncryptionKeyFile)
            sys.exit(1)

        if encryption_key is not None and len(encryption_key) > 0:
            options.encryption_key = encryption_key
        else:
            print("error: no key found in file '%s'" % optValEncryptionKeyFile)
            sys.exit(1)

    if optValStorageType is not None:
        if optValStorageType != swift_system and optValStorageType != s3_system:
            print("error: invalid storage type '%s'" % optValStorageType)
            print("valid values are '%s' and '%s'" % (swift_system, s3_system))
            sys.exit(1)
        else:
            if debug_mode:
                print("setting storage system to '%s'" % optValStorageType)
            storage_type = optValStorageType

    if len(args) > 0:
        if debug_mode:
            print("using storage system type '%s'" % storage_type)

        container_prefix = "com.swampbits.jukebox."
        creds_file = storage_type + "_creds.txt"
        creds = {}
        creds_file_path = os.path.join(os.getcwd(), creds_file)

        if os.path.exists(creds_file_path):
            if debug_mode:
                print("reading creds file '%s'" % creds_file_path)
            try:
                with open(creds_file, 'r') as input_file:
                    for line in input_file.readlines():
                        line = line.strip()
                        if len(line) > 0:
                            key, value = line.split("=")
                            key = key.strip()
                            value = value.strip()
                            creds[key] = value
            except IOError:
                if debug_mode:
                    print("error: unable to read file %s" % creds_file_path)
        else:
            print("no creds file (%s)" % creds_file_path)

        enc_iv = "sw4mpb1ts.juk3b0x"
        options.encryption_iv = enc_iv

        command = args[0]
        if command == 'help' or command == 'usage':
            show_usage()
        elif command == 'import':
            if not options.validate_options():
                sys.exit(1)
            with connect_storage_system(storage_type,
                                        creds,
                                        container_prefix,
                                        debug_mode) as storage_system:
                with Jukebox(options, storage_system) as jukebox:
                    jukebox.import_songs()
        elif command == 'play':
            if not options.validate_options():
                sys.exit(1)
            with connect_storage_system(storage_type,
                                        creds,
                                        container_prefix,
                                        debug_mode) as storage_system:
                with Jukebox(options, storage_system) as jukebox:
                    jukebox.play_songs()
        elif command == 'list-songs':
            if not options.validate_options():
                sys.exit(1)
            with Jukebox(options, None) as jukebox:
                jukebox.show_listings()
        elif command == 'list-containers':
            if not options.validate_options():
                sys.exit(1)
            with connect_storage_system(storage_type,
                                        creds,
                                        container_prefix,
                                        debug_mode) as storage_system:
                with Jukebox(options, storage_system) as jukebox:
                    jukebox.show_list_containers()
        else:
            print("Unrecognized command '%s'" % command)
            print('')
            show_usage()
    else:
        print("Error: no command given")
        show_usage()
