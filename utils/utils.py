import inspect
import maya.cmds as cmds
import re
import math
from maya.api import OpenMaya as om2

def camel_to_snake(camel_str):
    """Camel case to snake case.

    Args:
        camel_str (str):

    Returns:
        str:
    """
    # and insert an underscore between them, then convert to lowercase
    snake_str = re.sub(r'(?<!^)(?=[A-Z])', '_', camel_str).lower()
    if snake_str.find("f_k") >= 0:
        snake_str = snake_str.replace("f_k", "fk")
    if snake_str.find("i_k") >= 0:
        snake_str = snake_str.replace("i_k", "ik")
    return snake_str

def snake_to_camel(snake_str):
    """Snake case to camel case

    Args:
        snake_str (str):

    Returns:
        str:
    """
    # Split the string by underscores
    if snake_str.find("fk") > 0:
        snake_str = snake_str.replace("fk","FK")
    if snake_str.find("ik") > 0:
        snake_str = snake_str.replace("ik","IK")
    components = snake_str.split('_')
    # Capitalize the first letter of each component except the first one, and join them
    camel_case_str = components[0] + ''.join(x.title() for x in components[1:])
    return camel_case_str

import utils.node_wrapper as nw
def map_to_container(node:nw.Node, node_message_name:str, container_message_name:str ="container_node"):
    """Maps the node to the container by creating an attribute on both and connectiong
    them

    Args:
        node (nw.Node): 
        node_message_name (str): 
        container_message_name (str, optional): Defaults to "container_node".
    """
    container = node.get_container_node()

    if container is not None:
        node.add_attr(long_name=container_message_name, type="message")
        container.add_attr(long_name=node_message_name, type="message")
        container[node_message_name] >> node[container_message_name]

def get_classes_from_package(package, excluded_classes:list=[]):
    """Gets the classes from package

    Args:
        package (type):
        excluded_classes (list, optional): classes that won't be included. Defaults to [].

    Returns:
        list: list of packages
    """
    module_classes = [(name, obj) for name, obj in inspect.getmembers(package) if inspect.isclass(obj) and name not in excluded_classes]
    module_names = [x[0] for x in module_classes]
    module_classes = [x[1] for x in module_classes]
    return module_names, module_classes

def strip_trailing_numbers(input_string:str):
    """Strip trailing numbers in string

    Args:
        input_string (str):

    Returns:
        str: beginnning of string without numbers
    """
    return re.sub(r'\d+$', '', input_string)

def get_trailing_numbers(input_string:str):
    """Get trailing number from string

    Args:
        input_string (str):

    Returns:
        str:
    """
    match = re.search(r'\d+$', input_string)
    if match:
        return int(match.group())
    else:
        return ""
    
def get_max_trailing_number(input_str_list):
    """Gets max trailing number from list of strings

    Args:
        input_str_list (list(st)):

    Returns:
        int:
    """
    input_str_list = [get_trailing_numbers(x) for x in input_str_list]
    input_str_list = [float(x) for x in input_str_list if x != ""]
    if input_str_list == []:
        return 0
    return max(input_str_list)

def class_type_to_str(class_type:type):
    """Takes a class and makes it into a string

    Args:
        class_type (type):

    Returns:
        str:
    """
    if not isinstance(class_type, type) and not re.search(r"<class\s+'([^']*)'>", str(class_type)):
        return None
    pattern = r"'([^']*)'"

    match = re.search(pattern, str(class_type))

    if match:
        return match.group(1)
    else:
        return ""
def string_to_class(class_str:str):
    """Takes a string and tries to makes it into a class

    Args:
        class_str (str):

    Returns:
        type:
    """
    if re.search(r"<class\s+'([^']*)'>", str(class_str)):
        class_str = class_type_to_str(class_str)

    module_list = class_str.split(".")

    mod = __import__(module_list[0], {}, {}, [module_list[0]])
    module_list.pop(0)

    for module in module_list:
        if hasattr(mod, module):
            mod = getattr(mod, module)
        else:
            return None
    return mod

def kwargs_to_dict(**kwargs):
    """Function to make multilevel kwargs. Returns the dictionary created by
    the kwargs

    Returns:
        dict:
    """
    return kwargs

def uncapitalize(string:str):
    """Uncapitalize string

    Args:
        string (str):

    Returns:
        str:
    """
    return string[0].lower() + string[1:]

def unnest_dict(curr_dict:dict):
    """unnests dictionary to all have a depth of 1 dict. puts __ in between name
    ie. parent__child__grandchild as a unique key

    Args:
        curr_dict (dict):

    Returns:
        dict:
    """
    return_dict = {}

    # while there's still items in attr_kwargs
    while(len(curr_dict) > 0):
        item = curr_dict.popitem()
        key = item[0]
        data = item[1]
        
        #if its a dict put it back on to dict with new keys
        if isinstance(data, dict):
            for data_key in data:
                curr_dict[f"{key}__{data_key}"] = data[data_key]

        # if it's a list put it back on put it back 
        elif isinstance(data, list):
            if all(isinstance(x, (int, float, str)) for x in data):
                return_dict[key] = data
            else:
                for index, sub_data in enumerate(data):
                    curr_dict[f"{key}__{index}"] = sub_data

        else:
            return_dict[key] = data

    return return_dict

def get_rgb_from_index(index:int):
    """Gets rgb from maya's color index

    Args:
        index (int):

    Returns:
        list(float): 3 values making up the rgb of the color
    """
    return cmds.colorIndex(index, query=True)

def make_valid_maya_name(name:str):
    """Makes string into a maya name without throwing a warning

    Args:
        name (str):

    Returns:
        str: 
    """
    return name.replace("[", "_").replace("]", "").replace(" ", "_")

class Namespace:
    """Class of static functions to handle namespaces"""
    @classmethod
    def get_namespace(cls, name:str):
        """gets namespace from object name

        Args:
            name (str):

        Returns:
            str: namespace
        """
        if name.find(":") == -1:
            return ":"
        else:
            namespace = name.split("|")[-1].rpartition(":")[0]
            if namespace == "":
                return ":"
            return name.split("|")[-1].rpartition(":")[0]
    
    def get_parent_namespace(cls, name:str):
        """gets parent portion of the namespace

        Args:
            name (str):

        Returns:
            str: parent namespace
        """
        return cls.get_namespace(cls.get_namespace(name))
            
    @classmethod
    def strip_namespace(cls, name:str):
        """strip namespace from the object name

        Args:
            name (str):

        Returns:
            str: cleaned up name
        """
        if name.find(":") == -1:
            return name
        else:
            return name.rpartition(":")[-1]
    
    @classmethod
    def delete(cls, namespace:str):
        """delete namespace

        Args:
            namespace (str):
        """
        cmds.namespace(removeNamespace=namespace)

    @classmethod
    def exists(cls, namespace:str):
        """Returns if namespace exists

        Args:
            namespace (str): 

        Returns:
            bool:
        """
        return cmds.namespace(exists=namespace)
        
    @classmethod
    def strip_outer_colons(cls, namespace:str):
        """Strips outer colos of namespace

        Args:
            namespace (str):

        Returns:
            str:
        """
        return re.sub(r'^:+|:+$', '', namespace)
    
    @classmethod
    def add_outer_colons(cls, namespace:str):
        """Adds outer colons for namespace

        Args:
            namespace (str): _description_

        Returns:
            str:
        """
        return ":{}:".format(re.sub(r'^:+|:+$', '', namespace))
    
    @classmethod
    def add_namespace(cls, namespace:str):
        """Adds namespace

        Args:
            namespace (str):

        Returns:
            str:
        """
        # add an index at the end of a namespace
        cmds.namespace(addNamespace=cls.strip_outer_colons(namespace))
        return namespace
    
    @classmethod
    def child_namespaces(cls, namespace:str):
        """Returns list of child namespaces in given namespace

        Args:
            namespace (str):

        Returns:
            list: Child namespaces
        """
        cmds.namespace(setNamespace=namespace)
        child_namespaces = cmds.namespaceInfo(listOnlyNamespaces=True)
        cmds.namespace(setNamespace=":")

        if child_namespaces is None:
            return []
        return child_namespaces

    @classmethod
    def empty(cls, namespace:str):
        """Returns if namespace is empty of nodes and child namespaces

        Args:
            namespace (str):

        Returns:
            bool:
        """
        cmds.namespace(setNamespace=namespace)
        child_nodes = cmds.namespaceInfo(listOnlyDependencyNodes=True)
        child_namespaces = cmds.namespaceInfo(listOnlyNamespaces=True)
        cmds.namespace(setNamespace=":")

        if child_nodes is None and child_namespaces is None:
            return True
        return False
    
    @classmethod
    def equal_namespace(cls, namespace1:str, namespace2:str):
        """checks to see if namespaces are the same

        Args:
            namespace1 (str):
            namespace2 (str):

        Returns:
            bool:
        """
        return cls.strip_outer_colons(namespace1) == cls.strip_outer_colons(namespace2)

def identity_matrix():
    """Returns identity matrix in an array

    Returns:
        list:
    """
    return [
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0
    ]

def zero_matrix():
    """Returns zero matrix in an array

    Returns:
        list:
    """
    return [0.0 for x in range(16)]

def translate_to_matrix(translation):
    """Returns translation matrix in an array

    Args:
        translation (list): list of values for translation x, y, z

    Returns:
        list:
    """
    matrix = identity_matrix()
    matrix[12] = translation[0]
    matrix[13] = translation[1]
    matrix[14] = translation[2]

    return matrix

def scale_matrix(scale):
    """Returns translation matrix in an array

    Args:
        translation (list): list of values for translation x, y, z

    Returns:
        list:
    """
    matrix = identity_matrix()
    matrix[0] = scale[0]
    matrix[5] = scale[1]
    matrix[10] = scale[2]

    return matrix

class Matrix(om2.MMatrix):
    """Class for matrix operations derived from MMatrix"""
    def __init__(self, *args):
        """Initializes with list of values up to 16

        Args:
            args: list of values to add, if first one is nw.Attr gets values
            from that

        """
        if len(args) > 0 and isinstance(args[0], nw.Attr):
            if args[0].value is None:
                
                super(Matrix, self).__init__(zero_matrix())
            else:
                super(Matrix, self).__init__(args[0].value)
        elif len(args) == 16:
            super(Matrix, self).__init__(args)
        else:
            super(Matrix, self).__init__(*args)

    def get(self, r, c):
        """Gets value in cell

        Args:
            r (int): row
            c (int): column

        Returns:
            float:
        """
        return self[r * 4 + c]

    def setT(self, t):
        """Sets transform matrix

        Args:
            t (list): sets x,y,z transform values
        """
        self[12] = t[0]
        self[13] = t[1]
        self[14] = t[2]

    def __str__(self):
        """Returns string of translate, rotate, and scale values

        Returns:
            str:
        """
        # values = [x for x in self.transpose()]
        # return"[[{},{},{},{}],\n [{}, {}, {}, {}],\n [{}, {}, {}, {}],\n [{}, {}, {}, {}]]".format(*values)
        return "Translate: {}, {}, {} | Rotate: {}, {}, {} | Scale: {}, {}, {}".format(*self.translate(), *self.rotate(), *self.scale())
    
    def rotate(self):
        """Gets rotation values

        Returns:
            list:
        """
        return self.as_degrees()

    def translate(self):
        """Gets translate values

        Returns:
            list:
        """
        return self[12], self[13], self[14]

    def scale(self):
        """Gets Scale values

        Returns:
            list:
        """
        return om2.MVector(self.axis(0)).length(), om2.MVector(self.axis(1)).length(), om2.MVector(self.axis(2)).length()

    def axis(self, index):
        """returns a value column of the matrix

        Args:
            index (int):

        Returns:
            list: matrix column
        """
        i = index * 4
        return self[i], self[i + 1], self[i + 2]

    def as_radians(self):
        """Gets rotation as radians

        Returns:
            list:
        """
        rx, ry, rz, ro = om2.MTransformationMatrix(self).rotationComponents(asQuaternion=False)
        return rx, ry, rz

    def as_degrees(self):
        """Gets rotation as degrees

        Returns:
            list:
        """
        rx, ry, rz, ro = om2.MTransformationMatrix(self).rotationComponents(asQuaternion=False)
        return math.degrees(rx), math.degrees(ry), math.degrees(rz)

    # def rotation(self):
    #     return om2.Euler(om2.MTransformationMatrix(self).rotation())

    def quaternion(self):
        """Gets quaternion values

        Returns:
            list:
        """
        return om2.QuaternionOrPoint().setValue(self)
