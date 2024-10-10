import utils.node_wrapper as nw
import system.component_enum as component_enum

class NodeData(list):
    def __init__(self, *args):
        self.node_attr_list = []

        self.extend_attr_data(*args)

    def extend_attr_data(self, *args):
        if len(args) > 0 and isinstance(args[0], NodeData):
            args = args[0].node_attr_list
        else:
            args = [data for data in args if isinstance(data, AttrData)]
        self.node_attr_list.extend(args)

    def add_attr_data_attributes(self, node:nw.Node):
        # adding attrs
        num_children_dict = self.__get_num_children_dict()

        for data in self.node_attr_list:
            if data.do_add_attr:

                if data.name in num_children_dict.keys():
                    data.add_attr_kwargs["numberOfChildren"] = num_children_dict[data.name]

                if data.type == "compound" and not data.name in num_children_dict.keys():
                    continue

                node.add_attr(long_name=data.name, type=data.type, **data.add_attr_kwargs)

        # setting attrs and locking
        for data in self.node_attr_list:
            # dealing with attr value
            if data.value is not None:
                if isinstance(data.value, nw.Attr):
                    data.value >> node[data.name]
                else:
                    node[data.name] = data.value

            # locking
            if data.locked:
                node[data.name].set_locked(True)

    def publish_attr_data_attributes(self, node:nw.Node):
        container_node = node.get_container_node()

        if container_node is None:
            return
        for data in self.node_attr_list:
            if data.publish != False:
                if node.has_attr(data.name):
                    if isinstance(data.publish, str):
                        container_node.publish_attr(node[data.name], data.publish)
                    else:
                        container_node.publish_attr(node[data.name], data.name)

    def __get_num_children_dict(self):
        num_children_dict = {}
        for data in self.node_attr_list:
            attr_kwargs = data.add_attr_kwargs
            if "parent" in attr_kwargs.keys():
                parent_name = attr_kwargs["parent"]
                if parent_name not in num_children_dict.keys():
                    num_children_dict[parent_name] = 1
                else:
                    num_children_dict[parent_name] = num_children_dict[parent_name] + 1

        return num_children_dict

class AttrData:
    def __init__(self, attr_name, attr_type=None, attr_value=None, attr_publish=False, attr_locked=False, attr_keyable=False, attr_alias=None, **add_attr_kwargs):
        self.name = attr_name
        self.type = attr_type
        self.publish = attr_publish
        self.value = attr_value
        self.locked = attr_locked
        self.keyable = attr_keyable
        self.alias = attr_alias
        self.do_add_attr = self.type is not None

        self.add_attr_kwargs = add_attr_kwargs
        
        if not isinstance(self.type, str):
            enum_class = component_enum.get_enum_item_class(self.type)
            if enum_class is not None:
                enum_data = self.type
                self.type = "enum"
                self.add_attr_kwargs["enumName"] = enum_class.maya_enum_str()

                index = component_enum.get_index_of_item(enum_data)
                if index is not None:
                    self.value = index

            elif self.type is not None:
                raise RuntimeError("type is suppose to be of type string")
            
class HierData:
    hierarchy = "hierarchy"
    hier_name = "hierName"
    hier_parent_matrix = "hierParentMatrix"
    hier_parent_init_matrix = "hierParentInitMatrix"

    input_xform = "inputXform"
    input_xform_name = "inputXformName" 
    input_init_matrix = "inputInitMatrix"
    input_world_matrix = "inputWorldMatrix"

    output_xform = "outputXform"
    output_xform_name = "outputXformName" 
    output_init_matrix = "outputInitMatrix"
    output_world_matrix = "outputWorldMatrix"

    @classmethod
    def is_hier_attr(cls):
        pass
    
    @classmethod
    def get_input_attr_data(cls):
        return NodeData(
            AttrData(cls.hierarchy, attr_type="compound", parent="input"),
            AttrData(cls.hier_name, attr_type="string", parent=cls.hierarchy),
            AttrData(cls.hier_parent_matrix, attr_type="matrix", parent=cls.hierarchy),
            AttrData(cls.hier_parent_init_matrix, attr_type="matrix", parent=cls.hierarchy),

            AttrData(cls.input_xform, attr_type="compound", parent=cls.hierarchy, multi=True),
            AttrData(cls.input_xform_name, attr_type="string", parent=cls.input_xform),
            AttrData(cls.input_init_matrix, attr_type="matrix", parent=cls.input_xform),
            AttrData(cls.input_world_matrix, attr_type="matrix", parent=cls.input_xform),
        )
    
    @classmethod
    def get_output_attr_data(cls):
        return NodeData(
            AttrData(cls.output_xform, attr_type="compound", parent="output", multi=True),
            AttrData(cls.output_xform_name, attr_type="string", parent=cls.output_xform),
            AttrData(cls.output_init_matrix, attr_type="matrix", parent=cls.output_xform),
            AttrData(cls.output_world_matrix, attr_type="matrix", parent=cls.output_xform),
        )
    
class ComponentAttrData:
    def __init__(self, attr, attr_value):
        self.attr = attr
        self.attr_value = attr_value

    def __str__(self) -> str:
        return f"<ComponentAttrData> {self.attr}: {self.attr_value}"