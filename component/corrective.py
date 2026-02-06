import system.component_data as component_data
import system.component_enum_data as component_enum_data
import system.base_component as base_comp
import utils.utils as utils


class WeightDriver(base_comp._Hierarchy):
    """Holds driven weights from hierarchy

    Attributes:
        _OUT_DRIVER (str): str constant "driver"
        _OUT_WEIGHT (str): str constant "weight"
        _OUT_WEIGHT_NAME (str): str constant "name"
    """

    class_namespace = "weightDrv"
    component_type = component_enum_data.ComponentType.corrective

    _populate_output = False
    _check_output = False

    _OUT_DRIVER = "driver"
    _OUT_WEIGHT = "weight"
    _OUT_WEIGHT_NAME = "name"

    def _output_attr_build_data(self):
        node_data = super()._output_attr_build_data()

        node_data.extend_attr_data(
            component_data.AttrData(
                self._OUT_DRIVER,
                type_="compound",
                multi=True,
                parent=self.HIER_DATA.OUT_XFORM,
            ),
            component_data.AttrData(
                self._OUT_WEIGHT, type_="double", parent=self._OUT_DRIVER
            ),
            component_data.AttrData(
                self._OUT_WEIGHT_NAME, type_="string", parent=self._OUT_DRIVER
            ),
        )

        return node_data

    def _override_build(self, control_color=None, **kwargs):
        """connects input to output xforms

        Args:
            control_color (_type_, optional): only here for error purposes
        """
        self.connect_input_to_output()


class CorrectiveXforms(base_comp._Hierarchy):
    """Corrective xform component

    Attributes:
        __MAP_WEIGHT_DRV_CNTNR (str): str constant "weightDriverContainer"
    """

    component_type = component_enum_data.ComponentType.corrective
    input_node_type = "transform"
    _check_output = False
    _populate_output = False

    __MAP_WEIGHT_DRV_CNTNR = "weightDriverContainer"

    class_namespace = "CorrectiveXform"

    @property
    def _weight_driver_component(self) -> WeightDriver:
        """Returns weight driver component

        Returns:
            WeightDriver:
        """
        return self._get_node_from_key(self.__MAP_WEIGHT_DRV_CNTNR, as_component=True)

    def _override_build(self, control_color=None, **kwargs):
        self.__create_weight_driver_component()

    def __create_weight_driver_component(self):
        """Creates motion component and maps it to anim container"""
        weight_driver_inst = WeightDriver.create(source_component=self, parent=self)
        utils.map_to_container(
            weight_driver_inst.container_node, self.__MAP_WEIGHT_DRV_CNTNR
        )
