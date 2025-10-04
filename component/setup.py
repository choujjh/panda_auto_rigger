import system.base_component as base_comp
import system.component_data as component_data
import system.component_enum_data as component_enum_data
import component.control as control
import utils.utils as utils
import utils.node_wrapper as nw
from typing import Union

class Setup(base_comp.Hierarchy):
    """A Base class for setup autorigging components. Derived from Hierarchy"""
    root_transform_name = "setup"
    component_type = component_enum_data.ComponentType.setup
    class_namespace = "setup_"

    _LOC_SCALE = "locScale"
    _IN_SET_XFORM_FOLLOW_INDEX = "settingXformFollowIndex"
    _IN_SET_CNTRL_LOC_MAT = "inputSettingCntrlLocMatrix"
    _OUT_SET_CNTRL_LOC_MAT = "outputSettingCntrlLocMatrix"

    def _input_attr_build_data(self):
        node_data = super()._input_attr_build_data()
        node_data.extend_attr_data(
            component_data.AttrData(self._LOC_SCALE, type_="double", parent=self._IN, value=1, min=0.1),
            component_data.AttrData(self._IN_SET_XFORM_FOLLOW_INDEX, type_="long", parent=self._IN, min=0),
            component_data.AttrData(self._IN_SET_CNTRL_LOC_MAT, type_="matrix", parent=self._IN),
        )
        return node_data
    def _output_attr_build_data(self):
        node_data = super()._output_attr_build_data()
        node_data.extend_attr_data(
            component_data.AttrData(self._OUT_SET_CNTRL_LOC_MAT, type_="matrix", parent=self._OUT),
        )

        return node_data

    def _override_build(self, control_color=None, **kwargs):
        input_xforms = self.get_xform_attrs(xform_type=self.IO_ENUM.input)
        for index, input_xform in input_xforms.items():
            # creating control
            control_inst = control.Locator.create(instance_name=input_xform.xform_name, parent=self, color=control_color, xform_map_index=index)
            control_container = control_inst.container_node
            control_container[control_inst._LOC_SCALE] << self.input_node[self._LOC_SCALE]
            utils.Matrix.translate_matrix(0, index*1.5, 0).set_transform(control_inst.transform_node, world_space=True)
            if input_xform.init_matrix.value is not None:
                utils.Matrix(input_xform.init_matrix).set_transform(control_inst.transform_node, world_space=True)
                
            # connecting to output
            self._set_xform_attrs(
                index=index,
                xform_type=self.IO_ENUM.output,
                xform=self.XFORM(
                    init_matrix=control_container[base_comp.Control._OUT_WS_MAT],
                    world_matrix=control_container[base_comp.Control._OUT_WS_MAT],
                )
            )
    def _post_build(self, **post_build_kwargs):
        if not self.container_node[self._OUT_SET_CNTRL_LOC_MAT].has_src_connection():
            self.container_node[self._IN_SET_CNTRL_LOC_MAT] >> self.container_node[self._OUT_SET_CNTRL_LOC_MAT]
        super()._post_build(**post_build_kwargs)
    def get_as_source_xforms(self, is_parent_component=True):
        xforms = super().get_as_source_xforms(is_parent_component)
        for xform in xforms:
            xform.init_matrix = xform.world_matrix
            xform.init_inv_matrix = xform.world_inv_matrix
        return xforms
class SimpleLimb(Setup):
    """3 xform that aim and align to each other. middle xform stays inbetween and orients correctly to whatever the angle the other 2 xform make"""        
    _max_num_xforms = (3, 3)
    
    def _override_build(self, control_color, **kwargs):
        input_xforms = self.get_xform_attrs(xform_type=self.IO_ENUM.input)
        
        # creating controls
        # control 0
        control_inst0 = control.Locator.create(
            instance_name=self.input_node[self.HIER_DATA.INPUT_XFORM][0][self.HIER_DATA.INPUT_XFORM_NAME], 
            parent=self, 
            color=control_color,
            xform_map_index=0,)
        control_inst0.transform_node["ty"] = 8
        control_inst0.container_node[control_inst0._LOC_SCALE] << self.container_node[self._LOC_SCALE]
        for attr in ["rz","sx","sy","sz"]:
            control_inst0.transform_node[attr].set_locked(True)
            control_inst0.transform_node[attr].set_keyable(False)
        if input_xforms[0].init_matrix.value is not None:
            input_xforms[0].init_matrix.value.set_transform(control_inst0.transform_node, world_space=True)
        # control 1
        control_inst1 = control.Locator.create(
            instance_name=self.input_node[self.HIER_DATA.INPUT_XFORM][1][self.HIER_DATA.INPUT_XFORM_NAME], 
            parent=self, 
            color=control_color,
            xform_map_index=1,)
        control_inst1.transform_node["tz"] = 1
        control_inst1.container_node[control_inst1._LOC_SCALE] << self.container_node[self._LOC_SCALE]
        for attr in ["ty","rx","ry","rz","sx","sy","sz"]:
            control_inst1.transform_node[attr].set_locked(True)
            control_inst1.transform_node[attr].set_keyable(False)
        if input_xforms[1].loc_matrix.value is not None:
            input_xforms[1].loc_matrix.value.set_transform(control_inst1.transform_node)
        # control 2
        control_inst2_translate = control.Sphere.create(
            instance_name=self.input_node[self.HIER_DATA.INPUT_XFORM][2][self.HIER_DATA.INPUT_XFORM_NAME], 
            parent=self, 
            build_s=0.4, 
            color=control_color,
            xform_map_index=2)
        for attr in ["rx","ry","rz","sx","sy","sz"]:
            control_inst2_translate.transform_node[attr].set_locked(True)
            control_inst2_translate.transform_node[attr].set_keyable(False)
        control_inst2_orient = control.Locator.create(
            instance_name="xform2Orient", 
            parent=self, 
            color=control_color,
            xform_map_index=2)
        for attr in ["tx","ty","tz","sx","sy","sz"]:
            control_inst2_orient.transform_node[attr].set_locked(True)
            control_inst2_orient.transform_node[attr].set_keyable(False)
        if input_xforms[2].init_matrix.value is not None:
            init_matrix = utils.Matrix(input_xforms[2].init_matrix)
            control_inst2_translate.transform_node["translate"] = utils.Matrix(init_matrix).translate
        control_inst2_orient.container_node[control_inst2_orient._LOC_SCALE] << self.container_node[self._LOC_SCALE]

        # mid interp matrix
        mid_interp_matrix, xform2_translate = self.__create_mid_interp_matrix(
            control_inst0.container_node[base_comp.Control._OUT_WS_MAT], 
            control_inst2_translate.container_node[base_comp.Control._OUT_WS_MAT])
        control_inst1.container_node[base_comp.Control._IN_OFF_MAT] << mid_interp_matrix

        # xform0
        xform0_ws_mat_attr, xform0_inv_attr = self.__create_xform0(
            guide_transform0_ws_mat=control_inst0.container_node[base_comp.Control._OUT_WS_MAT], 
            guide_transform1_ws_mat=control_inst1.container_node[base_comp.Control._OUT_WS_MAT])

        # xform1
        xform1_ws_mat_attr, xform1_inv_attr = self.__create_xform1(
            guide_transform1_ws_mat=control_inst1.container_node[base_comp.Control._OUT_WS_MAT], 
            guide_transform2_ws_mat=control_inst2_translate.container_node[base_comp.Control._OUT_WS_MAT],
            xform0_ws_mat=xform0_ws_mat_attr,
            xform0_inv_mat=xform0_inv_attr)
        
        # xform2
        self.__create_xform2(
            xform1_ws_mat=xform1_ws_mat_attr, 
            xform2_translate=xform2_translate, 
            xform2_orient=control_inst2_orient.transform_node,
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
    def __create_xform0(self, guide_transform0_ws_mat:nw.Attr, guide_transform1_ws_mat:nw.Attr):
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
        aim_node["primaryInputAxis"] << self.container_node[self._PRM_VEC]
        aim_node["secondaryTargetMatrix"] << guide_transform0_ws_mat
        aim_node["secondaryInputAxis"] << self.container_node[self._SEC_VEC]
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
        self._set_xform_attrs(
            index = 0,
            xform_type=self.IO_ENUM.output,
            xform=self.XFORM(
                init_matrix=pick_mat["outputMatrix"],
                init_inv_matrix=mat_inv["outputMatrix"],
                world_matrix=pick_mat["outputMatrix"],
                loc_matrix=pick_mat["outputMatrix"]
            )
        )

        self.container_node.add_nodes(aim_node, pick_mat, mat_inv)
        return pick_mat["outputMatrix"], mat_inv["outputMatrix"]
    def __create_xform1(self, guide_transform1_ws_mat:nw.Attr, guide_transform2_ws_mat:nw.Attr, xform0_ws_mat:nw.Attr,  xform0_inv_mat:nw.Attr):
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
        aim_node["primaryInputAxis"] << self.container_node[self._PRM_VEC]
        aim_node["secondaryTargetMatrix"] << xform0_ws_mat
        aim_node["secondaryInputAxis"] << self.container_node[self._TER_VEC]
        aim_node["secondaryTargetVector"] << self.container_node[self._TER_VEC]
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
        self._set_xform_attrs(
            index = 1,
            xform_type=self.IO_ENUM.output,
            xform = self.XFORM(
                init_matrix=pick_mat["outputMatrix"],
                init_inv_matrix=mat_inv["outputMatrix"],
                world_matrix=pick_mat["outputMatrix"],
                loc_matrix=mat_loc["matrixSum"]
            )
        )

        self.container_node.add_nodes(aim_node, mat_inv, pick_mat, mat_loc)
        return pick_mat["outputMatrix"], mat_inv["outputMatrix"]
    def __create_xform2(self, xform1_ws_mat:nw.Attr, xform2_translate:nw.Node, xform2_orient:nw.Node, xform1_inv_mat:nw.Attr):
        """Creates all xform2 nodes

        Args:
            xform1_ws_mat (nw.Attr): xform1 world space matrix
            xform2_translate (nw.Node): node for xform2 translate
            xform2_orient (nw.Node): node for xform2 orient
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

        xform2_pick_scale_mat = nw.create_node("pickMatrix", "xform2_scale_mat")
        xform2_pick_scale_mat["inputMatrix"] << self.transform_node["worldMatrix"][0]
        xform2_pick_scale_mat["useTranslate"] = 0
        xform2_pick_scale_mat["useRotate"] = 0
        xform2_pick_scale_mat["useShear"] = 0
        xform2_mult_mat = nw.create_node("multMatrix", "xform2_orient_ws")
        xform2_mult_mat["matrixIn"][0] << xform2_pick_scale_mat["outputMatrix"]
        xform2_mult_mat["matrixIn"][1] << xform_matrix2_ws["output"]
        xform2_mult_mat["matrixIn"][2] << self.transform_node["worldInverseMatrix"][0]

        # connect to xform2 orient parent offset matrix
        xform2_mult_mat["matrixSum"] >> xform2_orient["offsetParentMatrix"]

        
        xform_pick_mat = nw.create_node("pickMatrix", "xform2_pick_no_scale")
        xform_pick_mat["inputMatrix"] << xform2_orient["worldMatrix"][0]
        xform_pick_mat["useScale"] = 0

        # xform2 loc
        xform_matrix2_loc = nw.create_node("multMatrix", "xform2_loc_mat")
        xform_matrix2_loc["matrixIn"][0] << xform_pick_mat["outputMatrix"]
        xform_matrix2_loc["matrixIn"][1] << xform1_inv_mat

        # xform2 connect to output xform
        self._set_xform_attrs(
            index=2,
            xform_type=self.IO_ENUM.output,
            xform=self.XFORM(
                init_matrix=xform_pick_mat["outputMatrix"],
                world_matrix=xform_pick_mat["outputMatrix"],
                loc_matrix=xform_matrix2_loc["matrixSum"]
            )
        )
        self.container_node.add_nodes(xform_matrix2_ws, xform_matrix2_loc, xform2_pick_scale_mat, xform2_mult_mat, xform_pick_mat)
class Mirror(Setup):
    """Class that mirrors all xforms given"""
    root_transform_name = None

    _IN_MIRROR_AXIS = "mirrorAxis"
    _IN_AXIS_SCALAR = "AxisScalar"
    _IN_NEG_AXIS_SCALAR = "negAxisScalar"
    _IN_MIRROR_MAT = "mirrorMatrix"
    _KWG_MIRROR_AXIS = "mirror_axis"

    @classmethod
    def create(cls, instance_name = None, parent = None, input_xforms:Union[list[component_data.Xform], int]=[], mirror_axis:Union[component_enum_data.AxisEnum, nw.Attr]=component_enum_data.AxisEnum.x, source_component = None, connect_hierarchy = True, connect_axis_vecs = True, control_color=None):
        setup_inst = super().create(instance_name, parent, input_xforms, source_component, connect_hierarchy, connect_axis_vecs, control_color)
        if isinstance(mirror_axis, nw.Attr):
            setup_inst.container_node[cls._IN_MIRROR_AXIS] << mirror_axis
        else:
            setup_inst.container_node[cls._IN_MIRROR_AXIS] = mirror_axis.name
        return setup_inst

    def _input_attr_build_data(self):
        node_data = super()._input_attr_build_data()
        node_data.extend_attr_data(
            component_data.AttrData(self._IN_MIRROR_AXIS, type_=component_enum_data.AxisEnum.x, parent=self._IN),
            component_data.AttrData(self._IN_AXIS_SCALAR, type_="float", value=1, locked=True, parent=self._IN),
            component_data.AttrData(self._IN_NEG_AXIS_SCALAR, type_="float", value=-1, locked=True, parent=self._IN),
            component_data.AttrData(self._IN_MIRROR_MAT, type_="matrix", parent=self._IN),
        )
        return node_data

    def _override_build(self, control_color=None, **kwargs):
        self.__create_mirror_scale_matrix()
        

        added_nodes = []
        input_xforms = self.get_xform_attrs(xform_type=self.IO_ENUM.input)
        for index, input_xform in input_xforms.items():
            mult_mat = nw.create_node("multMatrix", f"xform{index}_ws")
            mult_mat["matrixIn"][0] << input_xform.init_matrix
            mult_mat["matrixIn"][1] << self.container_node[self._IN_MIRROR_MAT]

            pick_mat = nw.create_node("pickMatrix", f"xform{index}_noScale")
            pick_mat["inputMatrix"] << mult_mat["matrixSum"]
            pick_mat["useScale"] = False
            pick_mat["useShear"] = False

            aim_mat = nw.create_node("aimMatrix", f"xform{index}_realign")
            for attr in ["inputMatrix", "primaryTargetMatrix", "secondaryTargetMatrix"]:
                aim_mat[attr] << pick_mat["outputMatrix"]
            aim_mat["primaryTargetVector"] = [-1, 0, 0]
            aim_mat["secondaryTargetVector"] = [0, -1, 0]
            for attr in ["primaryMode", "secondaryMode"]:
                aim_mat[attr] = 1

            self._set_xform_attrs(
                index=index,
                xform_type=self.IO_ENUM.output,
                xform = self.XFORM(
                    xform_name=input_xform.xform_name,
                    init_matrix=mult_mat["matrixSum"],
                    world_matrix=aim_mat["outputMatrix"]
                )
            )
            added_nodes.extend([mult_mat, pick_mat, aim_mat])

        # mirroring settings
        settings_mult_mat = nw.create_node("multMatrix", "settings_guide_mirror")
        settings_mult_mat["matrixIn"][0].set(utils.Matrix.scale_matrix(-1, -1, -1))
        settings_mult_mat["matrixIn"][1] << self.container_node[self._IN_SET_CNTRL_LOC_MAT]
        settings_mult_mat["matrixIn"][2].set(utils.Matrix.scale_matrix(-1, -1, -1))

        # settings_pick_mat = nw.create_node("pickMatrix", "settings_guide_mirror_noScale")
        # settings_pick_mat["inputMatrix"] << settings_mult_mat["matrixSum"]
        # settings_pick_mat["useScale"] = False
        # settings_pick_mat["useShear"] = False

        # settings_aim_mat = nw.create_node("aimMatrix", f"settings_xform{index}_realign")
        # for attr in ["inputMatrix", "primaryTargetMatrix", "secondaryTargetMatrix"]:
        #     settings_aim_mat[attr] << settings_mult_mat["matrixSum"]
        # settings_aim_mat["primaryTargetVector"] = [-1, 0, 0]
        # settings_aim_mat["secondaryTargetVector"] = [0, -1, 0]
        # for attr in ["primaryMode", "secondaryMode"]:
        #     settings_aim_mat[attr] = 1
        
        # settings_aim_mat["outputMatrix"] >> self.container_node[self._OUT_SET_CNTRL_LOC_MAT]
        settings_mult_mat["matrixSum"] >> self.container_node[self._OUT_SET_CNTRL_LOC_MAT]

        self.container_node.add_nodes(*added_nodes, settings_mult_mat)

    def __create_mirror_scale_matrix(self):
        """Creates mirror scale matrix from axis"""
        x_choice = nw.create_node("choice", "xScalar")
        y_choice = nw.create_node("choice", "YScalar")
        z_choice = nw.create_node("choice", "ZScalar")
        for axis_enum_index, axis in enumerate(component_enum_data.AxisEnum):
            axis_vec = axis.value
            for axis_index, choice_node in enumerate([x_choice, y_choice, z_choice]):
                if abs(axis_vec[axis_index]) < 0.001:
                    choice_node["input"][axis_enum_index] << self.container_node[self._IN_AXIS_SCALAR]
                else:
                    choice_node["input"][axis_enum_index] << self.container_node[self._IN_NEG_AXIS_SCALAR]
        scale_matrix = nw.create_node("fourByFourMatrix", "scaleMat4x4")
        scale_matrix["output"] >> self.container_node[self._IN_MIRROR_MAT]
        x_choice["output"] >> scale_matrix["in00"]
        x_choice["selector"] << self.container_node[self._IN_MIRROR_AXIS]
        y_choice["output"] >> scale_matrix["in11"]
        y_choice["selector"] << self.container_node[self._IN_MIRROR_AXIS]
        z_choice["output"] >> scale_matrix["in22"]
        z_choice["selector"] << self.container_node[self._IN_MIRROR_AXIS]

        self.container_node.add_nodes(x_choice, y_choice, z_choice, scale_matrix)