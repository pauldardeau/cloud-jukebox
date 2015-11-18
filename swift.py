from StorageSystem import StorageSystem


_storage_system_swift_supported = False

try:
    import swiftclient

    _storage_system_swift_supported = True
except ImportError:
    _storage_system_swift_supported = False


def is_available():
    return _storage_system_swift_supported


class SwiftStorageSystem(StorageSystem):
    def __init__(self, auth_host, account, username, password, debug_mode=False):
        StorageSystem.__init__(self, "Swift", debug_mode)
        self.auth_host = auth_host
        self.auth_port = 8080
        self.auth_version = "1"
        self.auth_prefix = "/auth/"
        self.auth_ssl = 0
        self.account = account
        self.username = username
        self.password = password
        self.set_metadata_prefix("x-meta-")
        self.auth_url = ""

        if self.auth_ssl:
            self.auth_url += "https://"
        else:
            self.auth_url += "http://"

        self.auth_url += "%s:%s%s" % (self.auth_host, self.auth_port, self.auth_prefix)

        if self.auth_version == "1":
            self.auth_url += "v1.0"

        self.account_username = "%s:%s" % (self.account, self.username)

    def __enter__(self):
        if self.is_debug_mode():
            print "attempting to connect to swift server at %s" % self.auth_url

        self.conn = swiftclient.Connection(
            self.auth_url, self.account_username, self.password,
            auth_version=self.auth_version, retries=1)
        dict_headers = self.conn.head_account()
        if dict_headers is not None:
            self.set_authenticated(True)
            self.set_list_containers(self.list_account_containers())

        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if self.conn is not None:
            if self.is_debug_mode():
                print "closing swift connection object"

            self.set_authenticated(0)
            self.set_list_containers([])
            self.conn.close()
            self.conn = None

    def list_account_containers(self):
        if self.conn is not None:
            try:
                dict_headers, list_containers = self.conn.get_account()
                if dict_headers is not None and list_containers is not None:
                    list_container_names = []
                    for dictContainer in list_containers:
                        list_container_names.append(dictContainer['name'])
                    return list_container_names
            except swiftclient.client.ClientException:
                pass

        return None

    def create_container(self, container_name):
        container_created = False
        if self.conn is not None:
            try:
                self.conn.put_container(container_name)
                self.add_container(container_name)
                container_created = True
            except swiftclient.client.ClientException:
                pass

        return container_created

    def delete_container(self, container_name):
        container_deleted = False
        if self.conn is not None:
            try:
                self.conn.delete_container(container_name)
                self.remove_container(container_name)
                container_deleted = True
            except swiftclient.client.ClientException:
                pass

        return container_deleted

    def list_container_contents(self, container_name):
        if self.conn is not None:
            try:
                dict_headers, list_contents = self.conn.get_container(container_name)
                if dict_headers is not None and list_contents is not None:
                    list_object_names = []
                    for object_record in list_contents:
                        list_object_names.append(object_record['name'])
                    return list_object_names
            except swiftclient.client.ClientException:
                pass

        return None

    def get_file_metadata(self, container_name, object_name):
        if self.conn is not None and container_name is not None and object_name is not None:
            try:
                return self.conn.head_object(container_name, object_name)
            except swiftclient.client.ClientException:
                pass

        return None

    def add_file(self, container_name, object_name, file_contents, headers=None):
        file_added = False

        if self.conn is not None and container_name is not None and \
                object_name is not None and file_contents is not None:

            if not self.has_container(container_name):
                self.create_container(container_name)

            try:
                self.conn.put_object(container_name, object_name, file_contents, headers=headers)
                file_added = True
            except swiftclient.client.ClientException:
                pass

        return file_added

    def delete_file(self, container_name, object_name):
        file_deleted = False

        if self.conn is not None and container_name is not None and object_name is not None:
            try:
                self.conn.delete_object(container_name, object_name)
                file_deleted = True
            except swiftclient.client.ClientException:
                pass

        return file_deleted

    def retrieve_file(self, container_name, object_name, local_file_path):
        file_bytes_retrieved = 0

        if self.conn is not None and container_name is not None and \
                object_name is not None and local_file_path is not None:

            try:
                dict_headers, file_contents = self.conn.get_object(container_name, object_name)
                if dict_headers is not None and file_contents is not None:
                    if len(file_contents) > 0:
                        try:
                            with open(local_file_path, 'wb') as content_file:
                                content_file.write(file_contents)
                            file_bytes_retrieved = len(file_contents)
                        except IOError:
                            print "error: unable to write to file '%s'" % local_file_path
                    else:
                        # create empty file
                        try:
                            open(local_file_path, 'w').close()
                            file_bytes_retrieved = 0
                        except IOError:
                            print "error: unable to write to file '%s'" % local_file_path
            except swiftclient.client.ClientException:
                pass

        return file_bytes_retrieved
