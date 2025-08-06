import system.component as component
import system.component_data as component_data
import system.component_enum_data as component_enum_data
import component.control as control
import utils.utils as utils

class Setup(component.Hierarchy):
    """A Base class for setup autorigging components. Derived from Hier"""
    root_transform_name = "setup"
    component_type = component_enum_data.ComponentType.setup

    def _get_input_node_attr_data(self):
        node_data = super()._get_input_node_attr_data()
        node_data.extend_attr_data(
            component_data.AttrData("primaryAxis", type_=component_enum_data.AxisEnum.y, publish=True),
            component_data.AttrData("secondaryAxis", type_=component_enum_data.AxisEnum.y, publish=True)
        )
        return node_data

    @classmethod
    def create(
        cls, 
        instance_name = 
        None, 
        parent=None, 
        num_xforms=3, 
        primary_axis:component_enum_data.MayaEnumAttr=component_enum_data.AxisEnum.x, 
        secondary_axis:component_enum_data.MayaEnumAttr=component_enum_data.AxisEnum.y, 
        **kwargs):

        kwargs["num_xforms"] = num_xforms
        kwargs["primary_axis"] = primary_axis
        kwargs["secondary_axis"] = secondary_axis
        return super().create(instance_name, parent, **kwargs)
    
    def _override_build(self, **kwargs):
        num_xforms = kwargs["num_xforms"]

        self.container_node["primaryAxis"] = component_enum_data.get_index_of_item(kwargs["primary_axis"])
        self.container_node["secondaryAxis"] = component_enum_data.get_index_of_item(kwargs["secondary_axis"])

        for index in range(num_xforms):
            input_xform_attrs = self._get_input_xform_attrs(index)

            # setting name
            input_xform_attrs[self.HIER_DATA.INPUT_XFORM_NAME].set(f"xform{index}")

            # creating control
            control_inst = control.Locator.create(instance_name=input_xform_attrs[self.HIER_DATA.INPUT_XFORM_NAME], parent=self)
            control_container = control_inst.container_node
            control_container["offsetMatrix"] = utils.translate_to_matrix([0, index*1.5, 0])

            # connecting to output
            self._set_output_xform_attrs(
                index,
                output_init_matrix=control_container["worldMatrix"],
                output_world_matrix=control_container["worldMatrix"],
            )

class SetupSimpleLimb(Setup):

    @classmethod
    def create(cls, instance_name=None, parent=None, **kwargs):
        return super().create(instance_name, parent, **kwargs)
    def _override_build(self, **kwargs):
        pass

        for index in range(3):
            input_xform_attrs = self._get_input_xform_attrs(index)

            input_xform_attrs[self.HIER_DATA.INPUT_XFORM_NAME].set(f"xform{index}")

        # xform1
        control_inst1 = control.Locator.create()

