cloud-jukebox
=============

Cloud jukebox in python

License
-------
BSD

Disambiguation
--------------
Any mention of 'swift' in this project refers to **OpenStack Swift** and not the
programming language (nor any other kind of Swift).

Overview
--------
This repo is python code that implements a music player where the songs are stored
in the cloud (in an object storage system). Currently, the songs may be stored in
either **OpenStack Swift** (https://wiki.openstack.org/wiki/Swift) or **AWS S3**
(or an S3-compliant system). Although the implementation is centered around audio
files, most of the code and functionality could easily be used for storing any
kind of file.

Dependencies/Prerequisites
--------------------------
### Storage
The cloud jukebox must have a storage system for data storage. Either **OpenStack Swift**
or **AWS S3** (or S3-compliant) can be used. For those who might want to experiment
without having an account in a real cloud-based object storage system, there's also
a filesystem storage system ('fs').

#### Swift Dependencies
* swiftclient  `pip install python-swiftclient`

#### AWS S3 Dependencies
* boto  `pip install boto3`

Configuration
-------------
You must enter your credentials for the storage system. If you're using OpenStack Swift, update
the values in **swift_creds.txt**.  If you're using S3, update the values in **s3_creds.txt**.

OpenStack Swift Server Configuration
------------------------------------
If you are using Swift All-In-One (SAIO), be sure that 'bind_ip' (/etc/swift/proxy-server.conf)
is using public network interface instead of localhost.

Song Metadata
-------------
Song metadata is stored in **SQLite**. This SQLite metadata database is stored in cloud
storage and is created automatically when importing songs. After the import is
complete, the cloud jukebox will also store this metadata database in cloud storage.

When starting the cloud jukebox for audio playback, the song metadata database will
automatically be downloaded from cloud storage.

Initializing Storage System
---------------------------
Before you can import songs, the containers (buckets) must first be created. To do this,
run the command:

`python jukebox_main.py --storage $STORAGE_SYSTEM init-storage`

This is a one-time initialization that needs to be done with each first use of a particular
storage system.

Importing Songs
---------------
1. Create a subdirectory named **'song-import'**
2. Copy your audio files into the song-import directory
3. Run the command `python jukebox_main.py --storage $STORAGE_SYSTEM import-songs`

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

For example, the MP3 version of the song 'Under My Thumb' from artist 'The Rolling Stones'
on the album 'Aftermath' should be named:

`The-Rolling-Stones--Aftermath--Under-My-Thumb.mp3`

Playing Songs
-------------
The cloud jukebox relies on an external music player and does not provide a music player
of its own.  On Mac OSX, the built-in **afplay** is used. On other Unix variants (Linux,
FreeBSD), **mplayer** is used.  On Windows, **MPC-HC** (3rd-party) player is used because
the built-in player is not well suited for this model of usage. If you do not have the
designated audio player on your system or there is an error in starting the audio player,
the jukebox will pause for 20 seconds to simulate the playing of the song.

MPC-HC Windows player can be found here: https://mpc-hc.org

Run the command: `python jukebox_main.py [options] play`

Options:

    --artist <artist_name>
    --album <album_name>
    --debug
    --file-cache-count <number_files_to_cache_locally>
    --integrity-checks
    --playlist <playlist_name>
    --song <song_name>
    --storage [swift|s3]

For playback, the downloaded songs will be stored locally in the **song-play** subdirectory. This
directory will be automatically created. Once playback of a song is complete, the song file is
deleted from this directory.

File Cache Count
----------------
When playback is started, the first song file is download and then playback begins.  Subsequent
song files are downloaded as a batch in the background. The number of files that are downloaded
at once is configurable. By default, 3 files are downloaded together. To change this value, use
the **--file-cache-count** command-line argument with the desired value.

Example: `python jukebox_main.py --storage $STORAGE_SYSTEM --file-cache-count 10 play`

Integrity Checks
----------------
Integrity checking is an option that can be enabled with the **--integrity-checks** command-line
argument. When integrity checking is enabled, an MD5 hash of the file will be captured during
import of songs and will be stored with the song's metadata. If the option is also turned on
for playing, the MD5 hash of the downloaded file will be checked against the one that was
calculated on import to verify file integrity.

Storage Type
------------
The cloud jukebox supports **OpenStack Swift** and **AWS S3** for storage of audio files.
Swift credentials are stored in **swift_creds.txt** and S3 credentials in **s3_creds.txt**. 
By default, the cloud jukebox is set to use OpenStack Swift storage.  To explicitly specify
the storage type, pass the **--storage** command-line option along with **'swift'** or **'s3'**.

Examples:

    python jukebox_main.py --storage s3 play
    python jukebox_main.py --storage swift play

Displaying Available Songs
----------------------
Run `python jukebox_main.py --storage $STORAGE_SYSTEM list-songs`

Displaying Available Albums
----------------------
Run `python jukebox_main.py --storage $STORAGE_SYSTEM list-albums`

Displaying Available Artists
----------------------
Run `python jukebox_main.py --storage $STORAGE_SYSTEM list-artists`

Displaying Available Playlists
----------------------
Run `python jukebox_main.py --storage $STORAGE_SYSTEM list-playlists`

Displaying List of Storage Containers
-------------------------------------
Run `python jukebox_main.py --storage $STORAGE_SYSTEM list-containers`

Debugging
---------
Pass the **--debug** command-line argument to enable debugging mode where detailed information
will be printed.
