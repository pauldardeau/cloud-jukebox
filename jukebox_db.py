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
                print "have db connection"
        else:
            print "unable to connect to database"
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if self.db_connection is not None:
            self.db_connection.close()
            self.db_connection = None

    def create_tables(self):
        if self.db_connection is not None:
            if self.debug_print:
                print "creating tables"

            sql = """CREATE TABLE song (
                  uid text,
                  filetime text,
                  origin_filesize integer,
                  stored_filesize integer,
                  padchar_count integer,
                  artist text,
                  songname text,
                  md5 text,
                  compressed integer,
                  encrypted integer,
                  container text,
                  objectname text)"""
            try:
                self.db_connection.execute(sql)
                return True
            except sqlite3.Error as e:
                print 'error creating table: ' + e.args[0]

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
                  origin_filesize,
                  stored_filesize,
                  padchar_count,
                  artist,
                  songname,
                  md5,
                  compressed,
                  encrypted,
                  container,
                  objectname
                  FROM song WHERE uid = ?"""
            cursor = self.db_connection.cursor()
            cursor.execute(sql, [file_name])
            song_fields = cursor.fetchone()
            if song_fields is not None:
                song = song_file.SongFile()
                song.uid = file_name
                song.file_time = song_fields[0]
                song.origin_file_size = song_fields[1]
                song.stored_file_size = song_fields[2]
                song.pad_char_count = song_fields[3]
                song.artist_name = song_fields[4]
                song.song_name = song_fields[5]
                song.md5 = song_fields[6]
                song.compressed = song_fields[7]
                song.encrypted = song_fields[8]
                song.container = song_fields[9]
                song.object_name = song_fields[10]
                return song
        return None

    def insert_song(self, song_file):
        insert_success = False

        if (self.db_connection is not None) and (song_file is not None):
            sql = "INSERT INTO song VALUES (?,?,?,?,?,?,?,?,?,?,?,?)"
            cursor = self.db_connection.cursor()
            sf = song_file  # alias to save typing
            uid = sf.uid
            file_time = sf.file_time
            origin_file_size = sf.origin_file_size
            stored_file_size = sf.stored_file_size
            pad_char_count = sf.pad_char_count
            artist = sf.artist_name
            song = sf.song_name
            md5 = sf.md5
            compressed = sf.compressed
            encrypted = sf.encrypted
            container = sf.container
            object_name = sf.object_name

            try:
                cursor.execute(sql,
                               [uid, file_time, origin_file_size, stored_file_size, pad_char_count, artist, song, md5,
                                compressed, encrypted, container, object_name])
                self.db_connection.commit()
                insert_success = True
            except sqlite3.Error as e:
                print "error inserting song: " + e.args[0]

        return insert_success

    def update_song(self, song_file):
        update_success = False

        if (self.db_connection is not None) and (song_file is not None) and (len(song_file.uid) > 0):
            sql = """UPDATE song SET filetime=?,
                  origin_filesize=?,
                  stored_filesize=?,
                  padchar_count=?,
                  artist=?,
                  songname=?,
                  md5=?,
                  compressed=?,
                  encrypted=?,
                  container=?,
                  objectname=? WHERE uid = ?"""
            cursor = self.db_connection.cursor()
            sf = song_file  # alias to save typing
            uid = sf.uid
            file_time = sf.file_time
            origin_file_size = sf.origin_file_size
            stored_file_size = sf.stored_file_size
            pad_char_count = sf.pad_char_count
            artist = sf.artist_name
            song = sf.song_name
            md5 = sf.md5
            compressed = sf.compressed
            encrypted = sf.encrypted
            container = sf.container
            object_name = sf.object_name

            try:
                cursor.execute(sql, [file_time, origin_file_size, stored_file_size, pad_char_count, artist, song, md5,
                                     compressed, encrypted, container, object_name, uid])
                self.db_connection.commit()
                update_success = True
            except sqlite3.Error as e:
                print "error updating song: " + e.args[0]

        return update_success

    def store_song_metadata(self, fs_song):
        db_song = self.retrieve_song(fs_song.uid)
        if db_song is not None:
            if fs_song != db_song:
                return self.update_song(fs_song)
            else:
                return True  # no insert or update needed (already up-to-date)
        else:
            # song is not in the database, insert it
            return self.insert_song(fs_song)

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
            sql = """SELECT uid,
                  filetime,
                  origin_filesize,
                  stored_filesize,
                  padchar_count,
                  artist,
                  songname,
                  md5,
                  compressed,
                  encrypted,
                  container,
                  objectname FROM song"""
            sql += self.sql_where_clause()

            cursor = self.db_connection.cursor()
            for row in cursor.execute(sql):
                song = song_file.SongFile()
                song.uid = row[0]
                song.file_time = row[1]
                song.origin_file_size = row[2]
                song.stored_file_size = row[3]
                song.pad_char_count = row[4]
                song.artist_name = row[5]
                song.song_name = row[6]
                song.md5 = row[7]
                song.compressed = row[8]
                song.encrypted = row[9]
                song.container = row[10]
                song.object_name = row[11]
                songs.append(song)
        return songs

    def show_listings(self):
        if self.db_connection is not None:
            sql = "SELECT artist, songname FROM song "
            sql += self.sql_where_clause()
            sql += " ORDER BY artist, songname"
            cursor = self.db_connection.cursor()
            for row in cursor.execute(sql):
                artist = row[0]
                song = row[1]
                print "%s, %s" % (artist, song)
