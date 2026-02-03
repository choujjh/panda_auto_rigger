import system.base_component as base_comp
import system.component_data as component_data
import utils.node_wrapper as nw


class HierLengths(base_comp._Component):
    """Creates lengths for each segment of a hierarchy

    Attributes:
        _IN_WRLD_MAT (str): str constant "worldMatrix"
        _OUT_LEN (str): str constant "length"
        _OUT_CURR_LEN (str): str constant "currLen"
        _OUT_CLIP_CURR_LEN (str): str constant "clipCurrLen"
    """
    class_namespace = "hierLen"

    _IN_WRLD_MAT = "worldMatrix"
    _OUT_LEN = "length"
    _OUT_CURR_LEN = "currLen"
    _OUT_CLIP_CURR_LEN = "clipCurrLen"

    @classmethod
    def create(
        cls,
        instance_name=None,
        parent=None,
        source_component: base_comp._Hierarchy = None,
    ):
        """create Hier dist component

        Args:
            instance_name (str, nw.Attr, optional): Defaults to None.
            parent (base_comp._Component, optional): Defaults to None.
            source_component (base_comp._Hierarchy, optional): Defaults to None.

        Returns:
            HierDist:
        """
        return cls._kwarg_create(**cls._process_locals(kwarg_dict=locals()))

    def _input_attr_build_data(self):
        """Creates input attr data

        Returns:
            component_data.NodeData:
        """
        node_data = super()._input_attr_build_data()
        node_data.extend_attr_data(
            component_data.AttrData(
                self._IN_WRLD_MAT, type_="matrix", parent=self._IN, multi=True
            )
        )
        return node_data

    def _output_attr_build_data(self):
        """Creates output attr data

        Returns:
            component_data.NodeData:
        """
        node_data = super()._output_attr_build_data()
        node_data.extend_attr_data(
            component_data.AttrData(
                self._OUT_LEN, type_="double", parent=self._OUT, multi=True
            ),
            component_data.AttrData(
                self._OUT_CURR_LEN, type_="double", parent=self._OUT
            ),
            component_data.AttrData(
                self._OUT_CLIP_CURR_LEN, type_="double", parent=self._OUT
            ),
        )
        return node_data

    def _pre_build(
        self,
        instance_name=None,
        parent=None,
        source_component: base_comp._Hierarchy = None,
        **kwargs,
    ):
        """Pre build connecting source component to this component

        Args:
            instance_name (str, nw.Attr, optional): Defaults to None.
            parent (base_component._Component, optional): Defaults to None.
            source_component (base_comp._Hierarchy, optional): Defaults to None.
        """
        super()._pre_build(instance_name, parent, **kwargs)

        if source_component is not None:
            for index, xform in enumerate(source_component.get_as_source_xforms()):
                self.container_node[self._IN_WRLD_MAT][index] << xform.world_matrix

    def _override_build(self, **kwargs):
        """Takes care of derived component creation. must be implemented by child class"""

        total_len_node = nw.create_node("plusMinusAverage", "totLenPlus")
        world_mat_indicies = self.container_node[self._IN_WRLD_MAT].get_indicies()

        # Adding xfgorm lengths
        added_nodes = []
        for index in world_mat_indicies[1:]:
            prev_attr = self.container_node[self._IN_WRLD_MAT][index - 1]
            attr = self.container_node[self._IN_WRLD_MAT][index]
            len_node = nw.create_node("distanceBetween", f"xform{index}Dist")
            len_node["inMatrix1"] << prev_attr
            len_node["inMatrix2"] << attr
            len_node["distance"] >> total_len_node["input1D"].next_index_attr()
            len_node["distance"] >> self.container_node[self._OUT_LEN].next_index_attr()

        # Getting unclip length
        unclip_len_node = nw.create_node("distanceBetween", "currLenDist")
        (
            unclip_len_node["inMatrix1"]
            << self.container_node[self._IN_WRLD_MAT][world_mat_indicies[0]]
        )
        (
            unclip_len_node["inMatrix2"]
            << self.container_node[self._IN_WRLD_MAT][world_mat_indicies[-1]]
        )
        unclip_len_node["distance"] >> self.container_node[self._OUT_CURR_LEN]

        # getting clip len
        curr_len_min_node = nw.create_node("min", "clipCurrLenMin")
        curr_len_min_node["input"][0] << unclip_len_node["distance"]
        curr_len_min_node["input"][1] << total_len_node["output1D"]
        curr_len_min_node["output"] >> self.container_node[self._OUT_CLIP_CURR_LEN]

        self.container_node.add_nodes(
            *added_nodes, total_len_node, unclip_len_node, curr_len_min_node
        )


class LawOfCos(base_comp._Component):
    pass
