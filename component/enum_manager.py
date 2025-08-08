from typing import Union

import system.component_enum_data as component_enum_data
import system.base_component as base_component
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
        
        axis_vec_container["axis"][item.name] >> choice_node["input"][index]
    if enum_attr is not None:
        enum_attr >> choice_node["selector"]

    return choice_node

class AxisVector(base_component.SingletonComponent):
    """Component of axis vectors that creates vectors from the enum"""
    class_namespace="axis_vec_manager"
    def __init__(self, container_node = None):
        super().__init__(container_node)
        self.self_component = None
    
    def _get_output_node_build_attr_data(self):
        node_data = super()._get_output_node_build_attr_data()

        attr_data = [component_data.AttrData("axis", type_="compound", parent="output")]
        for item in component_enum_data.AxisEnum:
            attr_data.append(component_data.AttrData(item.name, type_="double3", parent="axis"))
            attr_data.append(component_data.AttrData(f"{item.name}X", type_="double", parent=item.name))
            attr_data.append(component_data.AttrData(f"{item.name}Y", type_="double", parent=item.name))
            attr_data.append(component_data.AttrData(f"{item.name}Z", type_="double", parent=item.name))
        node_data.extend_attr_data(*attr_data)

        return node_data
    
    def _override_build(self, **kwargs):
        for item in component_enum_data.AxisEnum:
            self.output_node["axis"][item.name] = item.value

        self.output_node["axis"].set_locked(True)

class Color(base_component.SingletonComponent):
    """Component of colors that creates shaders from color enum"""
    class_namespace="color_manager"
    def _get_output_node_build_attr_data(self):
        node_data = super()._get_output_node_build_attr_data()

        attr_data = [component_data.AttrData("color", type_="compound", parent="output")]
        for item in component_enum_data.Color:
            attr_data.append(component_data.AttrData(item.name, type_="double3", parent="color"))
            attr_data.append(component_data.AttrData(f"{item.name}R", type_="double", parent=item.name))
            attr_data.append(component_data.AttrData(f"{item.name}G", type_="double", parent=item.name))
            attr_data.append(component_data.AttrData(f"{item.name}B", type_="double", parent=item.name))
        node_data.extend_attr_data(*attr_data)

        return node_data
    
    def _override_build(self, **kwargs):
        added_nodes = []
        for color_enum in component_enum_data.Color:
            index_color = utils.get_rgb_from_index(color_enum.value)
            self.output_node["color"][color_enum.name] = index_color

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
        color_manager_inst = cls.instance()

        index_color = utils.get_rgb_from_index(color.value)
        shader = nw.wrap_node(cmds.shadingNode("lambert", name=f"{color.name}Lamb", asShader=True))
        shader["color"] = index_color

        shader_sg = nw.wrap_node(cmds.sets(name=f"{color.name}LambSG", renderable=True, noSurfaceShader=True, empty=True))
        shader["outColor"] >> shader_sg["surfaceShader"]

        shader["color"] >> color_manager_inst.output_node["color"][color.name]

        color_manager_inst.container_node.add_nodes(shader, shader_sg)
        color_manager_inst.rename_nodes()
        
    
    @classmethod
    def apply_color(cls, obj:Union[nw.Transform, base_component.Control, nw.Node], color:component_enum_data.Color, connect=True):
        """Apply color to 

        Args:
            obj (Union[nw.Transform, component.Control, nw.Node]): _description_
            color (component_enum_data.Colors): _description_

        Raises:
            RuntimeError: _description_
        """
        if color == component_enum_data.Color.none:
            cls.get_shader(color=color)
            cmds.warning(f"not applying color to {obj} because color is None")
            return
        # switch obj from control component to transform node
        shapes_list = []
        if issubclass(type(obj), base_component.Control):
            transform = obj.transform_node
            if transform is None:
                cmds.warning(f"transform is None. did not apply color")
                raise RuntimeError("transform is None. did not apply color")
            elif not obj.can_set_color:
                cmds.warning(f"{obj.container_node} component is not able to set color")
                return
            obj = transform
        elif isinstance(obj, nw.Node) and obj.type_ !="transform":
            if obj.has_attr("overrideEnabled") and obj.has_attr("overrideRGBColors") and obj.has_attr("overrideColorRGB"):
                shapes_list = [obj]
        if isinstance(obj, nw.Transform):
            shapes_list = obj.get_shapes()

        # going through shapes list
        for shape in shapes_list:
            if shape.type_ == "nurbsSurface":
                cmds.sets([str(shape)], e=True, forceElement=str(cls.get_shader_sg(color)))
            else:
                shape["overrideEnabled"] = True
                shape["overrideRGBColors"] = 1
                if connect:
                    cls.get_shader(color)["color"] >> shape["overrideColorRGB"]
                else:
                    shape["overrideColorRGB"] = cls.get_shader(color)["color"]
        
                
        
    
