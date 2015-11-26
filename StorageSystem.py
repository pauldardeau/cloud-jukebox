# ******************************************************************************
# Storage system for cloud jukebox
# Copyright Paul Dardeau, SwampBits LLC, 2014
# BSD license -- see LICENSE file for details
#
# StorageSystem - abstract base class for an object storage system
#
# Swift_StorageSystem - storage system using Swift Object Storage (https://wiki.openstack.org/wiki/Swift)
# For getting started with Swift, see: http://docs.openstack.org/developer/swift/development_saio.html
#
# S3_StorageSystem - storage system using Amazon's S3 (using boto client)
# ******************************************************************************

import os.path


class StorageSystem:
    def __init__(self, storage_system_type, debug_mode=False):
        self.debug_mode = debug_mode
        self.is_authenticated = False
        self.compress_files = False
        self.encrypt_files = False
        self.list_containers = []
        self.container_prefix = ""
        self.metadata_prefix = ""
        self.storage_system_type = storage_system_type

    def get_storage_system_type(self):
        return self.storage_system_type

    def get_container_prefix(self):
        return self.container_prefix

    def set_container_prefix(self, container_prefix):
        self.container_prefix = container_prefix

    def un_prefixed_container(self, container_name):
        if len(self.container_prefix) > 0 and len(container_name) > 0:
            if container_name.startswith(self.container_prefix):
                return container_name[len(self.container_prefix):]
        return container_name

    def get_prefixed_container(self, container_name):
        return self.container_prefix + container_name

    def has_container(self, container_name):
        return container_name in self.list_containers

    def add_container(self, container_name):
        self.list_containers.append(container_name)

    def remove_container(self, container_name):
        self.list_containers.remove(container_name)

    def get_list_containers(self):
        return self.list_containers

    def set_list_containers(self, list_containers):
        if list_containers is not None:
            self.list_containers = list_containers
        else:
            self.list_containers = []

    def set_file_compression(self, compress_files):
        self.compress_files = compress_files

    def get_file_compression(self):
        return self.compress_files

    def set_file_encryption(self, encrypt_files):
        self.encrypt_files = encrypt_files

    def get_file_encryption(self):
        return self.encrypt_files

    def is_authenticated(self):
        return self.is_authenticated

    def set_authenticated(self, is_authenticated):
        self.is_authenticated = is_authenticated

    def is_debug_mode(self):
        return self.debug_mode

    def set_debug_mode(self, debug_mode):
        self.debug_mode = debug_mode

    def get_metadata_prefix(self):
        return self.metadata_prefix

    def set_metadata_prefix(self, metadata_prefix):
        self.metadata_prefix = metadata_prefix

    def delete_song_file(self, song_file_info):
        if song_file_info is not None:
            sfi = song_file_info
            return self.delete_file(sfi.container, sfi.object_name)

        return False

    def retrieve_song_file(self, song_file_info, local_directory):
        if song_file_info is not None and local_directory is not None:
            sfi = song_file_info
            file_path = os.path.join(local_directory, sfi.uid)
            return self.retrieve_file(sfi.container, sfi.object_name, file_path)

        return False

    def store_song_file(self, song_file_info, file_contents):
        if song_file_info is not None and file_contents is not None:
            sfi = song_file_info
            return self.add_file(sfi.container, sfi.object_name, file_contents,
                                 sfi.to_dictionary(self.get_metadata_prefix()))

        return False

    def add_file_from_path(self, container_name, object_name, file_path):
        try:
            with open(file_path, 'rb') as input_file:
                file_contents = input_file.read()
            return self.add_file(container_name, object_name, file_contents)
        except IOError:
            print "error: unable to read file %s" % file_path
            return False

    # @abstractmethod
    def list_account_containers(self):
        return None

    # @abstractmethod
    def create_container(self, container_name):
        return False

    # @abstractmethod
    def delete_container(self, container_name):
        return False

    # @abstractmethod
    def list_container_contents(self, container_name):
        return None

    # @abstractmethod
    def get_file_metadata(self, container_name, object_name):
        return None

    # @abstractmethod
    def add_file(self, container_name, object_name, file_contents, headers=None):
        return False

    # @abstractmethod
    def delete_file(self, container_name, object_name):
        return False

    # @abstractmethod
    def retrieve_file(self, container_name, object_name, local_file_path):
        return False


