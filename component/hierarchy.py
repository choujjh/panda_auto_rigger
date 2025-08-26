import system.base_component as base_component
import system.component_data as component_data
import component.control as control
import utils.node_wrapper as nw
import utils.utils as utils
import maya.cmds as cmds

class VisualizeHier(base_component.Hierarchy):
    """Helps visualize and debug hierarchies by creating chains for world space and local visualization"""
    root_transform_name = "vis_grp"

    @classmethod
    def create(cls, source_component:base_component.Hierarchy, instance_name = None, parent=None, **kwargs):
        kwargs["source_component"] = source_component
        return super().create(instance_name, parent, **kwargs)
    
    def _override_build(self, **kwargs):
        source_component= kwargs["source_component"]

        HIER_DATA = self.HIER_DATA

        ws_grp = nw.create_node("transform", "worldSpace_grp")
        cmds.parent(str(ws_grp), str(self.transform_node))
        ws_grp["offsetParentMatrix"] << self.transform_node["worldInverseMatrix"][0]
        loc_grp = nw.create_node("transform", "localSpace_grp")
        cmds.parent(str(loc_grp), str(self.transform_node))
        loc_grp["offsetParentMatrix"] << self.transform_node["worldInverseMatrix"][0]

        prev_loc_transform = loc_grp

        self._connect_source_hier_component(source_component=source_component)

        input_xforms = self._get_input_xform_attrs()
        for index, input_xform in input_xforms.items():            
            # making controls
            control_ws_inst = control.Axis.create(instance_name=f"{input_xform[HIER_DATA.INPUT_XFORM_NAME].value}_ws", parent=self)
            control_loc_inst = control.Axis.create(instance_name=f"{input_xform[HIER_DATA.INPUT_XFORM_NAME].value}_loc", parent=self)
            # locking transforms
            for attr_name in ["t", "r", "s"]:
                for axis in ["x", "y", "z"]:
                    control_ws_inst.transform_node[f"{attr_name}{axis}"].set_locked(True)
                    control_loc_inst.transform_node[f"{attr_name}{axis}"].set_locked(True)
            
            # setting up the rest of ws matrix
            cmds.parent(str(control_ws_inst.transform_node), str(ws_grp))
            input_xform[HIER_DATA.INPUT_WORLD_MATRIX] >> control_ws_inst.container_node["offsetMatrix"]

            # setting up the rest of local matrix
            cmds.parent(str(control_loc_inst.transform_node), str(prev_loc_transform))
            if index != 0:
                input_xform[HIER_DATA.INPUT_LOC_MATRIX] >> control_loc_inst.container_node["offsetMatrix"]
            else:
                input_xform[HIER_DATA.INPUT_WORLD_MATRIX] >> control_loc_inst.container_node["offsetMatrix"]
            prev_loc_transform = control_loc_inst.transform_node

            # connecting to component output
            output_xform = self._get_output_xform_attrs(index=index)[index]
            for input_name, output_name in HIER_DATA.get_paired_names(self.IO_ENUM.input, self.IO_ENUM.output):
                input_xform[input_name] >> output_xform[output_name]

        self.container_node.add_nodes(ws_grp)

class MergeHier(base_component.Hierarchy):
    class_namespace="merge_hier"
    def _get_input_node_build_attr_data(self):
        node_data = super()._get_input_node_build_attr_data()

        for input_name in self.HIER_DATA.get_input_data_names():
            node_data.remove(input_name)

        node_data.extend_attr_data(
            component_data.AttrData("hierParentMatricies", type_="matrix", multi=True, publish=True),
            component_data.AttrData(self.HIER_DATA.INPUT_XFORM, type_="compound", multi=True, publish=True),
            component_data.AttrData(self.HIER_DATA.INPUT_LOC_MATRIX, type_="matrix", parent=self.HIER_DATA.INPUT_XFORM, multi=True),
            component_data.AttrData("hierBlend", type_="float", parent="input", min=0),
        )
        
        return node_data
    @classmethod
    def create(cls, source_components=[], instance_name = None, parent=None, **kwargs):
        kwargs["source_components"] = utils.make_iterable(source_components)
                
        return super().create(instance_name, parent, **kwargs)
    def _override_build(self, **kwargs):
        HIER_DATA = self.HIER_DATA
        source_components = kwargs["source_components"]
        self._connect_source_hier_component(source_components=source_components)

        # connecting hier
        hier_parent_mat = nw.create_node("blendMatrix", "hierParentMatrixBlend")
        for xform_index, hier_attr in enumerate(self.container_node["hierParentMatricies"]):
            if xform_index == 0:
                hier_parent_mat["inputMatrix"] << hier_attr
            else:
                hier_parent_mat["target"][xform_index-1]["targetMatrix"] << hier_attr
        hier_parent_inv = nw.create_node("inverseMatrix", "hierParentInvMatrixBlend")
        hier_parent_inv["inputMatrix"] << hier_parent_mat["outputMatrix"]
        self.container_node[HIER_DATA.HIER_PARENT_MATRIX] << hier_parent_mat["outputMatrix"]
        self.container_node[HIER_DATA.HIER_PARENT_INV_MATRIX] << hier_parent_inv["outputMatrix"] #TODO erroring out

        # getting the weights for components
        added_nodes = [hier_parent_mat, hier_parent_inv]

        blend_weight_attrs = []
        for component_index in range(len(self.container_node[HIER_DATA.INPUT_XFORM])):
            if component_index != 0:
                clamp = nw.create_node("clampRange", f"component{component_index}_clamp")
                if component_index == 1:
                    clamp["input"] << self.container_node["hierBlend"]
                else:
                    component_weight = nw.create_node("subtract", name=f"component{xform_index}_envelope")
                    component_weight["input1"] << self.container_node["hierBlend"]
                    component_weight["input2"].set(xform_index-1)
                    clamp["input"] << component_weight["output"]
                    added_nodes.append(component_weight)
                added_nodes.append(clamp)
                blend_weight_attrs.append(clamp["output"])

        # creating blends
        prev_ws_attr = hier_parent_mat["outputMatrix"]
        hier_len = len(self.container_node[HIER_DATA.INPUT_XFORM][0][HIER_DATA.INPUT_LOC_MATRIX])
        for xform_index in range(hier_len):
            blend_mat = nw.create_node("blendMatrix", name=f"xform{xform_index}_loc_blend")

            #adding world space
            mult_mat = nw.create_node("multMatrix", name=f"xform{xform_index}_ws_mat")
            mult_mat["matrixIn"][0] << blend_mat["outputMatrix"]
            mult_mat["matrixIn"][1] << prev_ws_attr
            prev_ws_attr = mult_mat["matrixSum"]
            
            #local space blend
            for component_index, input_xform in enumerate(self.container_node[HIER_DATA.INPUT_XFORM]):
                loc_mat_attr = input_xform[HIER_DATA.INPUT_LOC_MATRIX][xform_index]
                if component_index == 0:
                    blend_mat["inputMatrix"] << loc_mat_attr
                else:
                    blend_mat["target"][component_index-1]["targetMatrix"] << loc_mat_attr
                    blend_mat["target"][component_index-1]["weight"] << blend_weight_attrs[component_index-1]
                added_nodes.extend([blend_mat, mult_mat])

            self._set_output_xform_attrs(
                index=xform_index,
                output_world_matrix=mult_mat["matrixSum"],
                output_loc_matrix=blend_mat["outputMatrix"],
            )
                        
        self.container_node.add_nodes(*added_nodes)

    def _connect_source_hier_component(self, source_components):
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
                if not issubclass(type(source_component), base_component.Hierarchy):
                    raise RuntimeError(f"{source_component.container_node} is not hierarchy component")
                
            for hier_index, source_component in enumerate(source_components):
                # input xform local attrs
                src_container = source_component.container_node
                src_xforms = src_container[HIER_DATA.OUTPUT_XFORM]
                for xform_index, src_out_xform  in enumerate(src_xforms):
                    self_loc_matrix = self.container_node[HIER_DATA.INPUT_XFORM][hier_index][HIER_DATA.INPUT_LOC_MATRIX][xform_index]
                    src_out_xform[HIER_DATA.OUTPUT_LOC_MATRIX] >> self_loc_matrix

                    src_container[HIER_DATA.HIER_PARENT_MATRIX] >> self.container_node["hierParentMatricies"][hier_index]
                # connect up output name, world matrix and init matricies 
                curr_src_container = source_components[0].container_node
                for index, src_out_xform in enumerate(curr_src_container[HIER_DATA.OUTPUT_XFORM]):
                    self._set_output_xform_attrs(
                        index=index,
                        output_xform_name=src_out_xform[HIER_DATA.OUTPUT_XFORM_NAME],
                        output_init_matrix=src_out_xform[HIER_DATA.OUTPUT_INIT_MATRIX],
                        output_init_inv_matrix=src_out_xform[HIER_DATA.OUTPUT_INIT_INV_MATRIX]
                    )
            
            # setting hiers
            source_container = source_components[0].container_node
            source_container[HIER_DATA.HIER_PARENT_INV_MATRIX] >> self.container_node[HIER_DATA.HIER_PARENT_INV_MATRIX]
            


        else:
            raise RuntimeError("source component needs to be iterable")
    def _populate_output_xforms(self):
        pass

    def _check_xforms(self):
        output_xform_len = len(self.output_node[self.HIER_DATA.OUTPUT_XFORM])
        if output_xform_len == 0:
            cmds.warning(f"{self.container_node} component has no xform output")
        
        return super()._check_xforms(False)
    
