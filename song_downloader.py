import threading


class SongDownloader(threading.Thread):
    def __init__(self, jb, list_songs):
        super(SongDownloader, self).__init__()
        self.jukebox = jb
        self.listSongs = list_songs

    def run(self):
        if self.jukebox is not None and self.listSongs is not None:
            self.jukebox.batch_download_start()
            for song_info in self.listSongs:
                self.jukebox.download_song(song_info)
            self.jukebox.batch_download_complete()
