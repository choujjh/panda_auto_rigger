from typing import Union

import system.component_enum_data as component_enum_data
import system.base_component as base_comp
import utils.node_wrapper as nw
import system.component_data as component_data
import utils.utils as utils
import maya.cmds as cmds


def axis_vec_choice_node(choice_node_name, enum_attr:nw.Attr=None):
    """creates a choice node for axis vectors. allows enum to generate a vector

    Args:
        choice_node_name (str):

    Returns:
        nw.Node: choice node
    """
    axis_vec_container = AxisVector.instance().container_node
    choice_node = nw.create_node("choice", name=f"{choice_node_name}AxisVecChoice")

    for index, item in enumerate(component_enum_data.AxisEnum):
        
        axis_vec_container[AxisVector._OUT_AXIS][item.name] >> choice_node["input"][index]
    if enum_attr is not None:
        enum_attr  >> choice_node["selector"]

    return choice_node

class AxisVector(base_comp.SingletonComponent):
    """Component of axis vectors that creates vectors from the enum"""
    class_namespace="axis_vec_manager"
    _OUT_AXIS = "axis"

    def __init__(self, container_node = None):
        super().__init__(container_node)
        self.self_component = None
    
    def _output_build_attr_data(self):
        node_data = super()._output_build_attr_data()

        attr_data = [component_data.AttrData(self._OUT_AXIS, type_="compound", parent=self._OUT)]
        for item in component_enum_data.AxisEnum:
            attr_data.append(component_data.AttrData(item.name, type_="double3", parent=self._OUT_AXIS))
            attr_data.append(component_data.AttrData(f"{item.name}X", type_="double", parent=item.name))
            attr_data.append(component_data.AttrData(f"{item.name}Y", type_="double", parent=item.name))
            attr_data.append(component_data.AttrData(f"{item.name}Z", type_="double", parent=item.name))
        node_data.extend_attr_data(*attr_data)

        return node_data
    
    def _override_build(self, **kwargs):
        for item in component_enum_data.AxisEnum:
            self.output_node[self._OUT_AXIS][item.name] = item.value

        self.output_node[self._OUT_AXIS].set_locked(True)

class Color(base_comp.SingletonComponent):
    """Component of colors that creates shaders from color enum"""
    class_namespace="color_manager"

    _OUT_COLOR = "color"
    def _output_build_attr_data(self):
        node_data = super()._output_build_attr_data()

        attr_data = [component_data.AttrData(self._OUT_COLOR, type_="compound", parent=self._OUT)]
        for item in component_enum_data.Color:
            attr_data.append(component_data.AttrData(item.name, type_="double3", parent=self._OUT_COLOR))
            attr_data.append(component_data.AttrData(f"{item.name}R", type_="double", parent=item.name))
            attr_data.append(component_data.AttrData(f"{item.name}G", type_="double", parent=item.name))
            attr_data.append(component_data.AttrData(f"{item.name}B", type_="double", parent=item.name))
        node_data.extend_attr_data(*attr_data)

        return node_data
    
    def _override_build(self, **kwargs):
        for color_enum in component_enum_data.Color:
            index_color = utils.get_rgb_from_index(color_enum.value)
            self.output_node[self._OUT_COLOR][color_enum.name] = index_color

        # self.output_node[self._OUT_COLOR].set_locked(True)

    @classmethod
    def get_shader(cls, color:component_enum_data.Color):
        """Gets shader for a given color. Creates component if not created.
        creates lambert and shading set if not created.

        Args:
            color (component_enum_data.Colors):

        Returns:
            nw.Node:
        """
        class_inst = cls.instance()
        if class_inst.container_node[color.name].get_src_connection() == None:
            cls._create_shader_set(color)
        return class_inst.container_node[color.name].get_src_connection().node
    
    @classmethod
    def get_shader_sg(cls, color:component_enum_data.Color):
        """Gets shader shading group for a given color (creates if component instance isn't created yet)

        Args:
            color (component_enum_data.Colors):

        Returns:
            nw.Node:
        """
        shader = cls.get_shader(color)
        return shader["outColor"].get_dest_connections()[0].node
    
    @classmethod
    def _create_shader_set(cls, color:component_enum_data.Color):
        """Creates shader set when given a color

        Args:
            color (component_enum_data.Colors):
        """
        shader = utils.make_lambert_shader(color=color, name=f"{color.name}")
        shader_sg = utils.get_shader_sg(shader)
        color_manager_inst = cls.instance()

        color_manager_inst.output_node[cls._OUT_COLOR][color.name] << shader["color"]
        color_manager_inst.container_node.add_nodes(shader, shader_sg)
        color_manager_inst.rename_nodes()
    @classmethod
    def get_rgb_attr(cls, color:component_enum_data.Color):
        """gets rgb attribute given a color

        Args:
            color (component_enum_data.Color):
        """
        return cls.instance().container_node[color.name]
        
                
        
    
