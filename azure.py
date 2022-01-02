import os.path

from typing import List

from storage_system import StorageSystem
import typing

_storage_system_azure_supported = False

try:
    from azure.storage import *
    _storage_system_azure_supported = True
except ImportError:
    _storage_system_azure_supported = False


def is_available():
    return _storage_system_azure_supported


class AzureStorageSystem(StorageSystem):
    def __init__(self, account_name: str, account_key: str, container_prefix: str, debug_mode: bool = False):
        StorageSystem.__init__(self, "Azure", debug_mode)
        self.account_name = account_name
        self.account_key = account_key
        if container_prefix is not None and len(container_prefix) > 0:
            self.container_prefix = container_prefix

    def __enter__(self):
        if self.debug_mode:
            print("attempting to connect to Azure")

        self.blob_service = BlobService(account_name=self.account_name, account_key=self.account_key)
        self.authenticated = True
        self.list_containers = self.list_account_containers()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if self.blob_service is not None:
            if self.debug_mode:
                print("closing Azure connection object")
            self.authenticated = False
            self.list_containers = None
            self.blob_service = None

    def list_account_containers(self) -> typing.Optional[List[str]]:
        if self.blob_service is not None:
            list_containers = self.blob_service.list_containers()
            list_container_names = []
            if list_containers is not None:
                for container in list_containers:
                    list_container_names.append(self.un_prefixed_container(container.name))

            return list_container_names
        return None

    def create_container(self, container_name: str) -> bool:
        container_created = False
        if self.blob_service is not None:
            if self.blob_service.create_container(self.prefixed_container(container_name)):
                self.add_container(container_name)
                container_created = True
        return container_created

    def delete_container(self, container_name: str) -> bool:
        container_deleted = False
        if self.blob_service is not None:
            if self.blob_service.delete_container(self.prefixed_container(container_name)):
                self.remove_container(container_name)
                container_deleted = True
        return container_deleted

    def list_container_contents(self, container_name: str) -> typing.Optional[List[str]]:
        if self.blob_service is not None:
            list_contents = []
            blobs = self.blob_service.list_blobs(self.prefixed_container(container_name))

            if blobs is not None:
                for blob in blobs:
                    list_contents.append(blob.name)
            return list_contents
        return None

    def get_object_metadata(self, container_name: str, object_name: str):
        if self.blob_service is not None and container_name is not None and object_name is not None:
            return self.blob_service.get_blob_properties(self.prefixed_container(container_name))
        return None

    def put_object(self, container_name: str, object_name: str, file_contents, headers=None) -> bool:
        object_added = False
        if self.blob_service is not None and container_name is not None and \
                object_name is not None and file_contents is not None:

            if not self.has_container(container_name):
                if not self.create_container(container_name):
                    if self.debug_mode:
                        print("error: unable to create container '%s'" % container_name)
                    return False

            resp = self.blob_service.put_block_blob_from_bytes(self.prefixed_container(container_name), object_name,
                                                               file_contents)
            if resp is None:
                object_added = True
            else:
                if self.debug_mode:
                    print("error: unable to store file '%s'" % object_name)

        return object_added

    def delete_object(self, container_name: str, object_name: str) -> bool:
        object_deleted = False
        if self.blob_service is not None and container_name is not None and object_name is not None:
            resp = self.blob_service.delete_blob(self.prefixed_container(container_name), object_name)
            if resp is None:
                object_deleted = True
            else:
                if self.debug_mode:
                    print("error: unable to delete file '%s'" % object_name)

        return object_deleted

    def get_object(self, container_name: str, object_name: str, local_file_path: str) -> int:
        bytes_retrieved = 0

        if self.blob_service is not None and container_name is not None and \
                object_name is not None and local_file_path is not None:

            resp = self.blob_service.get_blob_to_path(self.prefixed_container(container_name),
                                                      object_name,
                                                      local_file_path)
            if resp is None:
                if os.path.exists(local_file_path):
                    bytes_retrieved = os.path.getsize(local_file_path)
            else:
                if self.debug_mode:
                    print("error: unable to retrieve file '%s'" % object_name)

        return bytes_retrieved
