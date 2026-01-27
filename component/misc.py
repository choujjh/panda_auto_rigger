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
        _IN_CNTRL_CLR_R (str): str constant "controlColorR"
        _IN_CNTRL_CLR_G (str): str constant "controlColorG"
        _IN_CNTRL_CLR_B (str): str constant "controlColorB"
        _IN_SETUP_CLR (str): str constant "setupColor"
        _IN_SETUP_CLR_R (str): str constant "setupColorR"
        _IN_SETUP_CLR_G (str): str constant "setupColorG"
        _IN_SETUP_CLR_B (str): str constant "setupColorB"
        _PRM_VEC (str): str constant "primaryVec"
        _PRM_VEC_X (str): str constant "primaryVecX"
        _PRM_VEC_Y (str): str constant "primaryVecY"
        _PRM_VEC_Z (str): str constant "primaryVecZ"
        _SEC_VEC (str): str constant "secondaryVec"
        _SEC_VEC_X (str): str constant "secondaryVecX"
        _SEC_VEC_Y (str): str constant "secondaryVecY"
        _SEC_VEC_Z (str): str constant "secondaryVecZ"
        _TER_VEC (str): str constant "tertiaryVec"
        _TER_VEC_X (str): str constant "tertiaryVecX"
        _TER_VEC_Y (str): str constant "tertiaryVecY"
        _TER_VEC_Z (str): str constant "tertiaryVecZ"

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
    _IN_CNTRL_CLR_R = "controlColorR"
    _IN_CNTRL_CLR_G = "controlColorG"
    _IN_CNTRL_CLR_B = "controlColorB"
    _IN_SETUP_CLR = "setupColor"
    _IN_SETUP_CLR_R = "setupColorR"
    _IN_SETUP_CLR_G = "setupColorG"
    _IN_SETUP_CLR_B = "setupColorB"

    _PRM_VEC = base_comp._Hierarchy._PRM_VEC
    _PRM_VEC_X = base_comp._Hierarchy._PRM_VEC_X
    _PRM_VEC_Y = base_comp._Hierarchy._PRM_VEC_Y
    _PRM_VEC_Z = base_comp._Hierarchy._PRM_VEC_Z
    _SEC_VEC = base_comp._Hierarchy._SEC_VEC
    _SEC_VEC_X = base_comp._Hierarchy._SEC_VEC_X
    _SEC_VEC_Y = base_comp._Hierarchy._SEC_VEC_Y
    _SEC_VEC_Z = base_comp._Hierarchy._SEC_VEC_Z
    _TER_VEC = base_comp._Hierarchy._TER_VEC
    _TER_VEC_X = base_comp._Hierarchy._TER_VEC_X
    _TER_VEC_Y = base_comp._Hierarchy._TER_VEC_Y
    _TER_VEC_Z = base_comp._Hierarchy._TER_VEC_Z

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
            component_data.AttrData(
                self._IN_CNTRL_CLR, type_="double3", parent=self._IN
            ),
            component_data.AttrData(
                self._IN_CNTRL_CLR_R, type_="double", parent=self._IN_CNTRL_CLR
            ),
            component_data.AttrData(
                self._IN_CNTRL_CLR_G, type_="double", parent=self._IN_CNTRL_CLR
            ),
            component_data.AttrData(
                self._IN_CNTRL_CLR_B, type_="double", parent=self._IN_CNTRL_CLR
            ),
            component_data.AttrData(
                self._IN_SETUP_CLR, type_="double3", parent=self._IN
            ),
            component_data.AttrData(
                self._IN_SETUP_CLR_R, type_="double", parent=self._IN_SETUP_CLR
            ),
            component_data.AttrData(
                self._IN_SETUP_CLR_G, type_="double", parent=self._IN_SETUP_CLR
            ),
            component_data.AttrData(
                self._IN_SETUP_CLR_B, type_="double", parent=self._IN_SETUP_CLR
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
            component_data.AttrData(
                self._PRM_VEC, type_="double3", parent=self._OUT, value=[1, 0, 0]
            ),
            component_data.AttrData(
                self._PRM_VEC_X, type_="double", parent=self._PRM_VEC
            ),
            component_data.AttrData(
                self._PRM_VEC_Y, type_="double", parent=self._PRM_VEC
            ),
            component_data.AttrData(
                self._PRM_VEC_Z, type_="double", parent=self._PRM_VEC
            ),
            component_data.AttrData(
                self._SEC_VEC, type_="double3", parent=self._OUT, value=[0, 1, 0]
            ),
            component_data.AttrData(
                self._SEC_VEC_X, type_="double", parent=self._SEC_VEC
            ),
            component_data.AttrData(
                self._SEC_VEC_Y, type_="double", parent=self._SEC_VEC
            ),
            component_data.AttrData(
                self._SEC_VEC_Z, type_="double", parent=self._SEC_VEC
            ),
            component_data.AttrData(
                self._TER_VEC, type_="double3", parent=self._OUT, value=[0, 0, 1]
            ),
            component_data.AttrData(
                self._TER_VEC_X, type_="double", parent=self._TER_VEC
            ),
            component_data.AttrData(
                self._TER_VEC_Y, type_="double", parent=self._TER_VEC
            ),
            component_data.AttrData(
                self._TER_VEC_Z, type_="double", parent=self._TER_VEC
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
