import system.component as component
import system.component_data as component_data

class Setup(component.Component):
    
    def _get_input_node_attr_data(self):
        node_data = super()._get_input_node_attr_data()

        node_data.extend_attr_data(
            component_data.AttrData(name="numXforms", type="long", publish=True),
        )

        return node_data