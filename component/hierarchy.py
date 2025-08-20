import system.base_component as base_component
import component.control as control
import utils.node_wrapper as nw
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

        prev_loc_transform = None

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
            if prev_loc_transform is not None:
                cmds.parent(str(control_loc_inst.transform_node), str(prev_loc_transform))
            input_xform[HIER_DATA.INPUT_LOC_MATRIX] >> control_loc_inst.container_node["offsetMatrix"]
            prev_loc_transform = control_loc_inst.transform_node

            # connecting to component output
            output_xform = self._get_output_xform_attrs(index=index)[index]
            for input_name, output_name in zip(HIER_DATA.INPUT_DATA_NAMES, HIER_DATA.OUTPUT_DATA_NAMES):
                input_xform[input_name] >> output_xform[output_name]

        self.container_node.add_nodes(ws_grp)

        