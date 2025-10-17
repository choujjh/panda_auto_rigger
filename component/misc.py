import system.base_component as base_comp
import system.component_data as component_data
import system.component_enum_data as component_enum_data
import utils.utils as utils
import component.control as control
import utils.node_wrapper as nw
import maya.cmds as cmds

class VisualizeHier(base_comp._Hierarchy):
    """Helps visualize and debug hierarchies by creating chains for world space and local visualization"""
    root_transform_name = "grp"
    class_namespace = "hier_vis"

    def _override_build(self, control_color=None, **kwargs):
        ws_grp = nw.create_node("transform", "worldSpace_grp")
        loc_grp = nw.create_node("transform", "localSpace_grp")
        cmds.parent(str(loc_grp), str(ws_grp), str(self.transform_node))

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
            input_xform.world_matrix >> control_ws_inst.container_node[control._Control._IN_OFF_MAT]

            # setting up the rest of local matrix
            cmds.parent(str(control_loc_inst.transform_node), str(prev_loc_transform))
            if index != 0:
                input_xform.loc_matrix >> control_loc_inst.container_node[control._Control._IN_OFF_MAT]
            else:
                input_xform.world_matrix >> control_loc_inst.container_node[control._Control._IN_OFF_MAT]
            prev_loc_transform = control_loc_inst.transform_node

            # connecting to component output
            output_xform = self.get_xform_attrs(xform_type=self.IO_ENUM.output, index=index)
            for input_attr, output_attr in zip(input_xform, output_xform):
                input_attr >> output_attr

        self.container_node.add_nodes(ws_grp, loc_grp)
class MergeHier(base_comp._Hierarchy):
    """Merges multiple components together and outputs it"""
    class_namespace="merge_hier"

    _IN_HIER_PAR_MAT = "hierParentMatricies"
    _IN_HIER = "hierarchy"
    _IN_HIER_LOC_MAT = "hierarchyLocMatrix"
    _IN_HIER_BLEND = "hierBlend"
    _OUT_HIER_VIS = "hierVisibility"

    def _input_attr_build_data(self):
        node_data = super()._input_attr_build_data()
        node_data.extend_attr_data(
            component_data.AttrData(self._IN_HIER_PAR_MAT, type_="matrix", multi=True, publish=True),
            component_data.AttrData(self._IN_HIER, type_="compound", multi=True, publish=True),
            component_data.AttrData(self._IN_HIER_LOC_MAT, type_="matrix", multi=True, parent=self._IN_HIER),
            component_data.AttrData(self._IN_HIER_BLEND, type_="double", parent=self._IN, min=0),
        )
        
        return node_data
    def _output_attr_build_data(self):
        node_data = super()._output_attr_build_data()
        node_data.extend_attr_data(component_data.AttrData(self._OUT_HIER_VIS, type_="double", multi=True, parent=self._OUT, min=0, max=1))

        return node_data

    @classmethod
    def create(cls, instance_name = None, parent=None, source_components=[]):
        return cls._kwarg_create(**cls._local_kwargs(kwarg_dict=locals()))
    
    def _pre_build(self, instance_name=None, parent=None, source_components=[], **pre_build_kwargs):
        # get initial source_component
        source_component = None if len(source_components) < 1 else source_components[0]
        super()._pre_build(instance_name=instance_name, parent=parent, source_component=source_component, connect_parent_hier=True, connect_axis_vecs=True)
        
        # checking components
        self.__check_source_components(source_components=source_components)

        # connecting the rest of the components
        source_components = [] if source_component is None else source_components[1:]
        self.__connect_components(source_component=source_component, source_components=source_components)

    #pre build helper functions
    def __check_source_components(self, source_components=[]):
        """Checks that all components given are valid

        Args:
            source_components (list, optional): Defaults to [].

        Raises:
            RuntimeError: hier len is different than first
            RuntimeError: source component is the parent of this merge component
            RuntimeError: is not a hierarchy component
        """
        if len(source_components) < 1:
            return
        xform_len = len(source_components[0].container_node[self.HIER_DATA.OUT_XFORM])
        container_parents = []
        curr_par_cntnr = self.container_node.get_container_node()
        while curr_par_cntnr is not None:
            container_parents.append(curr_par_cntnr)
            curr_par_cntnr = curr_par_cntnr.get_container_node()
        for source_component in source_components:
            component_len = len(source_component.container_node[self.HIER_DATA.OUT_XFORM])
            if xform_len != component_len:
                raise RuntimeError(f"{source_component.container_node} has mismatched len. expecting {xform_len} got {component_len}")
            if source_component.container_node in container_parents:
                raise RuntimeError("source container cannot be parent of merge container")
            if not issubclass(type(source_component), base_comp._Hierarchy):
                raise RuntimeError(f"{source_component.container_node} is not hierarchy component")
    def __connect_components(self, source_component, source_components=[]):
        """Connects source components up to local hierarchy attribute

        Args:
            source_components (list, optional): Defaults to [].
        """
        set_component_vis = lambda index, component: (
            None if component.transform_node is None else 
            self.container_node[self._OUT_HIER_VIS][index] >> component.transform_node["visibility"])
        connect_hier_parent = lambda index, component: (
            component.container_node[self.HIER_DATA.HIER_PAR_MAT] >> self.container_node[self._IN_HIER_PAR_MAT][index]
        )

        set_component_vis(index=0, component=source_component)
        connect_hier_parent(index=0, component=source_component)
        for component_index, curr_component in enumerate(source_components):
            # hier parent
            hier_attr = self.container_node[self._IN_HIER][component_index][self._IN_HIER_LOC_MAT]

            for xform_index, xform in enumerate(curr_component.container_node[self.HIER_DATA.OUT_XFORM]):
                hier_attr[xform_index] << xform[self.HIER_DATA.OUT_LOC_MAT]

            # connecting to visibility
            set_component_vis(index=component_index+1, component=curr_component)
            connect_hier_parent(index=component_index+1, component=curr_component)

    def _override_build(self, **kwargs):
        num_hiers = len(self.container_node[self._IN_HIER_PAR_MAT])
        if num_hiers < 1:
            cmds.warning(f"{self.container_node} does not have any source hier components connected")
            return
        num_hiers_seg = 1 / (num_hiers - 1)
        hier_parent_blend = nw.create_node("blendMatrix", "hierParent_matBlend")
        vis_remaps = []
        for hier_index, hier_parent_attr in enumerate(self.container_node[self._IN_HIER_PAR_MAT]):
            # visibility
            vis_remaps.append(self.__create_vis_remap(hier_index=hier_index, num_hiers=num_hiers, num_hiers_seg=num_hiers_seg))

            # hier parent
            if hier_index == 0:
                hier_parent_blend["inputMatrix"] << hier_parent_attr
            else:
                hier_parent_blend["target"][hier_index-1]["targetMatrix"] << hier_parent_attr

        # xform operations
        input_xforms = self.get_xform_attrs(xform_type=self.IO_ENUM.input)
        blend_mats = []
        world_mats = []
        world_mat_attr = hier_parent_blend["outputMatrix"]
        for xform_index, in_xform in input_xforms.items():
            # blend loc matrix
            blend_mat = nw.create_node("blendMatrix", f"xform{xform_index}_locMatBlend")
            blend_mats.append(blend_mat)
            blend_mat["inputMatrix"] << in_xform.loc_matrix

            # world matrix
            world_mat = nw.create_node("multMatrix", f"xform{xform_index}_WorldMult")
            world_mats.append(world_mat)

            # setting world_matrix
            world_mat["matrixIn"][0] << blend_mat["outputMatrix"]
            world_mat["matrixIn"][1] << world_mat_attr
            world_mat_attr = world_mat["matrixSum"]

            # set output xform
            self._set_xform_attrs(
                index=xform_index,
                xform_type=self.IO_ENUM.output,
                xform=self.XFORM(
                    loc_matrix=blend_mat["outputMatrix"],
                    world_matrix=world_mat["matrixSum"]
                )
            )

        # hierarcy loop
        blend_weights = []
        for hier_index, hier_attr in enumerate(self.container_node[self._IN_HIER]):
            # remaps for weights
            blend_weight = nw.create_node("remapValue", f"hier{hier_index+1}_blendWeightRemap")
            blend_weight["inputMin"] = hier_index
            blend_weight["inputMax"] = hier_index + 1
            blend_weight["inputValue"] << self.container_node[self._IN_HIER_BLEND]
            blend_weights.append(blend_weight)

            # connect to hier_parent_blend
            hier_parent_blend["target"][hier_index]["weight"] << blend_weight["outValue"]

            for loc_index, loc_attr in enumerate(hier_attr[self._IN_HIER_LOC_MAT]):
                blend_mats[loc_index]["target"][hier_index]["targetMatrix"] << loc_attr
                blend_mats[loc_index]["target"][hier_index]["weight"] << blend_weight["outValue"]

        # set hierBlend max
        cmds.addAttr(str(self.container_node[self._IN_HIER_BLEND]), edit=True, max=num_hiers-1)

        # adding nodes
        self.container_node.add_nodes(hier_parent_blend, *blend_mats, *world_mats, *blend_weights, *vis_remaps)
    
    # override helper functions
    def __create_vis_remap(self, hier_index:int, num_hiers:int, num_hiers_seg:float):
        """creates hier visualize remap

        Args:
            hier_index (int): 
            num_hiers (int): 
            num_hiers_seg (float): 

        Returns:
            nw.Node: 
        """
        hier_vis_remap = nw.create_node("remapValue", f"hier{hier_index}_visRemap")
        hier_vis_remap["inputMax"] = num_hiers - 1
        hier_vis_remap["inputValue"] << self.container_node[self._IN_HIER_BLEND]

        value_index=0
        pre_seg_val = num_hiers_seg * (hier_index - 1)
        seg_val = num_hiers_seg * hier_index
        post_seg_val = num_hiers_seg * (hier_index + 1)
        if pre_seg_val >= 0.0:
            hier_vis_remap["value"][value_index]["value_Position"] = pre_seg_val
            hier_vis_remap["value"][value_index]["value_FloatValue"] = 0.49
            value_index += 1
        hier_vis_remap["value"][value_index]["value_Position"] = seg_val
        hier_vis_remap["value"][value_index]["value_FloatValue"] = 1
        value_index += 1
        if (pre_seg_val - 1.0) < 0.0005:
            hier_vis_remap["value"][value_index]["value_Position"] = post_seg_val
            hier_vis_remap["value"][value_index]["value_FloatValue"] = 0.49
            value_index += 1

        hier_vis_remap["outValue"] >> self.container_node[self._OUT_HIER_VIS][hier_index]

        return hier_vis_remap
class Cluster(base_comp._Hierarchy):
    class_namespace="clust"
    _check_output=False
    _max_num_xforms=(0, 0)

    _IN_CLUST_XFORM = "inClustXform"
    _OUT_CLUST_XFORM = "outClustXform"

    @classmethod
    def create(cls, instance_name = None, parent = None, input_xforms = None, source_component = None, connect_parent_hier = True, connect_axis_vecs = True, control_color=None):
        return super().create(instance_name, parent, None, source_component, connect_parent_hier, connect_axis_vecs, control_color)

    def _override_build(self, control_color=None, **kwargs):
        pass        
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
        self._populate_output_xforms()

        self.container_node.add_nodes(*added_nodes)
            



