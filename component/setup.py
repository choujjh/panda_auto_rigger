import system.component as component

class Setup(component.Component):
    
    def _get_input_node_attr_data(self):
        node_data = super()._get_input_node_attr_data()

        node_data.extend_attr_data(
            comp_data.AttrData(attr_name="numXforms", attr_type="integer"),
        )

        return node_data