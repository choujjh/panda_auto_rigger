import system.base_component as base_comp
import component.motion as motion
import component.misc as misc
import component.setup as setup
import component.control as control
import system.component_data as component_data
import system.component_enum_data as component_enum_data
import utils.node_wrapper as nw

class SimpleLimb(base_comp.Anim):
    """Simple Limb Anim component (has a merged fk, ik, and a settings control). used in conjunction with simpleLimb setup"""
    _setup_component_type = setup.SimpleLimb

    @classmethod
    def create(cls, instance_name = None, parent = None, primary_axis = component_enum_data.AxisEnum.x, secondary_axis = component_enum_data.AxisEnum.y, add_settings_cntrl = True, mirror_source = None, mirror_axis = component_enum_data.AxisEnum.x, source_component = None, connect_hierarchy = True, connect_axis_vecs = True, control_color=None, setup_color=None, hier_side = component_enum_data.CharacterSide.none):
        return super().create(instance_name, parent, 3, primary_axis, secondary_axis, add_settings_cntrl, mirror_source, mirror_axis, source_component, connect_hierarchy, connect_axis_vecs, control_color, setup_color, hier_side)

    def _override_build(self, control_color=None, **build_kwargs):
        HIER_DATA = self.HIER_DATA

        ik_inst = motion.SimpleIK.create(source_component=self.setup_component, control_color=control_color, parent=self)
        fk_inst = motion.FK.create(source_component=self.setup_component, control_color=control_color, parent=self)

        merge_hier_inst = misc.MergeHier.create(source_components = [fk_inst, ik_inst], parent=self)

        for index in range(len(self.container_node[HIER_DATA.OUTPUT_XFORM])):
            merge_output_xform = merge_hier_inst.container_node[HIER_DATA.OUTPUT_XFORM][index]
            self_output_xform = self.container_node[HIER_DATA.OUTPUT_XFORM][index]
            for attr_name in component_data.HierData.OUTPUT_DATA_NAMES:
                merge_output_xform[attr_name] >> self_output_xform[attr_name]

        # promoting to settings attr
        settings_transform = self.settings_component.transform_node

        settings_transform.add_attr("_", type="enum", enumName="FK_IK:")
        settings_transform["_"].set_locked(True)
        settings_transform["_"].set_keyable(True)
        self.settings_component.promote_attr_to_keyable(attr=merge_hier_inst.container_node[merge_hier_inst._IN_HIER_BLEND], name="blend")

        settings_transform.add_attr("__", type="enum", enumName="IK:")
        settings_transform["__"].set_locked(True)
        settings_transform["__"].set_keyable(True)
        self.settings_component.promote_attr_to_keyable(attr=ik_inst.container_node[ik_inst._IK_STRETCH_ENAB])
        self.settings_component.promote_attr_to_keyable(attr=ik_inst.container_node[ik_inst._IK_SOFT_IK_ENAB])
        self.settings_component.promote_attr_to_keyable(attr=ik_inst.container_node[ik_inst._IK_SOFT_BLEND_START])
        self.settings_component.promote_attr_to_keyable(attr=ik_inst.container_node[ik_inst._IK_BLEND_TYP])
        self.settings_component.promote_attr_to_keyable(attr=ik_inst.container_node[ik_inst._IK_BLEND_CRV])

class SingleXform(base_comp.Anim):
    """Single Joint Component"""

    @classmethod
    def create(cls, instance_name = None, parent = None, primary_axis = component_enum_data.AxisEnum.x, secondary_axis = component_enum_data.AxisEnum.y, add_settings_cntrl = True, mirror_source = None, mirror_axis = component_enum_data.AxisEnum.x, source_component = None, connect_hierarchy = True, connect_axis_vecs = True, control_color=None, setup_color=None, hier_side = component_enum_data.CharacterSide.none):
        return super().create(instance_name, parent, 1, primary_axis, secondary_axis, add_settings_cntrl, mirror_source, mirror_axis, source_component, connect_hierarchy, connect_axis_vecs, control_color, setup_color, hier_side)

    def _override_build(self, control_color=None, **build_kwargs):
        setup_out_xform0 = self.setup_component.get_xform_attrs(xform_type=self.IO_ENUM.output, index=0)
        self._set_xform_attrs(index=0, xform_type=self.IO_ENUM.input, xform_name=self.container_node[self._BLD_INST_NAME])

        cntrl_mult_matrix = nw.create_node("multMatrix", "cntrl_ws_offset_mat")
        cntrl_mult_matrix["matrixIn"][0]  << setup_out_xform0[self.HIER_DATA.OUTPUT_WORLD_MATRIX]
        cntrl_mult_matrix["matrixIn"][1]  << self.transform_node["worldInverseMatrix"][0]

        cntrl_inst = control.Circle.create(instance_name=self.container_node[self._BLD_INST_NAME], parent=self, build_s=4, color=control_color)
        cntrl_inst.container_node[cntrl_inst._IN_OFF_MAT] << cntrl_mult_matrix["matrixSum"]

        self.container_node.add_nodes(cntrl_mult_matrix)

        self._set_xform_attrs(
            index=0,
            xform_type=self.IO_ENUM.output,
            xform_name=self.container_node[self._BLD_INST_NAME],
            init_matrix=setup_out_xform0[self.HIER_DATA.OUTPUT_INIT_MATRIX],
            init_inv_matrix=setup_out_xform0[self.HIER_DATA.OUTPUT_WORLD_MATRIX],
            world_matrix=cntrl_inst.container_node[cntrl_inst._OUT_WS_MAT],
            world_inv_matrix=cntrl_inst.container_node[cntrl_inst._OUT_WS_INV_MAT],
        )
        self.rename_children()
