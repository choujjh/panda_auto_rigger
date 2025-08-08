import system.base_component as base_component
import system.component_data as component_data
import system.component_enum_data as component_enum_data
import component.control as control
import utils.utils as utils
import utils.node_wrapper as nw
import component.enum_manager as enum_manager
import maya.cmds as cmds

class Setup(base_component.Hierarchy):
    """A Base class for setup autorigging components. Derived from Hier"""
    root_transform_name = "setup"
    component_type = component_enum_data.ComponentType.setup

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
            self.input_node["locScale"] >> control_container["locScale"]
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
        added_nodes = []
        
        for index in range(3):
            input_xform_attrs = self._get_input_xform_attrs(index)
            input_xform_attrs[self.HIER_DATA.INPUT_XFORM_NAME].set(f"xform{index}")

        # creating controls
        control_inst0 = control.Locator.create(instance_name=self.input_node[self.HIER_DATA.INPUT_XFORM][0][self.HIER_DATA.INPUT_XFORM_NAME], parent=self)
        control_inst0.transform_node["ty"] = 8
        control_inst0.container_node["locScale"] << self.container_node["locScale"]
        for attr in "rz,sx,sy,sz".split(","):
            control_inst0.transform_node[attr].set_locked(True)
            control_inst0.transform_node[attr].set_keyable(False)
        control_inst1 = control.Locator.create(instance_name=self.input_node[self.HIER_DATA.INPUT_XFORM][1][self.HIER_DATA.INPUT_XFORM_NAME], parent=self)
        control_inst1.transform_node["tz"] = -1
        control_inst1.container_node["locScale"] << self.container_node["locScale"]
        for attr in "ty,rx,ry,rz,sx,sy,sz".split(","):
            control_inst1.transform_node[attr].set_locked(True)
            control_inst1.transform_node[attr].set_keyable(False)
        control_inst2 = control.Locator.create(instance_name=self.input_node[self.HIER_DATA.INPUT_XFORM][2][self.HIER_DATA.INPUT_XFORM_NAME], parent=self)
        control_inst2.container_node["locScale"] << self.container_node["locScale"]
        for attr in "rx,ry,rz,sx,sy,sz".split(","):
            control_inst2.transform_node[attr].set_locked(True)
            control_inst2.transform_node[attr].set_keyable(False)

        # aim matricies
        aim_matrix_mid_space = nw.create_node("aimMatrix", "mid_mat_aim_ws")
        aim_matrix0 = nw.create_node("aimMatrix", "aim_ws_xform0")
        aim_matrix1 = nw.create_node("aimMatrix", "aim_ws_xform1")

        # axis vectors
        primary_vec = enum_manager.axis_vec_choice_node(choice_node_name="primary_vec", enum_attr=self.input_node["primaryAxis"])
        secondary_vec = enum_manager.axis_vec_choice_node(choice_node_name="secondary_vec", enum_attr=self.input_node["secondaryAxis"])
        tertiary_vec = nw.create_node("crossProduct", "tertiary_vec")
        tertiary_vec["input1"] << primary_vec["output"]
        tertiary_vec["input2"] << secondary_vec["output"]
        added_nodes.extend([aim_matrix0, aim_matrix1, aim_matrix_mid_space, primary_vec, secondary_vec, primary_vec])

        # creating mid matrix
        xform0_translate = nw.create_node("rowFromMatrix", "xform0_ws_translate")
        xform0_translate["matrix"] << control_inst0.container_node["worldMatrix"]
        xform0_translate["input"] = 3

        xform2_translate = nw.create_node("rowFromMatrix", "xform2_ws_translate")
        xform2_translate["matrix"] << control_inst2.container_node["worldMatrix"]
        xform2_translate["input"] = 3
        
        mid_matrix_translate_4x4 = nw.create_node("fourByFourMatrix", "mid_mat_ws_translate_4x4")

        for index, axis in enumerate(["X", "Y", "Z"]):
            average = nw.create_node("average", f"mid_mat_t{axis}")
            added_nodes.append(average)
            xform0_translate[f"output{axis}"] >> average["input"][0]
            xform2_translate[f"output{axis}"] >> average["input"][1]

            average["output"] >> mid_matrix_translate_4x4[f"in3{index}"]

        added_nodes.extend([xform0_translate, xform2_translate, mid_matrix_translate_4x4])

        # setting mid matrix
        aim_matrix_mid_space["inputMatrix"] << mid_matrix_translate_4x4["output"]
        aim_matrix_mid_space["primaryTargetMatrix"] << control_inst2.container_node["worldMatrix"]
        aim_matrix_mid_space["secondaryTargetMatrix"] << control_inst0.container_node["worldMatrix"]
        aim_matrix_mid_space["primaryInputAxis"] = [1, 0, 0]
        aim_matrix_mid_space["secondaryInputAxis"] = [0, 0, 1]
        aim_matrix_mid_space["secondaryTargetVector"] = [0, 0, 1]
        aim_matrix_mid_space["secondaryMode"] = 2

        aim_matrix_mid_space["outputMatrix"] >> control_inst1.container_node["offsetMatrix"]



        # xform0
        aim_matrix0["inputMatrix"] << control_inst0.container_node["worldMatrix"]
        aim_matrix0["primaryTargetMatrix"] << control_inst1.container_node["worldMatrix"]
        aim_matrix0["primaryInputAxis"] << primary_vec["output"]
        aim_matrix0["secondaryTargetMatrix"] << control_inst0.container_node["worldMatrix"]
        aim_matrix0["secondaryInputAxis"] << secondary_vec["output"]
        aim_matrix0["secondaryTargetVector"] = [0, 0, 1]
        aim_matrix0["secondaryMode"] = 2

        # xform0 inverse
        xform_matrix0_inv = nw.create_node("inverseMatrix", "xform0_inv_mat")
        xform_matrix0_inv["inputMatrix"] << aim_matrix0["outputMatrix"]
        added_nodes.append(xform_matrix0_inv)

        # connect to output xform
        self._set_output_xform_attrs(
            index = 0,
            output_xform_name=self.input_node[self.HIER_DATA.INPUT_XFORM][0][self.HIER_DATA.INPUT_XFORM_NAME],
            output_init_matrix=aim_matrix0["outputMatrix"],
            output_init_inv_matrix=xform_matrix0_inv["outputMatrix"],
            output_world_matrix=aim_matrix0["outputMatrix"],
            output_loc_matrix=aim_matrix0["outputMatrix"]
        )

        # xform1
        aim_matrix1["inputMatrix"] << control_inst1.container_node["worldMatrix"]
        aim_matrix1["primaryTargetMatrix"] << control_inst2.container_node["worldMatrix"]
        aim_matrix1["primaryInputAxis"] << primary_vec["output"]
        aim_matrix1["secondaryTargetMatrix"] << aim_matrix0["outputMatrix"]
        aim_matrix1["secondaryInputAxis"] << tertiary_vec["output"]
        aim_matrix1["secondaryTargetVector"] << tertiary_vec["output"]
        aim_matrix1["secondaryMode"] = 2

        # xform1 inverse
        xform_matrix1_inv = nw.create_node("inverseMatrix", "xform1_inv_mat")
        xform_matrix1_inv["inputMatrix"] << aim_matrix1["outputMatrix"]

        # xform1 loc
        xform_matrix1_loc = nw.create_node("multMatrix", "xform1_loc_mat")
        xform_matrix1_loc["matrixIn"][0] << aim_matrix1["outputMatrix"]
        xform_matrix1_loc["matrixIn"][1] << xform_matrix0_inv["outputMatrix"]
        added_nodes.extend([xform_matrix1_inv, xform_matrix1_loc])

        # xform1 connect to output xform
        self._set_output_xform_attrs(
            index = 1,
            output_xform_name=self.input_node[self.HIER_DATA.INPUT_XFORM][1][self.HIER_DATA.INPUT_XFORM_NAME],
            output_init_matrix=aim_matrix1["outputMatrix"],
            output_init_inv_matrix=xform_matrix1_inv["outputMatrix"],
            output_world_matrix=aim_matrix1["outputMatrix"],
            output_loc_matrix=xform_matrix1_loc["matrixSum"]
        )

        #xform2
        xform_matrix2_row0 = nw.create_node("rowFromMatrix", "xform2_row0_mat")
        xform_matrix2_row0["matrix"] << aim_matrix1["outputMatrix"]
        xform_matrix2_row1 = nw.create_node("rowFromMatrix", "xform2_row1_mat")
        xform_matrix2_row1["matrix"] << aim_matrix1["outputMatrix"]
        xform_matrix2_row1["input"] = 1
        xform_matrix2_row2 = nw.create_node("rowFromMatrix", "xform2_row2_mat")
        xform_matrix2_row2["matrix"] << aim_matrix1["outputMatrix"]
        xform_matrix2_row2["input"] = 2
        xform_matrix2_ws = nw.create_node("fourByFourMatrix", "xform2_ws_mat_4x4")

        for row_index, row_node in enumerate([xform_matrix2_row0, xform_matrix2_row1, xform_matrix2_row2, xform2_translate]):
            for col_index, axis in enumerate(["X", "Y", "Z", "W"]):
                xform_matrix2_ws[f"in{row_index}{col_index}"] << row_node[f"output{axis}"]

        # xform2 inverse
        xform_matrix2_inv = nw.create_node("inverseMatrix", "xform2_inv_mat")
        xform_matrix2_inv["inputMatrix"] << xform_matrix2_ws["output"]

        # xform2 loc
        xform_matrix2_loc = nw.create_node("multMatrix", "xform2_loc_mat")
        xform_matrix2_loc["matrixIn"][0] << xform_matrix2_ws["output"]
        xform_matrix2_loc["matrixIn"][1] << xform_matrix1_inv["outputMatrix"]
        added_nodes.extend([xform_matrix2_row0, xform_matrix2_row1, xform_matrix2_row2, xform_matrix2_ws, xform_matrix2_inv, xform_matrix2_loc])

        # xform2 connect to output xform
        self._set_output_xform_attrs(
            index = 2,
            output_xform_name=self.input_node[self.HIER_DATA.INPUT_XFORM][2][self.HIER_DATA.INPUT_XFORM_NAME],
            output_init_matrix=xform_matrix2_ws["output"],
            output_init_inv_matrix=xform_matrix2_inv["outputMatrix"],
            output_world_matrix=xform_matrix2_ws["output"],
            output_loc_matrix=xform_matrix2_loc["matrixSum"]
        )

        self.container_node.add_nodes(*added_nodes)