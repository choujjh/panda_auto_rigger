import system.base_component as base_comp
import component.anim as anim
import component.motion as motion
import system.component_enum_data as component_enum_data
import utils.node_wrapper as nw
import system.component_data as component_data
import utils.utils as utils
from typing import Union


class _Character(base_comp._Component):
    """Base class for character

    Attributes
        root_component (component.anim.SingleXform):

        _IN_COLOR_CONST (str): str constant "colorConst"
        _IN_AXIS_VEC_CONST (str): str constant "axisVecConst"
        _SETUP_CLR (str): str constant "setupColor"
        _IN_MOT_VIS (str): str constant "motionVisibility"
        _IN_SETUP_VIS (str): str constant "setupVisibility"
    """

    component_type = component_enum_data.ComponentType.character
    class_namespace = "char"
    root_transform_name = "grp"

    _IN_COLOR_CONST = "colorConst"
    _IN_AXIS_VEC_CONST = "axisVecConst"
    _SETUP_CLR = "setupColor"
    _IN_MOT_VIS = "motionVisibility"
    _IN_SETUP_VIS = "setupVisibility"

    def _input_attr_build_data(self):
        """Defines all the added, published, or modified attributes for the
        input node. inherits all input node data from _Component

        Returns:
            comp_data.NodeData:
        """
        node_data = super()._input_attr_build_data()

        for enum_parent, enum_item in zip(
            [self._IN_COLOR_CONST, self._IN_AXIS_VEC_CONST],
            [component_enum_data.Color, component_enum_data.AxisEnum],
        ):
            attr_data = [
                component_data.AttrData(enum_parent, type_="compound", publish=True)
            ]
            for color_item in enum_item:
                if enum_parent == self._IN_COLOR_CONST:
                    values = utils.get_rgb_from_index(color_item)
                    suffix = "RGB"
                else:
                    values = color_item.value
                    suffix = "XYZ"
                attr_data.append(
                    component_data.AttrData(
                        color_item.name,
                        type_="double3",
                        parent=enum_parent,
                        locked=True,
                    )
                )
                for index in range(3):
                    attr_data.append(
                        component_data.AttrData(
                            f"{color_item.name}{suffix[index]}",
                            type_="double",
                            parent=color_item.name,
                            value=values[index],
                        )
                    )
            node_data.extend_attr_data(*attr_data)
        node_data.extend_attr_data(
            component_data.AttrData(
                self._IN_MOT_VIS,
                type_="bool",
                parent=self._IN,
                keyable=True,
                value=True,
            ),
            component_data.AttrData(
                self._IN_SETUP_VIS,
                type_="bool",
                parent=self._IN,
                keyable=True,
                value=True,
            ),
        )
        return node_data

    def _get_char_color_side_name(self, char_side: component_enum_data.CharacterSide):
        """Gets character side color name

        Args:
            char_side (component_enum_data.CharacterSide):

        Returns:
            str:
        """
        return f"{char_side.name}Color"

    def get_color_shader(
        self,
        char_side: Union[component_enum_data.CharacterSide, str],
        set_color: component_enum_data.Color = None,
    ):
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
            choice = (
                self.container_node[char_side_color_name].get_dest_connections()[0].node
            )
            shader = choice["output"].get_dest_connections()[0].node
        else:
            color_side_node_data = component_data.NodeData(
                component_data.AttrData(
                    char_side_color_name, type_=component_enum_data.Color
                )
            )
            color_side_node_data.add_attrs_to_node(self.input_node)
            self.container_node.publish_attr(
                self.input_node[char_side_color_name],
                attr_bind_name=char_side_color_name,
            )
            # choice node
            char_side_choice = nw.create_node(
                "choice", f"{char_side_color_name}_choice"
            )
            for index, color_attr in enumerate(
                self.container_node[self._IN_COLOR_CONST]
            ):
                char_side_choice["input"][index] << color_attr
            char_side_choice["selector"] << self.container_node[char_side_color_name]

            shader = utils.make_lambert_shader(
                color=char_side_choice["output"], name=char_side_color_name
            )
            shader_sg = utils.get_shader_sg(shader=shader)

            self.container_node.add_nodes(char_side_choice, shader, shader_sg)
            self.rename_nodes()

        if set_color is not None:
            self.container_node[char_side_color_name] = set_color.name

        return shader

    @property
    def root_component(self) -> anim.SingleXform:
        """Root component

        Returns:
            base_comp.Anim:
        """
        return self.child_components()[0]

    def _pre_build(
        self,
        instance_name: Union[str, nw.Attr] = None,
        parent: Union[base_comp._Component, nw.Container] = None,
        **kwargs,
    ):
        """Handles creation and connection of initial nodes

        Args:
            instance_name (str, nw.Attr, optional): component instance name. Defaults to None.
            parent (nw.Container, Component, optional): Defaults to None.
        """
        super()._pre_build(instance_name, parent)

        m_color = component_enum_data.Color.yellow
        m_char_side = component_enum_data.CharacterSide.mid
        m_char_shader = self.get_color_shader(m_char_side, set_color=m_color)
        setup_color = component_enum_data.Color.purple
        setup_char_side = self._SETUP_CLR
        setup_char_shader = self.get_color_shader(
            setup_char_side, set_color=setup_color
        )

        root_component = anim.SingleXform.create(
            instance_name="root",
            parent=self,
            source_component=None,
            control_color=m_char_shader,
            setup_color=setup_char_shader,
        )

        # change root transform
        transform_shape = root_component._motion_component.child_components()[
            1
        ].transform_node.get_shapes()[0]
        self.root_component._settings_guide_component.transform_node["tz"] = -9
        cntrl_pnt_len = len(transform_shape["controlPoints"])
        for control_point in [attr for attr in transform_shape["controlPoints"]][
            : cntrl_pnt_len - 3
        ]:
            control_point.set(utils.Vector(control_point.value) * 7)

        self.rename_nodes()

    def _post_build(self, **kwargs):
        """Inherited from _Component. in addition to _Component functionality, connects all child components that have motion and setup
        visibility to character's motion and setup visibility
        """
        child_components = self.child_components()
        for child_component in child_components:
            motion_vis = self.container_node[self._IN_MOT_VIS]
            setup_vis = self.container_node[self._IN_SETUP_VIS]

            if child_component.container_node.has_attr(self._IN_MOT_VIS):
                child_component.container_node[self._IN_MOT_VIS] << motion_vis
            if child_component.container_node.has_attr(self._IN_SETUP_VIS):
                child_component.container_node[self._IN_SETUP_VIS] << setup_vis
        super()._post_build(**kwargs)

    def axis_vec_choice_node(self, choice_node_name: str, enum_attr: nw.Attr = None):
        """Creates a choice node for axis vectors. allows enum to generate a vector

        Args:
            choice_node_name (str):

        Returns:
            nw.Node: choice node
        """
        choice_node = nw.create_node("choice", name=f"{choice_node_name}AxisVecChoice")

        for index, item in enumerate(component_enum_data.AxisEnum):
            (
                self.container_node[self._IN_AXIS_VEC_CONST][item.name]
                >> choice_node["input"][index]
            )
        if enum_attr is not None:
            enum_attr >> choice_node["selector"]

        return choice_node


class CustomCharacter(_Character):
    """Custom Character where Anim components can be added in. used as a base to add components into"""

    def _override_build(self, **kwargs):
        pass


class SimpleBiped(_Character):
    """Class for character component of a simple character"""

    @classmethod
    def create(
        cls,
        instance_name=None,
        parent=None,
        num_twist_xforms: int = 3,
        counter_rot_root: bool = True,
        **kwargs,
    ):
        """Class method to create component

        Args:
            instance_name (str, nw.Attr, optional): name of component. Defaults to None.
            parent (nw.Container, Component, optional): Defaults to None.
            num_twist_xforms (int, optional): arg for num twist xform in between limb components. Defaults to 3.
            counter_rot_root (bool, optional):  arg for limb component counter rotating root. Defaults to True.
        """
        cls._kwarg_create(**cls._process_locals(kwarg_dict=locals()))

    def _override_build(self, num_twist_xforms=3, counter_rot_root=True, **kwargs):
        """Creates all anim components of simple biped

        Args:
            num_twist_xforms (int, optional): arg for num twist xform in between limb components. Defaults to 3.
            counter_rot_root (bool, optional): arg for limb component counter rotating root.  Defaults to True.
        """
        # color
        setup_color = self.get_color_shader(
            char_side=self._SETUP_CLR, set_color=component_enum_data.Color.purple
        )

        l_char_shader = self.get_color_shader(
            char_side=component_enum_data.CharacterSide.left,
            set_color=component_enum_data.Color.blue,
        )
        r_char_shader = self.get_color_shader(
            char_side=component_enum_data.CharacterSide.right,
            set_color=component_enum_data.Color.red,
        )
        m_char_shader = self.get_color_shader(
            char_side=component_enum_data.CharacterSide.mid
        )

        spine = anim.FK.create(
            instance_name="spine",
            parent=self,
            hier_side=component_enum_data.CharacterSide.mid,
            control_color=m_char_shader,
            setup_color=setup_color,
            input_xforms=[
                component_data.Xform(
                    xform_name="waist",
                    init_matrix=utils.Matrix.translate_matrix(0, 8, 0),
                ),
                component_data.Xform(
                    xform_name="mid_spine",
                    init_matrix=utils.Matrix.translate_matrix(0, 11.5, 0),
                ),
                component_data.Xform(
                    xform_name="chest",
                    init_matrix=utils.Matrix.translate_matrix(0, 15, 0),
                ),
            ],
            add_settings_cntrl=False,
            primary_axis=component_enum_data.AxisEnum.y,
            secondary_axis=component_enum_data.AxisEnum.z,
        )

        # leg
        l_leg = anim.SimpleLimb.create(
            instance_name="leg",
            parent=self,
            hier_side=component_enum_data.CharacterSide.left,
            control_color=l_char_shader,
            setup_color=setup_color,
            input_xforms=[
                component_data.Xform(
                    xform_name="upleg",
                    init_matrix=utils.Matrix.translate_matrix(3, 8, 0),
                ),
                component_data.Xform(xform_name="loleg"),
                component_data.Xform(
                    xform_name="foot",
                    init_matrix=utils.Matrix.translate_matrix(4, 0, 0),
                ),
            ],
            num_twist_xforms=num_twist_xforms,
            counter_rot_root=counter_rot_root,
        )
        r_leg = l_leg.mirror(control_color=r_char_shader, setup_color=setup_color)

        # arm
        l_arm = anim.SimpleLimb.create(
            instance_name="arm",
            parent=self,
            hier_side=component_enum_data.CharacterSide.left,
            control_color=l_char_shader,
            setup_color=setup_color,
            input_xforms=[
                component_data.Xform(
                    xform_name="uparm",
                    init_matrix=utils.Matrix.translate_matrix(3, 15, 0),
                ),
                component_data.Xform(
                    xform_name="loarm",
                    loc_matrix=utils.Matrix.translate_matrix(0, 0, -1),
                ),
                component_data.Xform(
                    xform_name="hand",
                    init_matrix=utils.Matrix.translate_matrix(8, 12, 0),
                ),
            ],
            num_twist_xforms=num_twist_xforms,
            counter_rot_root=counter_rot_root,
        )
        r_arm = l_arm.mirror(control_color=r_char_shader, setup_color=setup_color)

        # hooking
        l_leg.hook(
            spine.container_node[spine.HIER_DATA.IN_XFORM][0],
            hook_mirror_component=True,
        )
        l_arm.hook(
            spine.container_node[spine.HIER_DATA.IN_XFORM][2],
            hook_mirror_component=True,
        )
        spine.hook(self.root_component)

        # adding root as default ik space
        for name, anim_inst in zip(
            ["l_leg", "r_leg", "l_arm", "r_arm"], [l_leg, r_leg, l_arm, r_arm]
        ):
            anim_inst.add_ik_space(
                space_name="root", space_src_data=self.root_component
            )
            motion.Visualize.create(
                instance_name=name, source_component=anim_inst, parent=self
            )
