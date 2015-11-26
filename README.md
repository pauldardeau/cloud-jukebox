cloud-jukebox
=============

Cloud jukebox in python

License
-------
BSD

Overview
--------
This repo is python code that implements a music player where the songs are stored
in the cloud. Currently, the songs may be stored in either **Swift** (https://wiki.openstack.org/wiki/Swift)
or in **Amazon S3**. Although the implementation is centered around audio files, most
of the code and functionality could easily be used for storing any kind of file. This
is why compression and encryption functionality is included (compression is not
needed for audio files such as MP3 files as they're already compressed, and most
people wouldn't be interested in encrypting their song files).

Dependencies/Prerequisites
--------------------------
###Storage###
The cloud jukebox must have a storage system for data storage. Either **Swift** or
**Amazon S3** can be used.

####Swift Dependencies####
* swiftclient  `pip install python-swiftclient`

####Amazon S3 Dependencies####
* boto  `pip install boto`

###Optional###
####Encryption Dependencies####
* pycrypto  `pip install pycrypto`

Configuration
-------------
You must enter your credentials for Swift or Amazon S3. If you're using Swift, update
the values in **swift_creds.txt**.  If you're using S3, update the values in **s3_creds.txt**.

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
3. Run the command `python jukeboxy.py import-songs`

###Song File Naming Convention###

    The-Artist-Name--The-Song-Name.ext
          |         |       |       |
          |         |       |       |----  file extension (e.g., 'mp3')
          |         |       |
          |         |       |---- name of the song with ' ' replaced with '-'
          |         |
          |         |---- double dashes to separate the artist name and song name
          |
          |---- artist name with ' ' replaced with '-'

For example, the MP3 version of the song 'Under My Thumb' from artist 'The Rolling Stones' should be named:

`The-Rolling-Stones--Under-My-Thumb.mp3`

Playing Songs
-------------
The cloud jukebox uses **afplay** on Mac OSX and **mplayer** on all other Unix variants (Linux, FreeBSD).
If you do not have the designated audio player on your system, you're on a different system (Windows),
or there is an error in starting the audio player, the jukebox will pause for 20 seconds to simulate
the playing of the song.

Run the command: `python jukebox.py play`

For playback, the downloaded songs will be stored locally in the **playlist** subdirectory. This
directory will be automatically created. Once playback of a song is complete, the song file is
deleted from this directory.

File Cache Count
----------------
When playback is started, the first song file is download and then playback begins.  Subsequent
song files are downloaded as a batch in the background. The number of files that are downloaded
at once is configurable. By default, 3 files are downloaded together. To change this value, use
the **--file-cache-count** command-line argument with the desired value.

Example: `python jukebox.py --file-cache-count 10 play`

Integrity Checks
----------------
Integrity checking is an option that can be enabled with the **--integrity-checks** command-line
argument. When integrity checking is enabled, an MD5 hash of the file will be captured during
import of songs and will be stored with the song's metadata. If the option is also turned on
for playing, the MD5 hash of the downloaded file will be checked against the one that was
calculated on import to verify file integrity.

Storage Type
------------
The cloud jukebox supports **Swift** and **Amazon S3** for storage of audio files.  Put your Swift
credentials in **swift_creds.txt**.  Put your S3 credentials in **s3_creds.txt**.  By default, the cloud
jukebox is set to use Swift storage.  To explicitly specify the storage type, pass the **--storage**
command-line option along with **'swift'** or **'s3'**.

Examples:

    python jukebox.py --storage s3 play
    python jukebox.py --storage swift play

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

    python jukebox.py --encrypt --key SK34slk3032u91 import-songs
    python jukebox.py --encrypt --keyfile keyfile.txt import-songs

    python jukebox.py --encrypt --key SK34slk3032u91 play
    python jukebox.py --encrypt --keyfile keyfile.txt play


Displaying Available Songs
----------------------
Run `python jukebox.py list-songs`

Displaying List of Storage Containers
-------------------------------------
Run `python jukebox.py list-containers`

Debugging
---------
Pass the **--debug** command-line argument to enable debugging mode where detailed information
will be printed.
