import inspect
import maya.cmds as cmds
import re

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
    module_classes = [name for name, obj in inspect.getmembers(package) if inspect.isclass(obj) and name not in excluded_classes]
    return module_classes

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

def kwarg_to_dict(**kwargs):
    return kwargs

def uncapitalize(string:str):
  return string[0].lower() + string[1:]

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