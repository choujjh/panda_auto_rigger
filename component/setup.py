import system.component as component
import system.component_data as comp_data

class Setup(component.Component):
    
    def _get_input_node_attr_data(self):
        node_data = super()._get_input_node_attr_data()

        node_data.extend_attr_data(
            comp_data.AttrData(attr_name="numXforms", attr_type="long", attr_publish=True),
        )

        return node_data