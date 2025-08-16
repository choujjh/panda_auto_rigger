import system.base_component as base_component
import component.control as control
import utils.node_wrapper as nw
import component.setup as setup
import system.component_data as component_data
import system.component_enum_data as component_enum_data
import maya.cmds as cmds

class FK(base_component.Hierarchy):
    """Given a hierarchy creates an FK chain to accompany it"""

    class_namespace = "FK"
    root_transform_name = "fk_grp"

    @classmethod
    def create(cls, source_component:base_component.Hierarchy, instance_name=None, parent=None, **kwargs):
        kwargs["source_component"] =source_component
        return super().create(instance_name, parent, **kwargs)

    def _override_build(self, **kwargs):
        #qol variables
        added_nodes = []
        HIER_DATA =self.HIER_DATA

        # connecting source component
        source_component = kwargs["source_component"]
        self._connect_source_hier_component(source_component=source_component)

        prev_ws_attr = self.container_node[HIER_DATA.HIER_PARENT_MATRIX]
        prev_init_inv_attr = self.container_node[HIER_DATA.HIER_PARENT_INIT_INV_MATRIX]
        for index, input_xform in enumerate(self.input_node[self.HIER_DATA.INPUT_XFORM]):
            control_inst = control.Circle.create(instance_name=input_xform[HIER_DATA.INPUT_XFORM_NAME], axis_vec=source_component.container_node["primaryVec"].value, parent=self)

            ws_mult_matrix = nw.create_node("multMatrix", f"xform{index}_ws_mat_mult")
            added_nodes.append(ws_mult_matrix)

            ws_mult_matrix["matrixIn"][0] << input_xform[HIER_DATA.INPUT_INIT_MATRIX]
            ws_mult_matrix["matrixIn"][1] << prev_init_inv_attr
            ws_mult_matrix["matrixIn"][2] << prev_ws_attr
            ws_mult_matrix["matrixIn"][3] << self.transform_node["worldInverseMatrix"][0]
            ws_mult_matrix["matrixSum"] >> control_inst.container_node["offsetMatrix"]
            
            prev_ws_attr = control_inst.container_node["worldMatrix"]
            prev_init_inv_attr = self.input_node[HIER_DATA.INPUT_XFORM][index][HIER_DATA.INPUT_INIT_INV_MATRIX]

            self._set_output_xform_index_attrs(
                index=index,
                output_xform_name=input_xform[HIER_DATA.INPUT_XFORM_NAME],
                output_init_matrix=input_xform[HIER_DATA.INPUT_INIT_MATRIX],
                output_init_inv_matrix=input_xform[HIER_DATA.INPUT_INIT_INV_MATRIX],
                output_world_matrix=control_inst.container_node["worldMatrix"]
            )


        self.container_node.add_nodes(*added_nodes)

class SimpleIK(base_component.Hierarchy):
    """Given the SimpleLimb creates a 2 chain IK chain"""

    class_namespace = "simple_IK"
    root_transform_name = "ik_grp"

    def _get_input_node_build_attr_data(self):
        node_data = super()._get_input_node_build_attr_data()
        node_data.extend_attr_data(
            component_data.AttrData("primaryVec", type_="double3", parent="input"),
            component_data.AttrData("primaryVecX", type_="double", parent="primaryVec"),
            component_data.AttrData("primaryVecY", type_="double", parent="primaryVec"),
            component_data.AttrData("primaryVecZ", type_="double", parent="primaryVec"),
            component_data.AttrData("secondaryVec", type_="double3", parent="input"),
            component_data.AttrData("secondaryVecX", type_="double", parent="secondaryVec"),
            component_data.AttrData("secondaryVecY", type_="double", parent="secondaryVec"),
            component_data.AttrData("secondaryVecZ", type_="double", parent="secondaryVec"),
            component_data.AttrData("tertiaryVec", type_="double3", parent="input"),
            component_data.AttrData("tertiaryVecX", type_="double", parent="tertiaryVec"),
            component_data.AttrData("tertiaryVecY", type_="double", parent="tertiaryVec"),
            component_data.AttrData("tertiaryVecZ", type_="double", parent="tertiaryVec"),
            component_data.AttrData("IK", type_="compound", parent="input"),
            component_data.AttrData("IKEndMatrix", type_="matrix", parent="IK"),
            component_data.AttrData("IKEndInitInvMatrix", type_="matrix", parent="IK"),
            component_data.AttrData("IKSide", type_="double", parent="IK"),
            component_data.AttrData("IKStretch", type_="bool", parent="IK", value=True),
            component_data.AttrData("softIKBlendStart", type_="double", parent="IK", value=0.9, min=0, max=1),
            component_data.AttrData("blendType", type_=component_enum_data.SoftIKBlendTypes.smoothStep, parent="IK"),
            component_data.AttrData("blendCurve", type_=component_enum_data.SoftIKBlendCurve.quadratic, parent="IK"),
        )
        
        return node_data

    @classmethod
    def create(cls, source_component:setup.SimpleLimb, instance_name = None, parent=None, **kwargs):
        kwargs["source_component"] = source_component
        return super().create(instance_name, parent, **kwargs)
    
    def _connect_source_hier_component(self, source_component):
        super()._connect_source_hier_component(source_component)
        for attr_name in ["primaryVec", "secondaryVec", "tertiaryVec", "IKSide"]:
            source_component.container_node[attr_name] >> self.container_node[attr_name]
    def __setup_ik_control(self, name:str, input_xform_index:int, parent_init_inv_matrix:nw.Attr, parent_world_matrix:nw.Attr):
        """Creates the IK control

        Args:
            name (str):
            input_xform_index (int): input matrix index for it's parent
            parent_init_inv_matrix (nw.Attr):
            parent_world_matrix (nw.Attr):

        Returns
            base_component.Control:
        """
        input_xform = self._get_input_xform_index_attrs(input_xform_index)
        control_inst = control.BoxControl.create(instance_name=input_xform[self.HIER_DATA.INPUT_XFORM_NAME], parent=self)
        for attr_name in ["sx", "sy", "sz"]:
            control_inst.transform_node[attr_name].set_locked(True)
            control_inst.transform_node[attr_name].set_keyable(False)

        mult_node = nw.create_node("multMatrix", f"{name}_cntrl_ws_mat")
        mult_node["matrixIn"][0] << input_xform[self.HIER_DATA.INPUT_INIT_MATRIX]
        mult_node["matrixIn"][1] << parent_init_inv_matrix
        mult_node["matrixIn"][2] << parent_world_matrix

        control_inst.container_node["offsetMatrix"] << mult_node["matrixSum"]
        self.container_node.add_nodes(mult_node)

        return control_inst
    def __create_dist_nodes(self, root_control:base_component.Control, end_control:base_component.Control):
        """Creates distance nodes for ik calculations. curr_len is the distance between root and end controls

        Args:
            root_control (base_component.Control):
            end_control (base_component.Control):
        Returns:
            len1_node:nw.Node, len2_node:nw.Node, curr_len_nodenw.Node:
        """
        input_xforms = self._get_input_xform_attrs()

        len1_node = nw.create_node("distanceBetween", "len1_init_dist")
        len1_node["inMatrix1"] << input_xforms[0][self.HIER_DATA.INPUT_INIT_MATRIX]
        len1_node["inMatrix2"] << input_xforms[1][self.HIER_DATA.INPUT_INIT_MATRIX]
        len2_node = nw.create_node("distanceBetween", "len2_init_dist")
        len2_node["inMatrix1"] << input_xforms[1][self.HIER_DATA.INPUT_INIT_MATRIX]
        len2_node["inMatrix2"] << input_xforms[2][self.HIER_DATA.INPUT_INIT_MATRIX]
        curr_len_node = nw.create_node("distanceBetween", "curr_total_dist")
        curr_len_node["inMatrix1"] << root_control.container_node["worldMatrix"]
        curr_len_node["inMatrix2"] << end_control.container_node["worldMatrix"]

        self.container_node.add_nodes(len1_node, len2_node, curr_len_node)
        return len1_node["distance"], len2_node["distance"], curr_len_node["distance"]
    def __create_soft_ik_nodes(self, len1_attr:nw.Attr, len2_attr:nw.Attr, curr_len_attr:nw.Attr):

        def __soft_ik_cos_expression_str(len1_attr:nw.Attr, len2_attr:nw.Attr, curr_len_attr:nw.Attr, soft_ik_cos_build_data_node:nw.Node):
            expression_str = [
                f"float $len1 = {len1_attr};",
                f"float $len2 = {len2_attr};",
                f"float $currLen = {curr_len_attr};",
                f"float $totalLen = $len1 + $len2;\n",

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
        
        def __soft_ik_len_expression_str(len1_attr:nw.Attr, len2_attr:nw.Attr, cos0_squared_attr:nw.Attr, init_height_attr:nw.Attr, solved_height_attr:nw.Attr, soft_ik_output_data_node:nw.Node):
            expression_str = [
                f"float $len1 = {len1_attr};",
                f"float $len2 = {len2_attr};",
                f"float $lenRatio = $len2 / $len1;\n",

                f"float $len1Scalar = sqrt({cos0_squared_attr}+pow({solved_height_attr}, 2));",
                f"float $len2Scalar = sqrt(1 - ($lenRatio * pow({init_height_attr}, 2)) + ($lenRatio * pow({solved_height_attr}, 2)));\n",

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
        cos_build_data_expression_str = __soft_ik_cos_expression_str(len1_attr=len1_attr, len2_attr=len2_attr, curr_len_attr=curr_len_attr, soft_ik_cos_build_data_node=cos_build_data)
        len_expression = nw.wrap_node(cmds.expression(string=cos_build_data_expression_str, name="soft_ik_cos_expression"))

        # creating blending for new height
        remap_cos = nw.create_node("remapValue", "soft_ik_cos_remap")
        remap_cos["inputMin"] << self.container_node["softIKBlendStart"]
        remap_cos["inputValue"] << cos_build_data["cos0"]

        smooth_step = nw.create_node("smoothStep", "soft_ik_smoothStep_blend")
        smooth_step["input"] << remap_cos["outValue"]

        cubic_mult = nw.create_node("multiply", "soft_ik_cublic_blend")
        cubic_mult["input"][0] << remap_cos["outValue"]
        cubic_mult["input"][0] << remap_cos["outValue"]
        cubic_mult["input"][0] << remap_cos["outValue"]

        blend_type_choice = nw.create_node("choice", "soft_ik_blendType_choice")
        blend_type_choice["selector"] << self.container_node["blendType"]
        blend_type_choice["input"][0] << smooth_step["output"]
        blend_type_choice["input"][1] << cubic_mult["output"]

        blend_curve_choice = nw.create_node("choice", "soft_ik_blendCurve_choice")
        blend_curve_choice["selector"] << self.container_node["blendCurve"]
        blend_curve_choice["input"][0] << cos_build_data["linearHeight"]
        blend_curve_choice["input"][1] << cos_build_data["quadraticHeight"]
        blend_curve_choice["input"][2] << cos_build_data["cubicHeight"]

        blended_height = nw.create_node("blendTwoAttr", "soft_ik_blended_height")
        blended_height["attributesBlender"] << blend_type_choice["output"]
        blended_height["input"][0] << cos_build_data["initHeight"]
        blended_height["input"][1] << blend_curve_choice["output"]

        blending_nodes = [remap_cos, smooth_step, cubic_mult, blend_type_choice, blend_curve_choice]

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
            soft_ik_output_data_node=soft_ik_output_data)
        len_expression = nw.wrap_node(cmds.expression(string=len_expression_str, name="soft_ik_len_expression"))

        new_len_nodes = [soft_ik_output_data, len_expression]

        self.container_node.add_nodes(cos_build_data, len_expression, *blending_nodes, *new_len_nodes)
        return soft_ik_output_data



    def __create_ik_build_data_nodes(self, len1_attr:nw.Attr, len2_attr:nw.Attr, curr_len_attr:nw.Attr):
        """Creates the trig hold value and distance nodes using law of cos. the holdValue will have the cos, sin, neg sin, and length of the ik

        Args:
            len1_attr (nw.Attr): 
            len2_attr (nw.Attr): 
            curr_len_attr (nw.Attr): 

        Returns:
            nw.Node: the node holding all trig values
        """
        def __ik_build_data_expression_str(len1_attr:nw.Attr, len2_attr:nw.Attr, curr_len_attr:nw.Attr, ik_build_data_node:nw.Node):
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
                f"float $totalLen = $len1 + $len2;\n",
                "float $poleVecLen = $len1;",
                
                "float $len1Squared = $len1 * $len1;",
                "float $len2Squared = $len2 * $len2;",
                "float $currLenSquared = $currLen * $currLen;\n",

                "float $cos0 = 1;",
                "float $sin0 = 0;",
                "float $cos1 = 1;",
                "float $sin1 = 0;\n",

                "if ($currLen < $totalLen) {",
                "\t$poleVecLen = ($currLen/$totalLen) * $len1;",
                "\t$cos0 = ($len1Squared + $currLenSquared - $len2Squared) / (2 * $len1 * $currLen);",
                "\t$cos1 = -1 * ($len1Squared + $len2Squared - $currLenSquared) / (2 * $len1 * $len2);",
                f"\tif ({self.container_node['IKSide']} < 0) {{",
                "\t\t$sin0 = sqrt(abs(1 - ($cos0 * $cos0)));",
                "\t\t$sin1 = -1 * sqrt(abs(1 - ($cos1 * $cos1)));\n",
                "\t}",
                "\telse {",
                "\t\t$sin0 = -1 * sqrt(abs(1 - ($cos0 * $cos0)));",
                "\t\t$sin1 = sqrt(abs(1 - ($cos1 * $cos1)));\n",
                "\t}",
                "}",

                f"else if ({self.container_node['IKStretch']} && $currLen > $totalLen) {{",
                "\t$scalar = $currLen/$totalLen;",
                "\t$len1 = $len1 * $scalar;",
                "\t$len2 = $len2 * $scalar;\n",
                "\t$poleVecLen = $len1;",
                "}",

                f"if ({self.container_node['tertiaryVecX']} < 0.0 || {self.container_node['tertiaryVecY']} < 0.0 || {self.container_node['tertiaryVecZ']} < 0.0) {{",
                "\t$sin0 = -1 * $sin0;",
                "\t$sin1 = -1 * $sin1;",
                "}",

                f"{ik_build_data_node['cos0']} = $cos0;",
                f"{ik_build_data_node['sin0']} = $sin0;",
                f"{ik_build_data_node['negSin0']} = -1 * $sin0;",

                f"{ik_build_data_node['cos1']} = $cos1;",
                f"{ik_build_data_node['sin1']} = $sin1;",
                f"{ik_build_data_node['negSin1']} = -1 * $sin1;",
                f"{ik_build_data_node['length1']} = $len1;",

                f"{ik_build_data_node['length2']} = $len2;",
                f"{ik_build_data_node['poleVecLen']} = $poleVecLen;"
            ]
            return "\n".join(expression_str)
        
        # node to store expression in
        ik_build_data_node = nw.create_node("network", "ik_build_data")
        ik_build_data_attrData = component_data.NodeData(
            component_data.AttrData("xform0Data", type_="compound"),
            component_data.AttrData("cos0", type_="double", parent="xform0Data"),
            component_data.AttrData("sin0", type_="double", parent="xform0Data"),
            component_data.AttrData("negSin0", type_="double", parent="xform0Data"),

            component_data.AttrData("xform1Data", type_="compound"),
            component_data.AttrData("cos1", type_="double", parent="xform1Data"),
            component_data.AttrData("sin1", type_="double", parent="xform1Data"),
            component_data.AttrData("negSin1", type_="double", parent="xform1Data"),
            component_data.AttrData("length1", type_="double", parent="xform1Data"),

            component_data.AttrData("xform2Data", type_="compound"),
            component_data.AttrData("length2", type_="double", parent="xform2Data"),
            component_data.AttrData("poleVecLen", type_="double"),
        )
        ik_build_data_attrData.add_attrs_to_node(ik_build_data_node)

        ik_trig_expression_str = __ik_build_data_expression_str(
            len1_attr=len1_attr,
            len2_attr=len2_attr,
            curr_len_attr=curr_len_attr,
            ik_build_data_node=ik_build_data_node)

        ik_trig_expression = nw.wrap_node(cmds.expression(
            string=ik_trig_expression_str, 
            name="ik_build_data_expression"))
        

        self.container_node.add_nodes(ik_build_data_node, ik_trig_expression)
        return ik_build_data_node
    def __create_local_matrix_nodes(self, ik_build_data_node:nw.Node):
        """Creates local matrix for IK using expressions

        Args:
            trig_hold_value (nw.Node): _description_

        Returns:
            _type_: _description_
        """
        def __local_matrix_expression_str(ik_build_data_node:nw.Node, rot0_loc_matrix:nw.Node, rot1_loc_matrix:nw.Node, rot2_loc_matrix:nw.Node):
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
            for index, rot_loc_matrix in enumerate([rot0_loc_matrix, rot1_loc_matrix, rot2_loc_matrix]):
                # no rotation on last matrix
                if index != 2:                  
                    cos = ik_build_data_node[f"cos{index}"]
                    sin = ik_build_data_node[f"sin{index}"]
                    neg_sin = ik_build_data_node[f"negSin{index}"]
                    expression_str.extend([                       
                        f"matrix $rot_matrix{index}[3][3] = <<1.0, 0.0, 0.0; 0.0, 1.0, 0.0; 0.0, 0.0, 1.0>>;\n",

                        f"if({self.container_node['tertiaryVecX']} != 0.0) {{",
                        f"\t$rot_matrix{index}[1][1] = {cos};",
                        f"\t$rot_matrix{index}[1][2] = {sin};",
                        f"\t$rot_matrix{index}[2][1] = {neg_sin};",
                        f"\t$rot_matrix{index}[2][2] = {cos};",
                        "}",
                        f"else if({self.container_node['tertiaryVecY']} != 0.0) {{",
                        f"\t$rot_matrix{index}[0][0] = {cos};",
                        f"\t$rot_matrix{index}[0][2] = {neg_sin};",
                        f"\t$rot_matrix{index}[2][0] = {sin};",
                        f"\t$rot_matrix{index}[2][2] = {cos};",
                        "}",
                        f"else if({self.container_node['tertiaryVecZ']} != 0.0) {{",
                        f"\t$rot_matrix{index}[0][0] = {cos};",
                        f"\t$rot_matrix{index}[0][1] = {neg_sin};",
                        f"\t$rot_matrix{index}[1][0] = {sin};",
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
                    ])
                # no translate on first matrix
                if index != 0:
                    length = ik_build_data_node[f"length{index}"]
                    expression_str.extend([
                        f"{rot_loc_matrix['in30']} = {self.container_node['primaryVecX']} * {length};",
                        f"{rot_loc_matrix['in31']} = {self.container_node['primaryVecY']} * {length};",
                        f"{rot_loc_matrix['in32']} = {self.container_node['primaryVecZ']} * {length};",

                    ])
            return "\n".join(expression_str)
        loc_rot_matricies = []
        for index in range(3):
            loc_rot_matricies.append(nw.create_node("fourByFourMatrix", f"xform{index}_loc_mat"))

        ik_loc_mat_expression_str = __local_matrix_expression_str(
            ik_build_data_node=ik_build_data_node,
            rot0_loc_matrix=loc_rot_matricies[0],
            rot1_loc_matrix=loc_rot_matricies[1],
            rot2_loc_matrix=loc_rot_matricies[2]
        )
        ik_loc_mat_expression = nw.wrap_node(cmds.expression(
            string=ik_loc_mat_expression_str, 
            name="ik_loc_mat_expression"))
        
        self.container_node.add_nodes(*loc_rot_matricies, ik_loc_mat_expression)
        return loc_rot_matricies
    def __create_pole_vec_nodes(self, ik_build_data_node:nw.Node, root_cntrl_ws_mat:nw.Attr, end_cntrl_ws_mat:nw.Attr):
        """Creates all pole vector nodes

        Args:
            ik_build_data_node (nw.Node): 
            root_cntrl_ws_mat (nw.Attr): 
            end_cntrl_ws_mat (nw.Attr): 

        Returns:
            base_component.Control: pole vector control
        """
        def __pole_vec_expression_str(pole_vec_control:nw.Transform):
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
                for transform, vec_name in zip(["Trans", "Rot"], ["secondaryVec", "primaryVec"]):
                    for extreme in ["max", "min"]:
                        dest_attr = pole_vec_control[f"{extreme}{transform}{axis}LimitEnable"]
                        src_attr = self.input_node[vec_name][index]
                        expression_str.append(f"{dest_attr} = ({src_attr} == 0);")
                expression_str.append("")
                
            return "\n".join(expression_str)
        # control
        pole_cntrl_inst = control.DiamondWireControl.create(instance_name="poleVec", parent=self)
        for attr_name in ["sx", "sy", "sz"]:
            pole_cntrl_inst.transform_node[attr_name].set_locked(True)
            pole_cntrl_inst.transform_node[attr_name].set_keyable(False)
        for t_, secondary_vec_axis in zip(pole_cntrl_inst.transform_node["translate"], self.input_node["secondaryVec"]):
            t_.set(self.container_node["IKSide"].value * secondary_vec_axis.value * 2)
        transform_limits_kwarg = {f"t{axis}":(0, 0) for axis in ["x", "y", "z"]}
        transform_limits_kwarg.update({f"r{axis}":(0, 0) for axis in ["x", "y", "z"]})
        cmds.transformLimits(str(pole_cntrl_inst.transform_node), **transform_limits_kwarg)

        # aim matrix
        aim_matrix = nw.create_node("aimMatrix", "pole_vec_start_mat")
        aim_matrix["inputMatrix"]
        aim_matrix["inputMatrix"] << root_cntrl_ws_mat
        aim_matrix["primaryTargetMatrix"] << end_cntrl_ws_mat
        aim_matrix["primaryInputAxis"] << self.container_node["primaryVec"]
        aim_matrix["secondaryTargetMatrix"] << root_cntrl_ws_mat
        aim_matrix["secondaryInputAxis"] << self.container_node["secondaryVec"]
        aim_matrix["secondaryTargetVector"] << self.container_node["secondaryVec"]

        # vectorizing length
        vec_mult = nw.create_node("multiplyDivide", "pole_vec_len_vec")
        for attr_name in ["X", "Y", "Z"]:
            vec_mult[f"input1{attr_name}"] << ik_build_data_node["poleVecLen"]
        vec_mult["input2"] << self.container_node["primaryVec"]

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
            tz_attr=pole_vec_ws_translate["outputZ"])
        pole_vec_parent_4x4["output"] >> pole_cntrl_inst.container_node["offsetMatrix"]

        # pole vec expression
        pole_vec_expression_str = __pole_vec_expression_str(pole_vec_control=pole_cntrl_inst.transform_node)

        pole_vec_expression = nw.wrap_node(cmds.expression(
            string=pole_vec_expression_str, 
            name="ik_pole_vec_expression"))

        self.container_node.add_nodes(aim_matrix, vec_mult, pole_vec_expression)
        return pole_cntrl_inst

    def _override_build(self, **kwargs):
        source_component = kwargs["source_component"]
        self._connect_source_hier_component(source_component)

        # controls
        root_control = self.__setup_ik_control(
            name="root", 
            input_xform_index=0, 
            parent_init_inv_matrix=self.input_node[self.HIER_DATA.HIER_PARENT_INIT_INV_MATRIX],
            parent_world_matrix=self.input_node[self.HIER_DATA.HIER_PARENT_MATRIX])
        end_control = self.__setup_ik_control(
            name="end",
            input_xform_index=2,
            parent_init_inv_matrix=self.container_node["IKEndInitInvMatrix"],
            parent_world_matrix=self.container_node["IKEndMatrix"])

        # get all expression calculations
        len1_attr, len2_attr, curr_len_attr = self.__create_dist_nodes(root_control=root_control, end_control=end_control)
        soft_ik_new_len = self.__create_soft_ik_nodes(len1_attr=len1_attr, len2_attr=len2_attr, curr_len_attr=curr_len_attr)
        ik_build_data = self.__create_ik_build_data_nodes(len1_attr=soft_ik_new_len["len1"], len2_attr=soft_ik_new_len["len2"], curr_len_attr=curr_len_attr)
        
        loc_matricies = self.__create_local_matrix_nodes(ik_build_data_node=ik_build_data)
        pole_cntrl_inst = self.__create_pole_vec_nodes(
            ik_build_data_node=ik_build_data,
            root_cntrl_ws_mat=root_control.container_node["worldMatrix"],
            end_cntrl_ws_mat=end_control.container_node["worldMatrix"])
        
        # create aim matrix
        ik_base_mat_aim = nw.create_node("aimMatrix", "ik_base_mat")
        ik_base_mat_aim["inputMatrix"] << root_control.container_node["worldMatrix"]
        ik_base_mat_aim["primaryTargetMatrix"] << end_control.container_node["worldMatrix"]
        ik_base_mat_aim["primaryInputAxis"] << self.container_node["primaryVec"]
        ik_base_mat_aim["secondaryTargetMatrix"] << pole_cntrl_inst.container_node["worldMatrix"]
        ik_base_mat_aim["secondaryInputAxis"] << self.container_node["secondaryVec"]
        ik_base_mat_aim["secondaryTargetVector"] << self.container_node["secondaryVec"]
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
                local_mat_attr = mult_matrix["matrixSum"]
            else:
                local_mat_attr = loc_matrix["output"]

            self._set_output_xform_index_attrs(
                index=index,
                output_world_matrix=mult_matrix["matrixSum"],
                output_loc_matrix=local_mat_attr
            )
            xform_output_nodes.append(mult_matrix)
                        
        # creating controls        
        self.container_node.add_nodes(ik_base_mat_aim, *xform_output_nodes)

        

            