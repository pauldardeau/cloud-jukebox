from storage_system import StorageSystem


class MemoryStorageSystem(StorageSystem):

    def __init__(self, debug_mode=False):
        StorageSystem.__init__(self, "Memory", debug_mode)
        self.list_containers = []
        self.container_objects = {}
        self.container_headers = {}

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        pass

    def list_account_containers(self):
        return self.list_containers

    def create_container(self, container_name):
        container_created = False
        self.container_objects[container_name] = {}
        self.container_headers[container_name] = {}
        if not self.has_container(container_name):
            self.list_containers.append(container_name)
            container_created = True
        return container_created

    def delete_container(self, container_name):
        container_deleted = False
        if self.has_container(container_name):
            del self.container_objects[container_name]
            del self.container_headers[container_name]
            self.list_containers.remove(container_name)
            container_deleted = True
        return container_deleted

    def list_container_contents(self, container_name):
        list_contents = []
        if container_name in self.container_objects:
            object_container = self.container_objects[container_name]
            list_contents = object_container.keys()
        return list_contents

    def get_object_metadata(self, container_name, object_name):
        if container_name is not None and object_name is not None:
            if container_name in self.container_headers:
                header_container = self.container_headers[container_name]
                return header_container[object_name]
        return None

    def put_object(self, container_name, object_name, file_contents, headers=None):
        object_added = False
        if container_name is not None and \
                object_name is not None and file_contents is not None:
            if not self.has_container(container_name):
                self.create_container(container_name)
            object_container = self.container_objects[container_name]
            object_container[object_name] = file_contents
            header_container = self.container_headers[container_name]
            header_container[object_name] = headers
            object_added = True
        return object_added

    def delete_object(self, container_name, object_name):
        object_deleted = False
        if container_name is not None and object_name is not None:
            if self.has_container(container_name):
                object_container = self.container_objects[container_name]
                if object_name in object_container:
                    del object_container[object_name]
                    object_deleted = True
                header_container = self.container_headers[container_name]
                if object_name in header_container:
                    del header_container[object_name]
                    object_deleted = True
        return object_deleted

    def get_object(self, container_name, object_name, local_file_path):
        bytes_retrieved = 0
        if container_name is not None and \
                object_name is not None and local_file_path is not None:
            if container_name in self.container_objects:
                object_container = self.container_objects[container_name]
                if object_name in object_container:
                    with open(local_file_path, 'w') as f:
                        f.write(object_container[object_name])
                    bytes_retrieved = len(object_container[object_name])
        return bytes_retrieved