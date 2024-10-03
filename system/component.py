import utils.node_wrapper as nw
import system.component_data as comp_data



class Component():
    # component_type = utils_enum.ComponentTypes.component
    # _use_transform
    def __init__(self, container_node=None, parent_container_node=None):
        self.container_node = container_node
        self.parent_container_node = parent_container_node

    @property
    def input_node_data(self) -> comp_data.NodeData:
        node = nw.create_node("network", "input")


        return comp_data.NodeData(
            node,
            # comp_data.AddAttrData("input", attr_type="compound", attr_publish=True),
            # comp_data.AddAttrData(attr_name="buildData", attr_type="compound", attr_publish=True),
            comp_data.AddAttrData(attr_name="componentClass", attr_type="string", attr_value="testing", attr_publish=True, attr_locked=True),
            # comp_data.AddAttrData(attr_name="componentType", attr_type="enum", publish=True, parent="buildData"),
            comp_data.AddAttrData(attr_name="instanceName", attr_type="string", attr_publish=True),
        )
    
    @property
    def output_node_data(self):
        return []
    
    @property
    def container_node_data(self):
        return []

    def create_component(self, parent_container=None, **initial_attr_kwargs):
        if self.container_node is None:
            self.initialize_component(**initial_attr_kwargs)
            self.build_component()

    def initialize_component(self, **initial_attr_kwargs):
        if self.container_node is None:
            input_node_data = self.input_node_data
            input_node_data.add_node_attrs()
            input_node = input_node_data.node


    def build_component(self):
        if self.container_node is None:
            pass