DOUBLE_DASHES = "--"

def decode_value(encoded_value: str) -> str:
    return encoded_value.replace("-", " ")


def encode_value(value: str) -> str:
    clean_value = remove_punctuation(value)
    return clean_value.replace(" ", "-")


def encode_artist_album(artist: str, album: str) -> str:
    return encode_value(artist) + DOUBLE_DASHES + encode_value(album)


def encode_artist_album_song(artist: str, album: str, song: str) -> str:
    return encode_artist_album(artist, album) + DOUBLE_DASHES + encode_value(song)


def remove_punctuation(s: str) -> str:
    if "'" in s:
        s = s.replace("'", "")

    if "!" in s:
        s = s.replace("!", "")

    if "?" in s:
        s = s.replace("?", "")

    return s
