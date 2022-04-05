import hashlib


def md5_for_file(path_to_file: str) -> str:
    with open(path_to_file, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()
