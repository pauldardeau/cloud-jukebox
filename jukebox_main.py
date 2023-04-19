import argparse
import fs_storage_system
import jukebox
import s3
import swift
import sys
import requests
import jukebox as jb
import jukebox_options
import utils


ARG_PREFIX = "--"
ARG_DEBUG = "debug"
ARG_FILE_CACHE_COUNT = "file-cache-count"
ARG_INTEGRITY_CHECKS = "integrity-checks"
ARG_STORAGE = "storage"
ARG_ARTIST = "artist"
ARG_PLAYLIST = "playlist"
ARG_SONG = "song"
ARG_ALBUM = "album"
ARG_COMMAND = "command"
ARG_FORMAT = "format"

CMD_DELETE_ALBUM = "delete-album"
CMD_DELETE_ARTIST = "delete-artist"
CMD_DELETE_PLAYLIST = "delete-playlist"
CMD_DELETE_SONG = "delete-song"
CMD_EXPORT_ALBUM = "export-album"
CMD_EXPORT_PLAYLIST = "export-playlist"
CMD_HELP = "help"
CMD_IMPORT_ALBUM = "import-album"
CMD_IMPORT_ALBUM_ART = "import-album-art"
CMD_IMPORT_PLAYLISTS = "import-playlists"
CMD_IMPORT_SONGS = "import-songs"
CMD_INIT_STORAGE = "init-storage"
CMD_LIST_ALBUMS = "list-albums"
CMD_LIST_ARTISTS = "list-artists"
CMD_LIST_CONTAINERS = "list-containers"
CMD_LIST_GENRES = "list-genres"
CMD_LIST_PLAYLISTS = "list-playlists"
CMD_LIST_SONGS = "list-songs"
CMD_PLAY = "play"
CMD_PLAY_ALBUM = "play-album"
CMD_SHOW_ALBUM = "show-album"
CMD_PLAY_PLAYLIST = "play-playlist"
CMD_RETRIEVE_CATALOG = "retrieve-catalog"
CMD_SHOW_ALBUM = "show-album"
CMD_SHOW_PLAYLIST = "show-playlist"
CMD_SHUFFLE_PLAY = "shuffle-play"
CMD_UPLOAD_METADATA_DB = "upload-metadata-db"
CMD_USAGE = "usage"

SS_FS = "fs"
SS_S3 = "s3"
SS_SWIFT = "swift"

CREDS_FILE_SUFFIX = "_creds.txt"

SWIFT_AUTH_HOST = "swift_auth_host"
SWIFT_ACCOUNT = "swift_account"
SWIFT_USER = "swift_user"
SWIFT_PASSWORD = "swift_password"
UPDATE_SWIFT_USER = "update_swift_user"
UPDATE_SWIFT_PASSWORD = "update_swift_password"

AWS_ACCESS_KEY = "aws_access_key"
AWS_SECRET_KEY = "aws_secret_key"
UPDATE_AWS_ACCESS_KEY = "update_aws_access_key"
UPDATE_AWS_SECRET_KEY = "update_aws_secret_key"

FS_ROOT_DIR = "root_dir"

AUDIO_FILE_TYPE_MP3 = "mp3"
AUDIO_FILE_TYPE_M4A = "m4a"
AUDIO_FILE_TYPE_FLAC = "flac"


def connect_swift_system(credentials, prefix: str, in_debug_mode: bool, for_update: bool):
    if not swift.is_available():
        print("error: swift is not supported on this system. please install swiftclient first.")
        sys.exit(1)

    swift_auth_host = ""
    swift_account = ""
    swift_user = ""
    swift_password = ""
    update_swift_user = ""
    update_swift_password = ""
    if SWIFT_AUTH_HOST in credentials:
        swift_auth_host = credentials[SWIFT_AUTH_HOST]
    if SWIFT_ACCOUNT in credentials:
        swift_account = credentials[SWIFT_ACCOUNT]
    if SWIFT_USER in credentials:
        swift_user = credentials[SWIFT_USER]
    if SWIFT_PASSWORD in credentials:
        swift_password = credentials[SWIFT_PASSWORD]
    if UPDATE_SWIFT_USER in credentials and UPDATE_SWIFT_PASSWORD in credentials:
        update_swift_user = credentials[UPDATE_SWIFT_USER]
        update_swift_password = credentials[UPDATE_SWIFT_PASSWORD]

    if in_debug_mode:
        print("%s='%s'" % (SWIFT_AUTH_HOST, swift_auth_host))
        print("%s='%s'" % (SWIFT_ACCOUNT, swift_account))
        print("%s='%s'" % (SWIFT_USER, swift_user))
        print("%s='%s'" % (SWIFT_PASSWORD, swift_password))
        if len(update_swift_user) > 0 and len(update_swift_password) > 0:
            print("%s='%s'" % (UPDATE_SWIFT_USER, update_swift_user))
            print("%s='%s'" % (UPDATE_SWIFT_PASSWORD, update_swift_password))

    if len(swift_account) == 0 or len(swift_user) == 0 or len(swift_password) == 0:
        print("error: no swift credentials given. please specify %s, %s, and %s in credentials" % (SWIFT_ACCOUNT, SWIFT_USER, SWIFT_PASSWORD))
        sys.exit(1)

    if for_update:
        user = update_swift_user
        password = update_swift_password
    else:
        user = swift_user
        password = swift_password

    return swift.SwiftStorageSystem(swift_auth_host,
                                    swift_account,
                                    user,
                                    password,
                                    in_debug_mode)


def connect_s3_system(credentials, prefix: str, in_debug_mode: bool, for_update: bool):
    if not s3.is_available():
        print("error: s3 is not supported on this system. please install boto3 (s3 client) first.")
        sys.exit(1)

    aws_access_key = ""
    aws_secret_key = ""
    update_aws_access_key = ""
    update_aws_secret_key = ""

    if AWS_ACCESS_KEY in credentials:
        aws_access_key = credentials[AWS_ACCESS_KEY]
    if AWS_SECRET_KEY in credentials:
        aws_secret_key = credentials[AWS_SECRET_KEY]

    if UPDATE_AWS_ACCESS_KEY in credentials and UPDATE_AWS_SECRET_KEY in credentials:
        update_aws_access_key = credentials[UPDATE_AWS_ACCESS_KEY]
        update_aws_secret_key = credentials[UPDATE_AWS_SECRET_KEY]

    if in_debug_mode:
        print("%s='%s'" % (AWS_ACCESS_KEY, aws_access_key))
        print("%s='%s'" % (AWS_SECRET_KEY, aws_secret_key))
        if len(update_aws_access_key) > 0 and len(update_aws_secret_key) > 0:
            print("%s='%s'" % (UPDATE_AWS_ACCESS_KEY, update_aws_access_key))
            print("%s='%s'" % (UPDATE_AWS_SECRET_KEY, update_aws_secret_key))

    if len(aws_access_key) == 0 or len(aws_secret_key) == 0:
        print("error: no s3 credentials given. please specify %s and %s in credentials file" % (AWS_ACCESS_KEY, AWS_SECRET_KEY))
        sys.exit(1)
    else:
        if for_update:
            access_key = update_aws_access_key
            secret_key = update_aws_secret_key
        else:
            access_key = aws_access_key
            secret_key = aws_secret_key

        return s3.S3StorageSystem(access_key,
                                  secret_key,
                                  prefix,
                                  in_debug_mode)


def connect_storage_system(system_type: str, credentials, prefix: str,
                           in_debug_mode: bool, for_update: bool):
    if system_type == SS_SWIFT:
        return connect_swift_system(credentials, prefix, in_debug_mode, for_update)
    elif system_type == SS_S3:
        return connect_s3_system(credentials, prefix, in_debug_mode, for_update)
    elif system_type == SS_FS:
        if FS_ROOT_DIR in credentials:
            root_dir = credentials[FS_ROOT_DIR]
            if root_dir is not None and len(root_dir) > 0:
                return fs_storage_system.FSStorageSystem(root_dir, in_debug_mode)
    else:
        return None


def show_usage():
    print('Supported Commands:')
    print('\t%s      - delete specified artist' % CMD_DELETE_ARTIST)
    print('\t%s       - delete specified album' % CMD_DELETE_ALBUM)
    print('\t%s    - delete specified playlist' % CMD_DELETE_PLAYLIST)
    print('\t%s        - delete specified song' % CMD_DELETE_SONG)
    print('\t%s               - show this help message' % CMD_HELP)
    print('\t%s       - import all new songs from %s subdirectory' % (CMD_IMPORT_SONGS, jukebox.SONG_IMPORT_DIR))
    print('\t%s   - import all new playlists from %s subdirectory' % (CMD_IMPORT_PLAYLISTS, jukebox.PLAYLIST_IMPORT_DIR))
    print('\t%s   - import all album art from %s subdirectory' % (CMD_IMPORT_ALBUM_ART, jukebox.ALBUM_ART_IMPORT_DIR))
    print('\t%s         - show listing of all available songs' % CMD_LIST_SONGS)
    print('\t%s       - show listing of all available artists' % CMD_LIST_ARTISTS)
    print('\t%s    - show listing of all available storage containers' % CMD_LIST_CONTAINERS)
    print('\t%s        - show listing of all available albums' % CMD_LIST_ALBUMS)
    print('\t%s        - show listing of all available genres' % CMD_LIST_GENRES)
    print('\t%s     - show listing of all available playlists' % CMD_LIST_PLAYLISTS)
    print('\t%s      - show songs in specified playlist' % CMD_SHOW_PLAYLIST)
    print('\t%s               - start playing songs' % CMD_PLAY)
    print('\t%s       - play songs randomly' % CMD_SHUFFLE_PLAY)
    print('\t%s      - play specified playlist' % CMD_PLAY_PLAYLIST)
    print('\t%s         - play specified album' % CMD_PLAY_ALBUM)
    print('\t%s         - show specified album' % CMD_SHOW_ALBUM)
    print('\t%s   - retrieve copy of music catalog' % CMD_RETRIEVE_CATALOG)
    print('\t%s - upload SQLite metadata' % CMD_UPLOAD_METADATA_DB)
    print('\t%s       - initialize storage system' % CMD_INIT_STORAGE)
    print('\t%s              - show this help message' % CMD_USAGE)
    print('')


def init_storage_system(storage_sys):
    if jb.initialize_storage_system(storage_sys):
        print("storage system successfully initialized")
        success = True
    else:
        print("error: unable to initialize storage system")
        success = False
    return success


def main():
    debug_mode = False
    storage_type = SS_SWIFT
    artist = ""
    playlist = None
    song = ""
    album = ""
    file_format = ""

    opt_parser = argparse.ArgumentParser()
    opt_parser.add_argument(ARG_PREFIX + ARG_DEBUG, action="store_true", help="run in debug mode")
    opt_parser.add_argument(ARG_PREFIX + ARG_FILE_CACHE_COUNT, type=int, help="number of songs to buffer in cache")
    opt_parser.add_argument(ARG_PREFIX + ARG_INTEGRITY_CHECKS, action="store_true",
                            help="check file integrity after download")
    opt_parser.add_argument(ARG_PREFIX + ARG_STORAGE, help="storage system type (%s, %s, %s)" % (SS_S3, SS_SWIFT, SS_FS))
    opt_parser.add_argument(ARG_PREFIX + ARG_ARTIST, type=str, help="limit operations to specified artist")
    opt_parser.add_argument(ARG_PREFIX + ARG_PLAYLIST, type=str, help="limit operations to specified playlist")
    opt_parser.add_argument(ARG_PREFIX + ARG_SONG, type=str, help="limit operations to specified song")
    opt_parser.add_argument(ARG_PREFIX + ARG_ALBUM, type=str, help="limit operations to specified album")
    opt_parser.add_argument(ARG_PREFIX + ARG_FORMAT, type=str, help="restrict play to specified audio file format")
    opt_parser.add_argument("command", help="command for jukebox")
    args = opt_parser.parse_args()
    if args is None:
        print("error: unable to obtain command-line arguments")
        sys.exit(1)
    options = jukebox_options.JukeboxOptions()

    if args.debug:
        debug_mode = True
        options.debug_mode = True

    if args.file_cache_count is not None and args.file_cache_count > 0:
        if debug_mode:
            print("setting file cache count=" + repr(args.file_cache_count))
        options.file_cache_count = args.file_cache_count

    if args.integrity_checks:
        if debug_mode:
            print("setting integrity checks on")
        options.check_data_integrity = True

    if args.storage is not None:
        supported_systems = (SS_SWIFT, SS_S3, SS_FS)
        if args.storage not in supported_systems:
            print("error: invalid storage type '%s'" % args.storage)
            print("supported systems are: %s" % str(supported_systems))
            sys.exit(1)
        else:
            if debug_mode:
                print("setting storage system to '%s'" % args.storage)
            storage_type = args.storage

    if args.artist is not None:
        artist = args.artist

    if args.playlist is not None:
        playlist = args.playlist

    if args.song is not None:
        song = args.song

    if args.album is not None:
        album = args.album

    if args.format is not None:
        file_format = args.format
        if file_format.startswith("."):
            file_format = file_format[1:]
        valid_file_formats = [AUDIO_FILE_TYPE_MP3, AUDIO_FILE_TYPE_M4A, AUDIO_FILE_TYPE_FLAC]
        if file_format not in valid_file_formats:
            print("error: invalid file format '%s'" % file_format)
            print("valid file formats: %s" % ",".join(valid_file_formats))
            sys.exit(1)

    if args.command:
        if debug_mode:
            print("using storage system type '%s'" % storage_type)

        container_prefix = ""
        creds_file = storage_type + CREDS_FILE_SUFFIX
        creds = {}
        creds_file_path = utils.path_join(utils.get_current_directory(), creds_file)

        if utils.file_exists(creds_file_path):
            if debug_mode:
                print("reading creds file '%s'" % creds_file_path)
            file_contents = utils.file_read_all_text(creds_file)
            if file_contents is not None:
                file_lines = file_contents.split("\n")
                for line in file_lines:
                    line = line.strip()
                    if len(line) > 0:
                        key, value = line.split("=")
                        creds[key.strip()] = value.strip()
            else:
                print("error: unable to read file %s" % creds_file_path)
                sys.exit(1)
        else:
            print("no creds file (%s)" % creds_file_path)
            sys.exit(1)

        command = args.command

        help_cmds = [CMD_HELP, CMD_USAGE]
        non_help_cmds = [CMD_IMPORT_SONGS, CMD_PLAY, CMD_SHUFFLE_PLAY, CMD_LIST_SONGS,
                         CMD_LIST_ARTISTS, CMD_LIST_CONTAINERS, CMD_LIST_GENRES,
                         CMD_LIST_ALBUMS, CMD_RETRIEVE_CATALOG, CMD_IMPORT_PLAYLISTS,
                         CMD_LIST_PLAYLISTS, CMD_SHOW_PLAYLIST, CMD_PLAY_PLAYLIST,
                         CMD_DELETE_SONG, CMD_DELETE_ALBUM, CMD_DELETE_PLAYLIST,
                         CMD_DELETE_ARTIST, CMD_UPLOAD_METADATA_DB,
                         CMD_IMPORT_ALBUM_ART, CMD_PLAY_ALBUM, CMD_SHOW_ALBUM]
        update_cmds = [CMD_IMPORT_SONGS, CMD_IMPORT_PLAYLISTS, CMD_DELETE_SONG,
                       CMD_DELETE_ALBUM, CMD_DELETE_PLAYLIST, CMD_DELETE_ARTIST,
                       CMD_UPLOAD_METADATA_DB, CMD_IMPORT_ALBUM_ART, CMD_INIT_STORAGE]
        all_cmds = help_cmds + non_help_cmds

        if command not in all_cmds:
            print("Unrecognized command '%s'" % command)
            print('')
            show_usage()
        else:
            if command in help_cmds:
                show_usage()
            else:
                if not options.validate_options():
                    sys.exit(1)
                try:
                    if command == CMD_UPLOAD_METADATA_DB:
                        options.suppress_metadata_download = True
                    else:
                        options.suppress_metadata_download = False

                    if command in update_cmds:
                        for_update = True
                    else:
                        for_update = False

                    with connect_storage_system(storage_type,
                                                creds,
                                                container_prefix,
                                                debug_mode,
                                                for_update) as storage_system:
                        if command == CMD_INIT_STORAGE:
                            if init_storage_system(storage_system):
                                sys.exit(0)
                            else:
                                sys.exit(1)
                        with jb.Jukebox(options, storage_system) as jukebox:
                            if command == CMD_IMPORT_SONGS:
                                jukebox.import_songs()
                            elif command == CMD_IMPORT_PLAYLISTS:
                                jukebox.import_playlists()
                            elif command == CMD_PLAY:
                                shuffle = False
                                jukebox.play_songs(shuffle, artist, album, file_format)
                            elif command == CMD_SHUFFLE_PLAY:
                                shuffle = True
                                jukebox.play_songs(shuffle, artist, album, file_format)
                            elif command == CMD_LIST_SONGS:
                                jukebox.show_listings()
                            elif command == CMD_LIST_ARTISTS:
                                jukebox.show_artists()
                            elif command == CMD_LIST_CONTAINERS:
                                jukebox.show_list_containers()
                            elif command == CMD_LIST_GENRES:
                                jukebox.show_genres()
                            elif command == CMD_LIST_ALBUMS:
                                jukebox.show_albums()
                            elif command == CMD_LIST_PLAYLISTS:
                                jukebox.show_playlists()
                            elif command == CMD_SHOW_PLAYLIST:
                                if playlist is not None:
                                    jukebox.show_playlist(playlist)
                                else:
                                    print("error: playlist must be specified using %s%s option" % (ARG_PREFIX, ARG_PLAYLIST))
                                    sys.exit(1)
                            elif command == CMD_PLAY_PLAYLIST:
                                if playlist is not None:
                                    jukebox.play_playlist(playlist)
                                else:
                                    print("error: playlist must be specified using %s%s option" % (ARG_PREFIX, ARG_PLAYLIST))
                                    sys.exit(1)
                            elif command == CMD_PLAY_ALBUM:
                                if album is not None and artist is not None:
                                    jukebox.play_album(artist, album)
                                else:
                                    print(
                                        "error: artist and album must be specified using %s%s and %s%s options" % (ARG_PREFIX, ARG_ARTIST, ARG_PREFIX, ARG_ALBUM))
                            elif command == CMD_SHOW_ALBUM:
                                if album is not None and artist is not None:
                                    jukebox.show_album(artist, album)
                                else:
                                    print(
                                        "error: artist and album must be specified using %s%s and %s%s options" % (ARG_PREFIX, ARG_ARTIST, ARG_PREFIX, ARG_ALBUM))
                            elif command == CMD_RETRIEVE_CATALOG:
                                pass
                            elif command == CMD_DELETE_SONG:
                                if song is not None:
                                    if jukebox.delete_song(song):
                                        print("song deleted")
                                    else:
                                        print("error: unable to delete song")
                                        sys.exit(1)
                                else:
                                    print("error: song must be specified using %s%s option" % (ARG_PREFIX, ARG_SONG))
                                    sys.exit(1)
                            elif command == CMD_DELETE_ARTIST:
                                if artist is not None:
                                    if jukebox.delete_artist(artist):
                                        print("artist deleted")
                                    else:
                                        print("error: unable to delete artist")
                                        sys.exit(1)
                                else:
                                    print("error: artist must be specified using %s%s option" % (ARG_PREFIX, ARG_ARTIST))
                                    sys.exit(1)
                            elif command == CMD_DELETE_ALBUM:
                                if album is not None:
                                    if jukebox.delete_album(album):
                                        print("album deleted")
                                    else:
                                        print("error: unable to delete album")
                                        sys.exit(1)
                                else:
                                    print("error: album must be specified using %s%s option" % (ARG_PREFIX, ARG_ALBUM))
                                    sys.exit(1)
                            elif command == CMD_DELETE_PLAYLIST:
                                if playlist is not None:
                                    if jukebox.delete_playlist(playlist):
                                        print("playlist deleted")
                                    else:
                                        print("error: unable to delete playlist")
                                        sys.exit(1)
                                else:
                                    print("error: playlist must be specified using %s%s option" % (ARG_PREFIX, ARG_PLAYLIST))
                                    sys.exit(1)
                            elif command == CMD_UPLOAD_METADATA_DB:
                                if jukebox.upload_metadata_db():
                                    print("metadata db uploaded")
                                else:
                                    print("error: unable to upload metadata db")
                                    sys.exit(1)
                            elif command == CMD_IMPORT_ALBUM_ART:
                                jukebox.import_album_art()
                except requests.exceptions.ConnectionError:
                    print("Error: unable to connect to storage system server")
                    sys.exit(1)
    else:
        print("Error: no command given")
        show_usage()


if __name__ == '__main__':
    main()
