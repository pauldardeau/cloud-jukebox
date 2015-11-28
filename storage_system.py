# ******************************************************************************
# Storage system for cloud jukebox
# Copyright Paul Dardeau, SwampBits LLC, 2014
# BSD license -- see LICENSE file for details
#
# StorageSystem - abstract base class for an object storage system
# ******************************************************************************

import os.path
import abc


class StorageSystem:
    __metaclass__ = abc.ABCMeta

    def __init__(self, storage_system_type, debug_mode=False):
        self.debug_mode = debug_mode
        self.authenticated = False
        self.compress_files = False
        self.encrypt_files = False
        self.list_containers = None
        self.container_prefix = ""
        self.metadata_prefix = ""
        self.storage_system_type = storage_system_type

    def un_prefixed_container(self, container_name):
        if len(self.container_prefix) > 0 and len(container_name) > 0:
            if container_name.startswith(self.container_prefix):
                return container_name[len(self.container_prefix):]
        return container_name

    def prefixed_container(self, container_name):
        return self.container_prefix + container_name

    def has_container(self, container_name):
        return self.list_containers is not None and container_name in self.list_containers

    def add_container(self, container_name):
        if self.list_containers is None:
            self.list_containers = []
        self.list_containers.append(container_name)

    def remove_container(self, container_name):
        if self.list_containers is not None:
            self.list_containers.remove(container_name)

    def delete_song_file(self, song_file):
        if song_file is not None:
            return self.delete_file(song_file.container, song_file.object_name)
        return False

    def retrieve_song_file(self, song_file, local_directory):
        if song_file is not None and local_directory is not None:
            file_path = os.path.join(local_directory, song_file.uid)
            return self.retrieve_file(song_file.container, song_file.object_name, file_path)
        return False

    def store_song_file(self, song_file, file_contents):
        if song_file is not None and file_contents is not None:
            return self.add_file(song_file.container, song_file.object_name, file_contents,
                                 song_file.to_dictionary(self.metadata_prefix))
        return False

    def add_file_from_path(self, container_name, object_name, file_path):
        try:
            with open(file_path, 'rb') as input_file:
                file_contents = input_file.read()
            return self.add_file(container_name, object_name, file_contents)
        except IOError:
            print("error: unable to read file %s" % file_path)
            return False

    @abc.abstractmethod
    def list_account_containers(self):
        return None

    @abc.abstractmethod
    def create_container(self, container_name):
        return False

    @abc.abstractmethod
    def delete_container(self, container_name):
        return False

    @abc.abstractmethod
    def list_container_contents(self, container_name):
        return None

    @abc.abstractmethod
    def get_file_metadata(self, container_name, object_name):
        return None

    @abc.abstractmethod
    def add_file(self, container_name, object_name, file_contents, headers=None):
        return False

    @abc.abstractmethod
    def delete_file(self, container_name, object_name):
        return False

    @abc.abstractmethod
    def retrieve_file(self, container_name, object_name, local_file_path):
        return False
