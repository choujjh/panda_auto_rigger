import system.component_enum_data as component_enum_data
import system.component_data as component_data
import system.base_component as base_comp
import component.enum_manager as enum_manager
import component.setup as setup
import component.motion as motion
import component.misc as misc
import component.control as control
import utils.node_wrapper as nw
import utils.utils as utils
from typing import Union
import maya.cmds as cmds


class _Anim(base_comp._Hierarchy):
    """Base class for anim autorigging components. Derived from Hierarchy. creates setup component in pre build


    Attributes:
        __setup_component_type (component.setup.Setup):
        _setup_component_type (component.setup.Setup): setup component type that will be used to be created. gets __setup_component_type from inherited class
        _setup_component (component.setup.Setup): setup component instance
        _motion_component (component.motion.MotionWrapper): motion component that contains all other motion components
        _cluster_component (component.misc.Cluster):
        _settings_component (component.control._Control):
        _settings_guide_component (component.control._Control):
        _mirror_dest_component (component.anim._Anim): mirror destination component
        _mirror_src_component (component.anim._Anim): mirror source component

        _IN_PRM_AXIS (str): str constant "primaryAxis"
        _IN_SEC_AXIS (str): str constant "secondaryAxis"
        _HIER_SIDE (str): str constant "hierSide"
        _IN_SET_XFORM_FOLLOW_INDEX (str): str constant "settingXformFollowIndex"
        _IN_SET_CNTRL_LOC_MAT (str): str constant "inputSettingCntrlLocMatrix"
        _IN_HAS_PARENT_HIER (str): str constant "hasHierParent"
        _IN_MOT_VIS (str): str constant "motionVisibility"
        _IN_SETUP_VIS (str): str constant "setupVisibility"
        _OUT_SET_CNTRL_LOC_MAT (str): str constant "outputSettingCntrlLocMatrix"
        _MIRROR_AXIS (str): str constant "mirrorAxis"
    """

    component_type = component_enum_data.ComponentType.anim
    __setup_component_type = utils.string_to_class("component.setup.Setup")
    input_node_name = "grp"
    input_node_type = "transform"
    class_namespace = "anim"

    _IN_PRM_AXIS = "primaryAxis"
    _IN_SEC_AXIS = "secondaryAxis"
    _HIER_SIDE = "hierSide"
    _IN_SET_XFORM_FOLLOW_INDEX = "settingXformFollowIndex"
    _IN_SET_CNTRL_LOC_MAT = "inputSettingCntrlLocMatrix"
    _IN_HAS_PARENT_HIER = "hasHierParent"
    _IN_MOT_VIS = "motionVisibility"
    _IN_SETUP_VIS = "setupVisibility"
    _OUT_SET_CNTRL_LOC_MAT = "outputSettingCntrlLocMatrix"
    _MIRROR_AXIS = "mirrorAxis"

    @property
    def _setup_component_type(self):
        """Returns class specific _setup_component_type. works for inherited classes"""
        return type(self).__setup_component_type

    @property
    def _setup_component(self) -> setup._Setup:
        """Returns setup component

        Returns:
            setup.Setup:
        """
        return self._get_node_from_key("setup_container", as_component=True)

    @property
    def _motion_component(self) -> motion.MotionWrapper:
        """Returns setup component

        Returns:
            setup.Setup:
        """
        return self._get_node_from_key("motion_container", as_component=True)

    @property
    def _cluster_component(self) -> misc.Cluster:
        """Returns cluster component

        Returns:
            misc.Cluster:
        """
        return self._get_node_from_key("clust_container", as_component=True)

    @property
    def _settings_component(self) -> control._Control:
        """Returns settings component (if one exists)

        Returns:
            Control:
        """
        if not self.container_node.has_attr("settings_container"):
            return
        return self._get_node_from_key("settings_container", as_component=True)

    @property
    def _settings_guide_component(self) -> control._Control:
        """Returns settings guide component (if one exists)

        Returns:
            Control:
        """
        if not self.container_node.has_attr("settings_guide_container"):
            return
        return self._get_node_from_key("settings_guide_container", as_component=True)

    @property
    def _mirror_dest_component(self) -> "_Anim":
        """Get mirror destination component

        Returns:
            Anim:
        """
        return self._get_node_from_key(self._MIRROR_SRC, as_component=True)

    @property
    def _mirror_src_component(self) -> "_Anim":
        """Get mirror source component

        Returns:
            Anim:
        """
        if self.container_node is not None:
            if self._MIRROR_DEST not in self._node_data_cache.keys():
                if self.container_node.has_attr(self._MIRROR_DEST):
                    if self.container_node[self._MIRROR_DEST].has_src_connection():
                        node = (
                            self.container_node[self._MIRROR_DEST]
                            .get_src_connection()
                            .node
                        )
                        self._node_data_cache[self._MIRROR_DEST] = node
        if self._MIRROR_DEST in self._node_data_cache.keys():
            node = self._node_data_cache[self._MIRROR_DEST]
            component = base_comp.get_component(node)
            if component is not None:
                return component
            return node

    def _input_attr_build_data(self):
        """Defines all the added, published, or modified attributes for the
        input node. inherits all input node data from _Hierarchy

        Returns:
            comp_data.NodeData:
        """
        node_data = super()._input_attr_build_data()
        node_data.extend_attr_data(
            component_data.AttrData(
                self._IN_PRM_AXIS, type_=component_enum_data.AxisEnum.x, publish=True
            ),
            component_data.AttrData(
                self._IN_SEC_AXIS, type_=component_enum_data.AxisEnum.y, publish=True
            ),
            component_data.AttrData(
                self._HIER_SIDE,
                type_=component_enum_data.CharacterSide.none,
                publish=True,
            ),
            component_data.AttrData(
                self._IN_SET_XFORM_FOLLOW_INDEX, type_="long", parent=self._IN, min=0
            ),
            component_data.AttrData(
                self._IN_SET_CNTRL_LOC_MAT, type_="matrix", parent=self._IN
            ),
            component_data.AttrData(
                self._IN_HAS_PARENT_HIER, type_="bool", parent=self._IN, value=False
            ),
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
        node_data.modify_add_attr_kwargs(
            self._BLD_INST_FORM, value=f"{{}}_{{}}_{type(self).class_namespace}"
        )
        return node_data

    def _output_attr_build_data(self):
        """Defines all the added, published, or modified attributes for the
        output node. inherits all output node data from _Hierarchy

        Returns:
            comp_data.NodeData:
        """
        node_data = super()._output_attr_build_data()
        node_data.extend_attr_data(
            component_data.AttrData(
                self._OUT_SET_CNTRL_LOC_MAT, type_="matrix", parent=self._OUT
            )
        )
        return node_data

    def get_short_namespace(self, instance_name: str = None):
        """Generates namespace without parentent namespace attached. takes into
        account hier side as well as instance name this time

        Args:
            instance_name (str, optional): generates with new instance name. used to generate namespaces to check. Defaults to None

        Returns:
            str:
        """
        format_str = self.container_node[self._BLD_INST_FORM].value

        # instance_name
        if instance_name is None:
            instance_name = self.container_node[self._BLD_INST_NAME].value

        if instance_name is None:
            instance_name = ""

        # hier sode
        hier_side = component_enum_data.CharacterSide.get(
            self.input_node[self._HIER_SIDE].value
        ).value
        if hier_side == f"{component_enum_data.CharacterSide.none.value}":
            hier_side = ""

        return utils.strip_characters(
            format_str.format(hier_side, instance_name),
            "_",
            leading=True,
            trailing=False,
        )

    @classmethod
    def create(
        cls,
        instance_name: Union[str, nw.Attr] = None,
        parent: Union[base_comp._Component, nw.Container] = None,
        input_xforms: Union[int, tuple] = 0,
        primary_axis: component_enum_data.AxisEnum = component_enum_data.AxisEnum.x,
        secondary_axis: component_enum_data.AxisEnum = component_enum_data.AxisEnum.y,
        add_settings_cntrl: bool = True,
        mirror_source: "_Anim" = None,
        mirror_axis: component_enum_data.AxisEnum = component_enum_data.AxisEnum.x,
        source_component: base_comp._Hierarchy = None,
        connect_parent_hier: bool = True,
        connect_axis_vecs: bool = True,
        control_color: Union[
            list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node
        ] = None,
        setup_color: Union[
            list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node
        ] = None,
        hier_side: component_enum_data.CharacterSide = component_enum_data.CharacterSide.none,
        **kwargs,
    ):
        """Class method to create component


        Args:
            instance_name (Union[str, nw.Attr], optional): name of component.. Defaults to None.
            parent (Union[base_comp._Component, nw.Container], optional): Defaults to None.
            input_xforms (Union[int, tuple], optional): input xforms to initialize component with.. Defaults to 0.
            primary_axis (component_enum_data.AxisEnum, optional): Defaults to component_enum_data.AxisEnum.x.
            secondary_axis (component_enum_data.AxisEnum, optional): Defaults to component_enum_data.AxisEnum.y.
            add_settings_cntrl (bool, optional): Defaults to True.
            mirror_source (_Anim, optional): mirror source component. Defaults to None.
            mirror_axis (component_enum_data.AxisEnum, optional): Defaults to component_enum_data.AxisEnum.x.
            source_component (base_comp._Hierarchy, optional):  source component to connect hierarchy from. Defaults to None.
            connect_parent_hier (bool, optional): Defaults to True.
            connect_axis_vecs (bool, optional): Defaults to True.
            control_color (Union[list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node], optional): Defaults to None.
            setup_color (Union[list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node], optional): Defaults to None.
            hier_side (component_enum_data.CharacterSide, optional): Defaults to component_enum_data.CharacterSide.none.

        Returns:
            _Anim:
        """
        return cls._kwarg_create(**cls._process_locals(kwarg_dict=locals()))

    def _pre_build(
        self,
        instance_name: Union[str, nw.Attr] = None,
        parent: Union[base_comp._Component, nw.Container] = None,
        input_xforms: Union[int, tuple] = 0,
        hier_side: component_enum_data.CharacterSide = component_enum_data.CharacterSide.none,
        primary_axis: component_enum_data.AxisEnum = component_enum_data.AxisEnum.x,
        secondary_axis: component_enum_data.AxisEnum = component_enum_data.AxisEnum.y,
        add_settings_cntrl: bool = True,
        mirror_source: "_Anim" = None,
        mirror_axis: component_enum_data.AxisEnum = component_enum_data.AxisEnum.x,
        setup_color: Union[
            list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node
        ] = None,
        control_color: Union[
            list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node
        ] = None,
        source_component: base_comp._Hierarchy = None,
        connect_parent_hier: bool = None,
        connect_axis_vecs: bool = True,
        **kwargs,
    ):
        """Handles creation and connection of initial nodes. adds setup, motion, and cluster component

        Args:
            instance_name (Union[str, nw.Attr], optional): name of component.. Defaults to None.
            parent (Union[base_comp._Component, nw.Container], optional): Defaults to None.
            input_xforms (Union[int, tuple], optional): input xforms to initialize component with.. Defaults to 0.
            hier_side (component_enum_data.CharacterSide, optional): Defaults to component_enum_data.CharacterSide.none.
            primary_axis (component_enum_data.AxisEnum, optional): Defaults to component_enum_data.AxisEnum.x.
            secondary_axis (component_enum_data.AxisEnum, optional): Defaults to component_enum_data.AxisEnum.y.
            add_settings_cntrl (bool, optional): Defaults to True.
            mirror_source (_Anim, optional): mirror source component. Defaults to None.
            mirror_axis (component_enum_data.AxisEnum, optional): Defaults to component_enum_data.AxisEnum.x.
            setup_color (Union[list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node], optional): Defaults to None.
            control_color (Union[list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node], optional): Defaults to None.x
            source_component (base_comp._Hierarchy, optional):  source component to connect hierarchy from. Defaults to None.
            connect_parent_hier (bool, optional): Defaults to True.
            connect_axis_vecs (bool, optional): Defaults to True.
        """
        # calling super
        super()._pre_build(
            instance_name=instance_name,
            parent=parent,
            input_xforms=input_xforms,
            source_component=source_component,
            connect_parent_hier=connect_parent_hier,
            connect_axis_vecs=connect_axis_vecs,
            **kwargs,
        )

        # setting values
        self.container_node[self._HIER_SIDE] = hier_side.name
        self.container_node[self._IN_PRM_AXIS] = primary_axis.name
        self.container_node[self._IN_SEC_AXIS] = secondary_axis.name

        # if mirror source connect other attrs from last time
        if mirror_source is not None:
            self._connect_mirror_source(mirror_source=mirror_source)
            self.input_node.add_attr(
                self._MIRROR_AXIS,
                type="enum",
                enumName=component_enum_data.AxisEnum.maya_enum_str(),
            )
            self.container_node.publish_attr(
                self.input_node[self._MIRROR_AXIS], attr_bind_name=self._MIRROR_AXIS
            )
            self.container_node[self._MIRROR_AXIS] = (
                component_enum_data.AxisEnum.index_of(mirror_axis)
            )

            # setting correct input xform
            setup_xforms = mirror_source._setup_component.get_xform_attrs(
                self.IO_ENUM.input
            )
            setup_xforms = {
                index: mirror_source.get_hook_xform(xform.init_matrix.parent)
                for index, xform in setup_xforms.items()
            }

            input_xforms = self.get_xform_attrs(xform_type=self.IO_ENUM.input)
            for input_xform in input_xforms.values():
                for attr in input_xform.attrs:
                    if isinstance(attr, nw.Attr):
                        ~attr
            for index, xform in setup_xforms.items():
                self._set_xform_attrs(
                    xform_type=self.IO_ENUM.input, index=index, xform=xform
                )

        # populating primary, secondary, and tertiary vectors
        self.__set_vectors()

        # create setup component
        self.__create_setup_component(
            input_xforms=input_xforms,
            setup_color=setup_color,
            mirror_source=mirror_source,
            mirror_axis=mirror_axis,
        )
        self.__create_motion_component()
        self.__create_clust_component()

        # adding settings cntrl
        if add_settings_cntrl:
            self.__create_settings_cntrls(
                setup_color=setup_color, control_color=control_color
            )

        # creating motion grp
        self.__internal_vis_setup()

        self.rename_nodes()

    def _post_build(self, **kwargs):
        """Build cleanup. sets build to true renames nodes, also tries to connect
        xform matricies and names. then raises warnings for any xform attribute not connected
        """
        for index, mot_xform in self._motion_component.get_xform_attrs(
            xform_type=self.IO_ENUM.output
        ).items():
            self._set_xform_attrs(
                index=index, xform=mot_xform, xform_type=self.IO_ENUM.output
            )

        super()._post_build(**kwargs)
        if self._mirror_src_component is not None:
            self.__mirror_controls_from_source()
        self._attach_output_xforms_to_settings_controls()

    # settings controls
    def __create_settings_cntrls(self, setup_color=None, control_color=None):
        """Creates settings control. creates settings guide if not mirrored

        Args:
            setup_color (component_enum_data.Color, optional): Defaults to None.
            control_color (component_enum_data.Color, optional): Defaults to None.
        """
        has_mirror_src = self._mirror_src_component is not None

        # settings init
        settings_init_choice = None
        settings_init = None
        if not has_mirror_src:
            settings_init_choice = nw.create_node("choice", "settings_init_choice")
            (
                settings_init_choice["selector"]
                << self.container_node[self._IN_SET_XFORM_FOLLOW_INDEX]
            )
            settings_init = control.Locator.create(
                instance_name="settings_guide",
                parent=self._setup_component,
                color=setup_color,
            )
            settings_init.promote_attr_to_keyable(
                self.container_node[self._IN_SET_XFORM_FOLLOW_INDEX],
            )
            settings_init.transform_node["translate"] = [1, 1, 1]
            utils.map_to_container(
                node=settings_init.container_node,
                node_message_name="settings_guide_container",
                container_message_name="anim_container",
                container=self.container_node,
            )

            self.container_node.add_nodes(settings_init_choice)

        settings_choice = nw.create_node("choice", "settings_choice")
        (
            settings_choice["selector"]
            << self.container_node[self._IN_SET_XFORM_FOLLOW_INDEX]
        )
        settings_mult = nw.create_node("multMatrix", "settings_ws_mult")

        # setting up controls
        settings = control.Gear.create(
            instance_name="settings", parent=self._motion_component, color=control_color
        )
        utils.map_to_container(
            node=settings.container_node,
            node_message_name="settings_container",
            container_message_name="anim_container",
            container=self.container_node,
        )
        for attr in ["t", "r", "s"]:
            for axis in ["x", "y", "z"]:
                settings.transform_node[f"{attr}{axis}"].set_locked(True)
                settings.transform_node[f"{attr}{axis}"].set_keyable(False)

        # inserting offset matrix to control
        if not has_mirror_src:
            (
                settings_init.container_node[settings_init._IN_OFF_MAT]
                << settings_init_choice["output"]
            )
            (
                settings_init.container_node[settings_init._OUT_LOC_MAT]
                >> self.container_node[self._IN_SET_CNTRL_LOC_MAT]
            )
        settings.container_node[settings._IN_OFF_MAT] << settings_mult["matrixSum"]
        (
            settings_mult["matrixIn"][0]
            << self._setup_component.container_node[self._OUT_SET_CNTRL_LOC_MAT]
        )
        settings_mult["matrixIn"][1] << settings_choice["output"]

        self.container_node.add_nodes(settings_choice, settings_mult)

    def _attach_output_xforms_to_settings_controls(self):
        """Takes finished output xforms and applies it to settings init choice"""
        output_xforms = self.get_xform_attrs(xform_type=self.IO_ENUM.output)
        settings_guide = self._settings_guide_component
        if settings_guide is not None:
            settings_guide_choice = (
                settings_guide.container_node[settings_guide._IN_OFF_MAT]
                .get_src_connection()
                .node
            )
            for index, output_xform in output_xforms.items():
                output_xform.init_matrix >> settings_guide_choice["input"][index]

            # reset max
            max = len(output_xforms.keys()) - 1
            max = 0 if max < 0 else max
            cmds.addAttr(
                str(settings_guide.transform_node[self._IN_SET_XFORM_FOLLOW_INDEX]),
                edit=True,
                max=max,
            )

            # set to max
            settings_guide.transform_node[self._IN_SET_XFORM_FOLLOW_INDEX] = max

        settings = self._settings_component
        if settings is not None:
            settings_choice = (
                settings.container_node[settings._IN_OFF_MAT]
                .get_src_connection()
                .node["matrixIn"][1]
                .get_src_connection()
                .node
            )
            for index, output_xform in output_xforms.items():
                output_xform.world_matrix >> settings_choice["input"][index]

    def __internal_vis_setup(self):
        """Sets up visibility for setup and motion groups"""
        # settings components
        settings_inst = self._settings_component
        settings_guide_inst = self._settings_guide_component

        # visibility attrs
        motion_vis_attr = self.container_node[self._IN_MOT_VIS]
        setup_vis_attr = self.container_node[self._IN_SETUP_VIS]

        # connecting
        motion_vis_attr >> self._motion_component.transform_node["v"]
        setup_vis_attr >> self._setup_component.transform_node["v"]

        if settings_inst is not None:
            motion_vis_attr >> settings_inst.transform_node["v"]
        if settings_guide_inst is not None:
            setup_vis_attr >> settings_guide_inst.transform_node["v"]

    # mirroring
    def mirror(
        self,
        control_color: component_enum_data.Color = None,
        setup_color: component_enum_data.Color = None,
        mirror_axis: component_enum_data.AxisEnum = component_enum_data.AxisEnum.x,
        **kwargs,
    ):
        """Mirrors component. returns new mirrored componenet

        Args:
            control_color (component_enum_data.Color, optional): Defaults to None.
            setup_color (component_enum_data.Color, optional): Defaults to None.
            mirror_axis (component_enum_data.AxisEnum, optional): Defaults to component_enum_data.AxisEnum.x.

        Returns:
            Hierarchy:
        """
        parent = self.container_node.get_container_node()
        add_settings_cntrl = self._settings_component is not None
        mirror_component = type(self).create(
            parent=parent,
            source_component=self,
            mirror_source=self,
            mirror_axis=mirror_axis,
            control_color=control_color,
            setup_color=setup_color,
            connect_parent_hier=False,
            connect_axis_vecs=False,
            add_settings_cntrl=add_settings_cntrl,
            **kwargs,
        )
        self._hook_mirror_component()

        return mirror_component

    def _connect_mirror_source(self, mirror_source: "_Anim"):
        """Connects all necessary attributes from mirror source

        Args:
            mirror_source (Anim): _description_
        """
        mirror_src_container = mirror_source.container_node
        self_container = self.container_node

        # add source and dest mirror attributes and connect it up
        mirror_src_container.add_attr(self._MIRROR_SRC, type="message")
        self_container.add_attr(self._MIRROR_DEST, type="message")

        mirror_src_container[self._MIRROR_SRC] >> self_container[self._MIRROR_DEST]

        # connect remap attrs
        primary_axis_remap = component_enum_data.AxisEnum.create_remap(
            "mirrorPrimaryAxisRemap"
        )
        secondary_axis_remap = component_enum_data.AxisEnum.create_remap(
            "mirrorSecondaryAxisRemap"
        )
        char_side_remap = component_enum_data.CharacterSide.create_remap(
            "mirrorHierSideRemap"
        )

        (
            primary_axis_remap["inputValue"]
            << mirror_src_container[mirror_source._IN_PRM_AXIS]
        )
        primary_axis_remap["outValue"] >> self_container[self._IN_PRM_AXIS]

        (
            secondary_axis_remap["inputValue"]
            << mirror_src_container[mirror_source._IN_SEC_AXIS]
        )
        secondary_axis_remap["outValue"] >> self_container[self._IN_SEC_AXIS]

        char_side_remap["inputValue"] << mirror_src_container[mirror_source._HIER_SIDE]
        char_side_remap["outValue"] >> self_container[self._HIER_SIDE]

        self.container_node.add_nodes(
            primary_axis_remap, secondary_axis_remap, char_side_remap
        )

        # connecting up other mirro source attributes
        (
            self_container[self._BLD_INST_NAME]
            << mirror_src_container[mirror_source._BLD_INST_NAME]
        )
        (
            self_container[self._IN_SET_XFORM_FOLLOW_INDEX]
            << mirror_src_container[mirror_source._IN_SET_XFORM_FOLLOW_INDEX]
        )
        (
            self_container[self._IN_SET_CNTRL_LOC_MAT]
            << mirror_src_container[mirror_source._OUT_SET_CNTRL_LOC_MAT]
        )

        self.rename_nodes()

    def __mirror_controls_from_source(self, color=None):
        """Mirrors the controls (to have the same shape as the other source)

        Args:
            color (Any, optional): Defaults to None.

        Raises:
            RuntimeError: can only be called from mirror destination component
        """

        if self._mirror_src_component is None:
            raise RuntimeError(
                "__mirror_controls can only be called if component is mirror dest"
            )
        for child_cntrl in self.get_all_descendants(
            component_enum_data.ComponentType.control
        ):
            mirror_control = child_cntrl.get_mirror_component()
            if issubclass(type(child_cntrl), control._Control):
                replace_control = child_cntrl.replace_control(
                    mirror_control, color=color
                )

                if (
                    replace_control.container_node[
                        replace_control._IN_OFF_MAT
                    ].value.det4x4()
                    > 0
                ):
                    scale_attr = replace_control.transform_node["scale"]

                    locked_attrs = [attr for attr in scale_attr if attr.is_locked()]
                    [attr.set_locked(False) for attr in locked_attrs]

                    scale_attr.set([-1, -1, -1])
                    replace_control.transform_node.freeze_transforms()

                    [attr.set_locked(True) for attr in locked_attrs]

    # hooking
    def hook(self, hook_src_data, hook_mirror_component: bool = True):
        """hooks xform to hier_parent. finds appropriate output xform and source hier parent

        Args:
            hook_src_data (any):
            hook_mirror_component (bool, optional): hooks mirror component. Defaults to True.
        """
        super().hook(hook_src_data, hook_mirror_component)
        if not self.container_node[self._IN_HAS_PARENT_HIER].has_src_connection():
            self.container_node[self._IN_HAS_PARENT_HIER] = True

    def unhook(self, unhook_mirror_component: bool = True):
        """unhook source hier parent.

        Args:
            unhook_mirror_component (bool, optional): Defaults to True.

        Returns:
            component_data.HierParent:
        """
        hier_parent = super().unhook(unhook_mirror_component)
        if not self.container_node[self._IN_HAS_PARENT_HIER].has_src_connection():
            self.container_node[self._IN_HAS_PARENT_HIER] = False
        return hier_parent

    # creating and connecting components
    def __set_vectors(self):
        """Creates nodes for primary, secondary, and tertiary vectors

        Args:
            mirror_source (Anim, optional): Defaults to None.
        """
        char_component = self.get_parent_type_component(
            component_enum_data.ComponentType.character, disable_warning=True
        )
        # adding prim, sec, ter vectors
        axis_vec_choice_node = None
        if char_component is not None and char_component:
            axis_vec_choice_node = char_component.axis_vec_choice_node
        else:
            axis_vec_choice_node = enum_manager.axis_vec_choice_node

        primary_choice_node = axis_vec_choice_node(
            choice_node_name="primary_vec_choice",
            enum_attr=self.container_node[self._IN_PRM_AXIS],
        )
        secondary_choice_node = axis_vec_choice_node(
            choice_node_name="primary_vec_choice",
            enum_attr=self.container_node[self._IN_SEC_AXIS],
        )
        primary_axis_attr = primary_choice_node["output"]
        secondary_axis_attr = secondary_choice_node["output"]
        tertiary_vec = nw.create_node("crossProduct", "tertiary_vec_prod")
        tertiary_vec["input1"] << primary_axis_attr
        tertiary_vec["input2"] << secondary_axis_attr
        tertiary_vec["output"] >> self.container_node[self._TER_VEC]

        self.container_node[self._PRM_VEC] << primary_axis_attr
        self.container_node[self._SEC_VEC] << secondary_axis_attr

        self.container_node.add_nodes(
            primary_choice_node, secondary_choice_node, tertiary_vec
        )

    def __create_setup_component(
        self,
        input_xforms: Union[int, tuple] = 0,
        setup_color=None,
        mirror_source: "_Anim" = None,
        mirror_axis: component_enum_data.AxisEnum = component_enum_data.AxisEnum.x,
    ):
        """Creates setup component and maps it to container

        Args:
            init_num_xforms (Union[int, tuple], optional): . Defaults to 0.
            setup_color (Any, optional): . Defaults to None.
            mirror_source (Anim, optional): . Defaults to None.
        """
        if mirror_source is None:
            setup_inst = self._setup_component_type.create(
                input_xforms=input_xforms,
                control_color=setup_color,
                parent=self,
                source_component=self,
            )
        else:
            setup_inst = setup.Mirror.create(
                input_xforms=input_xforms,
                control_color=setup_color,
                parent=self,
                source_component=self,
                mirror_axis=mirror_axis,
            )

        (
            setup_inst.container_node[setup_inst._IN_SET_XFORM_FOLLOW_INDEX]
            << self.container_node[self._IN_SET_XFORM_FOLLOW_INDEX]
        )
        (
            setup_inst.container_node[setup_inst._IN_SET_CNTRL_LOC_MAT]
            << self.container_node[self._IN_SET_CNTRL_LOC_MAT]
        )
        (
            setup_inst.container_node[setup_inst._OUT_SET_CNTRL_LOC_MAT]
            >> self.container_node[self._OUT_SET_CNTRL_LOC_MAT]
        )
        (
            setup_inst.container_node[setup_inst._IN_HAS_PARENT_HIER]
            << self.container_node[self._IN_HAS_PARENT_HIER]
        )
        utils.map_to_container(setup_inst.container_node, "setup_container")
        if self._mirror_src_component is None:
            self.container_node[self._IN_SET_XFORM_FOLLOW_INDEX] = (
                len(self.get_xform_attrs(self.IO_ENUM.input)) - 1
            )

    def __create_motion_component(self):
        """Creates motion component and maps it to anim container"""
        motion_inst = motion.MotionWrapper.create(
            source_component=self._setup_component, parent=self
        )
        utils.map_to_container(motion_inst.container_node, "motion_container")

    def __create_clust_component(self):
        """creates cluster component and maps it to anim container"""
        clust_inst = misc.Cluster.create(
            source_component=self._setup_component, parent=self
        )
        utils.map_to_container(clust_inst.container_node, "clust_container")


class SimpleLimb(_Anim):
    """Simple Limb Anim component (has a merged fk, ik, and a settings control). used in conjunction with simpleLimb setup

    Attributes:
        _ik_component (component.motion.SimpleIK): ik component
    """

    _setup_component_type = setup.SimpleLimb
    _max_num_xforms = (3, 3)

    @property
    def _ik_component(self) -> motion.SimpleIK:
        """Returns ik component

        Returns:
            motion.SetupIK:
        """
        return self._get_node_from_key("ik_container", as_component=True)

    @classmethod
    def create(
        cls,
        instance_name: Union[str, nw.Attr] = None,
        parent: Union[base_comp._Component, nw.Container] = None,
        input_xforms: Union[int, tuple] = 0,
        primary_axis: component_enum_data.AxisEnum = component_enum_data.AxisEnum.x,
        secondary_axis: component_enum_data.AxisEnum = component_enum_data.AxisEnum.y,
        add_settings_cntrl: bool = True,
        mirror_source: "_Anim" = None,
        mirror_axis: component_enum_data.AxisEnum = component_enum_data.AxisEnum.x,
        source_component: base_comp._Hierarchy = None,
        connect_parent_hier: bool = True,
        connect_axis_vecs: bool = True,
        control_color: Union[
            list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node
        ] = None,
        setup_color: Union[
            list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node
        ] = None,
        hier_side: component_enum_data.CharacterSide = component_enum_data.CharacterSide.none,
        num_twist_xforms: int = 3,
        counter_rot_root: bool = True,
        **kwargs,
    ):
        """Class method to create component

        Args:
            instance_name (Union[str, nw.Attr], optional): name of component.. Defaults to None.
            parent (Union[base_comp._Component, nw.Container], optional): Defaults to None.
            input_xforms (Union[int, tuple], optional): input xforms to initialize component with.. Defaults to 0.
            primary_axis (component_enum_data.AxisEnum, optional): Defaults to component_enum_data.AxisEnum.x.
            secondary_axis (component_enum_data.AxisEnum, optional): Defaults to component_enum_data.AxisEnum.y.
            add_settings_cntrl (bool, optional): Defaults to True.
            mirror_source (_Anim, optional): mirror source component. Defaults to None.
            mirror_axis (component_enum_data.AxisEnum, optional): Defaults to component_enum_data.AxisEnum.x.
            source_component (base_comp._Hierarchy, optional):  source component to connect hierarchy from. Defaults to None.
            connect_parent_hier (bool, optional): Defaults to True.
            connect_axis_vecs (bool, optional): Defaults to True.
            control_color (Union[list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node], optional): Defaults to None.
            setup_color (Union[list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node], optional): Defaults to None.
            hier_side (component_enum_data.CharacterSide, optional): Defaults to component_enum_data.CharacterSide.none.
            num_twist_xforms (int, optional): Defaults to 3.
            counter_rot_root (bool, optional): arg to counter rotate root xform. Defaults to True.

        Returns:
            SimpleLimb:
        """
        return cls._kwarg_create(**cls._process_locals(kwarg_dict=locals()))

    def _override_build(
        self,
        control_color: Union[
            list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node
        ] = None,
        num_twist_xforms: int = 3,
        counter_rot_root: bool = True,
        **kwargs,
    ):
        """Creates different motion components that go in motionWrapper component.
        also sets settings control to correct position

        Args:
            control_color (Union[list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node], optional): Defaults to None.
            num_twist_xforms (int, optional): Defaults to 3.
            counter_rot_root (bool, optional): arg to counter rotate root. Defaults to True.
        """
        ik_inst = motion.SimpleIK.create(
            source_component=self._motion_component,
            control_color=control_color,
            parent=self._motion_component,
        )
        fk_inst = motion.FK.create(
            source_component=self._motion_component,
            control_color=control_color,
            parent=self._motion_component,
        )

        utils.map_to_container(
            node=ik_inst.container_node,
            node_message_name="ik_container",
            container_message_name="anim_container",
            container=self.container_node,
        )

        merge_hier_inst = motion.Merge.create(
            source_components=[fk_inst, ik_inst], parent=self._motion_component
        )

        twist_hier_inst = motion.TwistHier.create(
            source_component=merge_hier_inst,
            parent=self._motion_component,
            num_twist_xforms=num_twist_xforms,
            counter_rot_root=counter_rot_root,
        )
        for index, output_xform in twist_hier_inst.get_xform_attrs(
            xform_type=self.IO_ENUM.output
        ).items():
            self._motion_component._set_xform_attrs(
                index=index,
                xform_type=self.IO_ENUM.output,
                xform=output_xform,
            )

        # promoting to settings attr
        if self._settings_component is not None:
            settings_transform = self._settings_component.transform_node

            settings_transform.add_attr("_", type="enum", enumName="FK_IK:")
            settings_transform["_"].set_locked(True)
            settings_transform["_"].set_keyable(True)
            self._settings_component.promote_attr_to_keyable(
                attr=merge_hier_inst.container_node[merge_hier_inst._IN_HIER_BLEND],
                name="blend",
            )

            settings_transform.add_attr("__", type="enum", enumName="IK:")
            settings_transform["__"].set_locked(True)
            settings_transform["__"].set_keyable(True)
            self._settings_component.promote_attr_to_keyable(
                attr=ik_inst.container_node[ik_inst._SPACE]
            )
            self._settings_component.promote_attr_to_keyable(
                attr=ik_inst.container_node[ik_inst._IK_STRETCH_ENAB]
            )
            self._settings_component.promote_attr_to_keyable(
                attr=ik_inst.container_node[ik_inst._IK_SOFT_IK_ENAB]
            )
            self._settings_component.promote_attr_to_keyable(
                attr=ik_inst.container_node[ik_inst._IK_SOFT_BLEND_START]
            )
            self._settings_component.promote_attr_to_keyable(
                attr=ik_inst.container_node[ik_inst._IK_BLEND_TYP]
            )
            self._settings_component.promote_attr_to_keyable(
                attr=ik_inst.container_node[ik_inst._IK_BLEND_CRV]
            )

        # setting settings transform
        if self._settings_guide_component is not None:
            self._settings_guide_component.transform_node["t"] = (
                -3 * self.container_node[self._SEC_VEC].value
            )
            ter_vec = self.container_node[self._TER_VEC].value
            if ter_vec != utils.Vector(0, 1, 0) or ter_vec != utils.Vector(0, -1, 0):
                self._settings_guide_component.transform_node["r"] = (
                    90 * utils.Vector(0, 1, 0) ^ ter_vec
                )

    def mirror(
        self,
        control_color: Union[
            list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node
        ] = None,
        setup_color: Union[
            list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node
        ] = None,
        mirror_axis: component_enum_data.AxisEnum = component_enum_data.AxisEnum.x,
        **kwargs,
    ):
        """Overriding mirror functionality adding in num_twist_xform and counter_rot_root
        to add into mirror function

        Args:
            control_color (Union[list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node], optional): Defaults to None.
            setup_color (Union[list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node], optional): Defaults to None.
            mirror_axis (component_enum_data.AxisEnum, optional): Defaults to component_enum_data.AxisEnum.x.

        Returns:
            _type_: _description_
        """
        num_twist_xforms = int(
            ((len(self.get_xform_attrs(self.IO_ENUM.output)) - 1) / 2) - 1
        )
        counter_rot_root = (
            True if len(self.container_node[self._CNTNR_CHLD_COMP]) == 3 else False
        )

        return super().mirror(
            control_color=control_color,
            setup_color=setup_color,
            mirror_axis=mirror_axis,
            num_twist_xforms=num_twist_xforms,
            counter_rot_root=counter_rot_root,
        )

    def add_ik_space(self, space_name: str, space_src_data):
        """adds space to ik end control

        Args:
            space_name (str):
            space_src_data (any): this data gets converted to xform
        """
        self._ik_component.add_ik_space(
            space_name=space_name, space_src_data=space_src_data
        )


class SingleXform(_Anim):
    """Single Joint Component"""

    _max_num_xforms = (1, 1)

    def _override_build(
        self,
        control_color: Union[
            list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node
        ] = None,
        **kwargs,
    ):
        """Overrides build for anim component. creates controls for single xform component

        Args:
            control_color (Union[list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node], optional): Defaults to None.
        """
        setup_out_xform0 = self._setup_component.get_xform_attrs(
            xform_type=self.IO_ENUM.output, index=0
        )

        cntrl_inst = control.Circle.create(
            parent=self._motion_component, color=control_color
        )
        (
            cntrl_inst.container_node[cntrl_inst._IN_OFF_MAT]
            << setup_out_xform0.world_matrix
        )

        self._motion_component._set_xform_attrs(
            index=0,
            xform_type=self.IO_ENUM.output,
            xform=self.XFORM(
                init_matrix=setup_out_xform0.init_matrix,
                init_inv_matrix=setup_out_xform0.init_inv_matrix,
                world_matrix=cntrl_inst.container_node[cntrl_inst._OUT_WS_MAT],
                world_inv_matrix=cntrl_inst.container_node[cntrl_inst._OUT_WS_INV_MAT],
            ),
        )
        if self._settings_guide_component is not None:
            self._settings_guide_component.transform_node["t"] = [0, 0, -3]


class FK(_Anim):
    """Anim FK. creates an FK Anim component. motion component is only an fk chain"""

    def _override_build(
        self,
        control_color: Union[
            list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node
        ] = None,
        **kwargs,
    ):
        """Overrides build for anim component. creates controls for FK component

        Args:
            control_color (Union[list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node]=None, optional): _description_. Defaults to None.
        """
        fk_inst = motion.FK.create(
            source_component=self._motion_component,
            parent=self._motion_component,
            control_color=control_color,
        )

        for index, xform in fk_inst.get_xform_attrs(self.IO_ENUM.output).items():
            self._motion_component._set_xform_attrs(
                index=index,
                xform_type=self.IO_ENUM.output,
                xform=xform,
            )
