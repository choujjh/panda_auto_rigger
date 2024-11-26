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
    
def control_setup_node(name="controlSetup") -> nw.Node:
    import component.control as control
    control_setup_node = nw.create_node("network", name)

    setup_node_data = component_data.NodeData(
        component_data.AttrData(attr_name="controlClass", attr_type="enum", enum_name=":".join(utils.get_classes_from_package(control))),
        component_data.AttrData(attr_name="instanceName", attr_type="string"),
        component_data.AttrData(attr_name="shapeColor", attr_type="enum", enum_name=component_enum.Colors.maya_enum_str()),
        component_data.AttrData(attr_name="attrs", attr_type="string", multi=True),
        component_data.AttrData(attr_name="lockAttrs", attr_type="compound"),
        component_data.AttrData(attr_name="lockDefaultAttrs", attr_type="bool", parent="lockAttrs"),
        component_data.AttrData(attr_name="lockTX", attr_type="bool", parent="lockAttrs"),
        component_data.AttrData(attr_name="lockTY", attr_type="bool", parent="lockAttrs"),
        component_data.AttrData(attr_name="lockTZ", attr_type="bool", parent="lockAttrs"),
        component_data.AttrData(attr_name="lockRX", attr_type="bool", parent="lockAttrs"),
        component_data.AttrData(attr_name="lockRY", attr_type="bool", parent="lockAttrs"),
        component_data.AttrData(attr_name="lockRZ", attr_type="bool", parent="lockAttrs"),
        component_data.AttrData(attr_name="lockSX", attr_type="bool", parent="lockAttrs"),
        component_data.AttrData(attr_name="lockSY", attr_type="bool", parent="lockAttrs"),
        component_data.AttrData(attr_name="lockSZ", attr_type="bool", parent="lockAttrs"),
        component_data.AttrData(attr_name="lockVis", attr_type="bool", parent="lockAttrs"),
        component_data.AttrData(attr_name="buildTranslate", attr_type="double3"),
        component_data.AttrData(attr_name="buildTranslateX", attr_type="double", parent="buildTranslate"),
        component_data.AttrData(attr_name="buildTranslateY", attr_type="double", parent="buildTranslate"),
        component_data.AttrData(attr_name="buildTranslateZ", attr_type="double", parent="buildTranslate"),
        component_data.AttrData(attr_name="buildRotate", attr_type="double3"),
        component_data.AttrData(attr_name="buildRotateX", attr_type="double", parent="buildRotate"),
        component_data.AttrData(attr_name="buildRotateY", attr_type="double", parent="buildRotate"),
        component_data.AttrData(attr_name="buildRotateZ", attr_type="double", parent="buildRotate"),
        component_data.AttrData(attr_name="buildScale", attr_type="double3"),
        component_data.AttrData(attr_name="buildScaleX", attr_type="double", parent="buildScale"),
        component_data.AttrData(attr_name="buildScaleY", attr_type="double", parent="buildScale"),
        component_data.AttrData(attr_name="buildScaleZ", attr_type="double", parent="buildScale"),
    )
    setup_node_data.add_attr_data_attributes(control_setup_node)

    return control_setup_node

class KwargToNode():
    def __init__(self, node, **attr_kwargs):
        self.set_node_attrs(node, **attr_kwargs)
    @classmethod
    def _modify_attr_kwarg_value(self, value):

        if component_enum.get_enum_item_class(value) is not None:
            value = component_enum.get_index_of_item(value)

        elif isinstance(value, type):
            value = value.__name__

        return value
    @classmethod
    def set_node_attrs(cls, node, **attr_kwargs):
        filtered_dict = cls._modify_attr_kwargs(attr_kwargs)

        for key in filtered_dict:
            if not node.has_attr(key):
                cmds.warning(f"{node}.{key} attr does not exist")
                continue
            dict_value = filtered_dict[key]
            if dict_value is not None:
                if isinstance(dict_value, nw.Attr):
                    dict_value >> node[key]
                else:
                    node[key].set(cls._modify_attr_kwarg_value(dict_value))
    @classmethod
    def _modify_attr_kwargs(cls, attr_kwargs:dict):
        return_dict = {}

        # while there's still items in attr_kwargs
        while(len(attr_kwargs) > 0):
            item = attr_kwargs.popitem()
            key = item[0]
            data = item[1]
            
            if isinstance(data, dict):
                for data_key in data:
                    attr_kwargs[f"{key}__{data_key}"] = data[data_key]

            elif isinstance(data, list):
                for index, sub_data in enumerate(data):
                    attr_kwargs[f"{key}__{index}"] = sub_data

            else:
                # modified keys
                new_key = cls._modify_attr_kwarg_key(key)
                # modify values 
                return_dict[new_key] = data

        return return_dict
    @classmethod
    def _modify_attr_kwarg_key(cls, key):
        pattern = r'(_|\d+)'
    
        # Use re.split to split by the pattern and keep the delimiters (numbers)
        key = utils.snake_to_camel(key)
        return_key = [part for part in re.split(pattern, key) if part not in  ("__", "")]
        # return_key = [utils.snake_to_camel(part) for part in return_key]
        
        new_return_key = [return_key[0]]
        new_return_key.extend([f"[{utils.uncapitalize(part)}]" for part in return_key[1:]])
        new_return_key = "".join(new_return_key)

        return new_return_key


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

    # node attr
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
    def create_component(self, **initial_attr_kwargs):
        if self.container_node is None:
            self.initialize_component(**initial_attr_kwargs)
            self.build_component()
    def initialize_component(self, **initial_attr_kwargs):
        if self.container_node is None:
            self.__create_base_nodes()
            KwargToNode(self.container_node, **initial_attr_kwargs)
    def build_component(self):
        if type(self).has_hier_attrs:
            self.xform_override_function()
    def __create_base_nodes(self):
        # input node
        if type(self).root_transform_name is not None:
            input_node = nw.create_node("transform", type(self).root_transform_name)
        else:
            input_node = nw.create_node("network", "input")
        input_node_attr_data = self._get_input_node_attr_data()
        input_node_attr_data.add_attr_data_attributes(input_node)

        # output node
        output_node_attr_data = self._get_output_node_attr_data()
        has_output_node = len(output_node_attr_data.node_attr_list) > 1
        if has_output_node:
            output_node = nw.create_node("network", "output")
            output_node_attr_data = self._get_output_node_attr_data()
            output_node_attr_data.add_attr_data_attributes(output_node)

        # container node
        self.__node_data_cache["container_node"] = nw.create_node("container", "component_container")
        container_node_attr_data = self._get_container_node_attr_data()
        container_node_attr_data.add_attr_data_attributes(self.container_node)
        if self.parent_container_node is not None:
            self.parent_container_node.add_nodes(self.container_node)

        # add to container -> map to container -> publish attributes
        # if output
        component_nodes = [input_node]
        if has_output_node:
            component_nodes.append(output_node)

        self.container_node.add_nodes(*component_nodes)

        utils.map_to_container(input_node, node_message_name="input_node")
        if has_output_node:
            utils.map_to_container(output_node, node_message_name="output_node")
            
            output_node_attr_data.publish_attr_data_attributes(output_node)
        
        input_node_attr_data.publish_attr_data_attributes(input_node)
        container_node_attr_data.publish_attr_data_attributes(self.container_node)

        # renaming to nodes
        self.rename_nodes()
    def xform_override_function(self):
        for index, attr in enumerate(self.input_node[component_data.HierData.input_xform]):
            attr[component_data.HierData.input_xform_name] >> self.output_node[component_data.HierData.output_xform][index][component_data.HierData.output_xform_name]
            attr[component_data.HierData.input_init_matrix] >> self.output_node[component_data.HierData.output_xform][index][component_data.HierData.output_init_matrix]
    
    # other functions
    def insert_component(self, component, parent_transform = None, **component_kwargs):
        component_inst = component(parent_container_node=self.container_node)
        component_inst.create_component(**component_kwargs)

        if parent_transform is None and self.transform_node is not None:
            parent_transform = self.transform_node

        if component_inst.transform_node is not None and parent_transform is not None:
            cmds.parent(str(component_inst.transform_node), str(parent_transform), relative=True)

        return component_inst
    def add_nodes(self, *nodes):
        self.container_node.add_nodes(*nodes)
        self.rename_nodes()
    def rename_nodes(self):
        def rename_node(node, full_namespace):
            if not node.name.startswith(full_namespace):
                strip_namespace_node = utils.Namespace.strip_namespace(str(node))
                node.rename(f"{full_namespace}:{strip_namespace_node}")
        full_namespace = self.full_namespace
        prev_namespace = utils.Namespace.get_namespace(self.container_node.name)

        # if you need to add the namespace
        if not utils.Namespace.equal_namespace(full_namespace, prev_namespace):
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

    def promote_attr(self, *attrs, **control_kwargs):
        control_setup = control_setup_node()
        self.add_nodes(control_setup)

        for index, attr in enumerate(attrs):
            control_setup[f"attrs[{index}]"] = attr.attr_name
        
        KwargToNode(control_setup, **control_kwargs)

        # create control
        # connect it up
        # re publish if needs be

        
