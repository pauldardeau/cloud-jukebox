from typing import List

from storage_system import StorageSystem
import property_set
import typing
import utils

METADATA_FILE_SUFFIX = ".meta"


class FSStorageSystem(StorageSystem):

    def __init__(self, root_dir: str, debug_mode: bool = False):
        StorageSystem.__init__(self, "FS", debug_mode)
        self.root_dir = root_dir
        self.list_containers: List[str] = []

    def __enter__(self):
        if not utils.directory_exists(self.root_dir):
            utils.create_directory(self.root_dir)
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        pass

    def get_container_dir(self, container_name) -> str:
        return utils.path_join(self.root_dir, container_name)

    def list_account_containers(self) -> typing.Optional[List[str]]:
        return utils.list_dirs_in_directory(self.root_dir)

    def create_container(self, container_name: str) -> bool:
        container_dir = self.get_container_dir(container_name)
        container_created = utils.create_directory(container_dir)
        if container_created:
            if self.debug_mode:
                print("container created: '%s'" % container_name)
        return container_created

    def delete_container(self, container_name: str) -> bool:
        container_dir = self.get_container_dir(container_name)
        container_deleted = utils.delete_directory(container_dir)
        if container_deleted:
            if self.debug_mode:
                print("container deleted: '%s'" % container_name)
        return container_deleted

    def list_container_contents(self, container_name: str) -> typing.Optional[List[str]]:
        container_dir = self.get_container_dir(container_name)
        if utils.directory_exists(container_dir):
            return utils.list_files_in_directory(container_dir)
        else:
            return None

    def get_object_metadata(self, container_name: str, object_name: str) -> typing.Optional[property_set.PropertySet]:
        if container_name is not None and \
                object_name is not None and \
                len(container_name) > 0 and \
                len(object_name) > 0:

            container_dir = self.get_container_dir(container_name)
            if utils.directory_exists(container_dir):
                object_path = utils.path_join(container_dir, object_name)
                meta_path = object_path + METADATA_FILE_SUFFIX
                if utils.file_exists(meta_path):
                    return property_set.read_from_file(meta_path)
                else:
                    print("error: metadata file does not exist")
            else:
                print("error: container directory does not exist")
        else:
            print("error: missing container name or object name")

        return None

    def put_object(self, container_name: str, object_name: str, file_contents: str,
                   headers: property_set.PropertySet = None) -> bool:
        object_added = False
        if container_name is not None and \
                object_name is not None and \
                file_contents is not None and \
                len(container_name) > 0 and \
                len(object_name) > 0 and \
                len(file_contents) > 0:

            container_dir = self.get_container_dir(container_name)
            if utils.directory_exists(container_dir):
                object_path = utils.path_join(container_dir, object_name)
                object_added = utils.file_write_all_bytes(object_path, file_contents)
                if object_added:
                    if self.debug_mode:
                        print("object added: %s/%s", container_name, object_name)
                    if headers is not None:
                        meta_path = object_path + METADATA_FILE_SUFFIX
                        headers.write_to_file(meta_path)
                else:
                    print("file_write_all_bytes failed to write object contents, put failed")
            else:
                print("container doesn't exist, can't put object")
        else:
            if self.debug_mode:
                if len(container_name) == 0:
                    print("container name is missing, can't put object")
                else:
                    if len(object_name) == 0:
                        print("object name is missing, can't put object")
                    else:
                        if len(file_contents) == 0:
                            print("object content is empty, can't put object")
        return object_added

    def delete_object(self, container_name: str, object_name: str) -> bool:
        object_deleted = False
        if container_name is not None and object_name is not None:
            container_dir = self.get_container_dir(container_name)
            object_path = utils.path_join(container_dir, object_name)
            if utils.file_exists(object_path):
                object_deleted = utils.delete_file(object_path)
                if object_deleted:
                    if self.debug_mode:
                        print("object deleted: %s/%s" % (container_name, object_name))
                    meta_path = object_path + METADATA_FILE_SUFFIX
                    if utils.file_exists(meta_path):
                        utils.delete_file(meta_path)
                else:
                    if self.debug_mode:
                        print("delete of object file failed")
            else:
                if self.debug_mode:
                    print("cannot delete object, path doesn't exist")
        else:
            if self.debug_mode:
                print("cannot delete object, container name or object name is missing")
        return object_deleted

    def get_object(self, container_name: str, object_name: str, local_file_path: str) -> int:
        bytes_retrieved = 0
        if container_name is not None and \
                object_name is not None and \
                local_file_path is not None and \
                len(container_name) > 0 and \
                len(object_name) > 0 and \
                len(local_file_path) > 0:

            container_dir = self.get_container_dir(container_name)
            object_path = utils.path_join(container_dir, object_name)
            if utils.file_exists(object_path):
                obj_file_contents = utils.file_read_all_bytes(object_path)
                if obj_file_contents is not None:
                    if self.debug_mode:
                        print("attempting to write object to '%s'" % local_file_path)
                    if utils.file_write_all_bytes(local_file_path, obj_file_contents):
                        bytes_retrieved = len(obj_file_contents)
                else:
                    print("error: unable to read object file '%s'" % object_path)
            else:
                print("error: object path does not exist, cannot retrieve object")
        else:
            print("error: missing container, object, or local file path")

        return bytes_retrieved
