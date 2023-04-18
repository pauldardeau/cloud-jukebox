

class JukeboxOptions:
    def __init__(self):
        self.debug_mode = False
        self.check_data_integrity = False
        self.file_cache_count = 3
        self.number_songs = 0
        self.suppress_metadata_download = False

    def validate_options(self) -> bool:
        if self.file_cache_count < 0:
            print("error: file cache count must be non-negative integer value")
            return False

        if self.number_songs < 0:
            print("error: number songs must be non-negative integer value")
            return False

        return True
