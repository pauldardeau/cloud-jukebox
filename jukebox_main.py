import argparse
import os
import s3
import swift
import sys
from jukebox import Jukebox
import jukebox_options


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
                  swift_user, and swift_password in credentials""")
            sys.exit(1)

        return swift.SwiftStorageSystem(swift_auth_host,
                                        swift_account,
                                        swift_user,
                                        swift_password,
                                        in_debug_mode)
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
                                      in_debug_mode)
    else:
        return None


def show_usage():
    print('Supported Commands:')
    print('\thelp            - show this help message')
    print('\timport-songs    - import all new songs from song-import subdirectory')
    print('\tlist-songs      - show listing of all available songs')
    print('\tlist-containers - show listing of all available storage containers')
    print('\tplay            - start playing songs')
    print('\tusage           - show this help message')
    print('')


def main():
    debug_mode = False
    swift_system = "swift"
    s3_system = "s3"
    storage_type = swift_system

    opt_parser = argparse.ArgumentParser()
    opt_parser.add_argument("--debug", action="store_true", help="run in debug mode")
    opt_parser.add_argument("--file-cache-count", type=int, help="number of songs to buffer in cache")
    opt_parser.add_argument("--integrity-checks", action="store_true", help="check file integrity after download")
    opt_parser.add_argument("--compress", action="store_true", help="use gzip compression")
    opt_parser.add_argument("--encrypt", action="store_true", help="encrypt file contents")
    opt_parser.add_argument("--key", help="encryption key")
    opt_parser.add_argument("--keyfile", help="path to file containing encryption key")
    opt_parser.add_argument("--storage", help="storage system type (s3 or swift)")
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
        if args.storage != swift_system and args.storage != s3_system:
            print("error: invalid storage type '%s'" % args.storage)
            print("valid values are '%s' and '%s'" % (swift_system, s3_system))
            sys.exit(1)
        else:
            if debug_mode:
                print("setting storage system to '%s'" % args.storage)
            storage_type = args.storage

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
        if command == 'help' or command == 'usage':
            show_usage()
        elif command == 'import-songs':
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


if __name__ == '__main__':
    main()