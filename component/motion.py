import system.base_component as base_component
import component.control as control
import utils.node_wrapper as nw

class FK(base_component.Hierarchy):
    """given a hierarchy creates an FK chain to accompany it
    """
    class_namespace = "FK"
    root_transform_name = "cntrl_grp"

    @classmethod
    def create(cls, source_component:base_component.Hierarchy, instance_name = None, parent=None, **kwargs):
        kwargs["source_component"] =source_component
        return super().create(instance_name, parent, **kwargs)

    def _override_build(self, **kwargs):
        #qol variables
        added_nodes = []
        HIER_DATA =self.HIER_DATA

        # connecting source component
        source_component = kwargs["source_component"]
        self._connect_source_hier_component(source_component=source_component)

        prev_ws_attr = self.container_node[HIER_DATA.HIER_PARENT_MATRIX]
        prev_init_inv_attr = self.container_node[HIER_DATA.HIER_PARENT_INIT_MATRIX]
        for index, input_xform in enumerate(self.input_node[self.HIER_DATA.INPUT_XFORM]):
            control_inst = control.Circle.create(instance_name=input_xform[HIER_DATA.INPUT_XFORM_NAME], parent=self)

            # loc_mult_matrix = nw.create_node("multMatrix", f"xform{index}_loc_mat_mult")
            ws_mult_matrix = nw.create_node("multMatrix", f"xform{index}_ws_mat_mult")
            added_nodes.append(ws_mult_matrix)

            ws_mult_matrix["matrixIn"][0] << input_xform[HIER_DATA.INPUT_INIT_MATRIX]
            ws_mult_matrix["matrixIn"][1] << prev_init_inv_attr
            ws_mult_matrix["matrixIn"][2] << prev_ws_attr
            ws_mult_matrix["matrixSum"] >> control_inst.container_node["offsetMatrix"]
            
            prev_ws_attr = control_inst.container_node["worldMatrix"]
            prev_init_inv_attr = self.input_node[HIER_DATA.INPUT_XFORM][index][HIER_DATA.INPUT_INIT_INV_MATRIX]

            self._set_output_xform_attrs(
                index=index,
                output_xform_name=input_xform[HIER_DATA.INPUT_XFORM_NAME],
                output_init_matrix=input_xform[HIER_DATA.INPUT_INIT_MATRIX],
                output_init_inv_matrix=input_xform[HIER_DATA.INPUT_INIT_INV_MATRIX],
                output_world_matrix=control_inst.container_node["worldMatrix"]
            )


        self.container_node.add_nodes(*added_nodes)

            

