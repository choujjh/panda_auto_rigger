import system.base_component as base_comp
import system.component_data as component_data
import system.component_enum_data as component_enum_data
import utils.utils as utils
import component.control as control
import utils.node_wrapper as nw
from typing import Union

class Cluster(base_comp._Component):
    class_namespace="clust"
    component_type = component_enum_data.ComponentType.cluster
    _max_num_xforms=(0, 0)

    HIER_DATA = base_comp._Hierarchy.HIER_DATA
    IO_ENUM = base_comp._Hierarchy.IO_ENUM
    XFORM = base_comp._Hierarchy.XFORM
    HIER_PARENT = base_comp._Hierarchy.HIER_PARENT
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

    def __init__(self, container_node = None):
        super().__init__(container_node)
        self.__hier_inst_var = None
    
    @property
    def __hier(self):
        if self.__hier_inst_var is not None:
            pass
        elif self.container_node is not None:
            self.__hier_inst_var = base_comp._Hierarchy(self.container_node)
        else:
            self.__hier_inst_var = base_comp._Hierarchy()
        return self.__hier_inst_var

    def _input_attr_build_data(self):
        node_data = super()._input_attr_build_data()
        node_data.extend_attr_data(self.HIER_DATA.get_xform_data(self.IO_ENUM.input))
        return node_data
    def _output_attr_build_data(self):
        node_data = super()._output_attr_build_data()
        node_data.extend_attr_data(self.HIER_DATA.get_xform_data(self.IO_ENUM.output))
        node_data.extend_attr_data(
            component_data.AttrData(self._PRM_VEC, type_="double3", parent=self._OUT, value=[1, 0, 0]),
            component_data.AttrData(self._PRM_VEC_X, type_="double", parent=self._PRM_VEC),
            component_data.AttrData(self._PRM_VEC_Y, type_="double", parent=self._PRM_VEC),
            component_data.AttrData(self._PRM_VEC_Z, type_="double", parent=self._PRM_VEC),
            component_data.AttrData(self._SEC_VEC, type_="double3", parent=self._OUT, value=[0, 1, 0]),
            component_data.AttrData(self._SEC_VEC_X, type_="double", parent=self._SEC_VEC),
            component_data.AttrData(self._SEC_VEC_Y, type_="double", parent=self._SEC_VEC),
            component_data.AttrData(self._SEC_VEC_Z, type_="double", parent=self._SEC_VEC),
            component_data.AttrData(self._TER_VEC, type_="double3", parent=self._OUT, value=[0, 0, 1]),
            component_data.AttrData(self._TER_VEC_X, type_="double", parent=self._TER_VEC),
            component_data.AttrData(self._TER_VEC_Y, type_="double", parent=self._TER_VEC),
            component_data.AttrData(self._TER_VEC_Z, type_="double", parent=self._TER_VEC),
        )
        return node_data

    @classmethod
    def create(cls,
               instance_name:Union[str, nw.Attr]=None, 
               parent:base_comp._Component=None, 
               source_component:base_comp._Hierarchy=None,
               connect_axis_vecs:bool=True, 
               control_color=None):
        return cls._kwarg_create(**cls._local_kwargs(kwarg_dict=locals()))
    def _pre_build(self, 
                   instance_name:Union[str, nw.Attr]=None, 
                   parent:base_comp._Component=None, 
                   source_component:base_comp._Hierarchy=None,
                   connect_axis_vecs:bool=True, 
                   **kwargs):
        # pre build
        super()._pre_build(instance_name=instance_name, parent=parent, **kwargs)

        if connect_axis_vecs:
            for attr in [self.__hier._PRM_VEC, self.__hier._SEC_VEC, self.__hier._TER_VEC]:
                self.container_node[attr] << source_component.container_node[attr]

    def _override_build(self, control_color=None, **kwargs):
        pass        
    #xform and hierarchy
    def get_xform_attrs(self, xform_type:component_enum_data.IO, index:Union[int, list]=None):
        """Gets a dict of xforms given indicies and type of xform. returns all if index is None

        Args:
            xform_type (component_enum_data.IO): selects input or output xform
            index (int, list):
        Returns:
            dict:
        """
        return self.__hier.get_xform_attrs(xform_type=xform_type, index=index)
    def _set_xform_attrs(self, index:int, xform:component_data.Xform, xform_type:component_enum_data.IO, set_when_data_is_attr:bool=False):
        """Sets xform

        Args:
            index (int): 
            xform (component_data.Xform): 
            xform_type (component_enum_data.IO): 
            set_when_data_is_attr (bool, optional): only sets and not connects if it's an attribute. Defaults to False.
        """
        return self.__hier._set_xform_attrs(index=index, xform=xform, xform_type=xform_type, set_when_data_is_attr=set_when_data_is_attr)

    def add_clust_xform(self, name:str, parent_xform:component_data.Xform=None, mirror_axis:component_enum_data.AxisEnum=None):
        """adds xform to cluster

        Args:
            name (str, optional): _description_. Defaults to "".
            parent_xform (component_data.Xform, optional): _description_. Defaults to None.
            mirror_axis (component_enum_data.AxisEnum, optional): _description_. Defaults to None.
        """

        input_xforms = self.get_xform_attrs(xform_type=self.IO_ENUM.input)
        len_index = len(input_xforms)
        input_xform = self.get_xform_attrs(index=len_index, xform_type=self.IO_ENUM.input)

        if parent_xform is not None:
            if mirror_axis is not None:
                parent_xform.xform_name = name
            else:
                parent_xform.xform_name = None
            parent_xform.loc_matrix = None

            self._set_xform_attrs(
                index=len_index,
                xform_type=self.IO_ENUM.input,
                xform=parent_xform)
        else:
            self._set_xform_attrs(
                index=len_index, 
                xform_type=self.IO_ENUM.input,
                xform=self.XFORM(xform_name=name))
        added_nodes = []
        inv_attr = None
        if mirror_axis is None:
            setup_cntrl = control.Locator.create(instance_name=input_xform.xform_name, parent=self)
            setup_cntrl.container_node[setup_cntrl._IN_OFF_MAT] << input_xform.world_matrix
            ws_attr = setup_cntrl.container_node[setup_cntrl._OUT_WS_MAT]
            setup_cntrl.container_node[setup_cntrl._BLD_INST_FORM] = setup_cntrl.container_node[setup_cntrl._BLD_INST_FORM].value.replace("_c", "_setup_c")
            setup_cntrl.transform_node["t"] = self.container_node[self._SEC_VEC].value * 2
            setup_cntrl.rename_nodes()
        else:
            mirror_plane_scale_val = [1 if x == 0 else -1 for x in  mirror_axis.value]
            
            mult_mat = nw.create_node("multMatrix", f"{input_xform.xform_name.value}_mirror_mat")
            mult_mat["matrixIn"][0].set(utils.Matrix.scale_matrix(-1, -1, -1))
            mult_mat["matrixIn"][1] << input_xform.loc_matrix
            mult_mat["matrixIn"][2].set(utils.Matrix.scale_matrix(*mirror_plane_scale_val))
            mult_mat["matrixIn"][3] << input_xform.world_matrix
            ws_attr = mult_mat["matrixSum"]

            inv_mat = nw.create_node("inverseMatrix", f"{input_xform.xform_name.value}_init_inv")
            inv_mat["inputMatrix"] << ws_attr
            inv_attr = inv_mat["outputMatrix"]

            added_nodes.extend([mult_mat, inv_mat])

        sphere_cntrl = control.Sphere.create(instance_name=input_xform.xform_name, parent=self, axis_vec=component_enum_data.AxisEnum.y, build_s=0.5)
        sphere_cntrl.container_node[sphere_cntrl._IN_OFF_MAT] << ws_attr

        self._set_xform_attrs(
            index=len_index,
            xform_type=self.IO_ENUM.output,
            xform=self.XFORM(
                init_matrix=ws_attr,
                init_inv_matrix=inv_attr,
                world_matrix=sphere_cntrl.container_node[sphere_cntrl._OUT_WS_MAT],
                loc_matrix=sphere_cntrl.container_node[sphere_cntrl._OUT_LOC_MAT]
            )
        )
        self.__hier._populate_output_xforms()

        self.container_node.add_nodes(*added_nodes)
            



