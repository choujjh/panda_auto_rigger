import system.base_component as base_comp
import component.enum_manager as enum_manager
import system.component_data as component_data
import system.component_enum_data as component_enum_data
import utils.utils as utils
import component.control as control
import component.matrix as matrix
import utils.node_wrapper as nw
from typing import Union
import maya.cmds as cmds


class Cluster(base_comp._Component):
    """a component to encapsulate non chained xforms.
    Inherits _Component

    Attributes:
        __Hier (base_comp.Hierarchy): component casted to _Hierarchy component
        HIER_DATA (base_comp._Hierarchy.HIER_DATA): constant for HierData class. easier for in class use
        IO_ENUM (base_comp._Hierarchy.IO_ENUM): constant for component_enum_data.IO class. easier for in class use
        XFORM (base_comp._Hierarchy.XFORM): constant for xform class. easier for in class use
        HIER_PARENT (base_comp._Hierarchy.HIER_PARENT): constant for HierParent class. easier for in class use
        _IN_HIER_SIDE (str): str constant "inHierSide"
        _IN_CNTRL_CLR (str): str constant "controlColor"
        _IN_SETUP_CLR (str): str constant "setupColor"
        _PRM_VEC (str): str constant "primaryVec"
        _SEC_VEC (str): str constant "secondaryVec"
        _TER_VEC (str): str constant "tertiaryVec"

    """

    class_namespace = "clust"
    component_type = component_enum_data.ComponentType.cluster
    input_node_type = "transform"
    input_node_name = "grp"

    HIER_DATA = base_comp._Hierarchy.HIER_DATA
    IO_ENUM = base_comp._Hierarchy.IO_ENUM
    XFORM = base_comp._Hierarchy.XFORM
    HIER_PARENT = base_comp._Hierarchy.HIER_PARENT

    _IN_HIER_SIDE = "inHierSide"
    _IN_XFORM_PAR = "inXformParent"
    _IN_CNTRL_CLR = "controlColor"
    _IN_SETUP_CLR = "setupColor"

    _PRM_VEC = base_comp._Hierarchy._PRM_VEC
    _SEC_VEC = base_comp._Hierarchy._SEC_VEC
    _TER_VEC = base_comp._Hierarchy._TER_VEC

    def __init__(self, container_node=None):
        super().__init__(container_node)
        self.__hier_inst_var = None

    @property
    def __hier(self):
        """component as _Hierarchy component

        Returns:
            base_comp._Hierarchy:
        """
        if self.__hier_inst_var is not None:
            pass
        elif self.container_node is not None:
            self.__hier_inst_var = base_comp._Hierarchy(self.container_node)
        else:
            self.__hier_inst_var = base_comp._Hierarchy()
        return self.__hier_inst_var

    @property
    def __setup_color(self):
        """color for setup components

        Returns:
            _type_: _description_
        """
        return self.__get_color(self.container_node[self._IN_SETUP_CLR])

    @property
    def __control_color(self):
        return self.__get_color(self.container_node[self._IN_CNTRL_CLR])

    def __get_color(self, attr: nw.Attr):
        connection = attr.get_src_connection()
        if connection is not None:
            if connection.node.type_ == "lambert":
                return connection.node
        return attr

    def _input_attr_build_data(self):
        """Defines all the added, published, or modified attributes for the
        input node. inherits all input node data from _Component

        Returns:
            comp_data.NodeData:
        """
        node_data = super()._input_attr_build_data()
        node_data.extend_attr_data(self.HIER_DATA.get_xform_data(self.IO_ENUM.input))
        node_data.extend_attr_data(
            component_data.AttrData(
                self._IN_HIER_SIDE,
                type_=component_enum_data.CharacterSide.none,
                parent=self.HIER_DATA.IN_XFORM,
            ),
            component_data.AttrData(
                self._IN_XFORM_PAR,
                type_="message",
                parent=self.HIER_DATA.IN_XFORM,
            ),
            *component_data.double3_attr_data(
                attr_name=self._IN_CNTRL_CLR,
                double3_type=component_enum_data.double3Types.rgb,
                parent=self._IN,
            ),
            *component_data.double3_attr_data(
                attr_name=self._IN_SETUP_CLR,
                double3_type=component_enum_data.double3Types.rgb,
                parent=self._IN,
            ),
        )
        node_data.modify_add_attr_kwargs(self._IN_HIER_SIDE, value=None, multi=True)
        return node_data

    def _output_attr_build_data(self):
        """Defines all the added, published, or modified attributes for the
        output node. inherits all output node data from _Component

        Returns:
            comp_data.NodeData:
        """
        node_data = super()._output_attr_build_data()
        node_data.extend_attr_data(self.HIER_DATA.get_xform_data(self.IO_ENUM.output))
        node_data.extend_attr_data(
            *component_data.double3_attr_data(
                attr_name=self._PRM_VEC, value=[1, 0, 0], parent=self._OUT
            ),
            *component_data.double3_attr_data(
                attr_name=self._SEC_VEC, value=[0, 1, 0], parent=self._OUT
            ),
            *component_data.double3_attr_data(
                attr_name=self._TER_VEC, value=[0, 0, 1], parent=self._OUT
            ),
        )
        return node_data

    @classmethod
    def create(
        cls,
        instance_name: Union[str, nw.Attr] = None,
        parent: base_comp._Component = None,
        source_component: base_comp._Hierarchy = None,
        connect_axis_vecs: bool = True,
        control_color: Union[
            list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node
        ] = None,
        setup_color: Union[
            list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node
        ] = None,
    ):
        """Class method to create component

        Args:
            instance_name (Union[str, nw.Attr], optional): name of component. Defaults to None.
            parent (base_comp._Component, optional): Defaults to None.
            source_component (base_comp._Hierarchy, optional): source component to connect hierarchy from. Defaults to None.
            connect_axis_vecs (bool, optional): Defaults to True.
            control_color (Union[list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node], optional): Defaults to None.

        Returns:
            _type_: _description_
        """
        return cls._kwarg_create(**cls._process_locals(kwarg_dict=locals()))

    def _pre_build(
        self,
        instance_name: Union[str, nw.Attr] = None,
        parent: base_comp._Component = None,
        source_component: base_comp._Hierarchy = None,
        connect_axis_vecs: bool = True,
        **kwargs,
    ):
        """Handles creation and connection of initial nodes

        Args:
            instance_name (Union[str, nw.Attr], optional): name of component. Defaults to None.
            parent (base_comp._Component, optional): Defaults to None.
            source_component (base_comp._Hierarchy, optional): source component to connect hierarchy from. Defaults to None.
            connect_axis_vecs (bool, optional): Defaults to True.
        """
        # pre build
        super()._pre_build(instance_name=instance_name, parent=parent, **kwargs)

        if connect_axis_vecs and source_component is not None:
            for attr in [
                self.__hier._PRM_VEC,
                self.__hier._SEC_VEC,
                self.__hier._TER_VEC,
            ]:
                self.container_node[attr] << source_component.container_node[attr]

    def _override_build(
        self,
        control_color: Union[
            list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node
        ] = None,
        setup_color: Union[
            list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node
        ] = None,
        **kwargs,
    ):
        """sets color attrs

        Args:
            control_color (Union[list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node], optional): _description_. Defaults to None.
            setup_color (Union[list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node], optional): _description_. Defaults to None.
        """
        for color, color_name in zip(
            [control_color, setup_color], [self._IN_CNTRL_CLR, self._IN_SETUP_CLR]
        ):
            color_vec = None
            if isinstance(color, component_enum_data.Color):
                color_vec = enum_manager.Color.instance().get_shader(color=color)[
                    "color"
                ]
            elif isinstance(color, nw.Node):
                if color.type_ != "lambert":
                    raise RuntimeError(f"{color} is not lambert node")
                color_vec = color["color"]
            else:
                color_vec = color

            if color_vec is not None:
                utils.set_connect_attr_data(self.container_node[color_name], color_vec)

    # xform and hierarchy
    def get_xform_attrs(
        self, xform_type: component_enum_data.IO, index: Union[int, list] = None
    ):
        """Gets a dict of xforms given indicies and type of xform. returns all if index is None

        Args:
            xform_type (component_enum_data.IO): selects input or output xform
            index (int, list):
        Returns:
            dict:
        """
        return self.__hier.get_xform_attrs(xform_type=xform_type, index=index)

    def _set_xform_attrs(
        self,
        index: int,
        xform: component_data.Xform,
        xform_type: component_enum_data.IO,
        set_when_data_is_attr: bool = False,
    ):
        """Sets xform

        Args:
            index (int):
            xform (component_data.Xform):
            xform_type (component_enum_data.IO):
            set_when_data_is_attr (bool, optional): only sets and not connects if it's an attribute. Defaults to False.
        """
        return self.__hier._set_xform_attrs(
            index=index,
            xform=xform,
            xform_type=xform_type,
            set_when_data_is_attr=set_when_data_is_attr,
        )

    # get from index
    def get_setup_index_component(self, index: int):
        """Gets setup component by the index

        Args:
            index (int):
        """
        input_xform = self.get_xform_attrs(index=index, xform_type=self.IO_ENUM.input)
        connected_containers = [
            attr.node.get_container_node()
            for attr in input_xform.world_matrix.get_dest_connections()
            if attr.node.get_container_node() is not None
        ]
        connected_components = [
            base_comp.get_component(container) for container in connected_containers
        ]

        return connected_components

    def get_control_index_component(self, index: int):
        """Gets control xform component by index

        Args:
            index (int):
        """
        setup_components = self.get_setup_index_component(index=index)
        control_component = [
            base_comp.get_component(
                component.container_node["worldMatrix"]
                .get_dest_connections()[0]
                .node.get_container_node()
            )
            for component in setup_components
        ]

        return control_component

    def add_clust_xform(
        self,
        name: str,
        parent_xform: component_data.Xform = None,
        mirror_axis: component_enum_data.AxisEnum = None,
    ):
        """adds xform to cluster

        Args:
            name (str, optional): Defaults to "".
            parent_xform (component_data.Xform, optional): Defaults to None.
            mirror_axis (component_enum_data.AxisEnum, optional): Defaults to None.
        """
        # normal add
        # add mirrored
        # add with local matrix already attached
        # add corrective (4 xforms)

        input_len = len(self.container_node[self.HIER_DATA.IN_XFORM])
        input_xform = self.get_xform_attrs(
            index=input_len, xform_type=self.IO_ENUM.input
        )

        if parent_xform is not None:
            # if parent_xform.xform_name is None:
            parent_xform.xform_name = name
            parent_xform.loc_matrix = None

            self._set_xform_attrs(
                index=input_len, xform_type=self.IO_ENUM.input, xform=parent_xform
            )
        else:
            self._set_xform_attrs(
                index=input_len,
                xform_type=self.IO_ENUM.input,
                xform=self.XFORM(xform_name=name),
            )
        added_nodes = []
        inv_attr = None
        if mirror_axis is None:
            setup_cntrl = control.Locator.create(
                instance_name=input_xform.xform_name,
                parent=self,
                color=self.__setup_color,
            )
            (
                setup_cntrl.container_node[setup_cntrl._IN_OFF_MAT]
                << input_xform.world_matrix
            )
            ws_attr = setup_cntrl.container_node[setup_cntrl._OUT_WS_MAT]
            setup_cntrl.insert_component_namespace_data(index=1, name="setup")
            setup_cntrl.transform_node["t"] = (
                self.container_node[self._SEC_VEC].value * 2
            )
        else:
            mirror_plane_scale_val = [1 if x == 0 else -1 for x in mirror_axis.value]

            mirror_inst = matrix.Mirror.create(
                instance_name=input_xform.xform_name,
                parent=self,
                input_matrix=input_xform.loc_matrix,
                input_scale_matrix=utils.Matrix.scale_matrix(*mirror_plane_scale_val),
                input_world_matrix=input_xform.world_matrix,
            )

            ws_attr = mirror_inst.container_node[mirror_inst._OUT_MIR_MAT]

            inv_mat = nw.create_node(
                "inverseMatrix", f"{input_xform.xform_name.value}_init_inv"
            )
            inv_mat["inputMatrix"] << ws_attr
            inv_attr = inv_mat["outputMatrix"]

            added_nodes.append(inv_mat)

        sphere_cntrl = control.Sphere.create(
            instance_name=input_xform.xform_name,
            parent=self,
            axis_vec=component_enum_data.AxisEnum.y,
            build_s=0.25,
            color=self.__control_color,
        )
        sphere_cntrl.container_node[sphere_cntrl._IN_OFF_MAT] << ws_attr

        self._set_xform_attrs(
            index=input_len,
            xform_type=self.IO_ENUM.output,
            xform=self.XFORM(
                init_matrix=ws_attr,
                init_inv_matrix=inv_attr,
                world_matrix=sphere_cntrl.container_node[sphere_cntrl._OUT_WS_MAT],
                loc_matrix=sphere_cntrl.container_node[sphere_cntrl._OUT_LOC_MAT],
            ),
        )
        self.__hier._populate_output_xforms()

        self.container_node.add_nodes(*added_nodes)

    def create_correctives(self, parent_xform: component_data.Xform):
        pass


class Mesh(base_comp._Component):
    """contains mesh nodes for character component"""

    class_namespace = "mesh"
    input_node_type = "transform"
    input_node_name = "grp"

    def _override_build(self, **kwargs):
        pass

    def add_mesh(self, mesh: nw.Transform):
        """adds mesh to component

        Args:
            mesh (nw.Transform):
        """
        cmds.parent(str(mesh), str(self.transform_node))
        self.container_node.add_nodes(mesh, include_hierarchy_below=True)
        self.rename_nodes()


class Wrapper(base_comp._Component):
    """Wrapping class with modifiable namespace"""

    input_node_type = "transform"
    input_node_name = "grp"

    @classmethod
    def create(cls, instance_name=None, parent=None, namespace: str = None, **kwargs):
        """Create wrapper instance with namespace being the modified namespace value

        Args:
            instance_name (str, nw.Attr, optional): name of component. Defaults to None.
            parent (nw.Container, Component, optional): Defaults to None.
            namespace (str): Defaults to None

        Returns:
            cls: returns class instance
        """
        return cls._kwarg_create(**cls._process_locals(kwarg_dict=locals()))

    def _override_build(self, namespace, **kwargs):
        """Sets namespace if namespace is not None

        Args:
            namespace (str):
        """
        if namespace is not None:
            self.set_namespace(namespace)

    def set_namespace(self, namespace: str):
        """Sets namespace of component

        Args:
            namespace (str):
        """
        namespace_attr = self.container_node[self._BLD_COMP_NAMESPC][0]
        namespace_attr.set_locked(False)
        namespace_attr[self._BLD_COMP_NAME].set(namespace)
        namespace_attr.set_locked(True)
        self.rename_nodes()


class AxisVectorPicker(base_comp._Component):
    """given 3 axis, and 3 vector outputs primary, secondary, and tertiary vectors

    Attributes:
        _IN_PRM_AXIS (str): str constant for "primaryAxis"
        _IN_SEC_AXIS (str): str constant for "secondaryAxis"
        _IN_TER_AXIS (str): str constant for "tertiaryAxis"
        _IN_X_VEC (str): str constant for "xVec"
        _IN_Y_VEC (str): str constant for "yVec"
        _IN_Z_VEC (str): str constant for "zVec"
        _OUT_PRM_VEC (str): str constant for "PrimaryVec"
        _OUT_SEC_VEC (str): str constant for "SecVec"
        _OUT_TER_VEC (str): str constant for "TerVec"
    """

    _IN_PRM_AXIS = "primaryAxis"
    _IN_SEC_AXIS = "secondaryAxis"
    _IN_TER_AXIS = "tertiaryAxis"

    _IN_X_VEC = "xVec"
    _IN_Y_VEC = "yVec"
    _IN_Z_VEC = "zVec"

    _OUT_PRM_VEC = "PrimaryVec"
    _OUT_SEC_VEC = "SecondaryVec"
    _OUT_TER_VEC = "TertiaryVec"

    def _input_attr_build_data(self):
        """Defines all the added, published, or modified attributes for the
        input node. inherits all input node data from _Component

        Returns:
            comp_data.NodeData:
        """
        node_data = super()._input_attr_build_data()

        node_data.extend_attr_data(
            component_data.AttrData(
                self._IN_PRM_AXIS, type_=component_enum_data.AxisEnum.x, parent=self._IN
            ),
            component_data.AttrData(
                self._IN_SEC_AXIS, type_=component_enum_data.AxisEnum.y, parent=self._IN
            ),
            component_data.AttrData(
                self._IN_TER_AXIS, type_=component_enum_data.AxisEnum.z, parent=self._IN
            ),
            *component_data.double3_attr_data(
                attr_name=self._IN_X_VEC, value=[1, 0, 0], parent=self._IN
            ),
            *component_data.double3_attr_data(
                attr_name=self._IN_Y_VEC, value=[0, 1, 0], parent=self._IN
            ),
            *component_data.double3_attr_data(
                attr_name=self._IN_Z_VEC, value=[0, 0, 1], parent=self._IN
            ),
        )

        return node_data

    def _output_attr_build_data(self):
        """Defines all the added, published, or modified attributes for the
        output node. inherits all output node data from _Component

        Returns:
            comp_data.NodeData:
        """
        node_data = super()._output_attr_build_data()

        node_data.extend_attr_data(
            *component_data.double3_attr_data(
                attr_name=self._OUT_PRM_VEC, parent=self._OUT
            ),
            *component_data.double3_attr_data(
                attr_name=self._OUT_SEC_VEC, parent=self._OUT
            ),
            *component_data.double3_attr_data(
                attr_name=self._OUT_TER_VEC, parent=self._OUT
            ),
        )
        return node_data

    def _override_build(self, **kwargs):
        """Takes care of component creation. adds all nodes needed for
        calculation

        Args:
            control_color (Union[list, utils.Vector, component_enum_data.Color,
            nw.Attr, nw.Node], optional): color for controls. Defaults to None.
        """
        added_nodes = []
        sec_mult = nw.create_node("multiply", "sec_mult")
        sec_mult["input"][0] << self.container_node[self._IN_SEC_AXIS]
        sec_mult["input"][1] = 10

        add_doub_lin = nw.create_node("addDoubleLinear", "prm_sec_combine")
        add_doub_lin["input1"] << sec_mult["output"]
        add_doub_lin["input2"] << self.container_node[self._IN_PRM_AXIS]

        ter_remap = nw.create_node("remapValue", "ter_remap")
        ter_remap["inputValue"] << add_doub_lin["output"]
        ter_remap["outValue"] >> self.container_node[self._IN_TER_AXIS]
        ter_remap["outputMax"] = 5
        ter_remap["inputMax"] = 55

        added_nodes.extend([sec_mult, add_doub_lin, ter_remap])

        axis_dict = {
            str(axis.value): component_enum_data.AxisEnum.index_of(axis)
            for axis in component_enum_data.AxisEnum
        }

        remap_index = 0

        for prim_index, prim_axis in enumerate(component_enum_data.AxisEnum):
            for sec_index, sec_axis in enumerate(component_enum_data.AxisEnum):
                prim_vec = utils.Vector(prim_axis.value)
                sec_vec = utils.Vector(sec_axis.value)

                ter_vec = list(prim_vec ^ sec_vec)
                for index, value in enumerate(ter_vec):
                    if value == 0:
                        ter_vec[index] = 0.0
                ter_vec = str(ter_vec)

                if ter_vec in ["[0.0, 0.0, 0.0]"]:
                    ter_index = prim_index
                else:
                    ter_index = axis_dict[ter_vec]

                out_scalar = ter_index / 5.0
                in_scalar = (prim_index + (sec_index * 10)) / 55.0

                ter_remap["value"][remap_index]["value_FloatValue"].set(out_scalar)
                ter_remap["value"][remap_index]["value_Position"].set(in_scalar - 0.001)
                ter_remap["value"][remap_index]["value_Interp"].set(0)
                remap_index = remap_index + 1

        input_vec_list = []
        for x in range(2):
            for input_vec in [
                self.container_node[self._IN_X_VEC],
                self.container_node[self._IN_Y_VEC],
                self.container_node[self._IN_Z_VEC],
            ]:
                if x == 0:
                    input_vec_list.append(input_vec)
                else:
                    mult_div = nw.create_node(
                        "multiplyDivide", f"neg_{input_vec.short_name}"
                    )
                    mult_div["input1"] << input_vec
                    mult_div["input2"] = [-1, -1, -1]
                    added_nodes.append(mult_div)

                    input_vec_list.append(mult_div["output"])

        in_axis_list = [
            self.container_node[attr_name]
            for attr_name in [self._IN_PRM_AXIS, self._IN_SEC_AXIS, self._IN_TER_AXIS]
        ]
        out_vec_list = [
            self.container_node[attr_name]
            for attr_name in [self._OUT_PRM_VEC, self._OUT_SEC_VEC, self._OUT_TER_VEC]
        ]

        for in_axis, out_vec in zip(in_axis_list, out_vec_list):
            choice = nw.create_node("choice", f"{out_vec.short_name}Choice")
            for index, input_vec in enumerate(input_vec_list):
                choice["input"][index] << input_vec
            choice["selector"] << in_axis
            choice["output"] >> out_vec
            added_nodes.append(choice)

        self.container_node.add_nodes(*added_nodes)


# class LawOfCos(base_comp._Component):
#     def _input_attr_build_data(self):
#         node_data = super()._input_attr_build_data()

#         node_data.extend_attr_data(
#             component_data.AttrData()
#         )
