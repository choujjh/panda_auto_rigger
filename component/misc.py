import system.base_component as base_comp
import system.component_data as component_data
import system.component_enum_data as component_enum_data
import component.control as control
import utils.node_wrapper as nw
import utils.utils as utils
import maya.cmds as cmds
from typing import Union

class VisualizeHier(base_comp.Hierarchy):
    """Helps visualize and debug hierarchies by creating chains for world space and local visualization"""
    root_transform_name = "v_grp"
    class_namespace = "hier_vis"

    def _override_build(self, **kwargs):
        ws_grp = nw.create_node("transform", "worldSpace_grp")
        cmds.parent(str(ws_grp), str(self.transform_node))
        ws_grp["offsetParentMatrix"] << self.transform_node["worldInverseMatrix"][0]
        loc_grp = nw.create_node("transform", "localSpace_grp")
        cmds.parent(str(loc_grp), str(self.transform_node))
        loc_grp["offsetParentMatrix"] << self.transform_node["worldInverseMatrix"][0]

        prev_loc_transform = loc_grp

        input_xforms = self.get_xform_attrs(xform_type=self.IO_ENUM.input)
        for index, input_xform in input_xforms.items():            
            # making controls
            control_ws_inst = control.Axis.create(instance_name=f"{input_xform.xform_name.value}_ws", parent=self)
            control_loc_inst = control.Axis.create(instance_name=f"{input_xform.xform_name.value}_loc", parent=self)
            # locking transforms
            for attr_name in ["t", "r", "s"]:
                for axis in ["x", "y", "z"]:
                    control_ws_inst.transform_node[f"{attr_name}{axis}"].set_locked(True)
                    control_loc_inst.transform_node[f"{attr_name}{axis}"].set_locked(True)
            
            # setting up the rest of ws matrix
            cmds.parent(str(control_ws_inst.transform_node), str(ws_grp))
            input_xform.world_matrix >> control_ws_inst.container_node[base_comp.Control._IN_OFF_MAT]

            # setting up the rest of local matrix
            cmds.parent(str(control_loc_inst.transform_node), str(prev_loc_transform))
            if index != 0:
                input_xform.loc_matrix >> control_loc_inst.container_node[base_comp.Control._IN_OFF_MAT]
            else:
                input_xform.world_matrix >> control_loc_inst.container_node[base_comp.Control._IN_OFF_MAT]
            prev_loc_transform = control_loc_inst.transform_node

            # connecting to component output
            output_xform = self.get_xform_attrs(xform_type=self.IO_ENUM.output, index=index)
            for input_attr, output_attr in zip(input_xform, output_xform):
                input_attr >> output_attr

        self.container_node.add_nodes(ws_grp)

class MergeHier(base_comp.Component):
    """Merges multiple components together and outputs it"""
    class_namespace="merge_hier"
    HIER_DATA = component_data.HierData
    IO_ENUM = component_enum_data.IO
    XFORM = component_data.Xform

    _IN_HIER_PAR_MAT = "hierParentMatricies"
    _IN_HIER_BLEND = "hierBlend"
    _KWG_SRC_COMPS = "source_components"

    def __init__(self, container_node=None):
        super().__init__(container_node)
        self.__hier_comp = base_comp.Hierarchy(container_node=container_node)

    def _input_attr_build_data(self):
        node_data = super()._input_attr_build_data()

        node_data.extend_attr_data(self.HIER_DATA.get_hier_data())

        node_data.extend_attr_data(
            component_data.AttrData(self._IN_HIER_PAR_MAT, type_="matrix", multi=True, publish=True),
            component_data.AttrData(self.HIER_DATA.INPUT_XFORM, type_="compound", multi=True, publish=True),
            component_data.AttrData(self.HIER_DATA.INPUT_LOC_MATRIX, type_="matrix", parent=self.HIER_DATA.INPUT_XFORM, multi=True),
            component_data.AttrData(self._IN_HIER_BLEND, type_="double", parent=self._IN, min=0),
        )
        
        return node_data
    
    def _output_attr_build_data(self):
        node_data = super()._output_attr_build_data()
        node_data.extend_attr_data(self.HIER_DATA.get_output_xform_data())

        return node_data

    @classmethod
    def create(cls, instance_name = None, parent=None, source_components=[], **kwargs):
        kwargs[cls._KWG_SRC_COMPS] = utils.make_iterable(source_components)
                
        pre_build_kwargs, build_kwargs, post_build_kwargs = cls._process_kwargs(instance_name=instance_name, parent=parent, source_components=source_components)
        return cls._filtered_create(pre_build_kwargs=pre_build_kwargs, build_kwargs=build_kwargs, post_build_kwargs=post_build_kwargs)
    
    @classmethod
    def _process_kwargs(cls, instance_name = None, parent = None, source_components=[]):
        pre_build_kwargs, build_kwargs, post_build_kwargs = super()._process_kwargs(instance_name, parent)
        pre_build_kwargs.update({
            cls._KWG_SRC_COMPS:source_components
        })
        return pre_build_kwargs, build_kwargs, post_build_kwargs

    def _pre_build(self, instance_name = None, parent=None, source_components=[], **pre_build_kwargs):
        super()._pre_build(instance_name, parent, **pre_build_kwargs)
        self._connect_source_hier_components(source_components=source_components)
        
        self.__hier_comp = base_comp.Hierarchy(container_node=self.container_node)

    def _override_build(self, **kwargs):
        hier_parent_mat = self.__connect_hier()
        blend_weight_attrs = self.__blend_weights()
        self.__blend_matricies(hier_parent_mat=hier_parent_mat, blend_weight_attrs=blend_weight_attrs)
        
    def __connect_hier(self):
        """Creates all nodes connected to hier"""
        # connecting hier
        hier_parent_mat = nw.create_node("blendMatrix", "hierParentMatrixBlend")
        for xform_index, hier_attr in enumerate(self.container_node[self._IN_HIER_PAR_MAT]):
            if xform_index == 0:
                hier_parent_mat["inputMatrix"] << hier_attr
            else:
                hier_parent_mat["target"][xform_index-1]["targetMatrix"] << hier_attr
        hier_parent_inv = nw.create_node("inverseMatrix", "hierParentInvMatrixBlend")
        hier_parent_inv["inputMatrix"] << hier_parent_mat["outputMatrix"]
        self.container_node[self.HIER_DATA.HIER_PARENT_MATRIX] << hier_parent_mat["outputMatrix"]
        self.container_node[self.HIER_DATA.HIER_PARENT_INV_MATRIX] << hier_parent_inv["outputMatrix"]

        self.container_node.add_nodes(hier_parent_mat, hier_parent_inv)
        return hier_parent_mat
    def __blend_weights(self):
        """creates all nodes for blending

        Returns:
            list(nw.Attr): list of attribute that has the blended weights for each index
        """
        blend_weight_attrs = []
        added_nodes = []
        for index in range(len(self.container_node[self.HIER_DATA.INPUT_XFORM])):
            if index != 0:
                clamp = nw.create_node("clampRange", f"component{index}_clamp")
                if index == 1:
                    clamp["input"] << self.container_node[self._IN_HIER_BLEND]
                else:
                    component_weight = nw.create_node("subtract", name=f"component{index}_envelope")
                    component_weight["input1"] << self.container_node[self._IN_HIER_BLEND]
                    component_weight["input2"].set(index-1)
                    clamp["input"] << component_weight["output"]
                    added_nodes.append(component_weight)
                added_nodes.append(clamp)
                blend_weight_attrs.append(clamp["output"])
        self.container_node.add_nodes(*added_nodes)

        return blend_weight_attrs
    def __blend_matricies(self, hier_parent_mat:nw.Node, blend_weight_attrs:list):
        """creates local, world, and inverse matricies

        Args:
            hier_parent_mat (nw.Node): 
            blend_weight_attrs (list): 
        """
        added_nodes = []
        prev_ws_attr = hier_parent_mat["outputMatrix"]
        hier_len = len(self.container_node[self.HIER_DATA.INPUT_XFORM][0][self.HIER_DATA.INPUT_LOC_MATRIX])
        for xform_index in range(hier_len):
            blend_mat = nw.create_node("blendMatrix", name=f"xform{xform_index}_loc_blend")

            #adding world space
            mult_mat = nw.create_node("multMatrix", name=f"xform{xform_index}_ws_mat")
            mult_mat["matrixIn"][0] << blend_mat["outputMatrix"]
            mult_mat["matrixIn"][1] << prev_ws_attr
            inverse_mat = nw.create_node("inverseMatrix", name=f"xform{xform_index}_inv_mat")
            inverse_mat["inputMatrix"] << mult_mat["matrixSum"]
            
            prev_ws_attr = mult_mat["matrixSum"]
            #local space blend
            for component_index, input_xform in enumerate(self.container_node[self.HIER_DATA.INPUT_XFORM]):
                loc_mat_attr = input_xform[self.HIER_DATA.INPUT_LOC_MATRIX][xform_index]
                if component_index == 0:
                    blend_mat["inputMatrix"] << loc_mat_attr
                else:
                    blend_mat["target"][component_index-1]["targetMatrix"] << loc_mat_attr
                    blend_mat["target"][component_index-1]["weight"] << blend_weight_attrs[component_index-1]
                added_nodes.extend([blend_mat, mult_mat, inverse_mat])


            self._set_xform_attrs(
                index=xform_index,
                xform_type=self.IO_ENUM.output,
                xform=self.XFORM(
                    world_matrix=mult_mat["matrixSum"],
                    world_inv_matrix=inverse_mat["outputMatrix"],
                    loc_matrix=blend_mat["outputMatrix"],
                )
            )
                        
        self.container_node.add_nodes(*added_nodes)
    def _set_xform_attrs(self, index:int, xform:component_data.Xform, xform_type:component_enum_data.IO, set_when_data_is_attr:bool=False, disable_warning:bool=False):
        """Sets xform based of index and xform type

        Args:
            index (int):
            xform (component_data.Xform):
            xform_type (component_enum_data.IO):
            set_when_data_is_attr (bool, optional): only sets value not connects them. Defaults to False.
            disable_warning (bool, optional): Defaults to False.

        Raises:
            RuntimeError: if xform_type is input
        """
        if self.HIER_DATA.is_input_enum(xform_type):
            raise RuntimeError(f"{self.container_node} mergeHier could not set output xforms. none exist")
        return self.__hier_comp._set_xform_attrs(index=index, xform=xform, xform_type=xform_type, set_when_data_is_attr=set_when_data_is_attr, disable_warning=disable_warning)
    
    def _connect_source_hier_components(self, source_components):
        """given a list of source components, connects them to this component

        Args:
            source_components (iter):

        Raises:
            RuntimeError: _description_
            RuntimeError: _description_
            RuntimeError: _description_
            RuntimeError: _description_
        """
        if utils.is_iterable(source_components) and len(source_components) > 0:
            #connect up local matricies
            HIER_DATA = self.HIER_DATA
            # checks first
            xform_len = len(source_components[0].container_node[HIER_DATA.OUTPUT_XFORM])
            for source_component in source_components:
                component_len = len(source_component.container_node[HIER_DATA.OUTPUT_XFORM])
                if xform_len != component_len:
                    raise RuntimeError(f"{source_component.container_node} has mismatched len. expecting {xform_len} got {component_len}")
                if source_component.container_node == self.container_node.get_container_node():
                    raise RuntimeError("source container cannot be parent container")
                if not issubclass(type(source_component), base_comp.Hierarchy):
                    raise RuntimeError(f"{source_component.container_node} is not hierarchy component")
                
            for hier_index, source_component in enumerate(source_components):
                # input xform local attrs
                src_container = source_component.container_node
                src_xforms = src_container[HIER_DATA.OUTPUT_XFORM]
                for xform_index, src_out_xform  in enumerate(src_xforms):
                    self_loc_matrix = self.container_node[HIER_DATA.INPUT_XFORM][hier_index][HIER_DATA.INPUT_LOC_MATRIX][xform_index]
                    src_out_xform[HIER_DATA.OUTPUT_LOC_MATRIX] >> self_loc_matrix

                    src_container[HIER_DATA.HIER_PARENT_MATRIX] >> self.container_node[self._IN_HIER_PAR_MAT][hier_index]
                # connect up output name, world matrix and init matricies 
                curr_src_container = source_components[0].container_node
                for index, src_out_xform in enumerate(curr_src_container[HIER_DATA.OUTPUT_XFORM]):
                    out_xform = self.container_node[HIER_DATA.OUTPUT_XFORM][index]

                    out_xform[HIER_DATA.OUTPUT_XFORM_NAME] << src_out_xform[HIER_DATA.OUTPUT_XFORM_NAME]
                    out_xform[HIER_DATA.OUTPUT_INIT_MATRIX] << src_out_xform[HIER_DATA.OUTPUT_INIT_MATRIX]
                    out_xform[HIER_DATA.OUTPUT_INIT_INV_MATRIX] << src_out_xform[HIER_DATA.OUTPUT_INIT_INV_MATRIX]
            
            # setting hiers
            source_container = source_components[0].container_node
            source_container[HIER_DATA.HIER_PARENT_INIT_INV_MATRIX] >> self.container_node[HIER_DATA.HIER_PARENT_INIT_INV_MATRIX]

        else:
            raise RuntimeError("source component needs to be iterable")
    
    def get_xform_attrs(self, xform_type:component_enum_data.IO, index:Union[int, list]=None):
        """Gets an xform. returns all if index is None

        Args:
            xform_type (component_enum_data.IO): selects input or output xform
            index (Union[int, list], optional): Defaults to None.

        Raises:
            RuntimeError: if xform_type is input

        Returns:
            component_data.Xform:
        """
        if self.HIER_DATA.is_input_enum(xform_type):
            raise RuntimeError(f"{self.container_node} mergeHier could not get output xforms. none exist")
        return self.__hier_comp.get_xform_attrs(xform_type=xform_type, index=index)