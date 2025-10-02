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

    @property
    def root_component(self):
        return self.child_components()[0]
    @classmethod
    def create(cls, instance_name = None, parent=None):
        return super().create(instance_name, parent)
    
    def _pre_build(self, instance_name = None, parent=None):
        super()._pre_build(instance_name, parent)

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

class SimpleBiped(CustomCharacter):
    """Class for character component of a simple character

    Args:
        CustomCharacter (_type_): _description_
    """
    def _override_build(self, **kwargs):
        # color
        setup_color = self.get_color_shader(char_side=self._SETUP_CLR, set_color=component_enum_data.Color.green)

        l_char_shader = self.get_color_shader(char_side=component_enum_data.CharacterSide.left, set_color=component_enum_data.Color.blue)
        r_char_shader = self.get_color_shader(char_side=component_enum_data.CharacterSide.right, set_color=component_enum_data.Color.red)
                
        # leg
        l_leg = anim.SimpleLimb.create(
        instance_name="leg", 
        parent=self,
        hier_side=component_enum_data.CharacterSide.left, 
        control_color=l_char_shader, 
        setup_color=setup_color,
        input_xforms=[
            component_data.Xform(xform_name="upleg", init_matrix=utils.Matrix.translate_matrix(3, 8, 0)),
            component_data.Xform(xform_name="loleg"),
            component_data.Xform(xform_name="foot", init_matrix=utils.Matrix.translate_matrix(4, 0, 0)),
        ],
        add_settings_cntrl=True)
        r_leg = l_leg.mirror(control_color=r_char_shader, setup_color=setup_color)

        # arm
        l_arm = anim.SimpleLimb.create(
        instance_name="arm", 
        parent=self,
        hier_side=component_enum_data.CharacterSide.left, 
        control_color=l_char_shader, 
        setup_color=setup_color,
        input_xforms=[
            component_data.Xform(xform_name="uparm", init_matrix=utils.Matrix.translate_matrix(3, 15, 0)),
            component_data.Xform(xform_name="loarm", loc_matrix=utils.Matrix.translate_matrix(0, 0, -1)),
            component_data.Xform(xform_name="hand", init_matrix=utils.Matrix.translate_matrix(8, 12, 0)),
        ],
        add_settings_cntrl=True)
        r_arm = l_arm.mirror(control_color=r_char_shader, setup_color=setup_color)
        
        root_xform = self.root_component.get_xform_attrs(index=0, xform_type=component_enum_data.IO.output)
        l_leg.hook(self.root_component)
        r_leg.hook(self.root_component)
        l_arm.hook(self.root_component)
        r_arm.hook(self.root_component)
        # l_leg._set_hier_parent_attrs(hier_parent=component_data.xform_to_hier_parent(root_xform))
        # r_leg._set_hier_parent_attrs(hier_parent=component_data.xform_to_hier_parent(root_xform))
        # l_arm._set_hier_parent_attrs(hier_parent=component_data.xform_to_hier_parent(root_xform))
        # r_arm._set_hier_parent_attrs(hier_parent=component_data.xform_to_hier_parent(root_xform))

