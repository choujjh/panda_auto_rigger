import system.base_component as base_comp
import utils.node_wrapper as nw
import system.component_data as component_data
import system.component_enum_data as component_enum_data
from typing import Union

import utils.utils as utils
import maya.cmds as cmds


class _Hierarchy(base_comp._Component):
    """A Class meant to be inherited for all hierarchy classes. hierarchy in this
    case is defined as a chain of matricies

    Attributes:
        HIER_DATA (component_data.HierData): constant for HierData class. easier for in class use
        IO_ENUM (component_enum_data.IO): constant for component_enum_data.IO class. easier for in class use
        XFORM (component_data.Xform): constant for xform class. easier for in class use
        HIER_PARENT (component_data.hierParent) constant for HierParent class. easier for in class use
        _max_num_xforms (tuple(int)): sets length of input and output xforms for initialization. -1 for no length
        _populate_output (bool): setting to populate output xforms in post_build
        _check_output (bool): setting to see if output xforms are checked

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

    class_namespace = "hier"
    component_type = component_enum_data.ComponentType.hier
    _max_num_xforms = (-1, -1)
    _populate_output = True
    _check_output = True

    HIER_DATA = component_data.HierData
    IO_ENUM = component_enum_data.IO
    XFORM = component_data.Xform
    HIER_PARENT = component_data.HierParent
    _PRM_VEC = "primaryVec"
    _PRM_VEC_X = "primaryVecX"
    _PRM_VEC_Y = "primaryVecY"
    _PRM_VEC_Z = "primaryVecZ"
    _SEC_VEC = "secondaryVec"
    _SEC_VEC_X = "secondaryVecX"
    _SEC_VEC_Y = "secondaryVecY"
    _SEC_VEC_Z = "secondaryVecZ"
    _TER_VEC = "tertiaryVec"
    _TER_VEC_X = "tertiaryVecX"
    _TER_VEC_Y = "tertiaryVecY"
    _TER_VEC_Z = "tertiaryVecZ"

    def _input_attr_build_data(self):
        """Defines all the added, published, or modified attributes for the
        input node. inherits all input node data from _Component

        Returns:
            comp_data.NodeData:
        """
        node_data = super()._input_attr_build_data()
        node_data.extend_attr_data(self.HIER_DATA.get_hier_parent_data())
        node_data.extend_attr_data(self.HIER_DATA.get_xform_data(self.IO_ENUM.input))
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
        parent: Union[base_comp._Component, nw.Container] = None,
        input_xforms: Union[list[component_data.Xform], int] = None,
        source_component: "_Hierarchy" = None,
        connect_parent_hier: bool = True,
        connect_axis_vecs: bool = True,
        control_color: Union[
            list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node
        ] = None,
    ):
        """Class method to create component

        Args:
            instance_name (Union[str, nw.Attr], optional): name of component. Defaults to None.
            parent (Union[_Component, nw.Container], optional): Defaults to None.
            input_xforms (Union[list[component_data.Xform], int], optional): input xforms to initialize component with. Defaults to None.
            source_component (_Hierarchy, optional): source component to connect hierarchy from. Defaults to None.
            connect_parent_hier (bool, optional): Defaults to True.
            connect_axis_vecs (bool, optional): Defaults to True.
            control_color (Union[list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node], optional): Defaults to None.

        Returns:
            _Hierarchy:
        """
        return cls._kwarg_create(**cls._process_locals(kwarg_dict=locals()))

    def _pre_build(
        self,
        instance_name: Union[str, nw.Attr] = None,
        parent: Union[base_comp._Component, nw.Container] = None,
        input_xforms: Union[list[component_data.Xform], int] = None,
        source_component: "_Hierarchy" = None,
        connect_parent_hier: bool = True,
        connect_axis_vecs: bool = True,
        **kwargs,
    ):
        """Handles creation and connection of initial nodes

        Args:
            instance_name (Union[str, nw.Attr], optional): name of component. Defaults to None.
            parent (Union[_Component, nw.Container], optional): Defaults to None.
            input_xforms (Union[list[component_data.Xform], int], optional): input xforms to initialize component with. Defaults to None.
            source_component (_Hierarchy, optional):  source component to connect hierarchy from. Defaults to None.
            connect_parent_hier (bool, optional): Defaults to None.
            connect_axis_vecs (bool, optional): Defaults to True.
        """
        super()._pre_build(instance_name, parent)

        source_xforms = None
        if source_component is not None and hasattr(
            source_component, "get_as_source_xforms"
        ):
            source_xforms = source_component.get_as_source_xforms(
                is_parent_component=utils.if_container_is_ancestor(
                    child=self.container_node, ancestor=source_component.container_node
                )
            )

        self._initialize_input_xform(
            input_xforms=input_xforms, source_xforms=source_xforms
        )

        # connect source component
        if source_component is not None:
            self._connect_source_component(
                source_component=source_component,
                connect_parent_hier=connect_parent_hier,
                connect_axis_vec=connect_axis_vecs,
            )

    def _override_build(
        self,
        control_color: Union[
            list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node
        ] = None,
        **kwargs,
    ):
        """Takes care of derived component creation. must be implemented by child class

        Args:
            control_color (Union[list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node], optional): color for controls. Defaults to None.
        """
        super()._override_build(**kwargs)

    def _post_build(self, **kwargs):
        """Build cleanup. sets build to true renames nodes, also tries to connect
        xform matricies and names. then raises warnings for any xform attribute not connected
        """
        super()._post_build()
        if type(self)._populate_output:
            self._populate_output_xforms()
        self.rename_nodes()
        if type(self)._check_output:
            self._check_output_xforms()

    # pre build
    def _initialize_input_xform(
        self,
        input_xforms: Union[list[component_data.Xform], int] = None,
        source_xforms: list = None,
    ):
        """Initializes input xform

        Args:
            input_xforms (Union[list[component_data.Xform], int], optional): Defaults to [].
            source_xforms (list, optional): Defaults to None.
            disable_warning (bool):

        Raises:
            RuntimeError: if list contains item that is not component_data
        """
        max_input_len, max_output_len = type(self)._max_num_xforms
        input_xforms_len = 0
        if max_input_len == -1 and source_xforms is not None:
            max_input_len = len(source_xforms)
        elif max_input_len == -1 and isinstance(input_xforms, int):
            max_input_len = input_xforms
        elif max_input_len == -1 and isinstance(input_xforms, list):
            input_xforms_len = len(input_xforms)
            max_input_len = input_xforms_len
        elif max_input_len == -1:
            max_input_len = -1
            cmds.warning(f"{self.container_node} xforms not initialized")
        elif isinstance(input_xforms, list):
            input_xforms_len = len(input_xforms)

        if max_output_len < max_input_len:
            max_output_len = max_input_len

        for index in range(max_output_len):
            # input
            init_xform = self.XFORM(xform_name=f"xform{index}")
            if index < max_input_len:
                input_xform = init_xform
                if index < input_xforms_len:
                    input_xform = input_xforms[index]
                self._set_xform_attrs(
                    index=index,
                    xform_type=self.IO_ENUM.input,
                    xform=input_xform,
                    set_when_data_is_attr=True,
                )
            self._set_xform_attrs(
                index=index,
                xform_type=self.IO_ENUM.output,
                xform=init_xform,
                set_when_data_is_attr=True,
            )

    def __populate_name(self, index: int):
        """Given the index tries to connect or set the output name

        Args:
            index (int): xform index
        """
        # set variables
        output_name = self.output_node[self.HIER_DATA.OUT_XFORM][index][
            self.HIER_DATA.OUT_XFORM_NAME
        ]
        if output_name.has_src_connection():
            return
        input_name = self.input_node[self.HIER_DATA.IN_XFORM][index][
            self.HIER_DATA.IN_XFORM_NAME
        ]
        output_ws_src = self.output_node[self.HIER_DATA.OUT_XFORM][index][
            self.HIER_DATA.OUT_WORLD_MAT
        ].get_src_connection()

        # check if needs to be set
        if output_name.value is not None and output_name.value != "":
            pass

        # if input and output xform match
        elif len(self.input_node[self.HIER_DATA.IN_XFORM]) >= len(
            self.output_node[self.HIER_DATA.OUT_XFORM]
        ):
            input_name >> output_name

        elif output_ws_src is not None:
            if output_ws_src.node.has_attr(self._BLD_INST_NAME):
                output_ws_src.node[self._BLD_INST_NAME] >> output_name

    def __populate_world_matrix(
        self,
        index: int,
        world_matrix_attr: nw.Attr,
        world_matrix_inv_attr: nw.Attr,
        is_init_matrix: bool = False,
    ):
        """Given the index tries to connect or set the output init matrix and output inverse init matrix

        Args:
            index (int): xform index
        """
        matrix_src = world_matrix_attr.get_src_connection()
        inv_matrix_src = world_matrix_inv_attr.get_src_connection()
        input_xform = self.get_xform_attrs(xform_type=self.IO_ENUM.input)
        output_xform = self.get_xform_attrs(xform_type=self.IO_ENUM.output)

        inverse_name = f"xform{index}_inverse"
        if is_init_matrix:
            inverse_name = f"xform{index}_init_inverse"

        added_nodes = []
        # pre check to see if it needs to return anything
        if inv_matrix_src is not None and matrix_src is not None:
            return []
        if inv_matrix_src is None and matrix_src is not None:
            if isinstance(matrix_src.node, nw.Transform):
                matrix_src.node["worldInverseMatrix"][0] >> world_matrix_inv_attr
            else:
                matrix_src_connections = [
                    attr.node
                    for attr in matrix_src.get_dest_connections()
                    if attr.node.type_ == "inverseMatrix"
                ]
                if matrix_src_connections == []:
                    inverse_node = nw.create_node("inverseMatrix", name=inverse_name)
                    inverse_node["inputMatrix"] << matrix_src
                    inverse_node["outputMatrix"] >> world_matrix_inv_attr
                    added_nodes.append(inverse_node)
                else:
                    matrix_src_connections[0]["outputMatrix"] >> world_matrix_inv_attr
        elif matrix_src is None and inv_matrix_src is not None:
            if isinstance(inv_matrix_src.node, nw.Transform):
                inv_matrix_src.node["worldMatrix"][0] >> world_matrix_attr
            elif inv_matrix_src.node.type_ == "inverseMatrix":
                new_matrix_src = inv_matrix_src.node["inputMatrix"].get_src_connection()
                if new_matrix_src is not None:
                    new_matrix_src >> world_matrix_attr

        elif world_matrix_attr.attr_name.find("Init") >= 0 and len(
            input_xform.keys()
        ) == len(output_xform.keys()):
            if matrix_src is None:
                input_xform[index].init_matrix >> world_matrix_attr
            if inv_matrix_src is None:
                input_xform[index].init_inv_matrix >> world_matrix_inv_attr

        return added_nodes

    def __populate_loc_matrix(self, index: int):
        """Given the index tries to connect or set the output local matrix

        Args:
            index (int): xform index
        """
        output_xform = self.get_xform_attrs(xform_type=self.IO_ENUM.output, index=index)
        output_loc_matrix = output_xform.loc_matrix
        output_world_matrix_src = output_xform.world_matrix.get_src_connection()
        added_nodes = []

        if output_loc_matrix.has_src_connection():
            return []
        elif output_world_matrix_src is None:
            return []

        # connect to parent
        else:
            if index == 0:
                prev_world_inv_matrix_src = self.container_node[
                    self.HIER_DATA.HIER_PAR_INV_MAT
                ]
            else:
                prev_world_inv_matrix_src = self.container_node[
                    self.HIER_DATA.OUT_XFORM
                ][index - 1][self.HIER_DATA.OUT_WORLD_INV_MAT]
                prev_world_inv_matrix_src = (
                    prev_world_inv_matrix_src.get_src_connection()
                )
            if prev_world_inv_matrix_src is None:
                return []

            # adding matrix mult
            mat_mult = nw.create_node("multMatrix", f"xform{index}_loc_output_matMult")
            mat_mult["matrixIn"][0] << output_world_matrix_src
            mat_mult["matrixIn"][1] << prev_world_inv_matrix_src
            mat_mult["matrixSum"] >> output_loc_matrix

            added_nodes.append(mat_mult)

            return added_nodes

    def __populate_init_loc_matrix(self, index: int):
        """Given the index tries to connect or set the output init local matrix

        Args:
            index (int):
        """
        input_xform = self.get_xform_attrs(index=index, xform_type=self.IO_ENUM.input)
        output_xform = self.get_xform_attrs(index=index, xform_type=self.IO_ENUM.output)

        if output_xform.init_loc_matrix.has_src_connection():
            return []

        if index > 0:
            parent_init_inv_src = self.get_xform_attrs(
                index=index - 1, xform_type=self.IO_ENUM.output
            ).init_inv_matrix.get_src_connection()
        else:
            parent_init_inv_src = self.get_hier_parent_attrs().init_inv_matrix

        world_init_src = output_xform.init_matrix.get_src_connection()

        if index > 0:
            parent_xform = self.get_xform_attrs(
                index=index - 1, xform_type=self.IO_ENUM.input
            )
            if (
                parent_xform.init_inv_matrix == parent_init_inv_src
                and world_init_src == input_xform.init_matrix
            ):
                self._set_xform_attrs(
                    index=index,
                    xform_type=self.IO_ENUM.output,
                    xform=self.XFORM(init_loc_matrix=input_xform.init_loc_matrix),
                )
                return []

        if parent_init_inv_src is not None and world_init_src is not None:
            mult_matrix = nw.create_node("multMatrix", f"xform{index}_init_loc_matMult")
            mult_matrix["matrixIn"][0] << world_init_src
            mult_matrix["matrixIn"][1] << parent_init_inv_src

            self._set_xform_attrs(
                index=index,
                xform_type=self.IO_ENUM.output,
                xform=self.XFORM(init_loc_matrix=mult_matrix["matrixSum"]),
            )

            return [mult_matrix]

        return []

        # and world_init_src is not None and

    def __populate_parent_world_init_loc_matrix(self, index: int):
        """Given the index tries to connect or set the output init local matrix

        Args:
            index (int):
        """
        input_xform = self.get_xform_attrs(index=index, xform_type=self.IO_ENUM.input)
        output_xform = self.get_xform_attrs(index=index, xform_type=self.IO_ENUM.output)

        if output_xform.parent_world_init_loc_matrix.has_src_connection():
            return []

        if index > 0:
            parent_world_src = self.get_xform_attrs(
                index=index - 1, xform_type=self.IO_ENUM.output
            ).world_matrix.get_src_connection()
        else:
            parent_world_src = self.get_hier_parent_attrs().matrix

        init_loc_matrix_src = output_xform.init_loc_matrix.get_src_connection()

        if index > 0:
            parent_xform = self.get_xform_attrs(
                index=index - 1, xform_type=self.IO_ENUM.input
            )
            if (
                parent_xform.world_matrix == parent_world_src
                and init_loc_matrix_src == input_xform.init_loc_matrix
            ):
                self._set_xform_attrs(
                    index=index,
                    xform_type=self.IO_ENUM.output,
                    xform=self.XFORM(
                        parent_world_init_loc_matrix=input_xform.parent_world_init_loc_matrix
                    ),
                )
                return []

        if parent_world_src is not None and init_loc_matrix_src is not None:
            mult_matrix = nw.create_node(
                "multMatrix", f"xform{index}_parent_world_init_local_matMult"
            )
            mult_matrix["matrixIn"][0] << init_loc_matrix_src
            mult_matrix["matrixIn"][1] << parent_world_src

            self._set_xform_attrs(
                index=index,
                xform_type=self.IO_ENUM.output,
                xform=self.XFORM(parent_world_init_loc_matrix=mult_matrix["matrixSum"]),
            )

            return [mult_matrix]

        return []

    def _populate_output_xforms(self):
        """Goes through the output xform attributes and tries to connect name, local matrix, and init matricies"""
        added_nodes = []
        output_xforms = self.get_xform_attrs(xform_type=self.IO_ENUM.output)
        for index, output_xform in output_xforms.items():
            self.__populate_name(index)
            added_nodes.extend(
                self.__populate_world_matrix(
                    index=index,
                    world_matrix_attr=output_xform.init_matrix,
                    world_matrix_inv_attr=output_xform.init_inv_matrix,
                    is_init_matrix=True,
                )
            )
            added_nodes.extend(
                self.__populate_world_matrix(
                    index=index,
                    world_matrix_attr=output_xform.world_matrix,
                    world_matrix_inv_attr=output_xform.world_inv_matrix,
                )
            )
            added_nodes.extend(self.__populate_loc_matrix(index=index))
            added_nodes.extend(self.__populate_init_loc_matrix(index=index))
            added_nodes.extend(
                self.__populate_parent_world_init_loc_matrix(index=index)
            )

        # add nodes to container
        self.container_node.add_nodes(*added_nodes)

    def _connect_source_component(
        self,
        source_component: "_Hierarchy",
        connect_parent_hier: bool = True,
        connect_axis_vec: bool = True,
    ):
        """Given a source Hier component connects it's hier output to this component's hier input

        Args:
            source_component (Component):
            connect_hierarchy (bool): connects hierarchy from source
            connect_axis_vec (bool): connects axis vec from source
        """
        # getting both containers
        self_container = self.container_node
        source_container = source_component.container_node

        source_xforms = source_component.get_as_source_xforms(
            is_parent_component=utils.if_container_is_ancestor(
                child=self.container_node, ancestor=source_component.container_node
            )
        )

        max_input_xform = type(self)._max_num_xforms[0]
        if max_input_xform >= 0 and max_input_xform < len(source_xforms):
            source_xforms = source_xforms[:max_input_xform]
        for index, xform in enumerate(source_xforms):
            self._set_xform_attrs(
                index=index,
                xform_type=self.IO_ENUM.input,
                xform=xform,
            )

        # if connect_hierarchy
        if connect_parent_hier:
            self._set_hier_parent_attrs(source_component.get_hier_parent_attrs())

        # connecting axis vectors
        if connect_axis_vec:
            for attr in [self._PRM_VEC, self._SEC_VEC, self._TER_VEC]:
                if source_container.has_attr(attr) and self_container.has_attr(attr):
                    source_container[attr] >> self_container[attr]

    # post build
    def _check_output_xforms(self, check_len: bool = True):
        """After component is built, checks to see if xforms were properly set

        Args:
            check_len (bool, optional): Defaults to True.
        """
        if check_len:
            input_xform_len = len(self.input_node[self.HIER_DATA.IN_XFORM])
            output_xform_len = len(self.output_node[self.HIER_DATA.OUT_XFORM])
            if output_xform_len == 0:
                cmds.warning(f"{self.container_node} component has no xform output")

            if input_xform_len > output_xform_len:
                cmds.warning(
                    f"input xform (len {input_xform_len}) longer than output xform (len {output_xform_len})"
                )

        for xform_attr in self.output_node[self.HIER_DATA.OUT_XFORM]:
            xform = self.XFORM(xform_attr)
            for attr in xform.attrs:
                if attr.type_ == "string":
                    if attr.value is None or attr.value == "":
                        cmds.warning(f"{attr} not set")
                elif not attr.has_src_connection():
                    cmds.warning(f"{attr} does not have connection")

    def get_as_source_xforms(self, is_parent_component=True):
        """When it is the source component returns xforms to be plugged in

        Args:
            is_parent_component (bool, optional): if parent component gives different xform. Defaults to True.

        Returns:
            list(component_data.Xform):
        """
        xform_type = self.IO_ENUM.input if is_parent_component else self.IO_ENUM.output
        return [x for x in self.get_xform_attrs(xform_type=xform_type).values()]

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
        if index is None:
            input_len = 0
            if self.container_node.has_attr(self.HIER_DATA.IN_XFORM):
                input_len = len(self.container_node[self.HIER_DATA.IN_XFORM])
            if self.HIER_DATA.is_input_enum(xform_type):
                indicies = utils.length_index_list(input_len)
            else:
                output_len = len(self.container_node[self.HIER_DATA.OUT_XFORM])
                if output_len > input_len:
                    indicies = utils.length_index_list(output_len)
                else:
                    indicies = utils.length_index_list(input_len)
        else:
            indicies = utils.make_iterable(index)
        xform_parent_name = self.HIER_DATA.get_xform_parent_name(xform_type=xform_type)
        xform_data = {
            index: self.XFORM(self.container_node[xform_parent_name][index])
            for index in indicies
        }
        if isinstance(index, int) and index is not None:
            return list(xform_data.values())[0]
        else:
            return xform_data

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
        set_xform = self.get_xform_attrs(xform_type=xform_type, index=index)
        for xform_attr, set_xform_attr in zip(xform, set_xform):
            if xform_attr is not None:
                utils.set_connect_attr_data(
                    attr=set_xform_attr,
                    data=xform_attr,
                    set_when_data_is_attr=set_when_data_is_attr,
                )

    def get_hier_parent_attrs(self):
        """gets hier parent attr and wraps it in HierParent class

        Returns:
            component_data.HierParent:
        """

        return self.HIER_PARENT(self.container_node[self.HIER_DATA.HIER_PAR])

    def _set_hier_parent_attrs(
        self,
        hier_parent: component_data.HierParent,
        set_when_data_is_attr: bool = False,
    ):
        """Sets HierParent

        Args:
            hier_parent (component_data.HierParent):
            set_when_data_is_attr (bool, optional): Defaults to False.
            disable_warning (bool, optional): Defaults to False.
        """
        for hier_parent, set_hier_parent in zip(
            hier_parent, self.get_hier_parent_attrs()
        ):
            if hier_parent is not None:
                utils.set_connect_attr_data(
                    attr=set_hier_parent,
                    data=hier_parent,
                    set_when_data_is_attr=set_when_data_is_attr,
                )

    # hooking
    def hook(self, hook_src_data, hook_mirror_component: bool = True):
        """Hooks xform to hier parent

        Args:
            hook_src_data (any): hook data that will be setting the hier parent
            hook_mirror(bool): also hooks mirror to it's corresponding source

        """
        # get parent hier that can be hooked first
        hier_parent = self.get_hook_hier_parent()

        self.unhook(unhook_mirror_component=hook_mirror_component)
        # convert hook data (go from highest level hier)
        hier_src_data = self.get_hook_source_data(hook_src_data=hook_src_data)

        for hook_src, hook_hier_parent in zip(hier_src_data, hier_parent):
            utils.set_connect_attr_data(attr=hook_hier_parent, data=hook_src)

        if hook_mirror_component:
            self._hook_mirror_component()

    def unhook(self, unhook_mirror_component: bool = True):
        """Unhooks Hierarchy

        Args:
            unhook_mirror_component (bool, optional): unhooks mirror component. Defaults to True.
        """
        hier_parent = self.get_hook_hier_parent()

        for attr in hier_parent:
            if attr.has_src_connection():
                ~attr
        if unhook_mirror_component:
            self.__unhook_mirror_component()

    def _hook_mirror_component(self):
        """Hooking the mirror component"""
        mirror_component = self.get_mirror_component()
        if mirror_component is None:
            return

        hook_src = self.get_hook_hier_parent()
        hook_src.matrix = hook_src.matrix.get_src_connection()
        hook_src.inv_matrix = hook_src.inv_matrix.get_src_connection()
        hook_src.init_inv_matrix = hook_src.init_inv_matrix.get_src_connection()

        if hook_src.matrix is not None:
            hook_src_cntnr = hook_src.matrix.node.get_container_node()
            if hook_src_cntnr is not None:
                mirror_hook_src_cntnr = base_comp.get_component(hook_src_cntnr)
                mirror_hook_src_cntnr = mirror_hook_src_cntnr.get_mirror_component()
                # TODO rather find the node of each attribute then try to find it in the published container_nodes
                if mirror_hook_src_cntnr is not None:
                    hook_src.matrix = mirror_hook_src_cntnr.container_node[
                        hook_src.matrix.attr_name
                    ]
                    hook_src.inv_matrix = mirror_hook_src_cntnr.container_node[
                        hook_src.inv_matrix.attr_name
                    ]
                    hook_src.init_inv_matrix = mirror_hook_src_cntnr.container_node[
                        hook_src.init_inv_matrix.attr_name
                    ]

        if [x for x in hook_src.attrs if x is not None] == []:
            return

        mirror_component.hook(hook_src, hook_mirror_component=False)

    def __unhook_mirror_component(self):
        """Unhook Mirror component"""
        mirror_component = self.get_mirror_component()
        if mirror_component is not None:
            mirror_component.unhook(unhook_mirror_component=False)

    def __get_hier_parent_source(self, hier_parent: component_data.HierParent):
        """Gets hier parent source and casts it to hier parent. returns none if source is not hier parent

        Args:
            hier_parent (component_data.HierParent):

        Returns:
            component_data.HierParent:
        """
        hier_parent_attr = None
        for attr in hier_parent.attrs:
            # has source connection
            if attr.has_src_connection():
                src_connection = attr.get_src_connection()
                if src_connection.parent is not None:
                    connection_parent = src_connection.parent
                    hier_parent_attr = connection_parent
                    if self.HIER_DATA.is_hier_parent_attr(connection_parent):
                        continue
            return None
        return self.HIER_PARENT(hier_parent_attr=hier_parent_attr)

    def get_hook_hier_parent(self):
        """gets setable hier parent meaning hier parent isn't connected to another hier parent

        Returns:
            component_data.HierParent:
        """
        curr_hier_parent = self.get_hier_parent_attrs()
        while True:
            next_hier_parent = self.__get_hier_parent_source(curr_hier_parent)
            if next_hier_parent is None:
                return curr_hier_parent
            curr_hier_parent = next_hier_parent

    def get_hook_source_data(self, hook_src_data):
        """converts hook_src_data to component_data.hierParent

        Args:
            hook_src_data (any):

        Returns:
            component_data.hierParent:
        """
        control_inst = None
        if isinstance(hook_src_data, self.HIER_PARENT):
            return hook_src_data
        if isinstance(hook_src_data, nw.Attr) and (
            self.HIER_DATA.is_input_xform_attr(hook_src_data)
            or self.HIER_DATA.is_output_xform_attr(hook_src_data)
        ):
            return component_data.xform_to_hier_parent(
                self.get_hook_xform(hook_src_data)
            )
        if (
            isinstance(hook_src_data, nw.Transform)
            and hook_src_data.get_container_node() is not None
        ):
            control_inst = base_comp.get_component(hook_src_data.get_container_node())
        elif isinstance(hook_src_data, nw.Transform):
            return self.HIER_PARENT(
                matrix=hook_src_data["worldMatrix"][0],
                inv_matrix=hook_src_data["worldInverseMatrix"][0],
                init_inv_matrix=hook_src_data["worldInverseMatrix"][0].value,
            )

        if issubclass(type(hook_src_data), _Hierarchy):
            hook_xform = self.get_hook_xform(
                hook_src_data.container_node[self.HIER_DATA.IN_XFORM][0]
            )
            return component_data.xform_to_hier_parent(hook_xform)
        from component.control import _Control

        if issubclass(type(hook_src_data), _Control):
            control_inst = hook_src_data

        if control_inst is not None:
            cntrl_map_attr = control_inst.container_node[control_inst._CNTNR_CNTRL_MAP]
            parent_component = base_comp.get_component(
                control_inst.container_node.get_container_node()
            )
            if parent_component is not None:
                if cntrl_map_attr.has_src_connection():
                    connection = cntrl_map_attr.get_src_connection()
                    if issubclass(type(parent_component), _Hierarchy):
                        hook_xform = self.get_hook_xform(
                            parent_component.container_node[self.HIER_DATA.IN_XFORM][
                                connection.index
                            ]
                        )
                        return component_data.xform_to_hier_parent(hook_xform)
                else:
                    hook_xform = self.get_hook_xform(
                        parent_component.container_node[self.HIER_DATA.IN_XFORM][0]
                    )
                    return component_data.xform_to_hier_parent(hook_xform)
            else:
                return self.HIER_PARENT(
                    matrix=control_inst.transform_node["worldMatrix"][0],
                    inv_matrix=control_inst.transform_node["worldInverseMatrix"][0],
                    init_inv_matrix=control_inst.transform_node["worldInverseMatrix"][
                        0
                    ].value,
                )

    def get_hook_xform(
        self, xform_attr: nw.Attr, ancestor_hier_comp: "_Hierarchy" = None
    ):
        """Gets hook xform at the end of chain that can be used to set hook data

        Args:
            xform (nw.Attr):
            ancestor_hier_comp (_Hierarchy): ancestor to look for if its in xform_attr's ancestors
        Raises:
            RuntimeError: not an xform attribute
            RuntimeError: xform not part of a hierarchy component
            RuntimeError: xform has more than one connection to output node

        Returns:
            component_data.Xform:
        """
        HIER_DATA = self.HIER_DATA

        # error checking
        if not self.HIER_DATA.is_input_xform_attr(
            xform_attr
        ) and HIER_DATA.is_output_xform_attr(xform_attr):
            raise RuntimeError(f"{xform_attr} is not xform attribute")
        if not issubclass(
            utils.string_to_class(
                xform_attr.node.get_container_node()[self._BLD_COMP_CLASS].value
            ),
            _Hierarchy,
        ):
            raise RuntimeError(
                f"xform not attached to hierarchy component. {xform_attr.node.get_container_node()} is not hierarchy component"
            )

        # ancestor hier
        ancestors = self.__get_hierarchy_ancestors(xform_attr.node.get_container_node())
        if (
            ancestor_hier_comp is not None
            and ancestor_hier_comp.container_node in ancestors
        ):
            ancestor = ancestor_hier_comp.container_node
        else:
            ancestor = ancestors[-1]

        # going from xform to xform
        while not (
            HIER_DATA.is_output_xform_attr(xform_attr)
            and xform_attr.node.get_container_node() == ancestor
        ):
            xform = self.XFORM(xform_attr)
            container = xform_attr.node.get_container_node()

            # input to output
            if HIER_DATA.is_input_xform_attr(xform_attr):
                if len(container[HIER_DATA.IN_XFORM]) == len(
                    container[HIER_DATA.OUT_XFORM]
                ):
                    xform_attr = container[HIER_DATA.OUT_XFORM][xform_attr.index]
                    continue

            # connect to next xform
            xform_connections = [
                attr.parent
                for attr in xform.init_matrix.get_dest_connections()
                if attr.parent is not None
                and (
                    HIER_DATA.is_input_xform_attr(attr.parent)
                    or HIER_DATA.is_output_xform_attr(attr.parent)
                )
            ]
            output_connections = [
                attr
                for attr in xform_connections
                if HIER_DATA.is_output_xform_attr(attr)
            ]
            if len(output_connections) != 0:
                xform_attr = output_connections[0]
                continue
            if len(xform_connections) != 0:
                xform_attr = xform_connections[0]
                continue

            # if connections is none try loc matrix
            if HIER_DATA.is_output_xform_attr(xform_attr):
                index = xform_attr.index
                connected_containers = []
                for attr in xform.loc_matrix.get_dest_connections():
                    container = attr.node.get_container_node()
                    if (
                        container is not None
                        and container.has_attr(self._BLD_COMP_CLASS)
                        and issubclass(
                            utils.string_to_class(
                                container[self._BLD_COMP_CLASS].value
                            ),
                            _Hierarchy,
                        )
                    ):
                        connected_containers.append(container)
                if len(connected_containers) != 0:
                    xform_attr = connected_containers[0][HIER_DATA.IN_XFORM][index]
                    continue

            # if connection is still none then break
            break

        return self.XFORM(xform_attr)

    def __get_hierarchy_ancestors(self, container: nw.Container):
        """Gets all ancestors that's of Hierarchy class/subclass

        Returns:
            list[nw.Container]:
        """
        if container is None:
            return None
        ancestor_containers = [container]
        while True:
            parent_container = ancestor_containers[-1].get_container_node()
            if parent_container is None or not parent_container.has_attr(
                self._BLD_COMP_CLASS
            ):
                return ancestor_containers
            if not issubclass(
                utils.string_to_class(parent_container[self._BLD_COMP_CLASS].value),
                _Hierarchy,
            ):
                return ancestor_containers
            ancestor_containers.append(parent_container)

    # other functionality
    def _create_orient_translate_blend(
        self,
        name: str,
        matrix_attr: nw.Attr,
        tx_attr: nw.Attr = None,
        ty_attr: nw.Attr = None,
        tz_attr: nw.Attr = None,
        tw_attr: nw.Attr = None,
    ):
        """Creates a blended matrix where the translate values are overriden

        Args:
            name (str):
            matrix_attr (nw.Attr): matrix to blend from
            tx_attr (nw.Attr): translate X attr. Defaults to None.
            ty_attr (nw.Attr): translate Y attr. Defaults to None.
            tz_attr (nw.Attr): translate Z attr. Defaults to None.
            tw_attr (nw.Attr, optional): translate W attr. Defaults to None.
        """
        row_nodes = []
        matrix_4x4 = nw.create_node("fourByFourMatrix", f"{name}_4x4_mat")
        # translate matrix
        for index, t_attr in enumerate([tx_attr, ty_attr, tz_attr, tw_attr]):
            if t_attr is not None:
                matrix_4x4[f"in3{index}"] << t_attr

        # orient part of the matrix
        for row_index in range(3):
            row_node = nw.create_node("rowFromMatrix", f"{name}_row{row_index}")
            row_node["input"] = row_index
            row_node["matrix"] << matrix_attr

            for col_index, axis in enumerate(["X", "Y", "Z", "W"]):
                matrix_4x4[f"in{row_index}{col_index}"] << row_node[f"output{axis}"]
            row_nodes.append(row_node)

        self.container_node.add_nodes(matrix_4x4, *row_nodes)
        return matrix_4x4

    def connect_input_to_output(self):
        """connects input xform to output xform"""
        input_xforms = self.get_xform_attrs(xform_type=self.IO_ENUM.input)
        for index, xform in input_xforms.items():
            self._set_xform_attrs(
                index=index, xform=xform, xform_type=self.IO_ENUM.output
            )

    def source_component_reconnect(self):
        input_xform = self.get_xform_attrs(xform_type=self.IO_ENUM.input)
        if len(input_xform.keys()) == 0:
            raise IndexError("input xform not longer than length of 0")
        source_component = input_xform[0].world_matrix.get_src_connection()
        if source_component is None:
            raise RuntimeError(f"{self.container_node} does not have source component")
        source_component = base_comp.get_component(
            source_component.node.get_container_node()
        )
        if not issubclass(type(source_component), _Hierarchy):
            raise RuntimeError(
                f"{source_component.container_node} must be of type _Hierarchy"
            )

        self._connect_source_component(
            source_component=source_component,
            connect_parent_hier=False,
            connect_axis_vec=False,
        )


class WeightDrivers(_Hierarchy):
    """weight drivers for anim component"""

    class_namespace = "weightDrv"

    _OUT_DRIVER = "driver"
    _OUT_WEIGHT = "weight"
    _OUT_WEIGHT_NAME = "weightName"

    def _output_attr_build_data(self):
        node_data = super()._output_attr_build_data()

        node_data.extend_attr_data(
            component_data.AttrData(
                self._OUT_DRIVER,
                type_="compound",
                multi=True,
                parent=self.HIER_DATA.OUT_XFORM,
            ),
            component_data.AttrData(
                self._OUT_WEIGHT, type_="double", parent=self._OUT_DRIVER
            ),
            component_data.AttrData(
                self._OUT_WEIGHT_NAME, type_="string", parent=self._OUT_DRIVER
            ),
        )

        return node_data

    def _override_build(self, control_color=None, **kwargs):
        """connects input to output xforms

        Args:
            control_color (_type_, optional): only here for error purposes
        """
        self.connect_input_to_output()
