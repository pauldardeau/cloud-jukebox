import io
import os.path
import sys

from typing import List

from storage_system import StorageSystem
import typing


_storage_system_minio_supported = False


try:
    import minio
    _storage_system_minio_supported = True
except ImportError:
    _storage_system_minio_supported = False


def is_available():
    return _storage_system_minio_supported


class MinioStorageSystem(StorageSystem):

    def __init__(self, access_key: str, secret_key: str,
                 endpoint_url: str, debug_mode: bool = False):
        StorageSystem.__init__(self, "Minio", debug_mode)
        self.debug_mode = debug_mode
        self.access_key = access_key
        self.secret_key = secret_key
        self.endpoint_url = endpoint_url
        if self.debug_mode:
            print("Using access_key='%s', secret_key='%s', endpoint_url='%s'" % (self.access_key, self.secret_key, self.endpoint_url))

    def __enter__(self):
        if self.debug_mode:
            print("attempting to connect to Minio")
        quoted_endpoint_url = "'%s'" % self.endpoint_url

        self.conn = minio.Minio(self.endpoint_url,
                                access_key=self.access_key,
                                secret_key=self.secret_key,
                                secure=False,
                                region="garage")
        self.authenticated = True
        self.list_containers = self.list_account_containers()

        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if self.conn is not None:
            if self.debug_mode:
                print("closing Minio connection object")

            self.authenticated = False
            self.list_containers = None
            # self.conn.close()
            self.conn = None

    def list_account_containers(self) -> typing.Optional[List[str]]:
        if self.debug_mode:
            print("list_account_containers")
        if self.conn is not None:
            # try:
                list_buckets = self.conn.list_buckets()

                list_container_names = []

                for bucket in list_buckets:
                    bucket_name = bucket.name
                    list_container_names.append(bucket_name)

                return list_container_names
            # except boto.exception.S3ResponseError:
            #    pass

        return None

    def create_container(self, container_name: str) -> bool:
        if self.debug_mode:
            print("create_container: '%s'" % container_name)

        container_created = False
        if self.conn is not None:
            # try:
                resp = self.conn.make_bucket(container_name)
                print("result of make_bucket: '" + repr(resp) + "'")
                self.add_container(container_name)
                container_created = True
            # except (boto.exception.S3CreateError, boto.exception.S3ResponseError):
            #    pass

        return container_created

    def delete_container(self, container_name: str) -> bool:
        if self.debug_mode:
            print("delete_container: '%s'" % container_name)

        container_deleted = False
        if self.conn is not None:
            # try:
                self.conn.remove_bucket(container_name)
                self.remove_container(container_name)
                container_deleted = True
            # except boto.exception.S3ResponseError:
            #    pass

        return container_deleted

    def list_container_contents(self, container_name: str) -> typing.Optional[List[str]]:
        if self.debug_mode:
            print("list_container_contents: '%s'" % container_name)

        if self.conn is not None:
            try:
                objectsIterator = self.conn.list_objects(container_name)
                list_contents = []
                for obj in objectsIterator:
                    list_contents.append(obj.object_name)

                return list_contents
            except Exception as exception:
                print("exception caught: %s" % type(exception).__name__)
            # except S3.Client.exceptions.NoSuchBucket:
            #    print("bucket does not exist")
            #    pass

        return None

    def get_object_metadata(self, container_name: str, object_name: str):
        if self.debug_mode:
            print("get_object_metadata: container='%s', object='%s'" % (container_name, object_name))

        if self.conn is not None and container_name is not None and object_name is not None:
            # try:
                result = self.conn.stat_object(container_name, object_name)
                dictMeta = {}
                dictMeta['last_modified'] = result.last_modified
                dictMeta['size'] = result.size

                return dictMeta
            # except boto.exception.S3ResponseError:
            #    pass

        return None

    def put_object(self, container_name: str, object_name: str, file_contents, headers=None) -> bool:

        object_added = False

        if self.conn is not None and container_name is not None and \
                object_name is not None and file_contents is not None:

            #if not self.has_container(container_name):
            #    self.create_container(container_name)

            try:
                bucket = container_name
                result = self.conn.put_object(bucket, object_name, io.BytesIO(file_contents), len(file_contents))
                if "HTTPStatusCode" in result:
                    status_code = result["HTTPStatusCode"]
                    if status_code == 200:
                        object_added = True
                else:
                    if "ResponseMetadata" in result:
                        resp_meta = result["ResponseMetadata"]
                        if "HTTPStatusCode" in resp_meta:
                            status_code = resp_meta["HTTPStatusCode"]
                            if status_code == 200:
                                object_added = True
                    else:
                        print(repr(result))
            except AttributeError as ae:
                print(repr(ae))
            except NameError as ne:
                print(repr(ne))
            except KeyError as ke:
                print(repr(ke))
            except minio.error.S3Error as me:
                print(repr(me))
            except:
                print("Exception ", sys.exc_info()[0], "occurred.")
                pass

        return object_added

    def delete_object(self, container_name: str, object_name: str) -> bool:
        if self.debug_mode:
            print("delete_object: container='%s', object='%s'" % (container_name, object_name))

        object_deleted = False

        if self.conn is not None and container_name is not None and object_name is not None:
            # try:
                self.conn.remove_object(container_name, object_name)
                object_deleted = True
            # except boto.exception.S3ResponseError:
            #    pass

        return object_deleted

    def get_object(self, container_name: str, object_name: str, local_file_path: str) -> int:
        if self.debug_mode:
            print("get_object: container='%s', object='%s', local_file_path='%s'" % (container_name,

     object_name,

     local_file_path))

        bytes_retrieved = 0

        if self.conn is not None and container_name is not None and \
                object_name is not None and local_file_path is not None:

            self.conn.fget_object(container_name, object_name, local_file_path)

            if os.path.exists(local_file_path):
                bytes_retrieved = os.path.getsize(local_file_path)

        return bytes_retrieved


