import system.base_component as base_comp
import system.component_data as component_data
import utils.node_wrapper as nw
import utils.utils as utils

class OrientTransformBlend(base_comp.Matrix):
    def _override_build(self, **build_kwargs):
        pass



class Twist(base_comp.Matrix):

    _IN_INIT_MATRIX = "initMatrix"
    _IN_INIT_PAR_INV_MATRIX = "initParentInvMatrix"
    _IN_LOC_INIT_MATRIX = "localInitMatrix"
    _IN_LOC_MATRIX = "localMatrix"
    _IN_PRM_VEC = "primaryVec"
    _IN_PRM_VEC_X = "primaryVecX"
    _IN_PRM_VEC_Y = "primaryVecY"
    _IN_PRM_VEC_Z = "primaryVecZ"
    _OUT_ROT_MATRIX = "rotMatrix"
    _KWG_LOC_MAT = "loc_matrix"
    _KWG_LOC_INIT_MAT = "loc_init_matrix"
    _KWG_INIT_MAT = "init_matrix"
    _KWG_INIT_PAR_INV_MAT = "init_parent_inv_matrix"
    _KWG_PRM_VEC = "primary_vec"


    def _input_attr_build_data(self):
        node_data = super()._input_attr_build_data()
        node_data.extend_attr_data(
            component_data.AttrData(self._IN_INIT_MATRIX, type_="matrix", parent=self._IN),
            component_data.AttrData(self._IN_INIT_PAR_INV_MATRIX, type_="matrix", parent=self._IN),
            component_data.AttrData(self._IN_LOC_INIT_MATRIX, type_="matrix", parent=self._IN),
            component_data.AttrData(self._IN_LOC_MATRIX, type_="matrix", parent=self._IN),
            component_data.AttrData(self._IN_PRM_VEC, type_="double3", parent=self._IN, value=[1, 0, 0]),
            component_data.AttrData(self._IN_PRM_VEC_X, type_="double", parent=self._IN_PRM_VEC),
            component_data.AttrData(self._IN_PRM_VEC_Y, type_="double", parent=self._IN_PRM_VEC),
            component_data.AttrData(self._IN_PRM_VEC_Z, type_="double", parent=self._IN_PRM_VEC),
        )

        return node_data
    def _output_attr_build_data(self):
        node_data = super()._output_attr_build_data()
        node_data.extend_attr_data(
            component_data.AttrData(self._OUT_ROT_MATRIX, type_="matrix", parent=self._OUT),
        )

        return node_data
    
    @classmethod
    def create(cls, 
               instance_name=None, 
               parent=None, 
               loc_matrix:nw.Attr=None, 
               loc_init_matrix:nw.Attr=None, 
               init_matrix:nw.Attr=None, 
               init_parent_inv_matrix:nw.Attr=None,
               primary_vec=None):
        pre_build_kwargs, build_kwargs, post_build_kwargs = cls._process_kwargs(
            instance_name=instance_name, 
            parent=parent, 
            loc_matrix=loc_matrix, 
            loc_init_matrix=loc_init_matrix, 
            init_matrix=init_matrix, 
            init_parent_inv_matrix=init_parent_inv_matrix,
            primary_vec=primary_vec)
        return cls._filtered_create(pre_build_kwargs=pre_build_kwargs, build_kwargs=build_kwargs, post_build_kwargs=post_build_kwargs)
    @classmethod
    def _process_kwargs(cls,
                        instance_name=None, 
                        parent=None, 
                        loc_matrix:nw.Attr=None, 
                        loc_init_matrix:nw.Attr=None, 
                        init_matrix:nw.Attr=None, 
                        init_parent_inv_matrix:nw.Attr=None,
                        primary_vec=None):
        pre_build_kwargs, build_kwargs, post_build_kwargs = super()._process_kwargs(instance_name, parent)
        pre_build_kwargs.update({
            cls._KWG_LOC_MAT: loc_matrix,
            cls._KWG_LOC_INIT_MAT: loc_init_matrix,
            cls._KWG_INIT_MAT: init_matrix,
            cls._KWG_INIT_PAR_INV_MAT: init_parent_inv_matrix,
            cls._KWG_PRM_VEC: primary_vec, 
        })
        return pre_build_kwargs, build_kwargs, post_build_kwargs
    def _pre_build(self, 
                   instance_name = None, 
                   parent = None, 
                   loc_matrix:nw.Attr=None, 
                   loc_init_matrix:nw.Attr=None, 
                   init_matrix:nw.Attr=None, 
                   init_parent_inv_matrix:nw.Attr=None,
                   primary_vec:nw.Attr=None,
                   **pre_build_kwargs):
        super()._pre_build(instance_name, parent, **pre_build_kwargs)
        utils.set_connect_attr_data(self.container_node[self._IN_LOC_MATRIX], loc_matrix)
        utils.set_connect_attr_data(self.container_node[self._IN_LOC_INIT_MATRIX], loc_init_matrix)
        utils.set_connect_attr_data(self.container_node[self._IN_INIT_MATRIX], init_matrix)
        utils.set_connect_attr_data(self.container_node[self._IN_INIT_PAR_INV_MATRIX], init_parent_inv_matrix)
        utils.set_connect_attr_data(self.container_node[self._IN_PRM_VEC], primary_vec)
    def _override_build(self, **build_kwargs):
        loc_matrix = self.container_node[self._IN_LOC_MATRIX]
        loc_init_matrix = self.container_node[self._IN_LOC_INIT_MATRIX]
        init_matrix = self.container_node[self._IN_INIT_MATRIX]
        init_par_inv_matrix = self.container_node[self._IN_INIT_PAR_INV_MATRIX]

        if not loc_init_matrix.has_src_connection():
            # make a new local matrix
            if not init_matrix.has_src_connection() or not init_par_inv_matrix.has_src_connection():
                raise RuntimeError(f"{loc_init_matrix} does not have connection and ({init_matrix} or {init_par_inv_matrix}) does not have connection. loc_init_matrix could not be calculated")
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
        aim_no_rot_matrix["primaryTargetVector"] << self.container_node[self._IN_PRM_VEC]

        no_rot_inv = nw.create_node("inverseMatrix", "noRotInvMatrix")
        no_rot_inv["inputMatrix"] << aim_no_rot_matrix["outputMatrix"]

        rot_matrix_mult = nw.create_node("multMatrix", "rotMatrixMult")
        rot_matrix_mult["matrixIn"][0] << loc_matrix
        rot_matrix_mult["matrixIn"][1] << no_rot_inv["outputMatrix"]

        self.container_node[self._OUT_ROT_MATRIX] << rot_matrix_mult["matrixSum"]
        
        self.container_node.add_nodes(aim_no_rot_matrix, no_rot_inv, rot_matrix_mult)