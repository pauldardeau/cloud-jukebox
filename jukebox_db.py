import sqlite3
import song_file


class JukeboxDB:
    def __init__(self, metadata_db_file_path=None, debug_print=False):
        self.debug_print = debug_print
        self.db_connection = None
        if metadata_db_file_path is not None and len(metadata_db_file_path) > 0:
            self.metadata_db_file_path = metadata_db_file_path
        else:
            self.metadata_db_file_path = 'jukebox_db.sqlite3'

    def is_open(self):
        return self.db_connection is not None

    def open(self):
        self.close()
        open_success = False
        self.db_connection = sqlite3.connect(self.metadata_db_file_path)
        if self.db_connection is not None:
            if not self.have_tables():
                open_success = self.create_tables()
            else:
                open_success = True
        return open_success

    def close(self):
        if self.db_connection is not None:
            self.db_connection.close()
            self.db_connection = None

    def __enter__(self):
        # look for stored metadata in the storage system
        self.db_connection = sqlite3.connect(self.metadata_db_file_path)
        if self.db_connection is not None:
            if self.debug_print:
                print("have db connection")
        else:
            print("unable to connect to database")
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if self.db_connection is not None:
            self.db_connection.close()
            self.db_connection = None

    def create_tables(self):
        if self.db_connection is not None:
            if self.debug_print:
                print("creating tables")

            create_genre_table = """CREATE TABLE genre (
                                 genre_uid TEXT UNIQUE NOT NULL,
                                 genre_name TEXT UNIQUE NOT NULL,
                                 genre_description TEXT)"""

            create_artist_table = """CREATE TABLE artist (
                                  artist_uid TEXT UNIQUE NOT NULL,
                                  artist_name TEXT UNIQUE NOT NULL,
                                  artist_description TEXT)"""

            create_album_table = """CREATE TABLE album (
                                 album_uid TEXT UNIQUE NOT NULL,
                                 album_name TEXT UNIQUE NOT NULL,
                                 album_description TEXT,
                                 artist_uid TEXT NOT NULL REFERENCES artist.artist_uid,
                                 genre_uid TEXT REFERENCES genre.genre_uid)"""

            create_song_table = """CREATE TABLE song (
                                song_uid TEXT UNIQUE NOT NULL,
                                file_time TEXT,
                                origin_file_size INTEGER,
                                stored_file_size INTEGER,
                                padchar_count INTEGER,
                                artist_name TEXT,
                                artist_uid TEXT REFERENCES artist.artist_uid,
                                song_name TEXT NOT NULL,
                                md5_hash TEXT NOT NULL,
                                compressed INTEGER,
                                encrypted INTEGER,
                                container_name TEXT NOT NULL,
                                object_name TEXT NOT NULL,
                                album_uid TEXT REFERENCES album.album_uid)"""

            create_playlist_table = """CREATE TABLE playlist (
                                    playlist_uid TEXT UNIQUE NOT NULL,
                                    playlist_name TEXT UNIQUE NOT NULL,
                                    playlist_description TEXT)"""

            create_playlist_song_table = """CREATE TABLE playlist_song (
                                         playlist_song_uid TEXT UNIQUE NOT NULL,
                                         playlist_uid TEXT NOT NULL REFERENCES playlist.playlist_uid,
                                         song_uid TEXT NOT NULL REFERENCES song.song_uid)"""

            try:
                self.db_connection.execute(create_genre_table)
                self.db_connection.execute(create_artist_table)
                self.db_connection.execute(create_album_table)
                self.db_connection.execute(create_song_table)
                self.db_connection.execute(create_playlist_table)
                self.db_connection.execute(create_playlist_song_table)
                return True
            except sqlite3.Error as e:
                print('error creating table: ' + e.args[0])

        return False 

    def have_tables(self):
        have_tables_in_db = False
        if self.db_connection is not None:
            sql = "SELECT name FROM sqlite_master WHERE type='table' AND name='song'"
            cursor = self.db_connection.cursor()
            cursor.execute(sql)
            name = cursor.fetchone()
            if name is not None:
                have_tables_in_db = True

        return have_tables_in_db

    def retrieve_song(self, file_name):
        if self.db_connection is not None:
            sql = """SELECT filetime,
                  origin_file_size,
                  stored_file_size,
                  padchar_count,
                  artist_name,
                  song_name,
                  md5_hash,
                  compressed,
                  encrypted,
                  container_name,
                  object_name,
                  album_uid
                  FROM song WHERE song_uid = ?"""
            cursor = self.db_connection.cursor()
            cursor.execute(sql, [file_name])
            song_fields = cursor.fetchone()
            if song_fields is not None:
                song = song_file.SongFile()
                song.song_uid = file_name
                song.file_time = song_fields[0]
                song.origin_file_size = song_fields[1]
                song.stored_file_size = song_fields[2]
                song.padchar_count = song_fields[3]
                song.artist_name = song_fields[4]
                song.song_name = song_fields[5]
                song.md5_hash = song_fields[6]
                song.compressed = song_fields[7]
                song.encrypted = song_fields[8]
                song.container_name = song_fields[9]
                song.object_name = song_fields[10]
                song.album_uid = song_fields[11]
                return song
        return None

    def insert_song(self, song):
        insert_success = False

        if self.db_connection is not None and song is not None:
            sql = "INSERT INTO song VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)"
            cursor = self.db_connection.cursor()
            try:
                cursor.execute(sql,
                               [song.song_uid, song.file_time, song.origin_file_size, song.stored_file_size,
                                song.padchar_count, song.artist_name, song.song_name, song.md5_hash,
                                song.compressed, song.encrypted, song.container_name, song.object_name,
                                song.album_uid])
                self.db_connection.commit()
                insert_success = True
            except sqlite3.Error as e:
                print("error inserting song: " + e.args[0])

        return insert_success

    def update_song(self, song):
        update_success = False

        if self.db_connection is not None and song is not None and song.song_uid:
            sql = """UPDATE song SET file_time=?,
                  origin_file_size=?,
                  stored_file_size=?,
                  padchar_count=?,
                  artist_name=?,
                  song_name=?,
                  md5_hash=?,
                  compressed=?,
                  encrypted=?,
                  container_name=?,
                  object_name=?,
                  album_uid=? WHERE song_uid = ?"""
            cursor = self.db_connection.cursor()

            try:
                cursor.execute(sql, [song.file_time, song.origin_file_size, song.stored_file_size, song.padchar_count,
                                     song.artist, song.song_name, song.md5_hash, song.compressed, song.encrypted,
                                     song.container_name, song.object_name, song.album_uid, song.song_uid])
                self.db_connection.commit()
                update_success = True
            except sqlite3.Error as e:
                print("error updating song: " + e.args[0])

        return update_success

    def store_song_metadata(self, song):
        db_song = self.retrieve_song(song.uid)
        if db_song is not None:
            if song != db_song:
                return self.update_song(song)
            else:
                return True  # no insert or update needed (already up-to-date)
        else:
            # song is not in the database, insert it
            return self.insert_song(song)

    @staticmethod
    def sql_where_clause(using_encryption=False, using_compression=False):
        if using_encryption:
            encryption = 1
        else:
            encryption = 0
            
        if using_compression:
            compression = 1
        else:
            compression = 0

        where_clause = ""
        where_clause += " WHERE "
        where_clause += "encrypted = "
        where_clause += str(encryption)
        where_clause += " AND "
        where_clause += "compressed = "
        where_clause += str(compression)
        return where_clause

    def retrieve_songs(self):
        songs = []
        if self.db_connection is not None:
            sql = """SELECT song_uid,
                  file_time,
                  origin_file_size,
                  stored_file_size,
                  padchar_count,
                  artist_name,
                  song_name,
                  md5_hash,
                  compressed,
                  encrypted,
                  container_name,
                  object_name,
                  album_uid FROM song"""
            sql += self.sql_where_clause()

            cursor = self.db_connection.cursor()
            for row in cursor.execute(sql):
                song = song_file.SongFile()
                song.song_uid = row[0]
                song.file_time = row[1]
                song.origin_file_size = row[2]
                song.stored_file_size = row[3]
                song.padchar_count = row[4]
                song.artist_name = row[5]
                song.song_name = row[6]
                song.md5_hash = row[7]
                song.compressed = row[8]
                song.encrypted = row[9]
                song.container_name = row[10]
                song.object_name = row[11]
                song.album_uid = row[12]
                songs.append(song)
        return songs

    def show_listings(self):
        if self.db_connection is not None:
            sql = "SELECT artist_name, song_name FROM song ORDER BY artist_name, song_name"
            cursor = self.db_connection.cursor()
            for row in cursor.execute(sql):
                artist = row[0]
                song = row[1]
                print("%s, %s" % (artist, song))

    def show_artists(self):
        if self.db_connection is not None:
            sql = "SELECT DISTINCT artist_name FROM song ORDER BY artist_name"
            cursor = self.db_connection.cursor()
            for row in cursor.execute(sql):
                artist = row[0]
                print("%s" % artist)

    def show_genres(self):
        if self.db_connection is not None:
            sql = "SELECT genre_name FROM genre ORDER BY genre_name"
            cursor = self.db_connection.cursor()
            for row in cursor.execute(sql):
                genre_name = row[0]
                print("%s" % genre_name)

    def show_albums(self):
        if self.db_connection is not None:
            sql = "SELECT album.album_name, artist.artist_name " + \
                  "FROM album, artist " + \
                  "WHERE album.artist_uid = artist_artist_uid " + \
                  "ORDER BY album.album_name"
            cursor = self.db_connection.cursor()
            for row in cursor.execute(sql):
                album_name = row[0]
                artist_name = row[1]
                print("%s (%s)" % (album_name, artist_name))
