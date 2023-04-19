import property_value
import typing
import utils

PS_TYPE_BOOL = "bool"
PS_TYPE_STRING = "string"
PS_TYPE_INT = "int"

PS_VALUE_TRUE = "true"
PS_VALUE_FALSE = "false"


class PropertySet(object):
    def __init__(self):
        self.map_props = {}

    def add(self, prop_name: str, prop_value: property_value.PropertyValue):
        if prop_value is not None:
            self.map_props[prop_name] = prop_value

    def clear(self):
        self.map_props = {}

    def contains(self, prop_name: str) -> bool:
        return prop_name in self.map_props

    def get_keys(self) -> list[str]:
        return list(self.map_props.keys())

    def get(self, prop_name) -> typing.Optional[property_value.PropertyValue]:
        if prop_name in self.map_props:
            return self.map_props[prop_name]
        else:
            return None

    def get_int_value(self, prop_name: str) -> int:
        pv: typing.Optional[property_value.PropertyValue] = self.get(prop_name)
        if pv is not None and pv.is_int():
            return pv.get_int_value()
        else:
            return 0

    def get_bool_value(self, prop_name: str) -> bool:
        pv: typing.Optional[property_value.PropertyValue] = self.get(prop_name)
        if pv is not None and pv.is_bool():
            return pv.get_bool_value()
        else:
            return False

    def get_string_value(self, prop_name: str) -> str:
        pv: typing.Optional[property_value.PropertyValue] = self.get(prop_name)
        if pv is not None and pv.is_string():
            return pv.get_string_value()
        else:
            return ""

    def write_to_file(self, file_path: str) -> bool:
        success = False
        s = self.to_string()
        if len(s) > 0:
            success = utils.file_write_all_text(file_path, s)
        return success

    def count(self) -> int:
        return len(self.map_props)

    def to_string(self) -> str:
        prop_string: str = ""
        for key in self.map_props:
            pv = self.map_props[key]
            if pv.is_bool():
                if pv.get_bool_value():
                    value = PS_VALUE_TRUE
                else:
                    value = PS_VALUE_FALSE
                prop_string += "%s|%s|%s\n" % (PS_TYPE_BOOL, key, value)
            elif pv.is_string():
                prop_string += "%s|%s|%s\n" % (PS_TYPE_STRING, key, pv.get_string_value())
            elif pv.is_int():
                prop_string += "%s|%s|%d\n" % (PS_TYPE_INT, key, pv.get_int_value())

        return prop_string


def read_from_file(file_path: str) -> typing.Optional[PropertySet]:
    file_contents = utils.file_read_all_text(file_path)
    if file_contents is not None and len(file_contents) > 0:
        file_lines = file_contents.split("\n")
        ps: PropertySet = PropertySet()

        for file_line in file_lines:
            stripped_line = file_line.strip()
            if len(stripped_line) > 0:
                fields = stripped_line.split("|")
                if len(fields) == 3:
                    data_type = fields[0]
                    prop_name = fields[1]
                    prop_value = fields[2]

                    if len(data_type) > 0 and len(prop_name) > 0 and len(prop_value) > 0:
                        if data_type == PS_TYPE_BOOL:
                            if prop_value == PS_VALUE_TRUE or prop_value == PS_VALUE_FALSE:
                                bool_value = prop_value == PS_VALUE_TRUE
                                ps.add(prop_name, property_value.new_bool_property_value(bool_value))
                            else:
                                print("error: invalid value for type bool '%s'" % data_type)
                                return None
                        elif data_type == PS_TYPE_STRING:
                            ps.add(prop_name, property_value.new_string_property_value(prop_value))
                        elif data_type == PS_TYPE_INT:
                            try:
                                int_value = int(prop_value)
                                ps.add(prop_name, property_value.new_int_property_value(int_value))
                            except ValueError:
                                print("error: unable to convert property %s value (%s) to integer" % (
                                prop_name, prop_value))
                                return None

        if ps.count() > 0:
            return ps
    else:
        print("error: unable to read data from file '%s'" % file_path)
        return None
