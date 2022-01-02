import hashlib


def md5_for_file(path_to_file: str) -> str:
    with open(path_to_file, 'rb') as f:
        d = hashlib.md5()
        for buf in f.read(4096):
            d.update(buf)
    return d.hexdigest()
