import system.base_component as base_comp
import component.motion as motion
import component.misc as misc
import component.setup as setup
import component.control as control
import utils.node_wrapper as nw
import utils.utils as utils

class SimpleLimb(base_comp.Anim):
    """Simple Limb Anim component (has a merged fk, ik, and a settings control). used in conjunction with simpleLimb setup"""
    _setup_component_type = setup.SimpleLimb
    _max_num_xforms = (3, 3)

    def _override_build(self, control_color=None, **build_kwargs):
        ik_inst = motion.SimpleIK.create(source_component=self.setup_component, control_color=control_color, parent=self)
        fk_inst = motion.FK.create(source_component=self.setup_component, control_color=control_color, parent=self)

        merge_hier_inst = misc.MergeHier.create(source_components = [fk_inst, ik_inst], parent=self)

        for index, output_xform in merge_hier_inst.get_xform_attrs(xform_type=self.IO_ENUM.output).items():
            self._set_xform_attrs(
                index=index, 
                xform_type=self.IO_ENUM.output,
                xform=output_xform)

        # promoting to settings attr
        if self.settings_component is not None:
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

        # setting settings transform
        if self.settings_guide_component is not None:
            self.settings_guide_component.transform_node["t"] = -3 * self.container_node[self._SEC_VEC].value
            ter_vec = self.container_node[self._TER_VEC].value
            if ter_vec != utils.Vector(0, 1, 0) or ter_vec != utils.Vector(0, -1, 0):
                self.settings_guide_component.transform_node["r"] = 90 * utils.Vector(0, 1, 0) ^ ter_vec

class SingleXform(base_comp.Anim):
    """Single Joint Component"""
    _max_num_xforms = (1, 1)

    def _override_build(self, control_color=None, **build_kwargs):
        setup_out_xform0 = self.setup_component.get_xform_attrs(xform_type=self.IO_ENUM.output, index=0)
        cntrl_mult_matrix = nw.create_node("multMatrix", "cntrl_ws_offset_mat")
        cntrl_mult_matrix["matrixIn"][0]  << setup_out_xform0.world_matrix
        cntrl_mult_matrix["matrixIn"][1]  << self.transform_node["worldInverseMatrix"][0]

        cntrl_inst = control.Circle.create(parent=self, color=control_color)
        cntrl_inst.container_node[cntrl_inst._IN_OFF_MAT] << cntrl_mult_matrix["matrixSum"]

        self.container_node.add_nodes(cntrl_mult_matrix)

        self._set_xform_attrs(
            index=0,
            xform_type=self.IO_ENUM.output,
            xform=self.XFORM(
                init_matrix=setup_out_xform0.init_matrix,
                init_inv_matrix=setup_out_xform0.init_inv_matrix,
                world_matrix=cntrl_inst.container_node[cntrl_inst._OUT_WS_MAT],
                world_inv_matrix=cntrl_inst.container_node[cntrl_inst._OUT_WS_INV_MAT],
            )
        )
        if self.settings_guide_component is not None:
            self.settings_guide_component.transform_node["t"] = [0, 0, -6]