import unittest

import property_value
import property_set


class TestPropertySet(unittest.TestCase):

    def test_getters_after_construction(self):
        ps = property_set.PropertySet()
        self.assertFalse(ps.contains("foo"), "contains should return False for all property names")
        self.assertEqual(ps.get_keys(), [], "get_keys should return empty list")
        self.assertIsNone(ps.get("foo"), "get should return None for all property names")
        self.assertEqual(ps.get_int_value("foo"), 0, "get_int_value should return 0")
        self.assertEqual(ps.get_bool_value("foo"), False, "get_bool_value should return False")
        self.assertEqual(ps.get_string_value("foo"), "", "get_string_value should return ''")

    def test_with_values(self):
        str_value = "foo"
        int_value = 7
        bool_value = True
        ps = property_set.PropertySet()
        ps.add("str_property", property_value.new_string_property_value(str_value))
        ps.add("int_property", property_value.new_int_property_value(int_value))
        ps.add("bool_property", property_value.new_bool_property_value(bool_value))

        self.assertTrue(ps.contains("str_property"), "contains should return True for existing properties")
        self.assertTrue(ps.contains("int_property"), "contains should return True for existing properties")
        self.assertTrue(ps.contains("bool_property"), "contains should return True for existing properties")

        self.assertEqual(len(ps.get_keys()), 3, "get_keys should return list with 3 items")
        self.assertEqual(ps.count(), 3, "count should return 3")
        self.assertIsNotNone(ps.get("str_property"), "get should not return None for existing property")
        self.assertIsNotNone(ps.get("int_property"), "get should not return None for existing property")
        self.assertIsNotNone(ps.get("bool_property"), "get should not return None for existing property")

        self.assertEqual(ps.get_int_value("int_property"), int_value, "get_int_value should return matching value")
        self.assertEqual(ps.get_bool_value("bool_property"), bool_value, "get_bool_value should return matching value")
        self.assertEqual(ps.get_string_value("str_property"), str_value, "get_string_value should return matching value")

        to_string_value = ps.to_string()
        self.assertTrue(len(to_string_value) > 0, "to_string() should return non-empty string")
        self.assertTrue(to_string_value.find("str_property") > -1, "to_string response should contain property name")
        self.assertTrue(to_string_value.find("int_property") > -1, "to_string response should contain property name")
        self.assertTrue(to_string_value.find("bool_property") > -1, "to_string response should contain property name")

        self.assertTrue(to_string_value.find(str_value) > -1, "to_string response should contain property value")
        self.assertTrue(to_string_value.find(str(int_value)) > -1, "to_string response should contain property value")
        self.assertTrue(to_string_value.find("true") > -1, "to_string response should contain property value")

        exp_to_string_value = "string|str_property|foo\nint|int_property|7\nbool|bool_property|true\n"
        self.assertEqual(to_string_value, exp_to_string_value, "to_string should return expected value")


if __name__ == '__main__':
    unittest.main()
