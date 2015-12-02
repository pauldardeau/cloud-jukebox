import unittest

from memory_storage_system import MemoryStorageSystem


class TestMemoryStorageSystem(unittest.TestCase):

    def setUp(self):
        self.mss = MemoryStorageSystem()
        self.mss.create_container('colors')
        self.mss.put_object('colors', 'red', 'red-value')
        self.mss.put_object('colors', 'green', 'green-value')
        self.mss.put_object('colors', 'blue', 'blue-value')
        self.mss.create_container('shapes')
        self.mss.put_object('shapes', 'square', 'square-value', {'object-type': 'shape'})
        self.mss.put_object('shapes', 'circle', 'circle-value', {'object-type': 'shape'})
        self.mss.put_object('shapes', 'triangle', 'triangle-value', {'object-type': 'shape'})

    def test_list_account_containers(self):
        container_names = self.mss.list_account_containers()
        self.assertIsNotNone(container_names)
        self.assertEqual(container_names, ['colors', 'shapes'])

    def test_create_container(self):
        self.assertTrue(self.mss.create_container('sizes'))
        self.assertFalse(self.mss.create_container('sizes'))
        self.assertFalse(self.mss.create_container('colors'))

    def delete_container(self):
        self.assertTrue(self.mss.delete_container('shapes'))
        self.assertFalse(self.mss.delete_container('foods'))

    def list_container_contents(self):
        self.assertTrue(False)

    def get_object_metadata(self):
        self.assertTrue(False)
        self.assertIsNone(self.mss.get_object_metadata('colors', 'green'))
        self.assertIsNotNone(self.mss.get_object_metadata('shapes', 'triangle'))
        object_type_value = self.mss.get_object_metadata('shapes', 'triangle')['object_type']
        self.assertEqual(object_type_value, 'shape')

    def put_object(self):
        self.assertTrue(self.mss.put_object('animals', 'monkey', 'bonzo'))
        self.assertTrue(self.mss.put_object('shapes', 'circle', 'new-circle-value'))
        self.assertTrue(self.mss.put_object('colors', 'magenta', 'magenta-value'))
        self.assertTrue(self.mss.put_object('colors', 'blue', 'blue-value', {'object-type': 'color'}))

    def delete_object(self):
        self.assertFalse(self.mss.delete_object('cars', 'toyota'))
        self.assertFalse(self.mss.delete_object('shapes', 'trapezoid'))
        self.assertTrue(self.mss.delete_object('shapes', 'circle'))

    def get_object(self):
        self.assertIsNone(self.mss.get_object('cars', 'honda'))
        self.assertIsNone(self.mss.get_object('shapes', 'rectangle'))
        self.assertEqual(self.mss.get_object('shapes', 'circle'), 'circle-value')
