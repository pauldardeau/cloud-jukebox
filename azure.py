import os.path
from StorageSystem import StorageSystem


_storage_system_azure_supported = False


try:
    from azure.storage import *
    _storage_system_azure_supported = True
except ImportError:
    _storage_system_azure_supported = False

from storage_system import StorageSystem


def is_available():
    return _storage_system_azure_supported


class AzureStorageSystem(StorageSystem):
   
    def __init__(self, account_name, account_key, container_prefix, debug_mode=False):
        StorageSystem.__init__(self, "Azure", debug_mode)
        self.account_name = account_name
        self.account_key = account_key
        if container_prefix is not None and len(container_prefix) > 0:
            self.set_container_prefix(container_prefix)

    def __enter__(self):
        if self.is_debug_mode():
            print "attempting to connect to Azure"

        self.blob_service = BlobService(account_name=self.account_name, account_key=self.account_key)
        self.set_authenticated(True)
        self.set_list_containers(self.list_account_containers())
        return self

    def __exit__(self, type, value, traceback):
        if self.blob_service is not None:
            if self.is_debug_mode():
                print "closing Azure connection object"
            self.set_authenticated(False)
            self.set_list_containers([])
            self.blob_service = None

    def list_account_containers(self):
        if self.blob_service is not None:
            list_containers = self.blob_service.list_containers()
            list_container_names = []
            if list_containers is not None:
                for container in list_containers:
                    list_container_names.append(self.unprefixed_container(container.name))

            return list_container_names
        return None
      
    def create_container(self, container_name):
        container_created = False
        if self.blob_service is not None:
            if self.blob_service.create_container(self.get_prefixed_container(container_name)):
                self.add_container(container_name)
                container_created = True
        return container_created

    def delete_container(self, container_name):
        container_deleted = False
        if self.blob_service is not None:
            if self.blob_service.delete_container(self.get_prefixed_container(container_name)):
                self.remove_container(container_name)
                container_deleted = True
        return container_deleted

    def list_container_contents(self, container_name):
        if self.blob_service is not None:
            list_contents = []
            blobs = self.blob_service.list_blobs(self.get_prefixed_container(container_name))
            
            if blobs is not None:
                for blob in blobs:
                    list_contents.append(blob.name)
            return list_contents
        return None

    def get_file_metadata(self, container_name, object_name):
        if self.blob_service is not None and container_name is not None and object_name is not None:
            return self.blob_service.get_blob_properties(self.get_prefixed_container(container_name))
        return None

    def add_file(self, container_name, object_name, file_contents, headers=None):
        file_added = False
        if self.blob_service is not None and container_name is not None and object_name is not None and \
                file_contents is not None:
            if not self.has_container(container_name):
                if not self.create_container(container_name):
                    if self.is_debug_mode():
                        print "error: unable to create container '%s'" % container_name
                    return False

            resp = self.blob_service.put_block_blob_from_bytes(self.get_prefixed_container(container_name), object_name,
                                                               file_contents)
            if resp is None:
                file_added = True
            else:
                if self.is_debug_mode():
                    print "error: unable to store file '%s'" % object_name
            
        return file_added
      
    def delete_file(self, container_name, object_name):
        file_deleted = False
        if self.blob_service is not None and container_name is not None and object_name is not None:
            resp = self.blob_service.delete_blob(self.get_prefixed_container(container_name), object_name)
            if resp is None:
                file_deleted = True
            else:
                if self.is_debug_mode():
                    print "error: unable to delete file '%s'" % (object_name)
            
        return file_deleted

    def retrieve_file(self, container_name, object_name, local_file_path):
        file_bytes_retrieved = 0
      
        if self.blob_service is not None and container_name is not None and object_name is not None and local_file_path \
                is not None:
            resp = self.blob_service.get_blob_to_path(self.get_prefixed_container(container_name), object_name,
                                                      local_file_path)
            if resp is None:
                if os.path.exists(local_file_path):
                    file_bytes_retrieved = os.path.getsize(local_file_path)
            else:
                if self.is_debug_mode():
                    print "error: unable to retrieve file '%s'" % (object_name)
            
        return file_bytes_retrieved

