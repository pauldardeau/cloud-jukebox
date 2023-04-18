import hashlib
import os
import os.path
import pathlib
from typing import List, Tuple

def md5_for_file(path_to_file: str) -> str:
    with open(path_to_file, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def get_file_size(path_to_file: str) -> int:
    return os.path.getsize(path_to_file)

def path_get_mtime(path: str) -> float:
    return os.path.getmtime(path)

def path_split_ext(file_path: str) -> Tuple[str, str]:
    return os.path.splitext(file_path)

def path_is_file(path_to_file: str) -> bool:
    path = pathlib.Path(path_to_file)
    return path.is_file()

def path_is_directory(path_to_dir: str) -> bool:
    path = pathlib.Path(path_to_dir)
    return path.is_dir()

def file_exists(path_to_file: str) -> bool:
    return os.path.exists(path_to_file) and path_is_file(path_to_file)


def rename_file(old_path_to_file: str, new_path_to_file: str) -> bool:
    try:
        os.rename(old_path_to_file, new_path_to_file)
        return True
    except:
        return False

def delete_file(path_to_file: str) -> bool:
    if file_exists(path_to_file):
        os.remove(path_to_file)
        return True
    else:
        return False

def directory_exists(path_to_dir: str) -> bool:
    return os.path.exists(path_to_dir) and path_is_directory(path_to_dir)

def path_join(dir_path: str, file_name: str) -> str:
    return os.path.join(dir_path, file_name)

def os_is_posix() -> bool:
    return os.name == 'posix'

def list_files_in_directory(dir_path: str) -> List[str]:
    file_list = []
    if directory_exists(dir_path):
        list_entries = os.listdir(dir_path)
        for entry in list_entries:
            if path_is_file(entry) and entry not in ['.', '..']:
                file_list.append(entry)
    return file_list

def list_dirs_in_directory(dir_path: str) -> List[str]:
    dir_list = []
    if directory_exists(dir_path):
        list_entries = os.listdir(dir_path)
        for entry in list_entries:
            if path_is_directory(entry):
                dir_list.append(entry)
    return dir_list

def delete_files_in_directory(dir_path: str) -> bool:
    if directory_exists(dir_path):
        file_list = list_files_in_directory(dir_path)
        for file in file_list:
            delete_file(file)
        return True
    else:
        return False

def get_current_directory() -> str:
    return os.getcwd()

def get_process_id() -> int:
    return os.getpid()

def create_directory(dir_path: str):
    os.makedirs(dir_path)
