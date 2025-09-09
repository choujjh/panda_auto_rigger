import system.base_component as base_comp
import component.anim as anim
import component.setup as setup
import system.component_enum_data as component_enum_data
import utils.node_wrapper as nw
import system.component_data as component_data
import utils.utils as utils
from typing import Union

class CustomCharacter(base_comp.Component):
    """Base class for character. takes care of a lot of the nice stuff like root transform and color and axis enum storing"""
    component_type = component_enum_data.ComponentType.character
    class_namespace = "char"
    root_transform_name = "grp"

    _IN_COLOR_CONST = "colorConst"
    _IN_AXIS_VEC_CONST = "axisVecConst"
    _SETUP_CLR = "setupColor"

    def _input_attr_build_data(self):
        node_data = super()._input_attr_build_data()

        for enum_parent, enum_item in zip([self._IN_COLOR_CONST, self._IN_AXIS_VEC_CONST], [component_enum_data.Color, component_enum_data.AxisEnum]):
            attr_data = [component_data.AttrData(enum_parent, type_="compound", publish=True)]
            for color_item in enum_item:
                if enum_parent == self._IN_COLOR_CONST:
                    values = utils.get_rgb_from_index(color_item)
                    suffix = "RGB"
                else:
                    values = color_item.value
                    suffix = "XYZ"
                attr_data.append(component_data.AttrData(color_item.name, type_="double3", parent=enum_parent, locked=True))
                for index in range(3):
                    attr_data.append(component_data.AttrData(
                        f"{color_item.name}{suffix[index]}", 
                        type_="double", 
                        parent=color_item.name, value=values[index]))
            node_data.extend_attr_data(*attr_data)

        return node_data
    def _get_char_color_side_name(self, char_side:component_enum_data.CharacterSide):
        return f"{char_side.name}Color"
    def get_color_shader(self, char_side:Union[component_enum_data.CharacterSide, str], set_color:component_enum_data.Color=None):
        """Gets shader for character side. creates if not created yet

        Args:
            char_side (Union[component_enum_data.CharacterSide, str]):
            set_color component_enum_data.Color: defaults to None

        Returns:
            nw.Node: shader
        """
        if isinstance(char_side, str):
            char_side_color_name = char_side
        else:
            char_side_color_name = self._get_char_color_side_name(char_side)

        shader = None
        if self.container_node.has_attr(char_side_color_name):
            choice = self.container_node[char_side_color_name].get_dest_connections()[0].node
            shader = choice["output"].get_dest_connections()[0].node
        else:
            color_side_node_data = component_data.NodeData(
                component_data.AttrData(char_side_color_name, type_=component_enum_data.Color)
            )
            color_side_node_data.add_attrs_to_node(self.input_node)
            self.container_node.publish_attr(self.input_node[char_side_color_name], attr_bind_name=char_side_color_name)
            # choice node
            char_side_choice = nw.create_node("choice", f"{char_side_color_name}_choice")
            for index, color_attr in enumerate(self.container_node[self._IN_COLOR_CONST]):
                char_side_choice["input"][index] << color_attr
            char_side_choice["selector"] << self.container_node[char_side_color_name]

            shader = utils.make_lambert_shader(color=char_side_choice["output"], name=char_side_color_name)
            shader_sg = utils.get_shader_sg(shader=shader)

            self.container_node.add_nodes(char_side_choice, shader, shader_sg)
            self.rename_nodes()
        
        if set_color is not None:
            self.container_node[char_side_color_name] = set_color.name

        return shader

    @classmethod
    def create(cls, instance_name = None, parent=None):
        return super().create(instance_name, parent)
    
    def _pre_build(self, instance_name = None, parent=None):
        super()._pre_build(instance_name, parent)

        import component.anim as anim

        m_color = component_enum_data.Color.yellow
        m_char_side = component_enum_data.CharacterSide.mid
        m_char_shader = self.get_color_shader(m_char_side, set_color=m_color)
        setup_color = component_enum_data.Color.purple
        setup_char_side = self._SETUP_CLR
        setup_char_shader = self.get_color_shader(setup_char_side, set_color=setup_color)

        anim.SingleXform.create(
            instance_name="root", 
            parent=self, 
            source_component=None, 
            control_color=m_char_shader, 
            setup_color=setup_char_shader
        )

        self.rename_nodes()
    def _override_build(self, **build_kwargs):
        pass

    def axis_vec_choice_node(self, choice_node_name, enum_attr:nw.Attr=None):
        """creates a choice node for axis vectors. allows enum to generate a vector

        Args:
            choice_node_name (str):

        Returns:
            nw.Node: choice node
        """
        choice_node = nw.create_node("choice", name=f"{choice_node_name}AxisVecChoice")

        for index, item in enumerate(component_enum_data.AxisEnum):
            self.container_node[self._IN_AXIS_VEC_CONST][item.name] >> choice_node["input"][index]
        if enum_attr is not None:
            enum_attr  >> choice_node["selector"]

        return choice_node

class SimpleCharacter(CustomCharacter):
    """Class for character component of a simple character

    Args:
        CustomCharacter (_type_): _description_
    """
    def _override_build(self, **kwargs):

        l_color = component_enum_data.Color.blue
        l_char_side = component_enum_data.CharacterSide.left
        l_char_shader = self.get_color_shader(l_char_side, set_color=l_color)
        
        l_leg_anim_inst = anim.SimpleLimb.create(
            instance_name="Leg", 
            parent=self, 
            control_color=l_char_shader,
            setup_color=self.get_color_shader(self._SETUP_CLR),
            hier_side=l_char_side)