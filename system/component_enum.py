from enum import Enum
import maya.cmds as cmds
# import maya.api.OpenMaya as om2
import utils.node_wrapper as nw
import utils.utils as utils

class MayaEnumAttr(Enum):
    """Class to give some nice functionality to help with enums in maya"""
    @classmethod
    def maya_enum_str(cls):
        """Creates maya string for adding it as an enum attribute

        Returns:
            str:
        """
        return_str = ""
        num_enums = len(cls)
        for i, enum in enumerate(cls):
            return_str += enum.name
            if i < num_enums - 1:
                return_str += ":"
        return return_str
    
    @classmethod
    def get(cls, index):
        """Get enum from index

        Args:
            index (int):

        Returns:
            enum: returns the enum
        """
        for i, curr_enum in enumerate(cls):
            if i == index:
                return curr_enum
            
    @classmethod
    def index_of(cls, enum):
        """Given an enum get the index of it in the enum

        Args:
            enum (enum):

        Returns:
            int: index
        """
        index = 0
        for item in cls:
            if item == enum:
                return index
            index += 1
    
    @ classmethod
    def get_enum_dict(cls):
        """Get a dictionary of name to value for the enum

        Returns:
            dict:
        """
        enum_dict = {data.name: data.value for data in cls}
        return enum_dict
            
    @classmethod
    def create_remap(cls, node_name:str, enum_dict=None):
        """Create maya node that uses the enum to map to its values

        Args:
            node_name (str):
            enum_dict (dic, optional): map of the results. Defaults to None.

        Returns:
            nw.Node: remap node
        """
        if enum_dict is None:
            enum_dict = cls.get_enum_dict()
        out_min = 0
        out_max = 0

        for key in enum_dict:
            value = enum_dict[key]
            if not isinstance(value, int) and isinstance(value, float):
                cmds.error("enum does not have numeric values")
            out_min = value
            out_max = value
            break
            

        # find max
        for key in enum_dict:
            value = enum_dict[key]
            if value < out_min:
                out_min = value
            if value > out_max:
                out_max = value

        map_len = len(enum_dict.keys())
        interval_len = 1.0/float(map_len-1)
        remap_node = nw.Node.create_node("remapValue", node_name)
        remap_node["outputMin"] = out_min
        remap_node["outputMax"] = out_max

        remap_node["inputMax"] = map_len - 1

        out_diff = out_max - out_min
        for index, key in enumerate(enum_dict.keys()):
            value = enum_dict[key] - out_min

            remap_node["value[{}].value_FloatValue".format(index)] = float(value)/out_diff
            remap_node["value[{}].value_Position".format(index)] = interval_len * index
            remap_node["value[{}].value_Interp".format(index)] = 1

        return remap_node
    
    @classmethod
    def long_name(cls, item):
        """Name item including class name

        Args:
            item (enum): 

        Returns:
            str:
        """
        return "utils.enum.{}.{}".format(type(item).__name__, item.name)
    
def get_enum_item_class(item)->MayaEnumAttr:
    """Gets enum class of item

    Args:
        item (enum):

    Returns:
        MayaEnumAttr:
    """
    import system.component_enum as component_enum
    for curr_enum_class in utils.get_classes_from_package(component_enum)[0]:
        curr_enum_class = getattr(component_enum, curr_enum_class)
        if isinstance(item, curr_enum_class) or item == curr_enum_class:
            return curr_enum_class

def get_index_of_item(item)->int:
    """gets index of item

    Args:
        item (enum):

    Returns:
        int: index
    """
    curr_enum_class = get_enum_item_class(item)
    if curr_enum_class == item:
        return None
    return curr_enum_class.index_of(item)
        
def get_item_long_name(item)->str:
    """Gets long name of item

    Args:
        item (enum):

    Returns:
        str:
    """
    curr_enum_class = get_enum_item_class(item)
    if curr_enum_class == item:
        return None
    return curr_enum_class.long_name(item)



class ComponentTypes(MayaEnumAttr):
    """Enum of different component types in the autorigger"""
    anim = 0
    character = 1
    component = 2
    control_setup = 3
    control = 4
    hier = 5
    matrix = 6
    motion = 7
    setup = 8


class Colors(MayaEnumAttr):
    """Enum of colors in the autorigger"""
    none = -1
    blue = 6
    dark_blue = 15
    dark_red = 11
    gold = 25
    green = 14
    light_blue = 18
    light_green = 19
    light_orange = 21
    light_pink = 20
    magenta = 9
    purple = 8
    red = 13
    yellow = 17

    @classmethod
    def create_remap(cls, name):
        enum_dict = cls.get_enum_dict()
        out_min = 0
        out_max = 0

        for key in enum_dict:
            value = enum_dict[key]
            if not isinstance(value, int) and not isinstance(value, float):
                cmds.error("enum does not have numeric values")
            out_min = value
            out_max = value
            break
            
        # find max
        for key in enum_dict:
            value = enum_dict[key]
            if value < out_min:
                out_min = value
            if value > out_max:
                out_max = value

        map_len = len(enum_dict.keys())
        interval_len = 1.0/float(map_len-1)
        remap_node = nw.Node.create_node("remapValue", name)
        remap_node["outputMin"] = out_min
        remap_node["outputMax"] = out_max

        remap_node["inputMax"] = map_len - 1

        out_diff = out_max - out_min
        for index, key in enumerate(enum_dict.keys()):
            value = enum_dict[key] - out_min

            remap_node["value[{}].value_FloatValue".format(index)] = float(value)/out_diff
            remap_node["value[{}].value_Position".format(index)] = interval_len * index
            remap_node["value[{}].value_Interp".format(index)] = 1

        return remap_node
        
class CharacterSide(MayaEnumAttr):
    """Enum of different sides in the autorigger"""
    none = "none"
    mid = "M"
    right = "R"
    left = "L"
    front = "Frnt"
    back = "Bck"
    top = "Top"
    bottom = "Btm"
    in_ = "In"
    out = "out"
    
    @classmethod
    def opposite(cls, side):
        """Gets the oppposite side

        Args:
            side (CharacterSide):

        Returns:
            CharacterSide: opposite side
        """
        opposite_dict = {
            cls.none: cls.none,
            cls.mid: cls.mid,

            cls.right: cls.left,
            cls.left: cls.right,

            cls.mid: cls.mid,

            cls.front: cls.back,
            cls.back: cls.front,

            cls.in_:cls.out,
            cls.out:cls.in_,

            cls.top: cls.bottom,
            cls.bottom: cls.top,
        }
        return opposite_dict[side]
    
    @classmethod
    def opposite_mapping(cls):
        enum_dict = {data.name: cls.index_of(cls.opposite(data)) for data in cls}
        return enum_dict
    
    @classmethod
    def maya_enum_str(cls):
        maya_str = super().maya_enum_str()
        maya_str = maya_str.replace("_", "")
        return maya_str
    
    @classmethod
    def create_remap(cls, node_name):
        return super().create_remap(node_name, enum_dict=cls.opposite_mapping())

class AxisEnums(MayaEnumAttr):
    """Enum of different axis"""
    x = [1.0, 0.0, 0.0]
    y = [0.0, 1.0, 0.0]
    z = [0.0, 0.0, 1.0]
    neg_x = [-1.0, 0.0, 0.0]
    neg_y = [0.0, -1.0, 0.0]
    neg_z = [0.0, 0.0, -1.0]

    @classmethod
    def other_axes(cls, axis):
        """Gets the other axis given an axis

        Args:
            axis (enum):

        Returns:
            _type_: _description_
        """
        index = cls.index_of(axis)
        if index < 3:
            other_index = [(index+1) % 3, (index+2) % 3]
        else:
            index = index - 3
            other_index = [((index+1) % 3) + 3, ((index+2) % 3) + 3]
        other_index = sorted(other_index)
        return [AxisEnums.get(other_index[0]), AxisEnums.get(other_index[1])]
    
    @classmethod
    def scale_vec(cls, axis):
        """gets the magnitude

        Args:
            axis (_type_): _description_

        Returns:
            _type_: _description_
        """
        axis = axis.value[:]
        for index in range(len(axis)):
            if axis[index] == 0:
                axis[index] = 1

        return axis
    
    @classmethod
    def opposite(cls, axis):
        """Gets the opposite axis

        Args:
            axis (AxisEnums):

        Returns:
            AxisEnums:
        """
        opposite_dict = {
            cls.x: cls.neg_x,
            cls.neg_x: cls.x,

            cls.y: cls.neg_y,
            cls.neg_y: cls.y,

            cls.z: cls.neg_z,
            cls.neg_z: cls.z,
        }

        return opposite_dict[axis]
    
    @classmethod
    def create_remap(cls, node_name):
        enum_dict = {data.name: cls.index_of(cls.opposite(data)) for data in cls}
        return super().create_remap(node_name, enum_dict)

class SelectorWeightTypes(MayaEnumAttr):
    """Enum for different interpolations"""
    wave = 0
    zipper = 1 