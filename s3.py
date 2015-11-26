import os.path
from StorageSystem import StorageSystem


_storage_system_s3_supported = False


try:
    import boto
    from boto.s3.connection import S3Connection
    from boto.s3.key import Key
    _storage_system_s3_supported = True
except ImportError:
    _storage_system_s3_supported = False


def is_available():
    return _storage_system_s3_supported


class S3StorageSystem(StorageSystem):
    def __init__(self, aws_access_key, aws_secret_key, container_prefix, debug_mode=False):
        StorageSystem.__init__(self, "S3", debug_mode)
        self.aws_access_key = aws_access_key
        self.aws_secret_key = aws_secret_key
        if container_prefix is not None and len(container_prefix) > 0:
            self.set_container_prefix(container_prefix)

    def __enter__(self):
        if self.debug_mode:
            print "attempting to connect to S3"

        self.conn = S3Connection(self.aws_access_key, self.aws_secret_key)
        self.authenticated = True
        self.list_containers = self.list_account_containers()

        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if self.conn is not None:
            if self.debug_mode:
                print "closing S3 connection object"

            self.authenticated = False
            self.list_containers = None
            self.conn.close()
            self.conn = None

    def list_account_containers(self):
        if self.conn is not None:
            try:
                rs = self.conn.get_all_buckets()

                list_container_names = []

                for container in rs:
                    list_container_names.append(self.un_prefixed_container(container.name))

                return list_container_names
            except boto.exception.S3ResponseError:
                pass

        return None

    def create_container(self, container_name):
        container_created = False
        if self.conn is not None:
            try:
                self.conn.create_bucket(self.prefixed_container(container_name))
                self.add_container(container_name)
                container_created = True
            except (boto.exception.S3CreateError, boto.exception.S3ResponseError):
                pass

        return container_created

    def delete_container(self, container_name):
        container_deleted = False
        if self.conn is not None:
            try:
                self.conn.delete_bucket(self.prefixed_container(container_name))
                self.remove_container(container_name)
                container_deleted = True
            except boto.exception.S3ResponseError:
                pass

        return container_deleted

    def list_container_contents(self, container_name):
        if self.conn is not None:
            try:
                container = self.conn.get_bucket(self.prefixed_container(container_name))
                rs = container.list()
                list_contents = []

                for key in rs:
                    list_contents.append(key.name)

                return list_contents
            except boto.exception.S3ResponseError:
                pass

        return None

    def get_file_metadata(self, container_name, object_name):
        if self.conn is not None and container_name is not None and object_name is not None:
            try:
                bucket = self.conn.get_bucket(self.prefixed_container(container_name))
                object_key = bucket.get_key(object_name)
                if object_key is not None:
                    pass

                # TODO: retrieve metadata key/values as dictionary
                return None
            except boto.exception.S3ResponseError:
                pass

        return None

    def add_file(self, container_name, object_name, file_contents, headers=None):
        file_added = False

        if self.conn is not None and container_name is not None and \
                object_name is not None and file_contents is not None:

            if not self.has_container(container_name):
                self.create_container(container_name)

            try:
                bucket = self.conn.get_bucket(self.prefixed_container(container_name))
                object_key = Key(bucket)
                object_key.key = object_name
                object_key.set_contents_from_string(file_contents)
                file_added = True
            except boto.exception.S3ResponseError:
                pass

        return file_added

    def delete_file(self, container_name, object_name):
        file_deleted = False

        if self.conn is not None and container_name is not None and object_name is not None:
            try:
                bucket = self.conn.get_bucket(self.prefixed_container(container_name))
                object_key = bucket.get_key(object_name)
                object_key.delete()
                file_deleted = True
            except boto.exception.S3ResponseError:
                pass

        return file_deleted

    def retrieve_file(self, container_name, object_name, local_file_path):
        file_bytes_retrieved = 0

        if self.conn is not None and container_name is not None and \
                object_name is not None and local_file_path is not None:

            try:
                bucket = self.conn.get_bucket(self.prefixed_container(container_name))
                object_key = bucket.get_key(object_name)
                object_key.get_contents_to_filename(local_file_path)
                if os.path.exists(local_file_path):
                    file_bytes_retrieved = os.path.getsize(local_file_path)
            except (Exception, boto.exception.S3ResponseError):
                pass

        return file_bytes_retrieved
