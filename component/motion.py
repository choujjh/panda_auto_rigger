import system.base_component as base_comp
import component.control as control
import component.setup as setup
import component.matrix as matrix
import utils.node_wrapper as nw
import system.component_data as component_data
import system.component_enum_data as component_enum_data
import component.hierarchy_helper as hier_helper
import maya.cmds as cmds
import utils.utils as utils
from typing import Union


class _Motion(base_comp._Hierarchy):
    """base class for motion autorigging components. Derived from Hierarchy"""

    component_type = component_enum_data.ComponentType.motion
    input_node_name = "grp"
    input_node_type = "transform"
    class_namespace = "motion"


class MotionWrapper(_Motion):
    """wraps motion components for anim use"""

    _populate_output = False
    _check_output = False

    def _override_build(
        self,
        control_color: Union[
            list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node
        ] = None,
        **kwargs,
    ):
        pass


class FK(_Motion):
    """Given a hierarchy creates an FK chain to accompany it"""

    class_namespace = "FK"

    def _override_build(
        self,
        control_color: Union[
            list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node
        ] = None,
        **kwargs,
    ):
        """adds fk control to all xforms from source

        Args:
            control_color (Union[list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node], optional): _description_. Defaults to None.
        """
        # qol variables
        added_nodes = []

        hier_parent = self.get_hier_parent_attrs()
        prev_ws_attr = hier_parent.matrix
        prev_inv_attr = hier_parent.init_inv_matrix
        input_xforms = self.get_xform_attrs(xform_type=self.IO_ENUM.input)
        for index, input_xform in input_xforms.items():
            control_inst = control.Circle.create(
                instance_name=input_xform.xform_name,
                axis_vec=self.container_node[self._PRM_VEC].value,
                parent=self,
                color=control_color,
                xform_map_index=index,
            )
            for attr in ["sx", "sy", "sz"]:
                control_inst.transform_node[attr].set_locked(True)
                control_inst.transform_node[attr].set_keyable(False)

            ws_mult_matrix = nw.create_node("multMatrix", f"xform{index}_ws_mat_mult")
            added_nodes.append(ws_mult_matrix)

            ws_mult_matrix["matrixIn"][0] << input_xform.world_matrix
            ws_mult_matrix["matrixIn"][1] << prev_inv_attr
            ws_mult_matrix["matrixIn"][2] << prev_ws_attr
            (
                ws_mult_matrix["matrixSum"]
                >> control_inst.container_node[control._Control._IN_OFF_MAT]
            )

            prev_ws_attr = control_inst.container_node[control._Control._OUT_WS_MAT]
            prev_inv_attr = input_xform.world_inv_matrix

            self._set_xform_attrs(
                index=index,
                xform_type=self.IO_ENUM.output,
                xform=self.XFORM(
                    world_matrix=control_inst.container_node[
                        control._Control._OUT_WS_MAT
                    ]
                ),
            )
        self.container_node.add_nodes(*added_nodes)


class SimpleIK(_Motion):
    """Given the SimpleLimb creates a 2 chain IK chain

    Attributes:
        _ROOT_WORLD_MAT (str): str constant "rootWorldMatrix"
        _ROOT_INIT_INV_MAT (str): str constant "rootInitInvMatrix"
        _END_WORLD_MAT (str): str constant "endWorldMatrix"
        _END_INIT_INV_MAT (str): str constant "endInitInvMatrix"
        _SPACE_SWITCH (str): str constant "spaceSwitch"
        _SPACE (str): str constant "space"
        _SPACE_MAT (str): str constant "spaceMatrix"
        _SPACE_INIT_INV_MAT (str): str constant "spaceInitInvMat"
        _IK (str): str constant "IK"
        _IK_STRETCH_ENAB (str): str constant "ikStretchEnabled"
        _IK_SOFT_BLEND_START (str): str constant "softIKBlendStart"
        _IK_SOFT_IK_ENAB (str): str constant "softIKEnabled"
        _IK_BLEND_TYP (str): str constant "blendType"
        _IK_BLEND_CRV (str): str constant "blendCurve"
    """

    class_namespace = "simpleIK"
    _max_num_xforms = (3, 3)

    _ROOT_WORLD_MAT = "rootWorldMatrix"
    _ROOT_INIT_INV_MAT = "rootInitInvMatrix"
    _END_WORLD_MAT = "endWorldMatrix"
    _END_INIT_INV_MAT = "endInitInvMatrix"
    _SPACE_SWITCH = "spaceSwitch"
    _SPACE = "space"
    _SPACE_MAT = "spaceMatrix"
    _SPACE_INIT_INV_MAT = "spaceInitInvMat"
    _IK = "IK"
    _IK_STRETCH_ENAB = "ikStretchEnabled"
    _IK_SOFT_BLEND_START = "softIKBlendStart"
    _IK_SOFT_IK_ENAB = "softIKEnabled"
    _IK_BLEND_TYP = "blendType"
    _IK_BLEND_CRV = "blendCurve"

    def _input_attr_build_data(self):
        """Defines all the added, published, or modified attributes for the
        input node. inherits all input node data from _Motion

        Returns:
            comp_data.NodeData:
        """
        node_data = super()._input_attr_build_data()
        node_data.extend_attr_data(
            component_data.AttrData(
                self._ROOT_WORLD_MAT, type_="matrix", parent=self._IN
            ),
            component_data.AttrData(
                self._ROOT_INIT_INV_MAT, type_="matrix", parent=self._IN
            ),
            component_data.AttrData(
                self._END_WORLD_MAT, type_="matrix", parent=self._IN
            ),
            component_data.AttrData(
                self._END_INIT_INV_MAT, type_="matrix", parent=self._IN
            ),
            component_data.AttrData(
                self._SPACE, type_="enum", enumName="None", parent=self._IN
            ),
            component_data.AttrData(
                self._SPACE_SWITCH, type_="compound", parent=self._IN, multi=True
            ),
            component_data.AttrData(
                self._SPACE_MAT, type_="matrix", parent=self._SPACE_SWITCH
            ),
            component_data.AttrData(
                self._SPACE_INIT_INV_MAT, type_="matrix", parent=self._SPACE_SWITCH
            ),
            component_data.AttrData(self._IK, type_="compound", parent=self._IN),
            component_data.AttrData(
                self._IK_STRETCH_ENAB, type_="bool", parent=self._IK, value=True
            ),
            component_data.AttrData(
                self._IK_SOFT_BLEND_START,
                type_="double",
                parent=self._IK,
                value=0.9,
                min=0,
                max=1,
            ),
            component_data.AttrData(
                self._IK_SOFT_IK_ENAB, type_="bool", parent=self._IK
            ),
            component_data.AttrData(
                self._IK_BLEND_TYP,
                type_=component_enum_data.SoftIKBlendTypes.smoothStep,
                parent=self._IK,
            ),
            component_data.AttrData(
                self._IK_BLEND_CRV,
                type_=component_enum_data.SoftIKBlendCurve.quadratic,
                parent=self._IK,
            ),
        )
        return node_data

    def _pre_build(
        self,
        instance_name=None,
        parent=None,
        input_xforms=None,
        source_component=None,
        connect_parent_hier=None,
        connect_axis_vecs=True,
        **kwargs,
    ):
        """Handles creation and connection of initial nodes

        Args:
            instance_name (Union[str, nw.Attr], optional): name of component. Defaults to None.
            parent (Union[_Component, nw.Container], optional): Defaults to None.
            input_xforms (Union[list[component_data.Xform], int], optional): input xforms to initialize component with. Defaults to None.
            source_component (_Hierarchy, optional):  source component to connect hierarchy from. Defaults to None.
            connect_parent_hier (bool, optional): Defaults to None.
            connect_axis_vecs (bool, optional): Defaults to True.
        """
        super()._pre_build(
            instance_name,
            parent,
            input_xforms,
            source_component,
            connect_parent_hier,
            connect_axis_vecs,
            **kwargs,
        )
        xforms = source_component.get_xform_attrs(
            xform_type=self.IO_ENUM.output, index=[0, 2]
        )
        if isinstance(source_component, setup.Mirror):
            # get from input
            self.container_node[self._ROOT_WORLD_MAT] << xforms[0].init_matrix
            self.container_node[self._ROOT_INIT_INV_MAT] << xforms[0].init_inv_matrix
            self.container_node[self._END_WORLD_MAT] << xforms[2].init_matrix
            self.container_node[self._END_INIT_INV_MAT] << xforms[2].init_inv_matrix

    def __create_space_switch_nodes(self):
        """Creates internal space switch nodes"""
        space_switch_choice = nw.create_node("choice", "spaceMatrixChoice")
        space_switch_init_inv_choice = nw.create_node(
            "choice", "spaceInitInvMatrix_choice"
        )

        space_len = len(self.container_node[self._SPACE_SWITCH])
        if space_len == 0:
            space_len = 1
        for index in range(space_len):
            (
                space_switch_choice["input"][index]
                << self.container_node[self._SPACE_SWITCH][index][self._SPACE_MAT]
            )
            (
                space_switch_init_inv_choice["input"][index]
                << self.container_node[self._SPACE_SWITCH][index][
                    self._SPACE_INIT_INV_MAT
                ]
            )

        space_switch_choice["selector"] << self.container_node[self._SPACE]
        space_switch_init_inv_choice["selector"] << self.container_node[self._SPACE]

        self.container_node.add_nodes(space_switch_choice, space_switch_init_inv_choice)

        return space_switch_choice, space_switch_init_inv_choice

    def __ik_control(
        self,
        name: str,
        input_xform_index: int,
        control_matrix: nw.Attr,
        control_inv_matrix: nw.Attr,
        parent_init_inv_matrix: nw.Attr,
        parent_world_matrix: nw.Attr,
        color: Union[
            list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node
        ] = None,
    ):
        """Creates the IK control. returns world matrix

        Args:
            name (str):
            input_xform_index (int): input matrix index for it's parent
            control_matrix (nw.Attr):
            control_matrix (nw.Attr):
            parent_init_inv_matrix (nw.Attr):
            parent_world_matrix (nw.Attr):
            color (Union[list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node]):

        Returns
            nw.Attr:
        """
        input_xform = self.get_xform_attrs(
            index=input_xform_index, xform_type=self.IO_ENUM.input
        )
        control_inst = control.Box.create(
            instance_name=input_xform.xform_name,
            parent=self,
            color=color,
            xform_map_index=input_xform_index,
        )
        for attr_name in ["sx", "sy", "sz"]:
            control_inst.transform_node[attr_name].set_locked(True)
            control_inst.transform_node[attr_name].set_keyable(False)

        # get orient of control
        build_offset = True
        if not control_matrix.has_src_connection():
            control_matrix = input_xform.world_matrix
            build_offset = False
        if not control_inv_matrix.has_src_connection():
            control_inv_matrix = input_xform.world_inv_matrix
            build_offset = False

        cntrl_ws_mult_node = nw.create_node("multMatrix", f"{name}_cntrl_ws_mat")
        cntrl_ws_mult_node["matrixIn"][0] << control_matrix
        cntrl_ws_mult_node["matrixIn"][1] << parent_init_inv_matrix
        cntrl_ws_mult_node["matrixIn"][2] << parent_world_matrix

        (
            control_inst.container_node[control._Control._IN_OFF_MAT]
            << cntrl_ws_mult_node["matrixSum"]
        )

        end_orient_matrix = control_inst.container_node[control_inst._OUT_WS_MAT]
        if build_offset:
            loc_mat = nw.create_node(
                "multMatrix", f"xform{input_xform_index}_offset_matrix"
            )
            loc_mat["matrixIn"][0] << input_xform.init_matrix
            loc_mat["matrixIn"][1] << control_inv_matrix
            (
                loc_mat["matrixIn"][2]
                << control_inst.container_node[control_inst._OUT_WS_MAT]
            )
            end_orient_matrix = loc_mat["matrixSum"]
            self.container_node.add_nodes(cntrl_ws_mult_node, loc_mat)

        self.container_node.add_nodes(cntrl_ws_mult_node)

        return end_orient_matrix

    def __create_dist_nodes(
        self, root_world_matrix: nw.Attr, end_world_matrix: nw.Attr
    ):
        """Creates distance nodes for ik calculations. curr_len is the distance between root and end controls

        Args:
            root_world_matrix (nw.Attr):
            end_world_matrix (nw.Attr):
        Returns:
            len1_node:nw.Node, len2_node:nw.Node, curr_len_nodenw.Node:
        """
        input_xforms = self.get_xform_attrs(xform_type=self.IO_ENUM.input)
        hier_parent = self.get_hier_parent_attrs()

        len1_node = nw.create_node("distanceBetween", "len1_init_dist")
        len1_node["inMatrix1"] << input_xforms[0].world_matrix
        len1_node["inMatrix2"] << input_xforms[1].world_matrix
        len2_node = nw.create_node("distanceBetween", "len2_init_dist")
        len2_node["inMatrix1"] << input_xforms[1].world_matrix
        len2_node["inMatrix2"] << input_xforms[2].world_matrix

        start_hierParent_invMult = nw.create_node(
            "multMatrix", "start_hierParentInvMult"
        )
        start_hierParent_invMult["matrixIn"][0] << root_world_matrix
        start_hierParent_invMult["matrixIn"][1] << hier_parent.inv_matrix

        end_hierParent_invMult = nw.create_node("multMatrix", "end_hierParentInvMult")
        end_hierParent_invMult["matrixIn"][0] << end_world_matrix
        end_hierParent_invMult["matrixIn"][1] << hier_parent.inv_matrix

        curr_len_node = nw.create_node("distanceBetween", "curr_total_dist")
        curr_len_node["inMatrix1"] << start_hierParent_invMult["matrixSum"]
        curr_len_node["inMatrix2"] << end_hierParent_invMult["matrixSum"]

        self.container_node.add_nodes(len1_node, len2_node, curr_len_node)
        return len1_node["distance"], len2_node["distance"], curr_len_node["distance"]

    def __create_soft_ik_nodes(
        self, len1_attr: nw.Attr, len2_attr: nw.Attr, curr_len_attr: nw.Attr
    ):
        """creates soft ik nodes

        Args:
            len1_attr (nw.Attr):
            len2_attr (nw.Attr):
            curr_len_attr (nw.Attr):
        """

        def __soft_ik_cos_expression_str(
            len1_attr: nw.Attr,
            len2_attr: nw.Attr,
            curr_len_attr: nw.Attr,
            soft_ik_cos_build_data_node: nw.Node,
        ):
            """Expression str for soft cos ik

            Args:
                len1_attr (nw.Attr):
                len2_attr (nw.Attr):
                curr_len_attr (nw.Attr):
                soft_ik_cos_build_data_node (nw.Node):

            Returns:
                str:
            """
            expression_str = [
                f"float $len1 = {len1_attr};",
                f"float $len2 = {len2_attr};",
                f"float $currLen = {curr_len_attr};",
                "if ($currLen < abs($len1 - $len2)) {",
                "\t$currLen = abs($len1 - $len2);",
                "}",
                "float $totalLen = $len1 + $len2;\n",
                "float $len1Squared = $len1 * $len1;",
                "float $len2Squared = $len2 * $len2;",
                "float $currLenSquared = $currLen * $currLen;\n",
                "float $cos0 = 1;\n",
                "if ($currLen < $totalLen) {",
                "\t$cos0 = ($len1Squared + $currLenSquared - $len2Squared) / (2 * $len1 * $currLen);",
                "}",
                "float $cos0Squared = $cos0 * $cos0;",
                "float $initHeight = sqrt(1 - $cos0Squared);",
                "float $linearHeight = 1 - $cos0;\n",
                f"{soft_ik_cos_build_data_node['cos0']} = $cos0;",
                f"{soft_ik_cos_build_data_node['cos0Squared']} = $cos0Squared;",
                f"{soft_ik_cos_build_data_node['initHeight']} = $initHeight;",
                f"{soft_ik_cos_build_data_node['linearHeight']} = $linearHeight;",
                f"{soft_ik_cos_build_data_node['quadraticHeight']} = $linearHeight * $linearHeight;",
                f"{soft_ik_cos_build_data_node['cubicHeight']} =  $linearHeight * $linearHeight * $linearHeight;",
            ]
            return "\n".join(expression_str)

        def __soft_ik_len_expression_str(
            len1_attr: nw.Attr,
            len2_attr: nw.Attr,
            cos0_squared_attr: nw.Attr,
            init_height_attr: nw.Attr,
            solved_height_attr: nw.Attr,
            soft_ik_output_data_node: nw.Node,
        ):
            """Expression str for soft len ik

            Args:
                len1_attr (nw.Attr):
                len2_attr (nw.Attr):
                cos0_squared_attr (nw.Attr):
                init_height_attr (nw.Attr):
                solved_height_attr (nw.Attr):
                soft_ik_output_data_node (nw.Node):

            Returns:
                str:
            """
            expression_str = [
                f"float $len1 = {len1_attr};",
                f"float $len2 = {len2_attr};",
                "float $lenRatio = $len2 / $len1;\n",
                "float $len1Scalar = 1.0;",
                "float $len2Scalar = 1.0;\n",
                f"if ({self.container_node[self._IK_SOFT_IK_ENAB]}) {{",
                f"\t$len1Scalar = sqrt({cos0_squared_attr}+pow({solved_height_attr}, 2));",
                f"\t$len2Scalar = sqrt(1 - ($lenRatio * pow({init_height_attr}, 2)) + ($lenRatio * pow({solved_height_attr}, 2)));\n",
                "}",
                f"{soft_ik_output_data_node['len1']} = $len1 * $len1Scalar;",
                f"{soft_ik_output_data_node['len2']} = $len2 * $len2Scalar;",
            ]

            return "\n".join(expression_str)

        # create cos build data node
        cos_build_data = nw.create_node("network", "soft_ik_cos_build_data")
        cos_build_data_attrData = component_data.NodeData(
            component_data.AttrData("cos0", type_="float"),
            component_data.AttrData("cos0Squared", type_="float"),
            component_data.AttrData("initHeight", type_="float"),
            component_data.AttrData("linearHeight", type_="float"),
            component_data.AttrData("quadraticHeight", type_="float"),
            component_data.AttrData("cubicHeight", type_="float"),
        )
        cos_build_data_attrData.add_attrs_to_node(cos_build_data)
        cos_build_data_expression_str = __soft_ik_cos_expression_str(
            len1_attr=len1_attr,
            len2_attr=len2_attr,
            curr_len_attr=curr_len_attr,
            soft_ik_cos_build_data_node=cos_build_data,
        )
        cos_expression = nw.wrap_node(
            cmds.expression(
                string=cos_build_data_expression_str, name="soft_ik_cos_expression"
            )
        )
        self.container_node.add_nodes(cos_expression)

        # creating blending for new height
        remap_cos = nw.create_node("remapValue", "soft_ik_cos_remap")
        remap_cos["inputMin"] << self.container_node[self._IK_SOFT_BLEND_START]
        remap_cos["inputValue"] << cos_build_data["cos0"]

        smooth_step = nw.create_node("smoothStep", "soft_ik_smoothStep_blend")
        smooth_step["input"] << remap_cos["outValue"]

        cubic_mult = nw.create_node("multiply", "soft_ik_cublic_blend")
        cubic_mult["input"][0] << remap_cos["outValue"]
        cubic_mult["input"][0] << remap_cos["outValue"]
        cubic_mult["input"][0] << remap_cos["outValue"]

        blend_type_choice = nw.create_node("choice", "soft_ik_blendType_choice")
        blend_type_choice["selector"] << self.container_node[self._IK_BLEND_TYP]
        blend_type_choice["input"][0] << smooth_step["output"]
        blend_type_choice["input"][1] << cubic_mult["output"]

        blend_curve_choice = nw.create_node("choice", "soft_ik_blendCurve_choice")
        blend_curve_choice["selector"] << self.container_node[self._IK_BLEND_CRV]
        blend_curve_choice["input"][0] << cos_build_data["linearHeight"]
        blend_curve_choice["input"][1] << cos_build_data["quadraticHeight"]
        blend_curve_choice["input"][2] << cos_build_data["cubicHeight"]

        blended_height = nw.create_node("blendTwoAttr", "soft_ik_blended_height")
        blended_height["attributesBlender"] << blend_type_choice["output"]
        blended_height["input"][0] << cos_build_data["initHeight"]
        blended_height["input"][1] << blend_curve_choice["output"]

        blending_nodes = [
            remap_cos,
            smooth_step,
            cubic_mult,
            blend_type_choice,
            blend_curve_choice,
        ]

        # finding new heights
        soft_ik_output_data = nw.create_node("network", "soft_ik_output_data")
        soft_ik_output_attrData = component_data.NodeData(
            component_data.AttrData("len1", type_="double"),
            component_data.AttrData("len2", type_="double"),
        )
        soft_ik_output_attrData.add_attrs_to_node(soft_ik_output_data)
        len_expression_str = __soft_ik_len_expression_str(
            len1_attr=len1_attr,
            len2_attr=len2_attr,
            cos0_squared_attr=cos_build_data["cos0Squared"],
            init_height_attr=cos_build_data["initHeight"],
            solved_height_attr=blended_height["output"],
            soft_ik_output_data_node=soft_ik_output_data,
        )
        len_expression = nw.wrap_node(
            cmds.expression(string=len_expression_str, name="soft_ik_len_expression")
        )

        self.container_node.add_nodes(
            cos_build_data,
            cos_expression,
            len_expression,
            *blending_nodes,
            soft_ik_output_data,
            blended_height,
        )
        return soft_ik_output_data

    def __create_ik_build_data_nodes(
        self, len1_attr: nw.Attr, len2_attr: nw.Attr, curr_len_attr: nw.Attr
    ):
        """Creates the trig hold value and distance nodes using law of cos. the holdValue will have the cos, sin, neg sin, and length of the ik

        Args:
            len1_attr (nw.Attr):
            len2_attr (nw.Attr):
            curr_len_attr (nw.Attr):

        Returns:
            nw.Node: the node holding all trig values
        """

        def __ik_build_data_expression_str(
            len1_attr: nw.Attr,
            len2_attr: nw.Attr,
            curr_len_attr: nw.Attr,
            loc_xform1_row: nw.Node,
            ik_build_data_node: nw.Node,
        ):
            """Expression str to get all trig values. stores in trig_hold_value_node

            Args:
                length1 (nw.Attr):
                length2 (nw.Attr):
                curr_length (nw.Attr):
                ik_build_data_node (nw.Node):

            Returns:
                str:
            """
            expression_str = [
                f"float $len1 = {len1_attr};",
                f"float $len2 = {len2_attr};",
                f"float $currLen = {curr_len_attr};",
                "if ($currLen < abs($len1 - $len2)) {",
                "\t$currLen = abs($len1 - $len2);",
                "}",
                "float $totalLen = $len1 + $len2;\n",
                "float $poleVecLen = $len1;",
                "float $len1Squared = $len1 * $len1;",
                "float $len2Squared = $len2 * $len2;",
                "float $currLenSquared = $currLen * $currLen;\n",
                "float $cos0 = 1;",
                "float $topRSin0 = 0;",
                "float $botLSin0 = 0;",
                "float $cos1 = 1;",
                "float $topRSin1 = 0;",
                "float $botLSin1 = 0;\n",
                "float $topRSin = 1;",
                f"if ({self.container_node[self._TER_VEC]}X != 0.0) {{",
                f"\t{loc_xform1_row['input']} = 1;",
                f"\t\tif ({loc_xform1_row['outputZ']} != 0) {{",
                f"\t\t\t$topRSin = {loc_xform1_row['outputZ']};",
                "\t}",
                "}",
                f"else if ({self.container_node[self._TER_VEC]}Y != 0.0) {{",
                f"\t{loc_xform1_row['input']} = 0;",
                f"\t\t\tif ({loc_xform1_row['outputZ']} != 0) {{",
                f"\t\t$topRSin = {loc_xform1_row['outputZ']};",
                "\t}",
                "}",
                f"else if ({self.container_node[self._TER_VEC]}Z != 0.0) {{",
                f"\t{loc_xform1_row['input']} = 0;",
                f"\t\t\tif ({loc_xform1_row['outputY']} != 0) {{",
                f"\t\t$topRSin = {loc_xform1_row['outputY']};",
                "\t}",
                "}",
                "if ($topRSin >= 0.0) {",
                "\t$topRSin = 1;",
                "}",
                "else {",
                "\t$topRSin = -1;",
                "}",
                "if ($currLen < $totalLen) {",
                "\t$poleVecLen = ($currLen/$totalLen) * $len1;",
                "\t$cos0 = ($len1Squared + $currLenSquared - $len2Squared) / (2 * $len1 * $currLen);",
                "\t$cos1 = -1 * ($len1Squared + $len2Squared - $currLenSquared) / (2 * $len1 * $len2);\n",
                "\tfloat $sin0Val = sqrt(abs(1 - ($cos0 * $cos0)));",
                "\tfloat $sin1Val = sqrt(abs(1 - ($cos1 * $cos1)));",
                "\t$topRSin0 = -1 * $topRSin * $sin0Val;",
                "\t$botLSin0 = $topRSin * $sin0Val;",
                "\t$topRSin1 = $topRSin * $sin1Val;",
                "\t$botLSin1 = -1 * $topRSin * $sin1Val;",
                "}",
                f"else if ({self.container_node[self._IK_STRETCH_ENAB]} && $currLen > $totalLen) {{",
                "\t$scalar = $currLen/$totalLen;",
                "\t$len1 = $len1 * $scalar;",
                "\t$len2 = $len2 * $scalar;\n",
                "\t$poleVecLen = $len1;",
                "}",
                f"{ik_build_data_node['cos0']} = $cos0;",
                f"{ik_build_data_node['topRSin0']} = $topRSin0;",
                f"{ik_build_data_node['botLSin0']} = $botLSin0;\n",
                f"{ik_build_data_node['cos1']} = $cos1;",
                f"{ik_build_data_node['topRSin1']} = $topRSin1;",
                f"{ik_build_data_node['botLSin1']} = $botLSin1;",
                f"{ik_build_data_node['length1']} = $len1;\n",
                f"{ik_build_data_node['length2']} = $len2;",
                f"{ik_build_data_node['poleVecLen']} = $poleVecLen;",
            ]
            return "\n".join(expression_str)

        # node to store expression in
        ik_build_data_node = nw.create_node("network", "ik_build_data")
        ik_build_data_attrData = component_data.NodeData(
            component_data.AttrData("xform0Data", type_="compound"),
            component_data.AttrData("cos0", type_="double", parent="xform0Data"),
            component_data.AttrData("topRSin0", type_="double", parent="xform0Data"),
            component_data.AttrData("botLSin0", type_="double", parent="xform0Data"),
            component_data.AttrData("xform1Data", type_="compound"),
            component_data.AttrData("cos1", type_="double", parent="xform1Data"),
            component_data.AttrData("topRSin1", type_="double", parent="xform1Data"),
            component_data.AttrData("botLSin1", type_="double", parent="xform1Data"),
            component_data.AttrData("length1", type_="double", parent="xform1Data"),
            component_data.AttrData("xform2Data", type_="compound"),
            component_data.AttrData("length2", type_="double", parent="xform2Data"),
            component_data.AttrData("poleVecLen", type_="double"),
        )
        ik_build_data_attrData.add_attrs_to_node(ik_build_data_node)

        xform1_loc_matrix_row = nw.create_node(
            "rowFromMatrix", name="xform1_loc_matrix_row"
        )
        (
            xform1_loc_matrix_row["matrix"]
            << self.container_node[self.HIER_DATA.IN_XFORM][1][
                self.HIER_DATA.IN_LOC_MAT
            ]
        )

        ik_trig_expression_str = __ik_build_data_expression_str(
            len1_attr=len1_attr,
            len2_attr=len2_attr,
            curr_len_attr=curr_len_attr,
            loc_xform1_row=xform1_loc_matrix_row,
            ik_build_data_node=ik_build_data_node,
        )

        ik_trig_expression = nw.wrap_node(
            cmds.expression(
                string=ik_trig_expression_str, name="ik_build_data_expression"
            )
        )

        self.container_node.add_nodes(
            ik_build_data_node, ik_trig_expression, xform1_loc_matrix_row
        )
        return ik_build_data_node

    def __create_local_matrix_nodes(self, ik_build_data_node: nw.Node):
        """Creates local matrix for IK using expressions

        Args:
            trig_hold_value (nw.Node): _description_

        Returns:
            _type_: _description_
        """

        def __local_matrix_expression_str(
            ik_build_data_node: nw.Node,
            rot0_loc_matrix: nw.Node,
            rot1_loc_matrix: nw.Node,
            rot2_point_matrix: nw.Node,
        ):
            """Expression string to make the local rotation matricies

            Args:
                trig_hold_value (nw.Node):
                rot0_loc_matrix (nw.Node):
                rot1_loc_matrix (nw.Node):
                rot2_loc_matrix (nw.Node):

            Returns:
                str:
            """
            expression_str = []
            for index, rot_loc_matrix in enumerate([rot0_loc_matrix, rot1_loc_matrix]):
                # no rotation on last matrix
                if index != 2:
                    cos = ik_build_data_node[f"cos{index}"]
                    topRSin = ik_build_data_node[f"topRSin{index}"]
                    botLSin = ik_build_data_node[f"botLSin{index}"]
                    expression_str.extend(
                        [
                            f"matrix $rot_matrix{index}[3][3] = <<1.0, 0.0, 0.0; 0.0, 1.0, 0.0; 0.0, 0.0, 1.0>>;\n",
                            f"if({self.container_node[self._TER_VEC]}X != 0.0) {{",
                            f"\t$rot_matrix{index}[1][1] = {cos};",
                            f"\t$rot_matrix{index}[1][2] = {topRSin};",
                            f"\t$rot_matrix{index}[2][1] = {botLSin};",
                            f"\t$rot_matrix{index}[2][2] = {cos};",
                            "}",
                            f"else if({self.container_node[self._TER_VEC]}Y != 0.0) {{",
                            f"\t$rot_matrix{index}[0][0] = {cos};",
                            f"\t$rot_matrix{index}[0][2] = {topRSin};",
                            f"\t$rot_matrix{index}[2][0] = {botLSin};",
                            f"\t$rot_matrix{index}[2][2] = {cos};",
                            "}",
                            f"else if({self.container_node[self._TER_VEC]}Z != 0.0) {{",
                            f"\t$rot_matrix{index}[0][0] = {cos};",
                            f"\t$rot_matrix{index}[0][1] = {topRSin};",
                            f"\t$rot_matrix{index}[1][0] = {botLSin};",
                            f"\t$rot_matrix{index}[1][1] = {cos};",
                            "}\n",
                            f"{rot_loc_matrix['in00']} = $rot_matrix{index}[0][0];",
                            f"{rot_loc_matrix['in01']} = $rot_matrix{index}[0][1];",
                            f"{rot_loc_matrix['in02']} = $rot_matrix{index}[0][2];",
                            f"{rot_loc_matrix['in10']} = $rot_matrix{index}[1][0];",
                            f"{rot_loc_matrix['in11']} = $rot_matrix{index}[1][1];",
                            f"{rot_loc_matrix['in12']} = $rot_matrix{index}[1][2];",
                            f"{rot_loc_matrix['in20']} = $rot_matrix{index}[2][0];",
                            f"{rot_loc_matrix['in21']} = $rot_matrix{index}[2][1];",
                            f"{rot_loc_matrix['in22']} = $rot_matrix{index}[2][2];\n",
                        ]
                    )
                # no translate on first matrix
                if index != 0:
                    length = ik_build_data_node[f"length{index}"]
                    expression_str.extend(
                        [
                            f"{rot_loc_matrix['in30']} = {self.container_node[self._PRM_VEC][0]} * {length};",
                            f"{rot_loc_matrix['in31']} = {self.container_node[self._PRM_VEC][1]} * {length};",
                            f"{rot_loc_matrix['in32']} = {self.container_node[self._PRM_VEC][2]} * {length};",
                        ]
                    )
            expression_str.extend(
                [
                    f"\n{rot2_point_matrix['inPointX']}={ik_build_data_node['length2']} * {self.container_node[self._PRM_VEC][1]};",
                    f"{rot2_point_matrix['inPointY']}={ik_build_data_node['length2']} * {self.container_node[self._PRM_VEC][1]};",
                    f"{rot2_point_matrix['inPointZ']}={ik_build_data_node['length2']} * {self.container_node[self._PRM_VEC][2]};",
                ]
            )
            return "\n".join(expression_str)

        loc_rot_matricies = []
        for index in range(2):
            loc_rot_matricies.append(
                nw.create_node("fourByFourMatrix", f"xform{index}_loc_mat")
            )

        world_rot_point = nw.create_node("pointMatrixMult", "xform2_transform_mult")

        ik_loc_mat_expression_str = __local_matrix_expression_str(
            ik_build_data_node=ik_build_data_node,
            rot0_loc_matrix=loc_rot_matricies[0],
            rot1_loc_matrix=loc_rot_matricies[1],
            rot2_point_matrix=world_rot_point,
        )
        ik_loc_mat_expression = nw.wrap_node(
            cmds.expression(
                string=ik_loc_mat_expression_str, name="ik_loc_mat_expression"
            )
        )

        self.container_node.add_nodes(
            *loc_rot_matricies, ik_loc_mat_expression, world_rot_point
        )
        return loc_rot_matricies, world_rot_point

    def __create_pole_vec_nodes(
        self,
        ik_build_data_node: nw.Node,
        root_cntrl_ws_mat: nw.Attr,
        end_cntrl_ws_mat: nw.Attr,
        color: Union[
            list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node
        ] = None,
    ):
        """Creates all pole vector nodes

        Args:
            ik_build_data_node (nw.Node):
            root_cntrl_ws_mat (nw.Attr):
            end_cntrl_ws_mat (nw.Attr):
            color ():

        Returns:
            base_component.Control: pole vector control
        """

        def __pole_vec_expression_str(pole_vec_control: nw.Transform):
            """Expression string for pole vector

            Args:
                pole_vec_control (nw.Transform):

            Returns:
                str:
            """
            expression_str = []
            for axis in ["X", "Y", "Z"]:
                rotate_piv = pole_vec_control[f"rotatePivot{axis}"]
                trans_attr = pole_vec_control[f"translate{axis}"]
                expression_str.append(f"{rotate_piv} = -1 * {trans_attr};")
            expression_str.append("")

            for index, axis in enumerate(["X", "Y", "Z"]):
                for transform, vec_name in zip(
                    ["Trans", "Rot"], [self._SEC_VEC, self._PRM_VEC]
                ):
                    for extreme in ["max", "min"]:
                        dest_attr = pole_vec_control[
                            f"{extreme}{transform}{axis}LimitEnable"
                        ]
                        src_attr = self.container_node[vec_name][index]
                        expression_str.append(f"{dest_attr} = ({src_attr} == 0);")
                expression_str.append("")

            return "\n".join(expression_str)

        # control
        pole_cntrl_inst = control.DiamondWire.create(
            instance_name="poleVec",
            parent=self,
            build_s=0.8,
            color=color,
            xform_map_index=1,
        )
        for attr_name in ["sx", "sy", "sz"]:
            pole_cntrl_inst.transform_node[attr_name].set_locked(True)
            pole_cntrl_inst.transform_node[attr_name].set_keyable(False)
        transform_limits_kwarg = {f"t{axis}": (0, 0) for axis in ["x", "y", "z"]}
        transform_limits_kwarg.update({f"r{axis}": (0, 0) for axis in ["x", "y", "z"]})
        cmds.transformLimits(
            str(pole_cntrl_inst.transform_node), **transform_limits_kwarg
        )

        # aim matrix
        aim_matrix = nw.create_node("aimMatrix", name="pole_vec_start_mat")
        aim_matrix["inputMatrix"]
        aim_matrix["inputMatrix"] << root_cntrl_ws_mat
        aim_matrix["primaryTargetMatrix"] << end_cntrl_ws_mat
        aim_matrix["primaryInputAxis"] << self.container_node[self._PRM_VEC]
        aim_matrix["secondaryTargetMatrix"] << root_cntrl_ws_mat
        aim_matrix["secondaryInputAxis"] << self.container_node[self._SEC_VEC]
        aim_matrix["secondaryTargetVector"] << self.container_node[self._SEC_VEC]

        # vectorizing length
        vec_mult = nw.create_node("multiplyDivide", "pole_vec_len_vec")
        for attr_name in ["X", "Y", "Z"]:
            vec_mult[f"input1{attr_name}"] << ik_build_data_node["poleVecLen"]
        vec_mult["input2"] << self.container_node[self._PRM_VEC]

        # getting ws point
        pole_vec_ws_translate = nw.create_node("pointMatrixMult", "pole_vec_translate")
        pole_vec_ws_translate["inMatrix"] << aim_matrix["outputMatrix"]
        pole_vec_ws_translate["inPoint"] << vec_mult["output"]

        # creating 4x4 matrix blend
        pole_vec_parent_4x4 = self._create_orient_translate_blend(
            name="pole_vec_parent",
            matrix_attr=aim_matrix["outputMatrix"],
            tx_attr=pole_vec_ws_translate["outputX"],
            ty_attr=pole_vec_ws_translate["outputY"],
            tz_attr=pole_vec_ws_translate["outputZ"],
        )
        (
            pole_vec_parent_4x4["output"]
            >> pole_cntrl_inst.container_node[control._Control._IN_OFF_MAT]
        )

        # pole vec expression
        pole_vec_expression_str = __pole_vec_expression_str(
            pole_vec_control=pole_cntrl_inst.transform_node
        )

        pole_vec_expression = nw.wrap_node(
            cmds.expression(
                string=pole_vec_expression_str, name="ik_pole_vec_expression"
            )
        )

        self.container_node.add_nodes(
            aim_matrix, vec_mult, pole_vec_expression, pole_vec_ws_translate
        )
        return pole_cntrl_inst

    def _override_build(
        self,
        control_color: Union[
            list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node
        ] = None,
        **kwargs,
    ):
        """creates 3 joint ik

        Args:
            control_color (Union[list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node], optional): Defaults to None.
        """
        # space switch to plug into controls
        space_switch_choice, space_switch_init_inv_choice = (
            self.__create_space_switch_nodes()
        )

        # controls
        hier_parent = self.get_hier_parent_attrs()
        root_offset_matrix = self.__ik_control(
            name="root",
            input_xform_index=0,
            control_matrix=self.input_node[self._ROOT_WORLD_MAT],
            control_inv_matrix=self.input_node[self._ROOT_INIT_INV_MAT],
            parent_init_inv_matrix=hier_parent.init_inv_matrix,
            parent_world_matrix=hier_parent.matrix,
            color=control_color,
        )
        end_offset_matrix = self.__ik_control(
            name="end",
            input_xform_index=2,
            control_matrix=self.input_node[self._END_WORLD_MAT],
            control_inv_matrix=self.input_node[self._END_INIT_INV_MAT],
            parent_init_inv_matrix=space_switch_init_inv_choice["output"],
            parent_world_matrix=space_switch_choice["output"],
            color=control_color,
        )

        # get all expression calculations
        len1_attr, len2_attr, curr_len_attr = self.__create_dist_nodes(
            root_world_matrix=root_offset_matrix, end_world_matrix=end_offset_matrix
        )
        soft_ik_new_len = self.__create_soft_ik_nodes(
            len1_attr=len1_attr, len2_attr=len2_attr, curr_len_attr=curr_len_attr
        )
        ik_build_data = self.__create_ik_build_data_nodes(
            len1_attr=soft_ik_new_len["len1"],
            len2_attr=soft_ik_new_len["len2"],
            curr_len_attr=curr_len_attr,
        )

        loc_matricies, xform2_rot_point = self.__create_local_matrix_nodes(
            ik_build_data_node=ik_build_data
        )
        pole_cntrl_inst = self.__create_pole_vec_nodes(
            ik_build_data_node=ik_build_data,
            root_cntrl_ws_mat=root_offset_matrix,
            end_cntrl_ws_mat=end_offset_matrix,
            color=control_color,
        )

        # create aim matrix
        ik_base_mat_aim = nw.create_node("aimMatrix", "ik_base_mat")
        ik_base_mat_aim["inputMatrix"] << root_offset_matrix
        ik_base_mat_aim["primaryTargetMatrix"] << end_offset_matrix
        ik_base_mat_aim["primaryInputAxis"] << self.container_node[self._PRM_VEC]
        (
            ik_base_mat_aim["secondaryTargetMatrix"]
            << pole_cntrl_inst.container_node[control._Control._OUT_WS_MAT]
        )
        ik_base_mat_aim["secondaryInputAxis"] << self.container_node[self._SEC_VEC]
        ik_base_mat_aim["secondaryTargetVector"] << self.container_node[self._SEC_VEC]
        ik_base_mat_aim["secondaryMode"] = 2

        # connecting to world matrix and local matrix
        xform_output_nodes = []
        prev_world_matrix = ik_base_mat_aim["outputMatrix"]
        for index, loc_matrix in enumerate(loc_matricies):
            mult_matrix = nw.create_node("multMatrix", f"xform{index}_ws_matMult")
            mult_matrix["matrixIn"][0] << loc_matrix["output"]
            mult_matrix["matrixIn"][1] << prev_world_matrix
            prev_world_matrix = mult_matrix["matrixSum"]
            if index == 0:
                local_mat_attr = None
            else:
                local_mat_attr = loc_matrix["output"]

            self._set_xform_attrs(
                index=index,
                xform_type=self.IO_ENUM.output,
                xform=self.XFORM(
                    world_matrix=mult_matrix["matrixSum"], loc_matrix=local_mat_attr
                ),
            )
            xform_output_nodes.append(mult_matrix)
            if index == 1:
                xform2_rot_point["inMatrix"] << mult_matrix["matrixSum"]

        xform2_world_matrix = self._create_orient_translate_blend(
            name="xform2_ws",
            matrix_attr=end_offset_matrix,
            tx_attr=xform2_rot_point["outputX"],
            ty_attr=xform2_rot_point["outputY"],
            tz_attr=xform2_rot_point["outputZ"],
        )
        self._set_xform_attrs(
            index=2,
            xform_type=self.IO_ENUM.output,
            xform=self.XFORM(world_matrix=xform2_world_matrix["output"]),
        )

        self.container_node.add_nodes(ik_base_mat_aim, *xform_output_nodes)

    def add_ik_space(self, space_name: str, space_src_data):
        """adds space to end control

        Args:
            space_name (str):
            space_src_data (any):
        """
        space_switch_attr = self.container_node[self._SPACE_SWITCH]
        space_init_inv_mat_node = (
            space_switch_attr[0][self._SPACE_INIT_INV_MAT]
            .get_dest_connections()[0]
            .node
        )
        space_mat_node = (
            space_switch_attr[0][self._SPACE_MAT].get_dest_connections()[0].node
        )

        space_src_data = self.get_hook_source_data(hook_src_data=space_src_data)
        if space_src_data is None:
            return
        space_index = 0
        if self.container_node[self._SPACE_SWITCH][0][
            self._SPACE_INIT_INV_MAT
        ].has_src_connection():
            space_index = len(self.container_node[self._SPACE_SWITCH])

        # space thing
        utils.set_connect_attr_data(
            attr=space_switch_attr[space_index][self._SPACE_MAT],
            data=space_src_data.matrix,
        )
        utils.set_connect_attr_data(
            attr=space_switch_attr[space_index][self._SPACE_INIT_INV_MAT],
            data=space_src_data.init_inv_matrix,
        )

        if space_index != 0:
            (
                space_switch_attr[space_index][self._SPACE_MAT]
                >> space_mat_node["input"][space_index]
            )
            (
                space_switch_attr[space_index][self._SPACE_INIT_INV_MAT]
                >> space_init_inv_mat_node["input"][space_index]
            )

        # change enum name
        space_attr = self.container_node[self._SPACE]
        enum_names = cmds.attributeQuery(
            space_attr.short_name, node=str(space_attr.node), listEnum=True
        )[0]

        # getting all enums connected that are the same
        enum_connect_attributes = []
        connection = space_attr
        while connection is not None:
            if connection.type_ != "enum":
                break
            if (
                cmds.attributeQuery(
                    connection.short_name, node=str(connection.node), listEnum=True
                )[0]
                != enum_names
            ):
                break
            enum_connect_attributes.append(connection)

            connection = connection.get_src_connection()

        for attr in enum_connect_attributes:
            if space_index == 0:
                enum_names = space_name
            else:
                enum_names = f"{enum_names}:{space_name}"
            cmds.addAttr(str(attr), edit=True, enumName=enum_names)


class SimpleIK2(_Motion):
    class_namespace = "simpleIK"
    _max_num_xforms = (3, 3)

    # TODO take out later
    _check_output = False
    _populate_output = False

    def _override_build(self, control_color=None, **kwargs):
        hier_helper.HierLengths.create(parent=self, source_component=self)


class TwistHier(_Motion):
    """Creates a hier with twist joints. inbetween twist joint number can be specified"""

    class_namespace = "twist_hier"
    input_node_name = "input"
    input_node_type = "network"

    @classmethod
    def create(
        cls,
        instance_name: Union[str, nw.Attr] = None,
        parent: Union[base_comp._Component, nw.Container] = None,
        input_xforms: Union[list[component_data.Xform], int] = None,
        source_component: base_comp._Hierarchy = None,
        connect_parent_hier: bool = True,
        connect_axis_vecs: bool = True,
        num_twist_xforms: int = 3,
        counter_rot_root: bool = True,
    ):
        """Class method to create component

        Args:
            instance_name (Union[str, nw.Attr], optional): name of component. Defaults to None.
            parent (Union[_Component, nw.Container], optional): Defaults to None.
            input_xforms (Union[list[component_data.Xform], int], optional): input xforms to initialize component with. Defaults to None.
            source_component (_Hierarchy, optional): source component to connect hierarchy from. Defaults to None.
            connect_parent_hier (bool, optional): Defaults to True.
            connect_axis_vecs (bool, optional): Defaults to True.
            num_twist_xforms (int, optional): Defaults to 3.
            counter_rot_root (bool, optional): arg to counter rotate root xform. Defaults to True.

        Returns:
            TwistHier:
        """
        return cls._kwarg_create(**cls._process_locals(kwarg_dict=locals()))

    def _override_build(
        self,
        control_color: Union[
            list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node
        ] = None,
        num_twist_xforms=3,
        counter_rot_root: bool = True,
        **kwargs,
    ):
        """Creates and connects twist xforms

        Args:
            control_color (Union[list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node], optional): Defaults to None.
            num_twist_xforms (int, optional): Defaults to 3.
            counter_rot_root (bool, optional): arg to counter rotate root xform. Defaults to True.
        """
        input_xforms = list(self.get_xform_attrs(xform_type=self.IO_ENUM.input).items())
        added_nodes = []

        if len(input_xforms) < 2:
            cmds.warning(
                f"{self.container_node}: len of xform is less than 2. no additional xforms added"
            )

        parent_init_inv_matrix = self.get_hier_parent_attrs().init_inv_matrix
        root_counter_rot_attr = None
        for xform_index, input_xform in input_xforms:
            if xform_index == 0:
                # if wanting to add counter twist
                if counter_rot_root:
                    twist_matrix_inst = matrix.Twist.create(
                        instance_name=f"xform{xform_index}_twist",
                        parent=self,
                        loc_matrix=input_xform.loc_matrix,
                        init_matrix=input_xform.init_matrix,
                        init_parent_inv_matrix=parent_init_inv_matrix,
                        primary_vec=self.container_node[self._PRM_VEC],
                    )
                    root_counter_rot_attr = twist_matrix_inst.container_node[
                        twist_matrix_inst._OUT_ROT_MATRIX
                    ]

                    # inverse root rot
                    root_counter_rot_inv = nw.create_node(
                        "inverseMatrix", "rootCounterRot_inv"
                    )
                    (
                        root_counter_rot_inv["inputMatrix"]
                        << twist_matrix_inst.container_node[
                            twist_matrix_inst._OUT_ROT_MATRIX
                        ]
                    )

                    # mult to world space to counter rotate world matrix
                    root_counter_rot_ws_mult = nw.create_node(
                        "multMatrix", "rootCounterRotWS_mult"
                    )
                    (
                        root_counter_rot_ws_mult["matrixIn"][0]
                        << root_counter_rot_inv["outputMatrix"]
                    )
                    root_counter_rot_ws_mult["matrixIn"][1] << input_xform.world_matrix
                    input_xform.world_matrix = root_counter_rot_ws_mult["matrixSum"]

                    added_nodes.extend([root_counter_rot_inv, root_counter_rot_ws_mult])

                # setting xform
                self._set_xform_attrs(
                    index=xform_index,
                    xform_type=self.IO_ENUM.output,
                    xform=self.XFORM(
                        world_matrix=input_xform.world_matrix,
                        init_matrix=input_xform.init_matrix,
                    ),
                )
                parent_init_inv_matrix = input_xform.init_inv_matrix

            else:
                twist_matrix_inst = matrix.Twist.create(
                    instance_name=f"xform{xform_index}_twist",
                    parent=self,
                    loc_matrix=input_xform.loc_matrix,
                    init_matrix=input_xform.init_matrix,
                    init_parent_inv_matrix=parent_init_inv_matrix,
                    primary_vec=self.container_node[self._PRM_VEC],
                )

                # setting values for next
                parent_init_inv_matrix = input_xform.init_inv_matrix

                # translate values
                loc_t_rot_row = nw.create_node(
                    "rowFromMatrix", f"xform{xform_index}_locTRotRow"
                )
                loc_t_rot_row["input"] = 3
                loc_t_rot_row["matrix"] << input_xform.loc_matrix

                # translate matrix
                loc_t_rot_4x4 = nw.create_node(
                    "fourByFourMatrix", f"xform{xform_index}_locTRot4x4"
                )
                loc_t_rot_4x4["in30"] << loc_t_rot_row["outputX"]
                loc_t_rot_4x4["in31"] << loc_t_rot_row["outputY"]
                loc_t_rot_4x4["in32"] << loc_t_rot_row["outputZ"]
                loc_t_rot_4x4["in33"] << loc_t_rot_row["outputW"]

                # creating new local matrix
                loc_mat_rot_mult = nw.create_node(
                    "multMatrix", f"xform{xform_index}_locRotMat"
                )
                (
                    loc_mat_rot_mult["matrixIn"][0]
                    << twist_matrix_inst.container_node[
                        twist_matrix_inst._OUT_ROT_MATRIX
                    ]
                )
                loc_mat_rot_mult["matrixIn"][1] << loc_t_rot_4x4["output"]
                if xform_index == 1 and root_counter_rot_attr is not None:
                    loc_mat_rot_mult["matrixIn"][2] << root_counter_rot_attr

                # segmenting matrix
                loc_mat_seg_blend = nw.create_node(
                    "blendMatrix", f"xform{xform_index}_locRotMatBlend"
                )
                (
                    loc_mat_seg_blend["target"][0]["targetMatrix"]
                    << loc_mat_rot_mult["matrixSum"]
                )
                loc_mat_seg_blend["target"][0]["weight"] = 1 / (num_twist_xforms + 1)

                # segmenting init matrix
                loc_mat_init_seg_blend = nw.create_node(
                    "blendMatrix", f"xform{xform_index}_locInitRotMatBlend"
                )
                (
                    loc_mat_init_seg_blend["target"][0]["targetMatrix"]
                    << loc_t_rot_4x4["output"]
                )
                loc_mat_init_seg_blend["target"][0]["weight"] = 1 / (
                    num_twist_xforms + 1
                )

                added_nodes.extend(
                    [
                        loc_t_rot_row,
                        loc_t_rot_4x4,
                        loc_mat_rot_mult,
                        loc_mat_seg_blend,
                        loc_mat_init_seg_blend,
                    ]
                )

                world_space_attr = input_xforms[xform_index - 1][1].world_matrix
                world_init_space_attr = input_xforms[xform_index - 1][1].init_matrix
                for sub_index in range(num_twist_xforms):
                    output_index = (
                        (xform_index - 1) * (num_twist_xforms + 1) + sub_index + 1
                    )

                    # ws twist matrix
                    twist_world_mat = nw.create_node(
                        "multMatrix", f"xform{xform_index}_twist{sub_index}_wsMult"
                    )
                    twist_world_mat["matrixIn"][0] << loc_mat_seg_blend["outputMatrix"]
                    twist_world_mat["matrixIn"][1] << world_space_attr

                    # ws init twist matrix
                    twist_init_world_mat = nw.create_node(
                        "multMatrix", f"xform{xform_index}_init_twist{sub_index}_wsMult"
                    )
                    (
                        twist_init_world_mat["matrixIn"][0]
                        << loc_mat_init_seg_blend["outputMatrix"]
                    )
                    twist_init_world_mat["matrixIn"][1] << world_init_space_attr

                    # setting attrs
                    world_space_attr = twist_world_mat["matrixSum"]
                    world_init_space_attr = twist_init_world_mat["matrixSum"]

                    self._set_xform_attrs(
                        index=output_index,
                        xform_type=self.IO_ENUM.output,
                        xform=self.XFORM(
                            xform_name=f"xform{xform_index}_twist{sub_index}",
                            init_matrix=twist_init_world_mat["matrixSum"],
                            world_matrix=twist_world_mat["matrixSum"],
                            loc_matrix=loc_mat_seg_blend["outputMatrix"],
                        ),
                    )
                    added_nodes.extend([twist_world_mat, twist_init_world_mat])

                input_xform.loc_matrix = None
                self._set_xform_attrs(
                    index=xform_index * (num_twist_xforms + 1),
                    xform_type=self.IO_ENUM.output,
                    xform=input_xform,
                )

        self.container_node.add_nodes(*added_nodes)
        return


class Visualize(_Motion):
    """Helps visualize and debug hierarchies by creating chains for world space and local visualization"""

    class_namespace = "hier_vis"

    def _override_build(
        self,
        control_color: Union[
            list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node
        ] = None,
        **kwargs,
    ):
        """creates world and local visualize controls

        Args:
            control_color (Union[list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node], optional): Defaults to None.
        """
        ws_grp = nw.create_node("transform", "worldSpace_grp")
        loc_grp = nw.create_node("transform", "localSpace_grp")
        cmds.parent(str(loc_grp), str(ws_grp), str(self.transform_node))

        prev_loc_transform = loc_grp

        self.connect_input_to_output()

        input_xforms = self.get_xform_attrs(xform_type=self.IO_ENUM.input)
        for index, input_xform in input_xforms.items():
            # making controls
            control_ws_inst = control.Axis.create(
                instance_name=f"{input_xform.xform_name.value}_ws", parent=self
            )
            control_loc_inst = control.Axis.create(
                instance_name=f"{input_xform.xform_name.value}_loc", parent=self
            )
            # locking transforms
            for attr_name in ["t", "r", "s"]:
                for axis in ["x", "y", "z"]:
                    control_ws_inst.transform_node[f"{attr_name}{axis}"].set_locked(
                        True
                    )
                    control_loc_inst.transform_node[f"{attr_name}{axis}"].set_locked(
                        True
                    )

            # setting up the rest of ws matrix
            cmds.parent(str(control_ws_inst.transform_node), str(ws_grp))
            (
                input_xform.world_matrix
                >> control_ws_inst.container_node[control._Control._IN_OFF_MAT]
            )

            # setting up the rest of local matrix
            cmds.parent(str(control_loc_inst.transform_node), str(prev_loc_transform))
            if index != 0:
                (
                    input_xform.loc_matrix
                    >> control_loc_inst.container_node[control._Control._IN_OFF_MAT]
                )
            else:
                (
                    input_xform.world_matrix
                    >> control_loc_inst.container_node[control._Control._IN_OFF_MAT]
                )
            prev_loc_transform = control_loc_inst.transform_node

        self.container_node.add_nodes(ws_grp, loc_grp)


class Merge(_Motion):
    """Merges multiple components together and outputs it"""

    class_namespace = "merge_hier"

    _IN_HIER_PAR_MAT = "hierParentMatricies"
    _IN_HIER = "hierarchy"
    _IN_HIER_LOC_MAT = "hierarchyLocMatrix"
    _IN_HIER_BLEND = "hierBlend"
    _OUT_HIER_VIS = "hierVisibility"

    def _input_attr_build_data(self):
        """Defines all the added, published, or modified attributes for the
        input node. inherits all input node data from _Hierarchy

        Returns:
            comp_data.NodeData:
        """
        node_data = super()._input_attr_build_data()
        node_data.extend_attr_data(
            component_data.AttrData(
                self._IN_HIER_PAR_MAT, type_="matrix", multi=True, publish=True
            ),
            component_data.AttrData(
                self._IN_HIER, type_="compound", multi=True, publish=True
            ),
            component_data.AttrData(
                self._IN_HIER_LOC_MAT, type_="matrix", multi=True, parent=self._IN_HIER
            ),
            component_data.AttrData(
                self._IN_HIER_BLEND, type_="double", parent=self._IN, min=0
            ),
        )

        return node_data

    def _output_attr_build_data(self):
        """Defines all the added, published, or modified attributes for the
        output node. inherits all output node data from _Hierarchy

        Returns:
            comp_data.NodeData:
        """
        node_data = super()._output_attr_build_data()
        node_data.extend_attr_data(
            component_data.AttrData(
                self._OUT_HIER_VIS,
                type_="double",
                multi=True,
                parent=self._OUT,
                min=0,
                max=1,
            )
        )

        return node_data

    @classmethod
    def create(
        cls,
        instance_name: Union[str, nw.Attr] = None,
        parent: Union[base_comp._Component, nw.Container] = None,
        source_components: list[base_comp._Hierarchy] = [],
    ):
        """Class method to create component

        Args:
            instance_name (Union[str, nw.Attr], optional): name of component. Defaults to None.
            parent (Union[_Component, nw.Container], optional): Defaults to None.
            source_components (list[base_comp._Hierarchy], optional): Defaults to [].

        Returns:
            _type_: _description_
        """
        return cls._kwarg_create(**cls._process_locals(kwarg_dict=locals()))

    def _pre_build(
        self,
        instance_name: Union[str, nw.Attr] = None,
        parent: Union[base_comp._Component, nw.Container] = None,
        source_components: list[base_comp._Hierarchy] = [],
        **pre_build_kwargs,
    ):
        """Handles creation and connection of initial nodes and sources

        Args:
            instance_name (Union[str, nw.Attr], optional): name of component. Defaults to None.
            parent (Union[_Component, nw.Container], optional): Defaults to None.
            source_components (list[base_comp._Hierarchy], optional): Defaults to [].
        """
        # get initial source_component
        source_component = None if len(source_components) < 1 else source_components[0]
        super()._pre_build(
            instance_name=instance_name,
            parent=parent,
            source_component=source_component,
            connect_parent_hier=True,
            connect_axis_vecs=True,
        )

        # checking components
        self.__check_source_components(source_components=source_components)

        # connecting the rest of the components
        source_components = [] if source_component is None else source_components[1:]
        self.__connect_components(
            source_component=source_component, source_components=source_components
        )

    # pre build helper functions
    def __check_source_components(self, source_components=[]):
        """Checks that all components given are valid

        Args:
            source_components (list, optional): Defaults to [].

        Raises:
            RuntimeError: hier len is different than first
            RuntimeError: source component is the parent of this merge component
            RuntimeError: is not a hierarchy component
        """
        if len(source_components) < 1:
            return
        xform_len = len(source_components[0].container_node[self.HIER_DATA.OUT_XFORM])
        container_parents = []
        curr_par_cntnr = self.container_node.get_container_node()
        while curr_par_cntnr is not None:
            container_parents.append(curr_par_cntnr)
            curr_par_cntnr = curr_par_cntnr.get_container_node()
        for source_component in source_components:
            component_len = len(
                source_component.container_node[self.HIER_DATA.OUT_XFORM]
            )
            if xform_len != component_len:
                raise RuntimeError(
                    f"{source_component.container_node} has mismatched len. expecting {xform_len} got {component_len}"
                )
            if source_component.container_node in container_parents:
                raise RuntimeError(
                    "source container cannot be parent of merge container"
                )
            if not issubclass(type(source_component), base_comp._Hierarchy):
                raise RuntimeError(
                    f"{source_component.container_node} is not hierarchy component"
                )

    def __set_component_vis(self, index: int, component: base_comp._Component):
        """Sets component visibility

        Args:
            index (int):
            component (base_comp._Component):
        """
        if component.transform_node is not None:
            (
                self.container_node[self._OUT_HIER_VIS][index]
                >> component.transform_node["visibility"]
            )

    def __connect_hier_parent(self, index: int, component: base_comp._Component):
        """Connects hier parent of source component

        Args:
            index (int):
            component (base_comp._Component):
        """
        (
            component.container_node[self.HIER_DATA.HIER_PAR_MAT]
            >> self.container_node[self._IN_HIER_PAR_MAT][index]
        )

    def __connect_components(self, source_component, source_components=[]):
        """Connects source components up to local hierarchy attribute

        Args:
            source_components (list, optional): Defaults to [].
        """
        self.__set_component_vis(index=0, component=source_component)
        self.__connect_hier_parent(index=0, component=source_component)
        for component_index, curr_component in enumerate(source_components):
            # hier parent
            hier_attr = self.container_node[self._IN_HIER][component_index][
                self._IN_HIER_LOC_MAT
            ]

            for xform_index, xform in enumerate(
                curr_component.container_node[self.HIER_DATA.OUT_XFORM]
            ):
                hier_attr[xform_index] << xform[self.HIER_DATA.OUT_LOC_MAT]

            # connecting to visibility
            self.__set_component_vis(
                index=component_index + 1, component=curr_component
            )
            self.__connect_hier_parent(
                index=component_index + 1, component=curr_component
            )

    def _override_build(self, **kwargs):
        """Merges the components together"""
        num_hiers = len(self.container_node[self._IN_HIER_PAR_MAT])
        if num_hiers < 1:
            cmds.warning(
                f"{self.container_node} does not have any source hier components connected"
            )
            return
        num_hiers_seg = 1 / (num_hiers - 1)
        hier_parent_blend = nw.create_node("blendMatrix", "hierParent_matBlend")
        vis_remaps = []
        for hier_index, hier_parent_attr in enumerate(
            self.container_node[self._IN_HIER_PAR_MAT]
        ):
            # visibility
            vis_remaps.append(
                self.__create_vis_remap(
                    hier_index=hier_index,
                    num_hiers=num_hiers,
                    num_hiers_seg=num_hiers_seg,
                )
            )

            # hier parent
            if hier_index == 0:
                hier_parent_blend["inputMatrix"] << hier_parent_attr
            else:
                (
                    hier_parent_blend["target"][hier_index - 1]["targetMatrix"]
                    << hier_parent_attr
                )

        # xform operations
        input_xforms = self.get_xform_attrs(xform_type=self.IO_ENUM.input)
        blend_mats = []
        world_mats = []
        world_mat_attr = hier_parent_blend["outputMatrix"]
        for xform_index, in_xform in input_xforms.items():
            # blend loc matrix
            blend_mat = nw.create_node("blendMatrix", f"xform{xform_index}_locMatBlend")
            blend_mats.append(blend_mat)
            blend_mat["inputMatrix"] << in_xform.loc_matrix

            # world matrix
            world_mat = nw.create_node("multMatrix", f"xform{xform_index}_WorldMult")
            world_mats.append(world_mat)

            # setting world_matrix
            world_mat["matrixIn"][0] << blend_mat["outputMatrix"]
            world_mat["matrixIn"][1] << world_mat_attr
            world_mat_attr = world_mat["matrixSum"]

            # set output xform
            self._set_xform_attrs(
                index=xform_index,
                xform_type=self.IO_ENUM.output,
                xform=self.XFORM(
                    loc_matrix=blend_mat["outputMatrix"],
                    world_matrix=world_mat["matrixSum"],
                ),
            )

        # hierarcy loop
        blend_weights = []
        for hier_index, hier_attr in enumerate(self.container_node[self._IN_HIER]):
            # remaps for weights
            blend_weight = nw.create_node(
                "remapValue", f"hier{hier_index + 1}_blendWeightRemap"
            )
            blend_weight["inputMin"] = hier_index
            blend_weight["inputMax"] = hier_index + 1
            blend_weight["inputValue"] << self.container_node[self._IN_HIER_BLEND]
            blend_weights.append(blend_weight)

            # connect to hier_parent_blend
            (
                hier_parent_blend["target"][hier_index]["weight"]
                << blend_weight["outValue"]
            )

            for loc_index, loc_attr in enumerate(hier_attr[self._IN_HIER_LOC_MAT]):
                blend_mats[loc_index]["target"][hier_index]["targetMatrix"] << loc_attr
                (
                    blend_mats[loc_index]["target"][hier_index]["weight"]
                    << blend_weight["outValue"]
                )

        # set hierBlend max
        cmds.addAttr(
            str(self.container_node[self._IN_HIER_BLEND]), edit=True, max=num_hiers - 1
        )

        # adding nodes
        self.container_node.add_nodes(
            hier_parent_blend, *blend_mats, *world_mats, *blend_weights, *vis_remaps
        )

    # override helper functions
    def __create_vis_remap(self, hier_index: int, num_hiers: int, num_hiers_seg: float):
        """creates hier visualize remap

        Args:
            hier_index (int):
            num_hiers (int):
            num_hiers_seg (float):

        Returns:
            nw.Node:
        """
        hier_vis_remap = nw.create_node("remapValue", f"hier{hier_index}_visRemap")
        hier_vis_remap["inputMax"] = num_hiers - 1
        hier_vis_remap["inputValue"] << self.container_node[self._IN_HIER_BLEND]

        value_index = 0
        pre_seg_val = num_hiers_seg * (hier_index - 1)
        seg_val = num_hiers_seg * hier_index
        post_seg_val = num_hiers_seg * (hier_index + 1)
        if pre_seg_val >= 0.0:
            hier_vis_remap["value"][value_index]["value_Position"] = pre_seg_val
            hier_vis_remap["value"][value_index]["value_FloatValue"] = 0.49
            value_index += 1
        hier_vis_remap["value"][value_index]["value_Position"] = seg_val
        hier_vis_remap["value"][value_index]["value_FloatValue"] = 1
        value_index += 1
        if (pre_seg_val - 1.0) < 0.0005:
            hier_vis_remap["value"][value_index]["value_Position"] = post_seg_val
            hier_vis_remap["value"][value_index]["value_FloatValue"] = 0.49
            value_index += 1

        (
            hier_vis_remap["outValue"]
            >> self.container_node[self._OUT_HIER_VIS][hier_index]
        )

        return hier_vis_remap


class Joint(_Motion):
    """creates a joint for every xform"""

    class_namespace = "jnt"

    def _override_build(self, control_color=None, **kwargs):
        input_xforms = self.get_xform_attrs(xform_type=self.IO_ENUM.input)

        self.connect_input_to_output()

        joints = []
        for index, input_xform in input_xforms.items():
            joint = nw.create_node("joint", f"{input_xform.xform_name.value}_jnt")
            joint["offsetParentMatrix"] << input_xform.world_matrix
            joint["radius"] = 0.5
            joints.append(joint)

        cmds.parent(*[str(joint) for joint in joints], str(self.transform_node))

        self.container_node.add_nodes(*joints)
