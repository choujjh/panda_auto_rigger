import system.base_component as base_component
import system.component_data as component_data
import system.component_enum_data as component_enum_data
import component.control as control
import utils.utils as utils
import utils.node_wrapper as nw
import component.enum_manager as enum_manager

class Setup(base_component.Hierarchy):
    """A Base class for setup autorigging components. Derived from Hierarchy"""
    root_transform_name = "setup"
    component_type = component_enum_data.ComponentType.setup
    class_namespace = "setup_"

    def _get_input_node_build_attr_data(self):
        node_data = super()._get_input_node_build_attr_data()
        node_data.extend_attr_data(
            component_data.AttrData("primaryAxis", type_=component_enum_data.AxisEnum.x, publish=True),
            component_data.AttrData("secondaryAxis", type_=component_enum_data.AxisEnum.y, publish=True),
            component_data.AttrData("locScale", type_="integer", publish=True, value=1, min=0.1),
            component_data.AttrData("cntrlColor", type_="double3")
        )
        return node_data

    @classmethod
    def create(
        cls, 
        instance_name=None, 
        parent=None, 
        num_xforms=3, 
        primary_axis:component_enum_data.MayaEnumAttr=component_enum_data.AxisEnum.x, 
        secondary_axis:component_enum_data.MayaEnumAttr=component_enum_data.AxisEnum.y, 
        **kwargs):

        kwargs["num_xforms"] = num_xforms
        kwargs["primary_axis"] = primary_axis
        kwargs["secondary_axis"] = secondary_axis
        component_inst = super().create(instance_name, parent, **kwargs)
        return component_inst
    
    def _override_build(self, **kwargs):
        num_xforms = kwargs["num_xforms"]

        self.container_node["primaryAxis"] = component_enum_data.get_index_of_item(kwargs["primary_axis"])
        self.container_node["secondaryAxis"] = component_enum_data.get_index_of_item(kwargs["secondary_axis"])

        for index in range(num_xforms):
            input_xform_attrs = self._get_input_xform_index_attrs(index)

            # setting name
            input_xform_attrs[self.HIER_DATA.INPUT_XFORM_NAME].set(f"xform{index}")

            # creating control
            control_inst = control.Locator.create(instance_name=input_xform_attrs[self.HIER_DATA.INPUT_XFORM_NAME], parent=self)
            control_container = control_inst.container_node
            control_container["locScale"] << self.input_node["locScale"]
            control_container["offsetMatrix"] = utils.translate_to_matrix([0, index*1.5, 0])

            # connecting to output
            self._set_output_xform_index_attrs(
                index,
                output_init_matrix=control_container["worldMatrix"],
                output_world_matrix=control_container["worldMatrix"],
            )

class SimpleLimb(Setup):
    """3 xform that aim and align to each other. middle xform stays inbetween and orients correctly to whatever the angle the other 2 xform make"""    
    def _get_output_node_build_attr_data(self):
        node_data =  super()._get_output_node_build_attr_data()
        node_data.extend_attr_data(
            component_data.AttrData("primaryVec", type_="double3", parent="output"),
            component_data.AttrData("primaryVecX", type_="double", parent="primaryVec"),
            component_data.AttrData("primaryVecY", type_="double", parent="primaryVec"),
            component_data.AttrData("primaryVecZ", type_="double", parent="primaryVec"),
            component_data.AttrData("secondaryVec", type_="double3", parent="output"),
            component_data.AttrData("secondaryVecX", type_="double", parent="secondaryVec"),
            component_data.AttrData("secondaryVecY", type_="double", parent="secondaryVec"),
            component_data.AttrData("secondaryVecZ", type_="double", parent="secondaryVec"),
            component_data.AttrData("tertiaryVec", type_="double3", parent="output"),
            component_data.AttrData("tertiaryVecX", type_="double", parent="tertiaryVec"),
            component_data.AttrData("tertiaryVecY", type_="double", parent="tertiaryVec"),
            component_data.AttrData("tertiaryVecZ", type_="double", parent="tertiaryVec"),
            component_data.AttrData("IK", type_="compound", parent="output"),
            component_data.AttrData("IKSide", type_="double", parent="IK"),
        )


        return node_data

    @classmethod
    def create(cls, instance_name=None, parent=None, **kwargs):
        return super().create(instance_name, parent, **kwargs)
    def _override_build(self, **kwargs):
        for index in range(3):
            input_xform_attrs = self._get_input_xform_index_attrs(index)
            input_xform_attrs[self.HIER_DATA.INPUT_XFORM_NAME].set(f"xform{index}")

        # creating controls
        control_inst0 = control.Locator.create(instance_name=self.input_node[self.HIER_DATA.INPUT_XFORM][0][self.HIER_DATA.INPUT_XFORM_NAME], parent=self)
        control_inst0.transform_node["ty"] = 8
        control_inst0.container_node["locScale"] << self.container_node["locScale"]
        for attr in ["rz","sx","sy","sz"]:
            control_inst0.transform_node[attr].set_locked(True)
            control_inst0.transform_node[attr].set_keyable(False)
        control_inst1 = control.Locator.create(instance_name=self.input_node[self.HIER_DATA.INPUT_XFORM][1][self.HIER_DATA.INPUT_XFORM_NAME], parent=self)
        control_inst1.transform_node["tz"] = 1
        control_inst1.container_node["locScale"] << self.container_node["locScale"]
        for attr in ["ty","rx","ry","rz","sx","sy","sz"]:
            control_inst1.transform_node[attr].set_locked(True)
            control_inst1.transform_node[attr].set_keyable(False)
        control_inst2 = control.Locator.create(instance_name=self.input_node[self.HIER_DATA.INPUT_XFORM][2][self.HIER_DATA.INPUT_XFORM_NAME], parent=self)
        control_inst2.container_node["locScale"] << self.container_node["locScale"]
        for attr in ["rx","ry","rz","sx","sy","sz"]:
            control_inst2.transform_node[attr].set_locked(True)
            control_inst2.transform_node[attr].set_keyable(False)

        # axis vectors
        primary_vec = enum_manager.axis_vec_choice_node(choice_node_name="primary_vec", enum_attr=self.input_node["primaryAxis"])
        primary_vec["output"] >> self.container_node["primaryVec"]
        secondary_vec = enum_manager.axis_vec_choice_node(choice_node_name="secondary_vec", enum_attr=self.input_node["secondaryAxis"])
        secondary_vec["output"] >> self.container_node["secondaryVec"]
        tertiary_vec = nw.create_node("crossProduct", "tertiary_vec")
        tertiary_vec["input1"] << primary_vec["output"]
        tertiary_vec["input2"] << secondary_vec["output"]
        tertiary_vec["output"] >> self.container_node["tertiaryVec"]
        self.container_node.add_nodes(primary_vec, secondary_vec, tertiary_vec)

        # mid interp matrix
        mid_interp_matrix, xform2_translate = self.__create_mid_interp_matrix(
            control_inst0.container_node["worldMatrix"], 
            control_inst2.container_node["worldMatrix"])
        control_inst1.container_node["offsetMatrix"] << mid_interp_matrix
        control_inst1.transform_node["tz"] >> self.container_node["IKSide"]

        # xform0
        xform0_ws_mat_attr, xform0_inv_attr = self.__create_xform0(
            guide_transform0_ws_mat=control_inst0.container_node["worldMatrix"], 
            guide_transform1_ws_mat=control_inst1.container_node["worldMatrix"], 
            primary_vec=primary_vec["output"], 
            secondary_vec=secondary_vec["output"])

        xform1_ws_mat_attr, xform1_inv_attr = self.__create_xform1(
            guide_transform1_ws_mat=control_inst1.container_node["worldMatrix"], 
            guide_transform2_ws_mat=control_inst2.container_node["worldMatrix"],
            xform0_ws_mat=xform0_ws_mat_attr,
            xform0_inv_mat=xform0_inv_attr,
            primary_vec=primary_vec["output"],
            tertiary_vec=tertiary_vec["output"])
        
        self.__create_xform2(
            xform1_ws_mat=xform1_ws_mat_attr, 
            xform2_translate=xform2_translate, 
            xform1_inv_mat=xform1_inv_attr)

    def __create_mid_interp_matrix(self, source_matrix:nw.Attr, target_matrix:nw.Attr):
        """Creates all nodes to have the middle interp matrix

        Args:
            source_matrix (nw.Attr):
            target_matrix (nw.Attr):
        Returns
            nw.Attr: mid interp matrix attr
            nw.Node: target_matrix translate node
        """
        # aim from source to target
        aim_matrix = nw.create_node("aimMatrix", "mid_mat_aim_ws")
        aim_matrix["inputMatrix"]  << source_matrix
        aim_matrix["primaryTargetMatrix"] << target_matrix
        aim_matrix["secondaryTargetMatrix"] << source_matrix
        aim_matrix["secondaryMode"] = 2
        aim_matrix["secondaryInputAxis"] = [0, 0, 1]
        aim_matrix["secondaryTargetVector"] = [0, 0, 1]

        # get translates of 2 matricies
        input_matricies = [source_matrix, target_matrix]
        translate_row_nodes = [nw.create_node("rowFromMatrix", "xform0_ws_translate"), 
                               nw.create_node("rowFromMatrix", "xform2_ws_translate")]

        for source_matrix, node in zip(input_matricies, translate_row_nodes):
            node["matrix"] << source_matrix
            node["input"]= 3

        # filling in translate for 4x4 matrix
        average_nodes = []
        for axis in ["X", "Y", "Z"]:
            average_node = nw.create_node("average", f"mid_mat_t{axis.lower()}")
            average_nodes.append(average_node)
            for t_index, node in enumerate(translate_row_nodes):
                node[f"output{axis}"] >> average_node["input"][t_index]        

        mid_matrix_inbetween_4x4 = self._create_orient_translate_blend(
            name="mid_mat_blend",
            matrix_attr=aim_matrix["outputMatrix"],
            tx_attr=average_nodes[0]["output"],
            ty_attr=average_nodes[1]["output"],
            tz_attr=average_nodes[2]["output"],
        )

        # scale compensate
        scale_comp = nw.create_node("multMatrix", "mid_mat_scale_compensate_ws")
        scale_comp["matrixIn"][0] << mid_matrix_inbetween_4x4["output"]
        scale_comp["matrixIn"][1] << self.transform_node["worldInverseMatrix"][0]

        # adding nodes to container
        self.container_node.add_nodes(aim_matrix, *translate_row_nodes, mid_matrix_inbetween_4x4, *average_nodes, scale_comp)
        return scale_comp["matrixSum"], translate_row_nodes[1]
    def __create_xform0(self, guide_transform0_ws_mat:nw.Attr, guide_transform1_ws_mat:nw.Attr, primary_vec:nw.Attr, secondary_vec:nw.Attr):
        """ Creates all xform0 nodes

        Args:
            guide_transform0_ws_mat (nw.Attr): guide transform0 world space matrix
            guide_transform1_ws_mat (nw.Attr): guide transform1 world space matrix
            primary_vec (nw.Attr):
            secondary_vec (nw.Attr):

        Returns:
            nw.Attr: xform0 world space matrix attr
            nw.Attr: xform0 world space inverse matrix attr
        """
        aim_node = nw.create_node("aimMatrix", "out_xform0_aim_ws_mat")

        # aim matrix ws
        aim_node["inputMatrix"] << guide_transform0_ws_mat
        aim_node["primaryTargetMatrix"] << guide_transform1_ws_mat
        aim_node["primaryInputAxis"] << primary_vec
        aim_node["secondaryTargetMatrix"] << guide_transform0_ws_mat
        aim_node["secondaryInputAxis"] << secondary_vec
        aim_node["secondaryTargetVector"] = [0, 0, 1]
        aim_node["secondaryMode"] = 2

        # pick out scale matrix
        pick_mat = nw.create_node("pickMatrix", "xform0_pick_mat")
        pick_mat["inputMatrix"] << aim_node["outputMatrix"]
        pick_mat["useScale"] = False
        pick_mat["useShear"] = False

        # xform0 inverse
        mat_inv = nw.create_node("inverseMatrix", "xform0_inv_mat")
        mat_inv["inputMatrix"] << pick_mat["outputMatrix"]

        # connect to output xform
        self._set_output_xform_index_attrs(
            index = 0,
            output_init_matrix=pick_mat["outputMatrix"],
            output_init_inv_matrix=mat_inv["outputMatrix"],
            output_world_matrix=pick_mat["outputMatrix"],
            output_loc_matrix=pick_mat["outputMatrix"]
        )

        self.container_node.add_nodes(aim_node, pick_mat, mat_inv)
        return pick_mat["outputMatrix"], mat_inv["outputMatrix"]
    def __create_xform1(self, guide_transform1_ws_mat:nw.Attr, guide_transform2_ws_mat:nw.Attr, xform0_ws_mat:nw.Attr,  xform0_inv_mat:nw.Attr, primary_vec:nw.Attr, tertiary_vec:nw.Attr):
        """Creates all xform1 nodes

        Args:
            guide_transform1_ws_mat (nw.Attr): guide transform1 world space matrix
            guide_transform2_ws_mat (nw.Attr): guide transform2 world space matrix
            xform0_ws_mat (nw.Attr): xform0 world space matrix
            xform0_inv_mat (nw.Attr): xform0 world space inverse matrix
            primary_vec (nw.Attr):
            tertiary_vec (nw.Attr):

        Returns:
            nw.Attr: xform1 world space matrix attr
            nw.Attr: xform1 world space inverse matrix attr
        """
        aim_node = nw.create_node("aimMatrix", "out_xform1_aim_ws_mat")

        # aim matrix ws
        aim_node["inputMatrix"] << guide_transform1_ws_mat
        aim_node["primaryTargetMatrix"] << guide_transform2_ws_mat
        aim_node["primaryInputAxis"] << primary_vec
        aim_node["secondaryTargetMatrix"] << xform0_ws_mat
        aim_node["secondaryInputAxis"] << tertiary_vec
        aim_node["secondaryTargetVector"] << tertiary_vec
        aim_node["secondaryMode"] = 2

        # pick out scale matrix
        pick_mat = nw.create_node("pickMatrix", "xform1_pick_mat")
        pick_mat["inputMatrix"] << aim_node["outputMatrix"]
        pick_mat["useScale"] = False
        pick_mat["useShear"] = False

        # xform1 inverse
        mat_inv = nw.create_node("inverseMatrix", "xform1_inv_mat")
        mat_inv["inputMatrix"] << pick_mat["outputMatrix"]

        # xform1 loc
        mat_loc = nw.create_node("multMatrix", "xform1_loc_mat")
        mat_loc["matrixIn"][0] << pick_mat["outputMatrix"]
        mat_loc["matrixIn"][1] << xform0_inv_mat

        # connect to output xform
        self._set_output_xform_index_attrs(
            index = 1,
            output_init_matrix=pick_mat["outputMatrix"],
            output_init_inv_matrix=mat_inv["outputMatrix"],
            output_world_matrix=pick_mat["outputMatrix"],
            output_loc_matrix=mat_loc["matrixSum"]
        )

        self.container_node.add_nodes(aim_node, mat_inv, pick_mat, mat_loc)
        return pick_mat["outputMatrix"], mat_inv["outputMatrix"]
    def __create_xform2(self, xform1_ws_mat:nw.Attr, xform2_translate:nw.Node, xform1_inv_mat:nw.Attr):
        """Creates all xform2 nodes

        Args:
            xform1_ws_mat (nw.Attr): xform1 world space matrix
            xform2_translate (nw.Node): node for xform2 translate
            xform1_inv_mat (nw.Attr): xform1 world space inverse matrix
        """
        xform_matrix2_ws = self._create_orient_translate_blend(
            name="xform2",
            matrix_attr=xform1_ws_mat,
            tx_attr=xform2_translate["outputX"],
            ty_attr=xform2_translate["outputY"],
            tz_attr=xform2_translate["outputZ"], 
            tw_attr=xform2_translate["outputW"], 
        )

        # xform2 inverse
        xform_matrix2_inv = nw.create_node("inverseMatrix", "xform2_inv_mat")
        xform_matrix2_inv["inputMatrix"] << xform_matrix2_ws["output"]

        # xform2 loc
        xform_matrix2_loc = nw.create_node("multMatrix", "xform2_loc_mat")
        xform_matrix2_loc["matrixIn"][0] << xform_matrix2_ws["output"]
        xform_matrix2_loc["matrixIn"][1] << xform1_inv_mat

        # xform2 connect to output xform
        self._set_output_xform_index_attrs(
            index = 2,
            output_init_matrix=xform_matrix2_ws["output"],
            output_init_inv_matrix=xform_matrix2_inv["outputMatrix"],
            output_world_matrix=xform_matrix2_ws["output"],
            output_loc_matrix=xform_matrix2_loc["matrixSum"]
        )
        self.container_node.add_nodes(xform_matrix2_ws, xform_matrix2_inv, xform_matrix2_loc)
        