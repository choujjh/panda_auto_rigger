import system.base_component as base_component
import component.motion as motion
import component.hierarchy as hierarchy
import system.component_data as component_data
import utils.node_wrapper as nw
import component.control as control

class SimpleLimbAnim(base_component.Anim):
    def _get_input_node_build_attr_data(self):
        node_data = super()._get_input_node_build_attr_data()
        node_data.extend_attr_data(
            component_data.AttrData("settingCntrlXformFollow", type_="long", publish=True, min=0, max=2),
            component_data.AttrData("settingCntrlInitMatrix", type_="matrix", publish=True)
        )
        return node_data

    def _override_build(self, **kwargs):
        HIER_DATA = self.HIER_DATA
        source_component = kwargs["source_component"]
        connect_hierarchy = kwargs["connect_hierarchy"]
        control_color = kwargs["control_color"]

        self._connect_source_hier_component(source_component=source_component, connect_hierarchy=connect_hierarchy)

        ik_inst = motion.SimpleIK.create(source_component=self, connect_hierarchy=True, control_color=control_color, parent=self)
        fk_inst = motion.FK.create(source_component=self, connect_hierarchy=True, control_color=control_color, parent=self)

        merge_hier_inst = hierarchy.MergeHier.create(source_components = [fk_inst, ik_inst], parent=self)

        for index in range(len(self.container_node[HIER_DATA.OUTPUT_XFORM])):
            merge_output_xform = merge_hier_inst.container_node[HIER_DATA.OUTPUT_XFORM][index]
            self_output_xform = self.container_node[HIER_DATA.OUTPUT_XFORM][index]
            for attr_name in component_data.HierData.get_output_data_names(init_matricies=False):
                merge_output_xform[attr_name] >> self_output_xform[attr_name]

        # settings control
        set_mult_matrix = nw.create_node("multMatrix", name="settings_ws")
        set_choice_inv_init = nw.create_node("choice", "settings_follow_init_inv_choice")
        set_choice_ws = nw.create_node("choice", "settings_follow_ws_choice")
        set_choice_inv_init["selector"] << self.container_node["settingCntrlXformFollow"]
        set_choice_ws["selector"] << self.container_node["settingCntrlXformFollow"]
        for index in range(3):
            set_choice_inv_init["input"][index] << self.container_node[HIER_DATA.OUTPUT_XFORM][index][HIER_DATA.OUTPUT_INIT_INV_MATRIX]
            set_choice_ws["input"][index] << merge_hier_inst.container_node[HIER_DATA.OUTPUT_XFORM][index][HIER_DATA.OUTPUT_WORLD_MATRIX]
        set_mult_matrix["matrixIn"][0] << self.container_node["settingCntrlInitMatrix"]
        set_mult_matrix["matrixIn"][1] << set_choice_inv_init["output"]
        set_mult_matrix["matrixIn"][2] << set_choice_ws["output"]

        settings_cntrl_inst = control.Gear.create(instance_name="settings", parent=self, color=control_color)
        for attr in ["t", "r", "s"]:
            for axis in ["x", "y", "z"]:
                settings_cntrl_inst.transform_node[f"{attr}{axis}"].set_locked(True)
                settings_cntrl_inst.transform_node[f"{attr}{axis}"].set_keyable(False)
        settings_cntrl_inst.container_node["offsetMatrix"] << set_mult_matrix["matrixSum"]
        set_transform = settings_cntrl_inst.transform_node

        set_transform.add_attr("_", type="enum", enumName="FK_IK:")
        set_transform["_"].set_locked(True)
        set_transform["_"].set_keyable(True)
        settings_cntrl_inst.promote_attr_to_keyable(attr=merge_hier_inst.container_node["hierBlend"], name="blend")

        set_transform.add_attr("__", type="enum", enumName="IK:")
        set_transform["__"].set_locked(True)
        set_transform["__"].set_keyable(True)
        settings_cntrl_inst.promote_attr_to_keyable(attr=ik_inst.container_node["IKStretchEnabled"], name="IKStretchEnabled")
        settings_cntrl_inst.promote_attr_to_keyable(attr=ik_inst.container_node["softIKEnabled"])
        settings_cntrl_inst.promote_attr_to_keyable(attr=ik_inst.container_node["softIKBlendStart"])
        settings_cntrl_inst.promote_attr_to_keyable(attr=ik_inst.container_node["blendType"])
        settings_cntrl_inst.promote_attr_to_keyable(attr=ik_inst.container_node["blendCurve"])



        self.container_node.add_nodes(set_mult_matrix, set_choice_inv_init, set_choice_ws)

    def _connect_source_hier_component(self, source_component, connect_hierarchy):
        super()._connect_source_hier_component(source_component, connect_hierarchy)
        for attr in ["settingCntrlXformFollow", "settingCntrlInitMatrix"]:
            source_component.container_node[attr] >> self.container_node[attr]
        

        


