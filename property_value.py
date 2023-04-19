
PV_TYPE_INT = "int"
PV_TYPE_BOOL = "bool"
PV_TYPE_STRING = "str"


class PropertyValue(object):
    def __init__(self, data_type: str):
        self.data_type = data_type
        self.int_value = 0
        self.bool_value = False
        self.string_value = ""

    def get_int_value(self) -> int:
        if self.is_int():
            return self.int_value
        else:
            print("warning: calling get_int_value, but data type is '%s'" % self.data_type)
            return 0

    def get_bool_value(self) -> bool:
        if self.is_bool():
            return self.bool_value
        else:
            print("warning: calling get_bool_value, but data type is '%s'" % self.data_type)
            return False

    def get_string_value(self) -> str:
        if self.is_string():
            return self.string_value
        else:
            print("warning: calling get_string_value, but data type is '%s'" % self.data_type)
            return ""

    def is_int(self) -> bool:
        return self.data_type == PV_TYPE_INT

    def is_bool(self) -> bool:
        return self.data_type == PV_TYPE_BOOL

    def is_string(self) -> bool:
        return self.data_type == PV_TYPE_STRING


def new_int_property_value(int_value: int) -> PropertyValue:
    pv = PropertyValue(PV_TYPE_INT)
    pv.int_value = int_value
    return pv


def new_bool_property_value(bool_value: bool) -> PropertyValue:
    pv = PropertyValue(PV_TYPE_BOOL)
    pv.bool_value = bool_value
    return pv


def new_string_property_value(str_value: str) -> PropertyValue:
    pv = PropertyValue(PV_TYPE_STRING)
    pv.string_value = str_value
    return pv
