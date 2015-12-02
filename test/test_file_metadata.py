import unittest

import file_metadata


class TestFileMetadata(unittest.TestCase):

    def setUp(self):
        self.fm = file_metadata.FileMetadata()
        self.fm.file_uid = "some_file_uid"
        self.fm.file_name = "some_file_name"
        self.fm.origin_file_size = 1024
        self.fm.stored_file_size = 512
        self.fm.pad_char_count = 5
        self.fm.file_time = "some_file_time"
        self.fm.md5_hash = "asdf"
        self.fm.compressed = 0
        self.fm.encrypted = 1
        self.fm.container_name = "some_container_name"
        self.fm.object_name = "some_object_name"

    def test_eq(self):
        fm2 = file_metadata.FileMetadata()
        fm2.file_uid = "some_file_uid"
        fm2.file_name = "some_file_name"
        fm2.origin_file_size = 1024
        fm2.stored_file_size = 512
        fm2.pad_char_count = 5
        fm2.file_time = "some_file_time"
        fm2.md5_hash = "asdf"
        fm2.compressed = 0
        fm2.encrypted = 1
        fm2.container_name = "some_container_name"
        fm2.object_name = "some_object_name"
        self.assertEqual(self.fm, fm2)

    def test_to_dictionary_no_prefix(self):
        d = self.fm.to_dictionary()
        self.assertEqual(d['file_uid'], 'some_file_uid')
        self.assertEqual(d['file_name'], 'some_file_name')
        self.assertEqual(d['origin_file_size'], 1024)
        self.assertEqual(d['stored_file_size'], 512)
        self.assertEqual(d['pad_char_count'], 5)
        self.assertEqual(d['file_time'], 'some_file_time')
        self.assertEqual(d['md5_hash'], 'asdf')
        self.assertEqual(d['compressed'], 0)
        self.assertEqual(d['encrypted'], 1)
        self.assertEqual(d['container_name'], 'some_container_name')
        self.assertEqual(d['object_name'], 'some_object_name')

    def test_to_dictionary_with_prefix(self):
        prefix = 'foo'
        d = self.fm.to_dictionary(prefix)
        self.assertEqual(d[prefix+'file_uid'], 'some_file_uid')
        self.assertEqual(d[prefix+'file_name'], 'some_file_name')
        self.assertEqual(d[prefix+'origin_file_size'], 1024)
        self.assertEqual(d[prefix+'stored_file_size'], 512)
        self.assertEqual(d[prefix+'pad_char_count'], 5)
        self.assertEqual(d[prefix+'file_time'], 'some_file_time')
        self.assertEqual(d[prefix+'md5_hash'], 'asdf')
        self.assertEqual(d[prefix+'compressed'], 0)
        self.assertEqual(d[prefix+'encrypted'], 1)
        self.assertEqual(d[prefix+'container_name'], 'some_container_name')
        self.assertEqual(d[prefix+'object_name'], 'some_object_name')

    def test_from_dictionary(self):
        d = self.fm.to_dictionary()
        fm2 = file_metadata.FileMetadata()
        fm2.from_dictionary(d)
        self.assertEqual(self.fm, fm2)


if __name__ == '__main__':
    unittest.main()
