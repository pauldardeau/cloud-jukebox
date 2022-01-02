import os.path
import abc
import typing

from typing import List


class StorageSystem:
    __metaclass__ = abc.ABCMeta

    def __init__(self, storage_system_type, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.authenticated = False
        self.compress_files = False
        self.encrypt_files = False
        self.list_containers = None
        self.container_prefix = ""
        self.metadata_prefix = ""
        self.storage_system_type = storage_system_type

    def un_prefixed_container(self, container_name: str) -> str:
        if len(self.container_prefix) > 0 and len(container_name) > 0:
            if container_name.startswith(self.container_prefix):
                return container_name[len(self.container_prefix):]
        return container_name

    def prefixed_container(self, container_name: str) -> str:
        return self.container_prefix + container_name

    def has_container(self, container_name) -> bool:
        return self.list_containers is not None and container_name in self.list_containers

    def add_container(self, container_name: str):
        if self.list_containers is None:
            self.list_containers = []
        self.list_containers.append(container_name)

    def remove_container(self, container_name: str):
        if self.list_containers is not None:
            self.list_containers.remove(container_name)

    def retrieve_file(self, fm, local_directory) -> int:
        if fm is not None and local_directory is not None:
            file_path = os.path.join(local_directory, fm.file_uid)
            # print("retrieving container=%s" % fm.container_name)
            # print("retrieving object=%s" % fm.object_name)
            return self.get_object(fm.container_name, fm.object_name, file_path)
        return 0

    def store_file(self, fm, file_contents) -> bool:
        if fm is not None and file_contents is not None:
            return self.put_object(fm.container_name,
                                   fm.object_name,
                                   file_contents,
                                   fm.to_dictionary(self.metadata_prefix))
        return False

    def add_file_from_path(self, container_name: str, object_name: str, file_path: str) -> bool:
        try:
            with open(file_path, 'rb') as input_file:
                file_contents = input_file.read()
            return self.put_object(container_name, object_name, file_contents)
        except IOError:
            print("error: unable to read file %s" % file_path)
            return False

    @abc.abstractmethod
    def list_account_containers(self) -> typing.Optional[List[str]]:
        return None

    @abc.abstractmethod
    def create_container(self, container_name: str) -> bool:
        return False

    @abc.abstractmethod
    def delete_container(self, container_name: str) -> bool:
        return False

    @abc.abstractmethod
    def list_container_contents(self, container_name: str) -> typing.Optional[List[str]]:
        return None

    @abc.abstractmethod
    def get_object_metadata(self, container_name: str, object_name: str):
        return None

    @abc.abstractmethod
    def put_object(self, container_name: str, object_name: str, file_contents, headers=None) -> bool:
        return False

    @abc.abstractmethod
    def delete_object(self, container_name: str, object_name: str) -> bool:
        return False

    @abc.abstractmethod
    def get_object(self, container_name: str, object_name: str, local_file_path: str) -> int:
        return 0
