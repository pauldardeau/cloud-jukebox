import argparse
import os
import s3
import swift
import azure
import sys
import requests
from jukebox import Jukebox
import jukebox_options


def connect_swift_system(credentials, prefix, in_debug_mode=False):
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
              swift_user, and swift_password in credentials""")
        sys.exit(1)

    return swift.SwiftStorageSystem(swift_auth_host,
                                    swift_account,
                                    swift_user,
                                    swift_password,
                                    in_debug_mode)


def connect_s3_system(credentials, prefix, in_debug_mode=False):
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
                                  in_debug_mode)


def connect_azure_system(credentials, prefix, in_debug_mode=False):
    if not azure.is_available():
        print("error: azure is not supported on this system. please install azure client first.")
        sys.exit(1)

    azure_account_name = ""
    azure_account_key = ""
    if "azure_account_name" in credentials:
        azure_account_name = credentials["azure_account_name"]
    if "azure_account_key" in credentials:
        azure_account_key = credentials["azure_account_key"]

    if in_debug_mode:
        print("azure_account_name='%s'" % azure_account_name)
        print("azure_account_key='%s'" % azure_account_key)

    if len(azure_account_name) == 0 or len(azure_account_key) == 0:
        print("""error: no azure credentials given. please specify azure_account_name
              and azure_account_key in credentials file""")
        sys.exit(1)
    else:
        return azure.AzureStorageSystem(azure_account_name,
                                        azure_account_key,
                                        prefix,
                                        in_debug_mode)


def connect_storage_system(system_name, credentials, prefix, in_debug_mode=False):
    if system_name == "swift":
        return connect_swift_system(credentials, prefix, in_debug_mode)
    elif system_name == "s3":
        return connect_s3_system(credentials, prefix, in_debug_mode)
    elif system_name == "azure":
        return connect_azure_system(credentials, prefix, in_debug_mode)
    else:
        return None


def show_usage():
    print('Supported Commands:')
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
    print('\tretrieve-catalog   - retrieve copy of music catalog')
    print('\tupload-metadata-db - upload SQLite metadata')
    print('\tusage              - show this help message')
    print('')


def main():
    debug_mode = False
    storage_type = "swift"
    artist = None
    shuffle = False
    playlist = None
    song = None
    album = None

    opt_parser = argparse.ArgumentParser()
    opt_parser.add_argument("--debug", action="store_true", help="run in debug mode")
    opt_parser.add_argument("--file-cache-count", type=int, help="number of songs to buffer in cache")
    opt_parser.add_argument("--integrity-checks", action="store_true", help="check file integrity after download")
    opt_parser.add_argument("--compress", action="store_true", help="use gzip compression")
    opt_parser.add_argument("--encrypt", action="store_true", help="encrypt file contents")
    opt_parser.add_argument("--key", help="encryption key")
    opt_parser.add_argument("--keyfile", help="path to file containing encryption key")
    opt_parser.add_argument("--storage", help="storage system type (s3, swift, azure)")
    opt_parser.add_argument("--artist", type=str, help="limit operations to specified artist")
    opt_parser.add_argument("--playlist", type=str, help="limit operations to specified playlist")
    opt_parser.add_argument("--song", type=str, help="limit operations to specified song")
    opt_parser.add_argument("--album", type=str, help="limit operations to specified album")
    opt_parser.add_argument("command", help="command for jukebox")
    args = opt_parser.parse_args()
    options = jukebox_options.JukeboxOptions()

    if args.debug:
        debug_mode = True
        options.debug_mode = True

    if args.file_cache_count > 0:
        if debug_mode:
            print("setting file cache count=" + repr(args.file_cache_count))
        options.file_cache_count = args.file_cache_count

    if args.integrity_checks:
        if debug_mode:
            print("setting integrity checks on")
        options.check_data_integrity = True

    if args.compress:
        if debug_mode:
            print("setting compression on")
        options.use_compression = True

    if args.encrypt:
        if debug_mode:
            print("setting encryption on")
        options.use_encryption = True

    if args.key:
        if debug_mode:
            print("setting encryption key='%s'" % args.key)
        options.encryption_key = args.key

    if args.keyfile is not None:
        if debug_mode:
            print("reading encryption key file='%s'" % args.keyfile)

        try:
            with open(args.keyfile, 'rt') as key_file:
                options.encryption_key = key_file.read().strip()
        except IOError:
            print("error: unable to read key file '%s'" % args.keyfile)
            sys.exit(1)

        if options.encryption_key is None or len(options.encryption_key) == 0:
            print("error: no key found in file '%s'" % args.keyfile)
            sys.exit(1)

    if args.storage is not None:
        supported_systems = ("swift", "s3", "azure")
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

    if args.command:
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
                        if line:
                            key, value = line.split("=")
                            creds[key.strip()] = value.strip()
            except IOError:
                if debug_mode:
                    print("error: unable to read file %s" % creds_file_path)
        else:
            print("no creds file (%s)" % creds_file_path)

        options.encryption_iv = "sw4mpb1ts.juk3b0x"

        command = args.command

        help_cmds = ['help', 'usage']
        non_help_cmds = ['import-songs','play','shuffle-play','list-songs',\
                         'list-artists','list-containers','list-genres',\
                         'list-albums','retrieve-catalog','import-playlists',\
                         'list-playlists','show-playlist','play-playlist',\
                         'delete-song','delete-album','delete-playlist', \
                         'upload-metadata-db','import-album-art']
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

                    with connect_storage_system(storage_type,
                                                creds,
                                                container_prefix,
                                                debug_mode) as storage_system:
                        with Jukebox(options, storage_system) as jukebox:
                            if command == 'import-songs':
                                jukebox.import_songs()
                            elif command == 'import-playlists':
                                jukebox.import_playlists()
                            elif command == 'play':
                                shuffle = False
                                jukebox.play_songs(shuffle, artist)
                            elif command == 'shuffle-play':
                                shuffle = True
                                jukebox.play_songs(shuffle, artist)
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
