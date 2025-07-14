import inspect
import maya.cmds as cmds
import re
import math
from maya.api import OpenMaya as om2

def camel_to_snake(camel_str):
    # Find all instances where a lowercase letter is followed by an uppercase letter
    # and insert an underscore between them, then convert to lowercase
    snake_str = re.sub(r'(?<!^)(?=[A-Z])', '_', camel_str).lower()
    if snake_str.find("f_k") >= 0:
        snake_str = snake_str.replace("f_k", "fk")
    if snake_str.find("i_k") >= 0:
        snake_str = snake_str.replace("i_k", "ik")
    return snake_str

def snake_to_camel(snake_str):
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
def map_to_container(node:nw.Node, node_message_name, container_message_name="container_node"):
    container = node.get_container_node()

    if container is not None:
        node.add_attr(long_name=container_message_name, type="message")
        container.add_attr(long_name=node_message_name, type="message")
        container[node_message_name] >> node[container_message_name]

def get_first_connected_node(attr:nw.Attr, as_source=True, as_dest=True) -> nw.Node:
    
    connection_list = attr.get_connections(as_src=as_source, as_dest=as_dest)
    if len(connection_list) == 0:
        return None
    
    return connection_list[0].node

def get_classes_from_package(package, excluded_classes:list=[]):
    module_classes = [(name, obj) for name, obj in inspect.getmembers(package) if inspect.isclass(obj) and name not in excluded_classes]
    module_names = [x[0] for x in module_classes]
    module_classes = [x[1] for x in module_classes]
    return module_names, module_classes

def strip_trailing_numbers(input_string):
    return re.sub(r'\d+$', '', input_string)

def get_trailing_numbers(input_string):
    match = re.search(r'\d+$', input_string)
    if match:
        return int(match.group())
    else:
        return ""
    
def get_max_trailing_numbers(input_str_list):
    input_str_list = [get_trailing_numbers(x) for x in input_str_list]
    input_str_list = [float(x) for x in input_str_list if x != ""]
    if input_str_list == []:
        return 0
    return max(input_str_list)

def class_type_to_str(class_type):
    if not isinstance(class_type, type) and not re.search(r"<class\s+'([^']*)'>", str(class_type)):
        return None
    pattern = r"'([^']*)'"

    match = re.search(pattern, str(class_type))

    if match:
        return match.group(1)
    else:
        return ""
def string_to_class(class_str):
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
    return kwargs

def uncapitalize(string:str):
  return string[0].lower() + string[1:]

def unnest_dict(curr_dict:dict):
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

def get_transform_locked_attrs(transform_node):
    transform_attrs = ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "visibility"]

    if not isinstance(transform_node, nw.Node):
        transform_node = nw.Node(transform_node)

    return [transform_node[attr] for attr in transform_attrs if transform_node[attr].is_locked()]

def freeze_transform(transform:nw.Node):
    transform_locked_attrs = get_transform_locked_attrs(str(transform))

    for locked_attrs in transform_locked_attrs:
        locked_attrs.set_locked(False)
    scale = transform["scale"].value
    
    cmds.makeIdentity(str(transform), apply=True)

    if scale[0] * scale[1] * scale[2] < 0:
        shapes = [nw.Node(x) for x in cmds.listRelatives(str(transform), shapes=True)]
        for x in shapes:
            if x.node_type == "nurbsSurface":
                cmds.reverseSurface(str(x))
                x["opposite"] = False
            elif x.node_type == "mesh":
                cmds.polyNormal(str(x), normalMode=0, constructionHistory=False)
                x["opposite"] = False

    for locked_attrs in transform_locked_attrs:
        locked_attrs.set_locked(True)

    transform["rotatePivot"] = [0.0, 0.0, 0.0]
    transform["scalePivot"] = [0.0, 0.0, 0.0]

def short_name(obj_name:str):
    return obj_name.split("|")[-1]

def get_index_rgb(index:int):

    return cmds.colorIndex(index, query=True)

def make_valid_maya_name(name):
    return name.replace("[", "_").replace("]", "")

import system.component_enum as component_enum
def set_color(transform:nw.Node, color:component_enum.Colors):
    transform["overrideEnabled"] = True
    transform["overrideColor"] = color.value

class Namespace:
    @classmethod
    def get_namespace(cls, name):
        if name.find(":") == -1:
            return ":"
        else:
            namespace = name.split("|")[-1].rpartition(":")[0]
            if namespace == "":
                return ":"
            return name.split("|")[-1].rpartition(":")[0]
    
    def get_parent_namespace(cls, name):
        return cls.get_namespace(cls.get_namespace(name))
            
    @classmethod
    def strip_namespace(cls, name):
        if name.find(":") == -1:
            return name
        else:
            return name.rpartition(":")[-1]
    
    @classmethod
    def delete(cls, name):
        cmds.namespace(removeNamespace=name)

    @classmethod
    def exists(cls, name):
        return cmds.namespace(exists=name)
        
    @classmethod
    def strip_outer_colons(cls, namespace):
        return re.sub(r'^:+|:+$', '', namespace)
    
    @classmethod
    def add_outer_colons(cls, namespace):
        return ":{}:".format(re.sub(r'^:+|:+$', '', namespace))
    
    @classmethod
    def add_namespace(cls, namespace):
        # add an index at the end of a namespace
        cmds.namespace(addNamespace=cls.strip_outer_colons(namespace))
        return namespace
    
    @classmethod
    def child_namespaces(cls, namespace):
        cmds.namespace(setNamespace=namespace)
        child_namespaces = cmds.namespaceInfo(listOnlyNamespaces=True)
        cmds.namespace(setNamespace=":")

        if child_namespaces is None:
            return []
        return child_namespaces

    @classmethod
    def empty(cls, namespace):
        cmds.namespace(setNamespace=namespace)
        child_nodes = cmds.namespaceInfo(listOnlyDependencyNodes=True)
        child_namespaces = cmds.namespaceInfo(listOnlyNamespaces=True)
        cmds.namespace(setNamespace=":")

        if child_nodes is None and child_namespaces is None:
            return True
        return False
    
    @classmethod
    def equal_namespace(cls, namespace1, namespace2):
        return cls.strip_outer_colons(namespace1) == cls.strip_outer_colons(namespace2)

def identity_matrix():
    return [
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0
    ]

def zero_matrix():
    return [0.0 for x in range(16)]

def translate_to_matrix(translation):
    matrix = identity_matrix()
    matrix[12] = translation[0]
    matrix[13] = translation[1]
    matrix[14] = translation[2]

    return matrix

def scale_matrix(scale):
    matrix = identity_matrix()
    matrix[0] = scale[0]
    matrix[5] = scale[1]
    matrix[10] = scale[2]

    return matrix

class Matrix(om2.MMatrix):
    def __init__(self, *args):
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
        return self[r * 4 + c]

    def setT(self, t):
        self[12] = t[0]
        self[13] = t[1]
        self[14] = t[2]

    def __str__(self):
        # values = [x for x in self.transpose()]
        # return"[[{},{},{},{}],\n [{}, {}, {}, {}],\n [{}, {}, {}, {}],\n [{}, {}, {}, {}]]".format(*values)
        return "Translate: {}, {}, {} | Rotate: {}, {}, {} | Scale: {}, {}, {}".format(*self.asT(), *self.asR(), *self.asS())
    
    def asR(self):
        return self.asDegrees()

    def asT(self):
        return self[12], self[13], self[14]

    def asS(self):

        return om2.MVector(self.axis(0)).length(), om2.MVector(self.axis(1)).length(), om2.MVector(self.axis(2)).length()

    def axis(self, index):
        i = index * 4
        return self[i], self[i + 1], self[i + 2]

    def asRadians(self):
        rx, ry, rz, ro = om2.MTransformationMatrix(self).rotationComponents(asQuaternion=False)
        return rx, ry, rz

    def asDegrees(self):
        rx, ry, rz, ro = om2.MTransformationMatrix(self).rotationComponents(asQuaternion=False)
        return math.degrees(rx), math.degrees(ry), math.degrees(rz)

    def rotation(self):
        return om2.Euler(om2.MTransformationMatrix(self).rotation())

    def quaternion(self):
        return om2.QuaternionOrPoint().setValue(self)
