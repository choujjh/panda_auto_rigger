import system.base_component as base_comp
import system.component_data as component_data
import system.component_enum_data as component_enum_data
import utils.node_wrapper as nw
import utils.utils as utils
from typing import Union


class _Matrix(base_comp._Component):
    """Base class _matrix"""

    component_type = component_enum_data.ComponentType.matrix
    class_namespace = "matrix"


class OrientTransformBlend(_Matrix):
    """Orient Transform Blend matrix"""

    pass


class Twist(_Matrix):
    """Twist matrix. takes a local matrix and a local init matrix and calculates
    twist

    Attributes:
        _IN_INIT_MATRIX (str): str constant "initMatrix"
        _IN_INIT_PAR_INV_MATRIX (str): str constant "initParentInvMatrix"
        _IN_LOC_INIT_MATRIX (str): str constant "localInitMatrix"
        _IN_LOC_MATRIX (str): str constant "localMatrix"
        _IN_PRM_VEC (str): str constant "primaryVec"
        _IN_PRM_VEC_X (str): str constant "primaryVecX"
        _IN_PRM_VEC_Y (str): str constant "primaryVecY"
        _IN_PRM_VEC_Z (str): str constant "primaryVecZ"
        _OUT_ROT_MATRIX (str): str constant "rotMatrix"

    """

    class_namespace = "matrixTwist"

    _IN_INIT_MATRIX = "initMatrix"
    _IN_INIT_PAR_INV_MATRIX = "initParentInvMatrix"
    _IN_LOC_INIT_MATRIX = "localInitMatrix"
    _IN_LOC_MATRIX = "localMatrix"
    _IN_PRM_VEC = "primaryVec"
    _IN_PRM_VEC_X = "primaryVecX"
    _IN_PRM_VEC_Y = "primaryVecY"
    _IN_PRM_VEC_Z = "primaryVecZ"
    _OUT_ROT_MATRIX = "rotMatrix"

    def _input_attr_build_data(self):
        """Defines all the added, published, or modified attributes for the
        input node. inherits all input node data from _Matrix

        Returns:
            comp_data.NodeData:
        """
        node_data = super()._input_attr_build_data()
        node_data.extend_attr_data(
            component_data.AttrData(
                self._IN_INIT_MATRIX, type_="matrix", parent=self._IN
            ),
            component_data.AttrData(
                self._IN_INIT_PAR_INV_MATRIX, type_="matrix", parent=self._IN
            ),
            component_data.AttrData(
                self._IN_LOC_INIT_MATRIX, type_="matrix", parent=self._IN
            ),
            component_data.AttrData(
                self._IN_LOC_MATRIX, type_="matrix", parent=self._IN
            ),
            component_data.AttrData(
                self._IN_PRM_VEC, type_="double3", parent=self._IN, value=[1, 0, 0]
            ),
            component_data.AttrData(
                self._IN_PRM_VEC_X, type_="double", parent=self._IN_PRM_VEC
            ),
            component_data.AttrData(
                self._IN_PRM_VEC_Y, type_="double", parent=self._IN_PRM_VEC
            ),
            component_data.AttrData(
                self._IN_PRM_VEC_Z, type_="double", parent=self._IN_PRM_VEC
            ),
        )

        return node_data

    def _output_attr_build_data(self):
        """Defines all the added, published, or modified attributes for the
        output node. inherits all output node data from _Matrix

        Returns:
            comp_data.NodeData:
        """
        node_data = super()._output_attr_build_data()
        node_data.extend_attr_data(
            component_data.AttrData(
                self._OUT_ROT_MATRIX, type_="matrix", parent=self._OUT
            ),
        )

        return node_data

    @classmethod
    def create(
        cls,
        instance_name: Union[str, nw.Attr] = None,
        parent: Union[base_comp._Component, nw.Container] = None,
        loc_matrix: nw.Attr = None,
        loc_init_matrix: nw.Attr = None,
        init_matrix: nw.Attr = None,
        init_parent_inv_matrix: nw.Attr = None,
        primary_vec: nw.Attr = None,
    ):
        """creates twist matrix

        Args:
            instance_name (Union[str, nw.Attr], optional): Defaults to None.
            parent (Union[base_comp._Component, nw.Container], optional): Defaults to None.
            loc_matrix (nw.Attr, optional): Defaults to None.
            loc_init_matrix (nw.Attr, optional): Defaults to None.
            init_matrix (nw.Attr, optional): Defaults to None.
            init_parent_inv_matrix (nw.Attr, optional): Defaults to None.
            primary_vec (nw.Attr, optional): Defaults to None.

        Returns:
            Twist:
        """
        return cls._kwarg_create(**cls._process_locals(kwarg_dict=locals()))

    def _pre_build(
        self,
        instance_name: Union[str, nw.Attr] = None,
        parent: Union[base_comp._Component, nw.Container] = None,
        loc_matrix: nw.Attr = None,
        loc_init_matrix: nw.Attr = None,
        init_matrix: nw.Attr = None,
        init_parent_inv_matrix: nw.Attr = None,
        primary_vec: nw.Attr = None,
        **kwargs,
    ):
        """Connects up attributes given to input node

        Args:
            instance_name (_type_, optional): _description_. Defaults to None.
            parent (_type_, optional): _description_. Defaults to None.
            loc_matrix (nw.Attr, optional): _description_. Defaults to None.
            loc_init_matrix (nw.Attr, optional): _description_. Defaults to None.
            init_matrix (nw.Attr, optional): _description_. Defaults to None.
            init_parent_inv_matrix (nw.Attr, optional): _description_. Defaults to None.
            primary_vec (nw.Attr, optional): _description_. Defaults to None.
        """
        super()._pre_build(instance_name, parent, **kwargs)
        utils.set_connect_attr_data(
            self.container_node[self._IN_LOC_MATRIX], loc_matrix
        )
        utils.set_connect_attr_data(
            self.container_node[self._IN_LOC_INIT_MATRIX], loc_init_matrix
        )
        utils.set_connect_attr_data(
            self.container_node[self._IN_INIT_MATRIX], init_matrix
        )
        utils.set_connect_attr_data(
            self.container_node[self._IN_INIT_PAR_INV_MATRIX], init_parent_inv_matrix
        )
        utils.set_connect_attr_data(self.container_node[self._IN_PRM_VEC], primary_vec)

    def _override_build(self, **kwargs):
        """Builds matrix nodes for Twist.

        Raises:
            RuntimeError: if local matrix is not connected or init matrix and init
            parent inverse matrix is not connected. local matrix used in calculation
            is then not valid
        """
        loc_matrix = self.container_node[self._IN_LOC_MATRIX]
        loc_init_matrix = self.container_node[self._IN_LOC_INIT_MATRIX]
        init_matrix = self.container_node[self._IN_INIT_MATRIX]
        init_par_inv_matrix = self.container_node[self._IN_INIT_PAR_INV_MATRIX]

        if not loc_init_matrix.has_src_connection():
            # make a new local matrix
            if (
                not init_matrix.has_src_connection()
                or not init_par_inv_matrix.has_src_connection()
            ):
                raise RuntimeError(
                    f"{loc_init_matrix} does not have connection and ({init_matrix} or {init_par_inv_matrix}) does not have connection. loc_init_matrix could not be calculated"
                )
            loc_init_matrix_mult = nw.create_node("multMatrix", "locInitMatrixMult")
            loc_init_matrix_mult["matrixIn"][0] << init_matrix
            loc_init_matrix_mult["matrixIn"][1] << init_par_inv_matrix
            loc_init_matrix = loc_init_matrix_mult["matrixSum"]
            self.container_node.add_nodes(loc_matrix)

        aim_no_rot_matrix = nw.create_node("aimMatrix", "aimNoRotMatrix")
        aim_no_rot_matrix["inputMatrix"] << loc_init_matrix
        aim_no_rot_matrix["primaryTargetMatrix"] << loc_matrix
        aim_no_rot_matrix["primaryMode"] = 2
        aim_no_rot_matrix["primaryInputAxis"] << self.container_node[self._IN_PRM_VEC]
        (
            aim_no_rot_matrix["primaryTargetVector"]
            << self.container_node[self._IN_PRM_VEC]
        )

        no_rot_inv = nw.create_node("inverseMatrix", "noRotInvMatrix")
        no_rot_inv["inputMatrix"] << aim_no_rot_matrix["outputMatrix"]

        rot_matrix_mult = nw.create_node("multMatrix", "rotMatrixMult")
        rot_matrix_mult["matrixIn"][0] << loc_matrix
        rot_matrix_mult["matrixIn"][1] << no_rot_inv["outputMatrix"]

        pick_mat = nw.create_node("pickMatrix", "rotMatPick")
        pick_mat["inputMatrix"] << rot_matrix_mult["matrixSum"]
        pick_mat["useTranslate"] = False
        pick_mat["useScale"] = False
        pick_mat["useShear"] = False

        self.container_node[self._OUT_ROT_MATRIX] << pick_mat["outputMatrix"]

        self.container_node.add_nodes(
            aim_no_rot_matrix,
            no_rot_inv,
            rot_matrix_mult,
            loc_init_matrix_mult,
            pick_mat,
        )


class Mirror(_Matrix):
    """Mirror mirrors input matrix

    Attributes:
        _IN_MAT (str): str constant "inputMatrix"
        _IN_SCALE_MAT (str): str constant "inputScaleMatrix"
        _IN_WRD_MAT (str): str constant "inputWorldMatrix"
        _OUT_WRLD_MAT (str): str constant "worldMatrix"

    Returns:
        _type_: _description_
    """

    class_namespace = "mirror_matrix"
    input_node_type = "multMatrix"

    _IN_MAT = "inputMatrix"
    _IN_SCALE_MAT = "inputScaleMatrix"
    _IN_WRD_MAT = "inputWorldMatrix"
    _OUT_WRLD_MAT = "worldMatrix"

    @classmethod
    def create(
        cls,
        instance_name: Union[str, nw.Attr] = None,
        parent: Union[base_comp._Component, nw.Container] = None,
        input_matrix: Union[utils.Matrix, nw.Attr] = None,
        input_scale_matrix: Union[utils.Matrix, nw.Attr] = None,
        input_world_matrix: Union[utils.Matrix, nw.Attr] = None,
        mirror_behavior: bool = True,
        **kwargs,
    ):
        """Class method to create component

        Args:
            instance_name (Union[str, nw.Attr], optional): Defaults to None.
            parent (Union[base_comp._Component, nw.Container], optional): Defaults to None.
            input_matrix (Union[utils.Matrix, nw.Attr], optional): Defaults to None.
            scale_matrix (Union[utils.Matrix, nw.Attr], optional): Defaults to None.
            input_world_matrix (Union[utils.Matrix, nw.Attr], optional): Defaults to None.
            mirror_behavior (bool, optional): Defaults to True.

        Returns:
            _type_: _description_
        """
        return cls._kwarg_create(**cls._process_locals(kwarg_dict=locals()))

    def _input_attr_build_data(self):
        """Defines all the added, published, or modified attributes for the
        input node. Can be added onto by inherited classes

        Returns:
            comp_data.NodeData:
        """
        node_data = super()._input_attr_build_data()
        node_data.extend_attr_data(
            component_data.AttrData("matrixIn[1]", publish=self._IN_MAT),
            component_data.AttrData("matrixIn[2]", publish=self._IN_SCALE_MAT),
            component_data.AttrData("matrixIn[3]", publish=self._IN_WRD_MAT),
            component_data.AttrData("matrixSum", publish=self._OUT_WRLD_MAT),
        )
        return node_data

    def _pre_build(
        self,
        instance_name=None,
        parent=None,
        input_matrix=None,
        input_scale_matrix=None,
        input_world_matrix=None,
        mirror_behavior: bool = True,
        **kwargs,
    ):
        """Handles creation and connection of initial nodes

        Args:
            instance_name (_type_, optional): _description_. Defaults to None.
            parent (_type_, optional): _description_. Defaults to None.
            mirror_behavior (bool, optional): _description_. Defaults to True.
        """
        super()._pre_build(instance_name, parent, **kwargs)
        self.set_mirror_behavior(mirror_behavior)
        utils.set_connect_attr_data(self.container_node[self._IN_MAT], input_matrix)
        utils.set_connect_attr_data(
            self.container_node[self._IN_SCALE_MAT], input_scale_matrix
        )
        utils.set_connect_attr_data(
            self.container_node[self._IN_WRD_MAT], input_world_matrix
        )

    def _override_build(self, **kwargs):
        pass

    def set_mirror_behavior(self, mirror_behavior: bool):
        """Sets matrix to mirror behavior of input matrix simular to joint mirroring behaviors

        Args:
            mirror_behavior (bool):
        """
        if mirror_behavior:
            self.input_node["matrixIn"][0] = utils.Matrix.scale_matrix(-1, -1, -1)
        else:
            self.input_node["matrixIn"][0] = utils.Matrix.identity_matrix()
