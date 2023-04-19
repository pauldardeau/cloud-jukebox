import unittest

import property_value


class TestPropertyValue(unittest.TestCase):

    def test_new_int_property_value(self):
        int_value = 5
        pv = property_value.new_int_property_value(int_value)
        self.assertIsNotNone(pv, "new_int_property_value should not return None")
        self.assertTrue(pv.is_int(), "is_int should be true after creating with new_int_property_value")
        self.assertFalse(pv.is_bool(), "is_bool should be false after creating with new_int_property_value")
        self.assertFalse(pv.is_string(), "is_string should be false after creating with new_int_property_value")
        self.assertEqual(pv.get_int_value(), int_value, "get_int_value should return value used in construction")
        self.assertEqual(pv.get_bool_value(), False, "get_bool_value should return False when constructed with int")
        self.assertEqual(pv.get_string_value(), "", "get_string_value should return '' when constructed with int")

    def test_new_bool_property_value(self):
        bool_value = True
        pv = property_value.new_bool_property_value(bool_value)
        self.assertIsNotNone(pv, "new_bool_property_value should not return None")
        self.assertTrue(pv.is_bool(), "is_bool should be true after creating with new_bool_property_value")
        self.assertFalse(pv.is_int(), "is_int should be false after creating with new_bool_property_value")
        self.assertFalse(pv.is_string(), "is_string should be false after creating with new_bool_property_value")
        self.assertEqual(pv.get_bool_value(), bool_value, "get_bool_value should return value used in construction")
        self.assertEqual(pv.get_int_value(), 0, "get_int_value should return 0 when constructed with bool")
        self.assertEqual(pv.get_string_value(), "", "get_string_value should return '' when constructed with bool")

    def test_new_string_property_value(self):
        string_value = "foo"
        pv = property_value.new_string_property_value(string_value)
        self.assertIsNotNone(pv, "new_string_property_value should not return None")
        self.assertTrue(pv.is_string(), "is_string should be true after creating with new_string_property_value")
        self.assertFalse(pv.is_int(), "is_int should be false after creating with new_string_property_value")
        self.assertFalse(pv.is_bool(), "is_bool should be false after creating with new_string_property_value")
        self.assertEqual(pv.get_bool_value(), False, "get_bool_value should return False when constructed with string")
        self.assertEqual(pv.get_int_value(), 0, "get_int_value should return 0 when constructed with bool")
        self.assertEqual(pv.get_string_value(), string_value, "get_string_value should return value used to construct")


if __name__ == '__main__':
    unittest.main()
