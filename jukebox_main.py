import argparse
import os
import fs_storage_system
import s3
import swift
import sys
import requests
import jukebox as jb
import jukebox_options

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
    if "swift_auth_host" in credentials:
        swift_auth_host = credentials["swift_auth_host"]
    if "swift_account" in credentials:
        swift_account = credentials["swift_account"]
    if "swift_user" in credentials:
        swift_user = credentials["swift_user"]
    if "swift_password" in credentials:
        swift_password = credentials["swift_password"]
    if "update_swift_user" in credentials and "update_swift_password" in credentials:
        update_swift_user = credentials["update_swift_user"]
        update_swift_password = credentials["update_swift_password"]

    if in_debug_mode:
        print("swift_auth_host='%s'" % swift_auth_host)
        print("swift_account='%s'" % swift_account)
        print("swift_user='%s'" % swift_user)
        print("swift_password='%s'" % swift_password)
        if len(update_swift_user) > 0 and len(update_swift_password) > 0:
            print("update_swift_user='%s'" % update_swift_user)
            print("update_swift_password='%s'" % update_swift_password)

    if len(swift_account) == 0 or len(swift_user) == 0 or len(swift_password) == 0:
        print("""error: no swift credentials given. please specify swift_account,
              swift_user, and swift_password in credentials""")
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

    if "aws_access_key" in credentials:
        aws_access_key = credentials["aws_access_key"]
    if "aws_secret_key" in credentials:
        aws_secret_key = credentials["aws_secret_key"]

    if "update_aws_access_key" in credentials and "update_aws_secret_key" in credentials:
        update_aws_access_key = credentials["update_aws_access_key"]
        update_aws_secret_key = credentials["update_aws_secret_key"]

    if in_debug_mode:
        print("aws_access_key='%s'" % aws_access_key)
        print("aws_secret_key='%s'" % aws_secret_key)
        if len(update_aws_access_key) > 0 and len(update_aws_secret_key) > 0:
            print("update_aws_access_key='%s'" % update_aws_access_key)
            print("update_aws_secret_key='%s'" % update_aws_secret_key)

    if len(aws_access_key) == 0 or len(aws_secret_key) == 0:
        print("""error: no s3 credentials given. please specify aws_access_key
              and aws_secret_key in credentials file""")
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


def connect_storage_system(system_name: str, credentials, prefix: str,
                           in_debug_mode: bool, for_update: bool):
    if system_name == SS_SWIFT:
        return connect_swift_system(credentials, prefix, in_debug_mode, for_update)
    elif system_name == SS_S3:
        return connect_s3_system(credentials, prefix, in_debug_mode, for_update)
    elif system_name == SS_FS:
        if "root_dir" in credentials:
            root_dir = credentials["root_dir"]
            if root_dir is not None and len(root_dir) > 0:
                return fs_storage_system.FSStorageSystem(root_dir, in_debug_mode)
    else:
        return None


def show_usage():
    print('Supported Commands:')
    print('\tdelete-artist      - delete specified artist')
    print('\tdelete-album       - delete specified album')
    print('\tdelete-playlist    - delete specified playlist')
    print('\tdelete-song        - delete specified song')
    print('\thelp               - show this help message')
    print('\timport-songs       - import all new songs from song-import subdirectory')
    print('\timport-playlists   - import all new playlists from playlist-import subdirectory')
    print('\timport-album-art   - import all album art from album-art-import subdirectory')
    print('\tlist-songs         - show listing of all available songs')
    print('\tlist-artists       - show listing of all available artists')
    print('\tlist-containers    - show listing of all available storage containers')
    print('\tlist-albums        - show listing of all available albums')
    print('\tlist-genres        - show listing of all available genres')
    print('\tlist-playlists     - show listing of all available playlists')
    print('\tshow-playlist      - show songs in specified playlist')
    print('\tplay               - start playing songs')
    print('\tshuffle-play       - play songs randomly')
    print('\tplay-playlist      - play specified playlist')
    print('\tplay-album         - play specified album')
    print('\tretrieve-catalog   - retrieve copy of music catalog')
    print('\tupload-metadata-db - upload SQLite metadata')
    print('\tinit-storage       - initialize storage system')
    print('\tusage              - show this help message')
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
    opt_parser.add_argument("--" + ARG_DEBUG, action="store_true", help="run in debug mode")
    opt_parser.add_argument("--" + ARG_FILE_CACHE_COUNT, type=int, help="number of songs to buffer in cache")
    opt_parser.add_argument("--" + ARG_INTEGRITY_CHECKS, action="store_true",
                            help="check file integrity after download")
    opt_parser.add_argument("--" + ARG_STORAGE, help="storage system type (%s, %s, %s)" % (SS_S3, SS_SWIFT, SS_FS))
    opt_parser.add_argument("--" + ARG_ARTIST, type=str, help="limit operations to specified artist")
    opt_parser.add_argument("--" + ARG_PLAYLIST, type=str, help="limit operations to specified playlist")
    opt_parser.add_argument("--" + ARG_SONG, type=str, help="limit operations to specified song")
    opt_parser.add_argument("--" + ARG_ALBUM, type=str, help="limit operations to specified album")
    opt_parser.add_argument("--" + ARG_FORMAT, type=str, help="restrict play to specified audio file format")
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
        valid_file_formats = ["mp3", "m4a", "flac"]
        if file_format not in valid_file_formats:
            print("error: invalid file format '%s'" % file_format)
            print("valid file formats: %s" % ",".join(valid_file_formats))
            sys.exit(1)

    if args.command:
        if debug_mode:
            print("using storage system type '%s'" % storage_type)

        container_prefix = ""
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
                        if line:
                            key, value = line.split("=")
                            creds[key.strip()] = value.strip()
            except IOError:
                if debug_mode:
                    print("error: unable to read file %s" % creds_file_path)
        else:
            print("no creds file (%s)" % creds_file_path)

        command = args.command

        help_cmds = ['help', 'usage']
        non_help_cmds = ['import-songs', 'play', 'shuffle-play', 'list-songs',
                         'list-artists', 'list-containers', 'list-genres',
                         'list-albums', 'retrieve-catalog', 'import-playlists',
                         'list-playlists', 'show-playlist', 'play-playlist',
                         'delete-song', 'delete-album', 'delete-playlist',
                         'delete-artist', 'upload-metadata-db',
                         'import-album-art', 'play-album']
        update_cmds = ['import-songs', 'import-playlists', 'delete-song',
                       'delete-album', 'delete-playlist', 'delete-artist',
                       'upload-metadata-db', 'import-album-art', 'init-storage']
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
                    if command == 'upload-metadata-db':
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
                        if command == 'init-storage':
                            if init_storage_system(storage_system):
                                sys.exit(0)
                            else:
                                sys.exit(1)
                        with jb.Jukebox(options, storage_system) as jukebox:
                            if command == 'import-songs':
                                jukebox.import_songs()
                            elif command == 'import-playlists':
                                jukebox.import_playlists()
                            elif command == 'play':
                                shuffle = False
                                jukebox.play_songs(shuffle, artist, album, file_format)
                            elif command == 'shuffle-play':
                                shuffle = True
                                jukebox.play_songs(shuffle, artist, album, file_format)
                            elif command == 'list-songs':
                                jukebox.show_listings()
                            elif command == 'list-artists':
                                jukebox.show_artists()
                            elif command == 'list-containers':
                                jukebox.show_list_containers()
                            elif command == 'list-genres':
                                jukebox.show_genres()
                            elif command == 'list-albums':
                                jukebox.show_albums()
                            elif command == 'list-playlists':
                                jukebox.show_playlists()
                            elif command == 'show-playlist':
                                if playlist is not None:
                                    jukebox.show_playlist(playlist)
                                else:
                                    print("error: playlist must be specified using --playlist option")
                                    sys.exit(1)
                            elif command == 'play-playlist':
                                if playlist is not None:
                                    jukebox.play_playlist(playlist)
                                else:
                                    print("error: playlist must be specified using --playlist option")
                                    sys.exit(1)
                            elif command == 'play-album':
                                if album is not None and artist is not None:
                                    jukebox.play_album(artist, album)
                                else:
                                    print(
                                        "error: artist and album must be specified using --artist and --album options")
                            elif command == 'retrieve-catalog':
                                pass
                            elif command == 'delete-song':
                                if song is not None:
                                    if jukebox.delete_song(song):
                                        print("song deleted")
                                    else:
                                        print("error: unable to delete song")
                                        sys.exit(1)
                                else:
                                    print("error: song must be specified using --song option")
                                    sys.exit(1)
                            elif command == 'delete-artist':
                                if artist is not None:
                                    if jukebox.delete_artist(artist):
                                        print("artist deleted")
                                    else:
                                        print("error: unable to delete artist")
                                        sys.exit(1)
                                else:
                                    print("error: artist must be specified using --artist option")
                                    sys.exit(1)
                            elif command == 'delete-album':
                                if album is not None:
                                    if jukebox.delete_album(album):
                                        print("album deleted")
                                    else:
                                        print("error: unable to delete album")
                                        sys.exit(1)
                                else:
                                    print("error: album must be specified using --album option")
                                    sys.exit(1)
                            elif command == 'delete-playlist':
                                if playlist is not None:
                                    if jukebox.delete_playlist(playlist):
                                        print("playlist deleted")
                                    else:
                                        print("error: unable to delete playlist")
                                        sys.exit(1)
                                else:
                                    print("error: playlist must be specified using --playlist option")
                                    sys.exit(1)
                            elif command == 'upload-metadata-db':
                                if jukebox.upload_metadata_db():
                                    print("metadata db uploaded")
                                else:
                                    print("error: unable to upload metadata db")
                                    sys.exit(1)
                            elif command == 'import-album-art':
                                jukebox.import_album_art()
                except requests.exceptions.ConnectionError:
                    print("Error: unable to connect to storage system server")
                    sys.exit(1)
    else:
        print("Error: no command given")
        show_usage()


if __name__ == '__main__':
    main()
