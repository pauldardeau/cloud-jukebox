cloud-jukebox
=============

Cloud jukebox in python

License
-------
BSD

Overview
--------
This repo is python code that implements a music player where the songs are stored
in the cloud. Currently, the songs may be stored in either **Swift** (https://wiki.openstack.org/wiki/Swift),
**Amazon S3**, or in **Azure**. Although the implementation is centered around audio files, most
of the code and functionality could easily be used for storing any kind of file. This
is why compression and encryption functionality is included (compression is not
needed for audio files such as MP3 files as they're already compressed, and most
people wouldn't be interested in encrypting their song files).

Dependencies/Prerequisites
--------------------------
### Storage
The cloud jukebox must have a storage system for data storage. Either **Swift**,
**Amazon S3**, or **Azure** can be used.

#### Swift Dependencies
* swiftclient  `pip install python-swiftclient`

#### Amazon S3 Dependencies
* boto  `pip install boto3`

#### Microsoft Azure Dependencies
???

### Optional
#### Encryption Dependencies
* pycrypto  `pip install pycrypto`

Configuration
-------------
You must enter your credentials for the storage system. If you're using Swift, update
the values in **swift_creds.txt**.  If you're using S3, update the values in **s3_creds.txt**.
For Azure, update the values in **azure_creds.txt**.

Swift Server Configuration
--------------------------
If you are using Swift All-In-One (SAIO), be sure that 'bind_ip' (/etc/swift/proxy-server.conf) is using public network interface instead of localhost.

Song Metadata
-------------
Song metadata is stored in **SQLite**. This SQLite metadata database is stored in cloud
storage and is created automatically when importing songs. After the import is
complete, the cloud jukebox will also store this metadata database in cloud storage.

When starting the cloud jukebox for audio playback, the song metadata database will
automatically be downloaded from cloud storage.

Importing Songs
---------------
1. Create a subdirectory named **'song-import'**
2. Copy your MP3 files into the song-import directory
3. Run the command `python jukebox_main.py import-songs`

### Song File Naming Convention

    The-Artist-Name--The-Album-Name--The-Song-Name.ext
          |         |       |               |       |
          |         |       |               |       |----  file extension (e.g., 'mp3')
          |         |       |               |
          |         |       |               |---- name of the song (' ' replaced with '-')
          |         |       |
          |         |       |---- album name (' ' replaced with '-')
          |         |
          |         |---- double dashes to separate the artist name and album name
          |
          |---- artist name (' ' replaced with '-')

For example, the MP3 version of the song 'Under My Thumb' from artist 'The Rolling Stones' on the album 'Aftermath' should be named:

`The-Rolling-Stones--Aftermath--Under-My-Thumb.mp3`

Playing Songs
-------------
The cloud jukebox relies on an external music player and does not provide a music player
of its own.  On Mac OSX, the built-in **afplay** is used. On other Unix variants (Linux, FreeBSD), **mplayer** is used.  On Windows, **MPC-HC** (3rd-party) player is used because the built-in
player is not well suited for this model of usage. If you do not have the designated audio
player on your system or there is an error in starting the audio player, the jukebox will
pause for 20 seconds to simulate the playing of the song.

MPC-HC Windows player can be found here: https://mpc-hc.org

Run the command: `python jukebox_main.py [options] play`

Options:

    --artist <artist_name>
    --album <album_name>
    --compress
    --debug
    --encrypt
    --file-cache-count <number_files_to_cache_locally>
    --integrity-checks
    --key <encryption_key>
    --keyfile <path_to_file_containing_encryption_key>
    --playlist <playlist_name>
    --song <song_name>
    --storage [swift|s3|azure]

For playback, the downloaded songs will be stored locally in the **song-play** subdirectory. This
directory will be automatically created. Once playback of a song is complete, the song file is
deleted from this directory.

File Cache Count
----------------
When playback is started, the first song file is download and then playback begins.  Subsequent
song files are downloaded as a batch in the background. The number of files that are downloaded
at once is configurable. By default, 3 files are downloaded together. To change this value, use
the **--file-cache-count** command-line argument with the desired value.

Example: `python jukebox_main.py --file-cache-count 10 play`

Integrity Checks
----------------
Integrity checking is an option that can be enabled with the **--integrity-checks** command-line
argument. When integrity checking is enabled, an MD5 hash of the file will be captured during
import of songs and will be stored with the song's metadata. If the option is also turned on
for playing, the MD5 hash of the downloaded file will be checked against the one that was
calculated on import to verify file integrity.

Storage Type
------------
The cloud jukebox supports **Swift**, **Amazon S3**, and **Azure** for storage of audio files.
Swift credentials are stored in **swift_creds.txt**, S3 credentials in **s3_creds.txt**, and
Azure credentials in **azure_creds.txt**.  By default, the cloud jukebox is set to use Swift
storage.  To explicitly specify the storage type, pass the **--storage** command-line option
along with **'swift'**, **'s3'**, or **'azure'**.

Examples:

    python jukebox_main.py --storage s3 play
    python jukebox_main.py --storage swift play
    python jukebox_main.py --storage azure play

Compression
-----------
Compression is supported through the use of the **zlib** module. To enable it, you must specify
the **--compress** command-line argument. If you import files using compression, you must also
specify compression for playing.

Compression is not needed for audio files, as they're already compressed. This functionality
may be useful for other types of files.

Encryption
----------
**AES** encryption is supported. To enable it, you must specify the **--encrypt** command-line argument
along with either the encryption key or the name of the file that contains the encryption key.
AES-256 is used. If you import files using encryption, you must also specify encryption for
playing. To use encryption, you must have the **pycrypto** module installed.

Encryption is probably not desired for song files, but may be desired for other types of files.

Examples:

    python jukebox_main.py --encrypt --key SK34slk3032u91 import-songs
    python jukebox_main.py --encrypt --keyfile keyfile.txt import-songs

    python jukebox_main.py --encrypt --key SK34slk3032u91 play
    python jukebox_main.py --encrypt --keyfile keyfile.txt play


Displaying Available Songs
----------------------
Run `python jukebox_main.py list-songs`

Displaying Available Albums
----------------------
Run `python jukebox_main.py list-albums`

Displaying Available Artists
----------------------
Run `python jukebox_main.py list-artists`

Displaying Available Playlists
----------------------
Run `python jukebox_main.py list-playlists`

Displaying List of Storage Containers
-------------------------------------
Run `python jukebox_main.py list-containers`

Debugging
---------
Pass the **--debug** command-line argument to enable debugging mode where detailed information
will be printed.
