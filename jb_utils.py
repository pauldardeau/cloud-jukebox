DOUBLE_DASHES = "--"

def decode_value(encoded_value: str) -> str:
    return encoded_value.replace("-", " ")


def encode_value(value: str) -> str:
    clean_value = remove_punctuation(value)
    return clean_value.replace(" ", "-")


def encode_artist_album(artist: str, album: str) -> str:
    clean_artist = remove_punctuation(artist)
    clean_album = remove_punctuation(album)
    return encode_value(clean_artist) + DOUBLE_DASHES + encode_value(clean_album)


def encode_artist_album_song(artist: str, album: str, song: str) -> str:
    clean_artist = remove_punctuation(artist)
    clean_album = remove_punctuation(album)
    clean_song = remove_punctuation(song)
    return encode_artist_album(clean_artist, clean_album) + DOUBLE_DASHES + encode_value(clean_song)


def remove_punctuation(s: str) -> str:
    if "'" in s:
        s = s.replace("'", "")

    if "!" in s:
        s = s.replace("!", "")

    if "?" in s:
        s = s.replace("?", "")

    return s
