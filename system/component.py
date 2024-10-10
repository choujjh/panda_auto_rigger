import utils.node_wrapper as nw
import system.component_data as component_data
import system.component_enum as component_enum
import re

import utils.utils as utils

import maya.cmds as cmds

def get_component(container_node):
    if container_node is None:
        return None
    if container_node.has_attr("componentClass"):
        component_class = utils.string_to_class(container_node["componentClass"].value)
        return component_class(container_node)
    


class Component():
    component_type = component_enum.ComponentTypes.component
    root_transform_name = None
    class_namespace = "component"
    has_hier_attrs = False

    def __init__(self, container_node=None, parent_container_node=None):
        # self.container_node = container_node
        self.parent_container_node = parent_container_node
        self.__node_data_cache = {}
        self.__namespace_cache = {"full_namespace":"", "short_namespace":"", "instance_namespace":"", "hier_side":"", "instance_name":""}
        self.class_name = utils.class_type_to_str(type(self))
        if container_node is not None:
            self.__node_data_cache["container_node"] = container_node
    def __get_node_data_from_cache(self, key):
        if key not in self.__node_data_cache.keys():
            self.__node_data_cache[key] = utils.get_first_connected_node(self.container_node[key], as_source=True)
        
        return self.__node_data_cache[key]

    # node property
    @property 
    def container_node(self)->nw.Container:
        if "container_node" in self.__node_data_cache.keys():
            return self.__node_data_cache["container_node"]
    @property 
    def input_node(self)->nw.Node:
        if self.container_node is not None:
            return self.__get_node_data_from_cache("input_node")
    @property 
    def output_node(self)->nw.Node:
        if self.container_node is not None:
            return self.__get_node_data_from_cache("output_node")
    @property 
    def transform_node(self)->nw.Node:
        if type(self).root_transform_name is not None:
            return self.input_node

    #namespace functions
    @property
    def full_namespace(self):
        self.__update_full_namespace()
        return self.__namespace_cache["full_namespace"]
    @property
    def short_namespace(self):
        self.__update_short_namespace()
        return self.__namespace_cache["short_namespace"]
    @property
    def instance_namespace(self):
        self.__update_instance_namespace()
        return self.__namespace_cache["instance_namespace"]
    def __update_full_namespace(self):
        parent_container = None
        if self.container_node is not None:
            parent_container = self.container_node.get_container_node()
        short_namespace = self.short_namespace
        full_namespace = ""
        cached_full_namespace = self.__namespace_cache["full_namespace"]
        if parent_container is None:
            if cached_full_namespace.find(short_namespace) != 1:
                full_namespace = f":{short_namespace}"
        else:
            parent_namespace = utils.Namespace.get_namespace(str(parent_container))
            if cached_full_namespace.find(parent_namespace) != 0:
                full_namespace = f"{utils.Namespace.get_namespace(str(parent_container))}:{short_namespace}"
            else:
                cached_full_namespace = cached_full_namespace.replace(parent_namespace, "", 1)
                if cached_full_namespace.find(short_namespace) != 1:
                    full_namespace = f"{utils.Namespace.get_namespace(str(parent_container))}:{short_namespace}"
                    
        if full_namespace != "":
            self.__namespace_cache["full_namespace"] = full_namespace
    def __update_short_namespace(self):
        instance_namespace = self.instance_namespace
        short_namespace = ""

        if instance_namespace is not None and instance_namespace != "":
            if not self.__namespace_cache["short_namespace"].startswith(f"{instance_namespace}__"):
                short_namespace = f"{instance_namespace}__{type(self).class_namespace}"
        else:
            if self.__namespace_cache["short_namespace"] != type(self).class_namespace:
                short_namespace = type(self).class_namespace

        if short_namespace != "":
            self.__namespace_cache["short_namespace"] = short_namespace
    def __update_instance_namespace(self):
        instance_namespace = ""

        if self.input_node is None:
            return

        side = None
        if self.input_node.has_attr("hierSide"):
            side = self.input_node["hierSide"].value
            if side != self.__namespace_cache["hier_side"]:
                self.__namespace_cache["hier_side"] = side
                
                if side is not None and side != "":
                    instance_namespace = f"{component_enum.CharacterSide.get(side).value}_"

        instance_name = None
        if self.input_node.has_attr("instanceName"):
            instance_name = self.input_node["instanceName"].value
            if instance_name != self.__namespace_cache["instance_name"]:
                self.__namespace_cache["instance_name"] = instance_name
                
                if instance_name is not None and instance_name!= "":
                    instance_namespace = f"{instance_namespace}{instance_name}"

        if instance_namespace != "":
            self.__namespace_cache["instance_namespace"] = instance_namespace

    # node add attr data
    def _get_input_node_attr_data(self) -> component_data.NodeData:
        node_data =  component_data.NodeData(
            component_data.AttrData(attr_name="input", attr_type="compound", attr_publish=True),
            component_data.AttrData(attr_name="buildData", attr_type="compound", attr_publish=True),
            component_data.AttrData(attr_name="componentClass", attr_type="string", attr_value=self.class_name, attr_locked=True, parent="buildData"),
            component_data.AttrData(attr_name="componentType", attr_type=type(self).component_type, attr_locked=True, parent="buildData"),
            component_data.AttrData(attr_name="instanceName", attr_type="string", parent="buildData"),
        )
        if type(self).root_transform_name is not None:
            node_data.extend_attr_data(
                component_data.AttrData(attr_name="offsetParentMatrix", attr_publish="offsetMatrix"),
                component_data.AttrData(attr_name="worldMatrix[0]", attr_publish="worldMatrix"),
            )
        if type(self).has_hier_attrs:
            node_data.extend_attr_data(component_data.HierData.get_input_attr_data())
        return node_data
    def _get_output_node_attr_data(self) -> component_data.NodeData:
        node_data = component_data.NodeData(
            component_data.AttrData(attr_name="output", attr_type="compound", attr_publish=True),
        )
        if type(self).has_hier_attrs:
            node_data.extend_attr_data(component_data.HierData.get_output_attr_data())
        
        return node_data
    def _get_container_node_attr_data(self) -> component_data.NodeData:
        return component_data.NodeData()

    # creating nodes
    def __create_base_nodes(self):
        # input node
        if type(self).root_transform_name is not None:
            input_node = nw.create_node("transform", type(self).root_transform_name)
        else:
            input_node = nw.create_node("network", "input")
        input_node_attr_data = self._get_input_node_attr_data()
        input_node_attr_data.add_attr_data_attributes(input_node)

        # output node
        output_node = nw.create_node("network", "output")
        output_node_attr_data = self._get_output_node_attr_data()
        output_node_attr_data.add_attr_data_attributes(output_node)

        # container node
        self.__node_data_cache["container_node"] = nw.create_node("container", "component_container")
        container_node_attr_data = self._get_container_node_attr_data()
        container_node_attr_data.add_attr_data_attributes(self.container_node)
        if self.parent_container_node is not None:
            self.parent_container_node.add_nodes(self.container_node)

        # add to container
        self.container_node.add_nodes(input_node, output_node)
        
        # map to container
        utils.map_to_container(input_node, node_message_name="input_node")
        utils.map_to_container(output_node, node_message_name="output_node")

        input_node_attr_data.publish_attr_data_attributes(input_node)
        output_node_attr_data.publish_attr_data_attributes(output_node)
        container_node_attr_data.publish_attr_data_attributes(self.container_node)

        # renaming to nodes
        self.rename_nodes()

    def create_component(self, **initial_attr_kwargs):
        if self.container_node is None:
            self.initialize_component(**initial_attr_kwargs)
            self.build_component()

    def initialize_component(self, **initial_attr_kwargs):
        if self.container_node is None:
            self.__create_base_nodes()
            self.__initialize_attrs(initial_attr_kwargs)

    def build_component(self):
        if type(self).has_hier_attrs:
            self.xform_override_function()

    def xform_override_function(self):
        for index, attr in enumerate(self.input_node[component_data.HierData.input_xform]):
            attr[component_data.HierData.input_xform_name] >> self.output_node[component_data.HierData.output_xform][index][component_data.HierData.output_xform_name]
            attr[component_data.HierData.input_init_matrix] >> self.output_node[component_data.HierData.output_xform][index][component_data.HierData.output_init_matrix]

    # initialize kwargs
    def __initialize_attrs(self, attr_kwargs):
        attr_kwargs = self._modify_attr_kwargs(attr_kwargs)

        for key in attr_kwargs:
            attr_data = attr_kwargs[key]
            if attr_data is not None:
                if isinstance(attr_data.attr_value, nw.Attr):
                    attr_data.attr_value >> attr_data.attr
                else:
                    attr_data.attr.set(attr_data.attr_value)
    def _modify_attr_kwarg_key(self, key):
        pattern = r'(_|\d+)'
    
        # Use re.split to split by the pattern and keep the delimiters (numbers)
        key = utils.snake_to_camel(key)
        return_key = [part for part in re.split(pattern, key) if part not in  ("__", "")]
        # return_key = [utils.snake_to_camel(part) for part in return_key]
        
        new_return_key = [return_key[0]]
        new_return_key.extend([f"[{utils.uncapitalize(part)}]" for part in return_key[1:]])
        new_return_key = "".join(new_return_key)

        return new_return_key
    def _modify_attr_kwarg_value(self, attr_name, value):

        if not self.container_node.has_attr(attr_name):
            cmds.warning(f"not have attribute {self.container_node}.{attr_name} exists")
            return None
        
        attr = self.container_node[attr_name]

        if attr.attr_type == "enum" and component_enum.get_enum_item_class(value) is not None:
            value = component_enum.get_index_of_item(value)

        if not isinstance(value, component_data.ComponentAttrData):
            value = component_data.ComponentAttrData(attr, value)

        return value
    def _modify_attr_kwargs(self, attr_kwargs:dict):
        return_dict = {}

        # while there's still items in attr_kwargs
        while(len(attr_kwargs) > 0):
            item = attr_kwargs.popitem()
            key = item[0]
            data = item[1]
            
            if isinstance(data, dict):
                for data_key in data:
                    attr_kwargs[f"{key}__{data_key}"] = data[data_key]

            else:
                # modified keys
                new_key = self._modify_attr_kwarg_key(key)
                # modify values 
                return_dict[key] = self._modify_attr_kwarg_value(new_key, data)

        return return_dict

    # other class functions
    def insert_component(self, component, **component_kwargs):
        component_inst = component(parent_container_node=self.container_node)
        component_inst.create_component(**component_kwargs)

        return component_inst
    def rename_nodes(self):
        def rename_node(node, full_namespace):
            if not node.name.startswith(full_namespace):
                strip_namespace_node = utils.Namespace.strip_namespace(str(node))
                node.rename(f"{full_namespace}:{strip_namespace_node}")
        full_namespace = self.full_namespace
        prev_namespace = utils.Namespace.get_namespace(self.container_node.name)

        # if you need to add the namespace
        if full_namespace != prev_namespace:
            # if namespace doesn't exist
            if utils.Namespace.exists(full_namespace):
                parent_namespace = utils.Namespace.get_namespace(full_namespace)
                child_namespaces = [utils.Namespace.strip_namespace(x) for x in utils.Namespace.child_namespaces(parent_namespace)]
                # add something to instance namespace if it's none
                if self.input_node["instanceName"].value == "" or self.input_node["instanceName"].value is None:
                    self.input_node["instanceName"] = "temp"
                # getting just the instance_namespace portion of children namespaces
                child_namespaces = [x.split("__", 1)[0] for x in child_namespaces if x.startswith(utils.strip_trailing_numbers(self.instance_namespace))]
                if child_namespaces != []:
                    highest_trailing_number = utils.get_max_trailing_numbers(child_namespaces)
                    instance_name = utils.strip_trailing_numbers(self.input_node["instanceName"].value)
                    self.input_node["instanceName"] = f"{instance_name}{int(highest_trailing_number + 1)}"

                # give it a unique namespace by giving instance_namespace a new value
                full_namespace = self.full_namespace
            
            utils.Namespace.add_namespace(full_namespace)

        rename_node(self.container_node, full_namespace)
        for node in self.container_node.get_nodes():
            # TODO replace later with if it's a component not just a container
            if node.node_type != "container":
                rename_node(node, full_namespace)

        # check if nothing else in namespace delete
        if utils.Namespace.empty(prev_namespace):
            utils.Namespace.delete(prev_namespace)