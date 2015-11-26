import threading


class SongDownloader(threading.Thread):
    def __init__(self, jb, list_songs):
        super(SongDownloader, self).__init__()
        self.jukebox = jb
        self.list_songs = list_songs

    def run(self):
        if self.jukebox is not None and self.list_songs is not None:
            self.jukebox.batch_download_start()
            for song in self.list_songs:
                self.jukebox.download_song(song)
            self.jukebox.batch_download_complete()
