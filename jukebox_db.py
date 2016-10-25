import sqlite3
from song_metadata import SongMetadata
from file_metadata import FileMetadata


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
                if not open_success:
                    print('error: unable to create all tables')
            else:
                open_success = True
        return open_success

    def close(self):
        did_close = False
        if self.db_connection is not None:
            self.db_connection.close()
            self.db_connection = None
            did_close = True
        return did_close

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

    def create_table(self, sql):
        try:
            table_created = self.db_connection.execute(sql)
            if not table_created:
                print('creation of table failed')
                print('%s' % sql)
            return table_created
        except sqlite3.Error as e:
            print('error creating table: ' + e.args[0])
            return False

    def create_tables(self):
        if self.db_connection is not None:
            if self.debug_print:
                print("creating tables")

            create_genre_table = "CREATE TABLE genre (" + \
                                 "genre_uid TEXT UNIQUE NOT NULL," + \
                                 "genre_name TEXT UNIQUE NOT NULL," + \
                                 "genre_description TEXT)"

            create_artist_table = "CREATE TABLE artist (" + \
                                  "artist_uid TEXT UNIQUE NOT NULL," + \
                                  "artist_name TEXT UNIQUE NOT NULL," + \
                                  "artist_description TEXT)"

            create_album_table = "CREATE TABLE album (" + \
                                 "album_uid TEXT UNIQUE NOT NULL," + \
                                 "album_name TEXT UNIQUE NOT NULL," + \
                                 "album_description TEXT," + \
                                 "artist_uid TEXT NOT NULL REFERENCES artist(artist_uid)," + \
                                 "genre_uid TEXT REFERENCES genre(genre_uid))"

            create_song_table = "CREATE TABLE song (" + \
                                "song_uid TEXT UNIQUE NOT NULL," + \
                                "file_time TEXT," + \
                                "origin_file_size INTEGER," + \
                                "stored_file_size INTEGER," + \
                                "pad_char_count INTEGER," + \
                                "artist_name TEXT," + \
                                "artist_uid TEXT REFERENCES artist(artist_uid)," + \
                                "song_name TEXT NOT NULL," + \
                                "md5_hash TEXT NOT NULL," + \
                                "compressed INTEGER," + \
                                "encrypted INTEGER," + \
                                "container_name TEXT NOT NULL," + \
                                "object_name TEXT NOT NULL," + \
                                "album_uid TEXT REFERENCES album(album_uid))"

            create_playlist_table = "CREATE TABLE playlist (" + \
                                    "playlist_uid TEXT UNIQUE NOT NULL," + \
                                    "playlist_name TEXT UNIQUE NOT NULL," + \
                                    "playlist_description TEXT)"

            create_playlist_song_table = "CREATE TABLE playlist_song (" + \
                                         "playlist_song_uid TEXT UNIQUE NOT NULL," + \
                                         "playlist_uid TEXT NOT NULL REFERENCES playlist(playlist_uid)," + \
                                         "song_uid TEXT NOT NULL REFERENCES song(song_uid))"

            try:
                return self.create_table(create_genre_table) and \
                       self.create_table(create_artist_table) and \
                       self.create_table(create_album_table) and \
                       self.create_table(create_song_table) and \
                       self.create_table(create_playlist_table) and \
                       self.create_table(create_playlist_song_table)
            except sqlite3.Error as e:
                print('error creating table: ' + e.args[0])

        return False 

    def have_tables(self):
        have_tables_in_db = False
        if self.db_connection is not None:
            sql = "SELECT name " + \
                  "FROM sqlite_master " + \
                  "WHERE type='table' AND name='song'"
            cursor = self.db_connection.cursor()
            cursor.execute(sql)
            name = cursor.fetchone()
            if name is not None:
                have_tables_in_db = True

        return have_tables_in_db

    def id_for_artist(self, artist_name):
        pass

    def id_for_album(self, artist_name, album_name):
        pass

    def insert_artist(self, artist_name):
        pass

    def insert_album(self, album_name, artist_id):
        pass

    def albums_for_artist(self, artist_id):
        pass

    def get_artists(self):
        pass

    def songs_for_album(self, album_id):
        pass

    def songs_for_artist(self, artist_id):
        pass

    def get_playlists(self):
        pass

    def get_playlist(self, playlist_id):
        pass

    def songs_for_query(self, sql, query_args=None):
        result_songs = []
        db_cursor = self.db_connection.cursor()
        if query_args is not None:
            db_results = db_cursor.execute(sql, query_args)
        else:
            db_results = db_cursor.execute(sql)
        for row in db_results:
            song = SongMetadata()
            song.fm = FileMetadata()
            song.fm.file_uid = row[0]
            song.fm.file_time = row[1]
            song.fm.origin_file_size = row[2]
            song.fm.stored_file_size = row[3]
            song.fm.pad_char_count = row[4]
            song.artist_name = row[5]
            song.artist_uid = row[6]
            song.song_name = row[7]
            song.fm.md5_hash = row[8]
            song.fm.compressed = row[9]
            song.fm.encrypted = row[10]
            song.fm.container_name = row[11]
            song.fm.object_name = row[12]
            song.album_uid = row[13]
            result_songs.append(song)
        return result_songs
                
    def retrieve_song(self, file_name):
        if self.db_connection is not None:
            sql = """SELECT song_uid,
                  file_time,
                  origin_file_size,
                  stored_file_size,
                  pad_char_count,
                  artist_name,
                  artist_uid,
                  song_name,
                  md5_hash,
                  compressed,
                  encrypted,
                  container_name,
                  object_name,
                  album_uid
                  FROM song WHERE song_uid = ?"""
            song_results = self.songs_for_query(sql, [file_name])
            if song_results is not None and song_results:
                return song_results[0]
        return None

    def insert_song(self, song):
        insert_success = False

        if self.db_connection is not None and song is not None:
            sql = "INSERT INTO song VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
            cursor = self.db_connection.cursor()
            try:
                cursor.execute(sql,
                               [song.fm.file_uid,
                                song.fm.file_time,
                                song.fm.origin_file_size,
                                song.fm.stored_file_size,
                                song.fm.pad_char_count,
                                song.artist_name,
                                "",
                                song.song_name,
                                song.fm.md5_hash,
                                song.fm.compressed,
                                song.fm.encrypted,
                                song.fm.container_name,
                                song.fm.object_name,
                                song.album_uid])
                self.db_connection.commit()
                insert_success = True
            except sqlite3.Error as e:
                print("error inserting song: " + e.args[0])

        return insert_success

    def update_song(self, song):
        update_success = False

        if self.db_connection is not None and song is not None and song.fm.file_uid:
            sql = """UPDATE song SET file_time=?,
                  origin_file_size=?,
                  stored_file_size=?,
                  pad_char_count=?,
                  artist_name=?,
                  artist_uid=?,
                  song_name=?,
                  md5_hash=?,
                  compressed=?,
                  encrypted=?,
                  container_name=?,
                  object_name=?,
                  album_uid=? WHERE song_uid = ?"""
            cursor = self.db_connection.cursor()

            try:
                cursor.execute(sql, [song.fm.file_time,
                                     song.fm.origin_file_size,
                                     song.fm.stored_file_size,
                                     song.fm.pad_char_count,
                                     song.artist_name,
                                     "",
                                     song.song_name,
                                     song.fm.md5_hash,
                                     song.fm.compressed,
                                     song.fm.encrypted,
                                     song.fm.container_name,
                                     song.fm.object_name,
                                     song.album_uid,
                                     song.fm.file_uid])
                self.db_connection.commit()
                update_success = True
            except sqlite3.Error as e:
                print("error updating song: " + e.args[0])

        return update_success

    def store_song_metadata(self, song):
        db_song = self.retrieve_song(song.fm.file_uid)
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
                  pad_char_count,
                  artist_name,
                  artist_uid,
                  song_name,
                  md5_hash,
                  compressed,
                  encrypted,
                  container_name,
                  object_name,
                  album_uid FROM song"""
            sql += self.sql_where_clause()
            songs = self.songs_for_query(sql)
        return songs

    def songs_for_artist(self, artist_name):
        songs = []
        if self.db_connection is not None:
            sql = """SELECT song_uid,
                  file_time,
                  origin_file size,
                  stored_file size,
                  pad_char_count,
                  artist_name,
                  artist_uid,
                  song_name,
                  md5_hash,
                  compressed,
                  encrypted,
                  container_name,
                  object_name,
                  album_uid FROM song"""
            sql += self.sql_where_clause()
            sql += " AND artist = ?"
            songs = self.songs_for_query(sql, [artist_name])
        return songs

    def show_listings(self):
        if self.db_connection is not None:
            sql = "SELECT artist_name, song_name " + \
                  "FROM song " + \
                  "ORDER BY artist_name, song_name"
            cursor = self.db_connection.cursor()
            for row in cursor.execute(sql):
                artist = row[0]
                song = row[1]
                print("%s, %s" % (artist, song))

    def show_artists(self):
        if self.db_connection is not None:
            sql = "SELECT DISTINCT artist_name " + \
                  "FROM song " + \
                  "ORDER BY artist_name"
            cursor = self.db_connection.cursor()
            for row in cursor.execute(sql):
                artist = row[0]
                print("%s" % artist)

    def show_genres(self):
        if self.db_connection is not None:
            sql = "SELECT genre_name " + \
                  "FROM genre " + \
                  "ORDER BY genre_name"
            cursor = self.db_connection.cursor()
            for row in cursor.execute(sql):
                genre_name = row[0]
                print("%s" % genre_name)

    def show_artist_albums(self, artist_name):
        pass

    def show_albums(self):
        if self.db_connection is not None:
            sql = "SELECT album.album_name, artist.artist_name " + \
                  "FROM album, artist " + \
                  "WHERE album.artist_uid = artist.artist_uid " + \
                  "ORDER BY album.album_name"
            cursor = self.db_connection.cursor()
            for row in cursor.execute(sql):
                album_name = row[0]
                artist_name = row[1]
                print("%s (%s)" % (album_name, artist_name))

    def show_playlists(self):
        pass

