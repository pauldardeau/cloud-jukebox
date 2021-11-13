import os.path
from storage_system import StorageSystem


_storage_system_s3_supported = False


try:
    import boto3
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
        self.debug_mode = False
        if container_prefix is not None and len(container_prefix) > 0:
            if self.debug_mode:
                print("using container_prefix='%s'" % container_prefix)
            self.container_prefix = container_prefix

    def __enter__(self):
        if self.debug_mode:
            print("attempting to connect to S3")

        self.conn = boto3.client('s3',
                                 endpoint_url='https://s3.us-central-1.wasabisys.com',
                                 aws_access_key_id=self.aws_access_key,
                                 aws_secret_access_key=self.aws_secret_key)
        self.authenticated = True
        self.list_containers = self.list_account_containers()

        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if self.conn is not None:
            if self.debug_mode:
                print("closing S3 connection object")

            self.authenticated = False
            self.list_containers = None
            #self.conn.close()
            self.conn = None

    def list_account_containers(self):
        if self.debug_mode:
            print("list_account_containers")
        if self.conn is not None:
            #try:
                rs = self.conn.list_buckets()

                list_container_names = []

                list_buckets = rs['Buckets']
                
                for container in list_buckets:
                    container_name = container['Name']
                    list_container_names.append(self.un_prefixed_container(container_name))

                return list_container_names
            #except boto.exception.S3ResponseError:
            #    pass

        return None

    def create_container(self, container_name):
        if self.debug_mode:
            print("create_container: '%s'" % container_name)

        container_created = False
        if self.conn is not None:
            #try:
                self.conn.create_bucket(container_name)
                self.add_container(container_name)
                container_created = True
            #except (boto.exception.S3CreateError, boto.exception.S3ResponseError):
            #    pass

        return container_created

    def delete_container(self, container_name):
        if self.debug_mode:
            print("delete_container: '%s'" % container_name)

        container_deleted = False
        if self.conn is not None:
            #try:
                self.conn.delete_bucket(self.prefixed_container(container_name))
                self.remove_container(container_name)
                container_deleted = True
            #except boto.exception.S3ResponseError:
            #    pass

        return container_deleted

    def list_container_contents(self, container_name):
        if self.debug_mode:
            print("list_container_contents: '%s'" % container_name)

        if self.conn is not None:
            try:
                response = self.conn.list_objects_v2(Bucket=container_name)
                meta = response['ResponseMetadata']
                status_code = meta['HTTPStatusCode']
                if status_code == 200:
                    list_contents = []
                    contents = response['Contents']

                    for objDict in contents:
                        list_contents.append(objDict['Key'])

                    return list_contents
            except Exception as exception:
                print("exception caught: %s" % type(exception).__name__)
            #except S3.Client.exceptions.NoSuchBucket:
            #    print("bucket does not exist")
            #    pass

        return None

    def get_object_metadata(self, container_name, object_name):
        if self.debug_mode:
            print("get_object_metadata: container='%s', object='%s'" % (container_name, object_name))

        if self.conn is not None and container_name is not None and object_name is not None:
            #try:
                bucket = self.conn.head_object(Bucket=container_name, Key=object_name)
                #object_key = bucket.get_key(object_name)
                #if object_key is not None:
                #    pass

                # TODO: retrieve metadata key/values as dictionary
                return None
            #except boto.exception.S3ResponseError:
            #    pass

        return None

    def put_object(self, container_name, object_name, file_contents, headers=None):
        if self.debug_mode:
            print("put_object: container='%s', object='%s'" % (container_name, object_name))

        object_added = False

        if self.conn is not None and container_name is not None and \
                object_name is not None and file_contents is not None:

            if not self.has_container(container_name):
                self.create_container(container_name)

            #try:
                #TODO: implement put_object
                #bucket = self.conn.get_bucket(self.prefixed_container(container_name))
                #object_key = Key(bucket)
                #object_key.key = object_name
                #object_key.set_contents_from_string(file_contents)
                #object_added = True
            #except boto.exception.S3ResponseError:
            #    pass

        return object_added

    def delete_object(self, container_name, object_name):
        if self.debug_mode:
            print("delete_object: container='%s', object='%s'" % (container_name, object_name))

        object_deleted = False

        if self.conn is not None and container_name is not None and object_name is not None:
            #try:
                self.conn.delete_object(container_name, object_name)
                #bucket = self.conn.get_bucket(self.prefixed_container(container_name))
                #object_key = bucket.get_key(object_name)
                #object_key.delete()
                object_deleted = True
            #except boto.exception.S3ResponseError:
            #    pass

        return object_deleted

    def get_object(self, container_name, object_name, local_file_path):
        if self.debug_mode:
            print("get_object: container='%s', object='%s', local_file_path='%s'" % (container_name, object_name, local_file_path))

        bytes_retrieved = 0

        if self.conn is not None and container_name is not None and \
                object_name is not None and local_file_path is not None:

            #try:
                self.conn.download_file(container_name, object_name, local_file_path)
                #bucket = self.conn.get_bucket(self.prefixed_container(container_name))
                #object_key = bucket.get_key(object_name)
                #object_key.get_contents_to_filename(local_file_path)
                if os.path.exists(local_file_path):
                    bytes_retrieved = os.path.getsize(local_file_path)
            #except (Exception, boto.exception.S3ResponseError):
            #    pass

        return bytes_retrieved
