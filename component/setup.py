import system.component as component
import component.control as control
import utils.utils as utils

class Setup(component.Hierarchy):
    """A Base class for setup autorigging components. Derived from Hier"""
    root_transform_name = "setup"

    @classmethod
    def create(cls, instance_name = None, parent=None, num_xforms=3, **kwargs):
        kwargs["num_xforms"] = num_xforms
        return super().create(instance_name, parent, **kwargs)
    
    def _override_build(self, **kwargs):
        num_xforms = kwargs["num_xforms"]

        for index in range(num_xforms):
            input_xform_attrs = self._get_input_xform_attrs(index)

            # setting name
            input_xform_attrs[self.HIER_DATA.INPUT_XFORM_NAME].set(f"xform{index}")

            # creating control
            control_inst = control.LocatorControl.create(instance_name=input_xform_attrs[self.HIER_DATA.INPUT_XFORM_NAME], parent=self)
            control_container = control_inst.container_node
            control_container["offsetMatrix"] = utils.translate_to_matrix([0, index*1.5, 0])

            # connecting to output
            self._set_output_xform_attrs(
                index,
                output_init_matrix=control_container["worldMatrix"],
                output_world_matrix=control_container["worldMatrix"],
            )