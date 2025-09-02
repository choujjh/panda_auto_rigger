import system.base_component as base_comp
import system.component_data as component_data
import system.component_enum_data as component_enum_data
import component.control as control
import utils.utils as utils
import utils.node_wrapper as nw
import component.enum_manager as enum_manager

class Setup(base_comp.Hierarchy):
    """A Base class for setup autorigging components. Derived from Hierarchy"""
    root_transform_name = "setup"
    component_type = component_enum_data.ComponentType.setup
    class_namespace = "setup_"

    _IN_PRMY_AXIS = "primaryAxis"
    _IN_SEC_AXIS = "secondaryAxis"
    _LOC_SCALE = "locScale"
    _HIER_SIDE = "hierSide"
    _KWG_NUM_XFORMS = "num_xforms"
    _KWG_PRMY_AXIS = "primary_axis"
    _KWG_SEC_AXIS = "secondary_axis"
    _KWG_HIER_SIDE = "hier_side"

    def _get_input_node_build_attr_data(self):
        node_data = super()._get_input_node_build_attr_data()
        node_data.extend_attr_data(
            component_data.AttrData(self._HIER_SIDE, type_=component_enum_data.CharacterSide.none, parent=self._IN),
            component_data.AttrData(self._IN_PRMY_AXIS, type_=component_enum_data.AxisEnum.x, publish=True),
            component_data.AttrData(self._IN_SEC_AXIS, type_=component_enum_data.AxisEnum.y, publish=True),
            component_data.AttrData(self._LOC_SCALE, type_="double", publish=True, value=1, min=0.1),
        )
        return node_data
    def _get_output_node_build_attr_data(self):
        node_data = super()._get_output_node_build_attr_data()
        node_data.extend_attr_data(
            component_data.AttrData(self._PRM_VEC, type_="double3", parent=self._OUT),
            component_data.AttrData(self._PRM_VEC_X, type_="double", parent=self._PRM_VEC),
            component_data.AttrData(self._PRM_VEC_Y, type_="double", parent=self._PRM_VEC),
            component_data.AttrData(self._PRM_VEC_Z, type_="double", parent=self._PRM_VEC),
            component_data.AttrData(self._SEC_VEC, type_="double3", parent=self._OUT),
            component_data.AttrData(self._SEC_VEC_X, type_="double", parent=self._SEC_VEC),
            component_data.AttrData(self._SEC_VEC_Y, type_="double", parent=self._SEC_VEC),
            component_data.AttrData(self._SEC_VEC_Z, type_="double", parent=self._SEC_VEC),
            component_data.AttrData(self._TER_VEC, type_="double3", parent=self._OUT),
            component_data.AttrData(self._TER_VEC_X, type_="double", parent=self._TER_VEC),
            component_data.AttrData(self._TER_VEC_Y, type_="double", parent=self._TER_VEC),
            component_data.AttrData(self._TER_VEC_Z, type_="double", parent=self._TER_VEC),
        )
        return node_data

    @classmethod
    def create(
        cls, 
        instance_name=None, 
        parent=None, 
        num_xforms=3, 
        control_color=None,
        hier_side:component_enum_data.CharacterSide=component_enum_data.CharacterSide.none,
        primary_axis:component_enum_data.MayaEnumAttr=component_enum_data.AxisEnum.x, 
        secondary_axis:component_enum_data.MayaEnumAttr=component_enum_data.AxisEnum.y, 
        **kwargs):

        kwargs[cls._KWG_NUM_XFORMS] = num_xforms
        kwargs[cls._KWG_PRMY_AXIS] = primary_axis
        kwargs[cls._KWG_SEC_AXIS] = secondary_axis
        kwargs[cls._KWG_CNTRL_CLR] = control_color

        component_inst = cls()
        component_inst._pre_build(instance_name=instance_name, hier_side=hier_side, parent=parent)
        component_inst._override_build(**kwargs)
        component_inst._post_build()

        return component_inst
    
    def _pre_build(self, instance_name=None, hier_side=component_enum_data.CharacterSide.none,  parent=None):
        super()._pre_build(instance_name, parent)
        self.input_node[self._HIER_SIDE]=hier_side.name

    def _override_build(self, **kwargs):
        num_xforms = kwargs[self._KWG_NUM_XFORMS]
        control_color = kwargs[self._KWG_CNTRL_CLR]

        self.container_node[self._IN_PRMY_AXIS] = component_enum_data.get_index_of_item(kwargs[self._KWG_PRMY_AXIS])
        self.container_node[self._IN_SEC_AXIS] = component_enum_data.get_index_of_item(kwargs[self._KWG_SEC_AXIS])

        input_xforms = self._get_input_xform_attrs(utils.length_index_list(num_xforms))
        for index, input_xform in input_xforms.items():

            # setting name
            input_xform[self.HIER_DATA.INPUT_XFORM_NAME].set(f"xform{index}")

            # creating control
            control_inst = control.Locator.create(instance_name=input_xform[self.HIER_DATA.INPUT_XFORM_NAME], parent=self, color=control_color)
            control_container = control_inst.container_node
            control_container[control_inst._LOC_SCALE] << self.input_node[self._LOC_SCALE]
            control_container[base_comp.Control._IN_OFF_MAT] = utils.translate_to_matrix([0, index*1.5, 0])

            # connecting to output
            self._set_output_xform_attrs(
                index,
                output_init_matrix=control_container[base_comp.Control._OUT_WS_MAT],
                output_world_matrix=control_container[base_comp.Control._OUT_WS_MAT],
            )
        
class SimpleLimb(Setup):
    """3 xform that aim and align to each other. middle xform stays inbetween and orients correctly to whatever the angle the other 2 xform make"""

    _IN_SET_CNTRL_XFORM_FOLLOW = "settingCntrlXformFollow"
    _IN_SET_CNTRL_LOC_MAT = "inputSettingCntrlLocMatrix"
    _OUT_SET_CNTRL_LOC_MAT = "outputSettingCntrlLocMatrix"

    def _get_input_node_build_attr_data(self):
        node_data = super()._get_input_node_build_attr_data()
        node_data.extend_attr_data(
            component_data.AttrData(self._IN_SET_CNTRL_XFORM_FOLLOW, type_="long", publish=True, min=0, max=2, value=2),
            component_data.AttrData(self._IN_SET_CNTRL_LOC_MAT, type_="matrix", publish=True),
        )

        return node_data
    
    def _get_output_node_build_attr_data(self):
        node_data = super()._get_output_node_build_attr_data()
        node_data.extend_attr_data(
            component_data.AttrData(self._OUT_SET_CNTRL_LOC_MAT, type_="matrix", publish=True),
        )

        return node_data
        

    @classmethod
    def create(
        cls, 
        instance_name=None, 
        parent=None, 
        control_color=None,
        hier_side:component_enum_data.CharacterSide=component_enum_data.CharacterSide.none,
        primary_axis:component_enum_data.MayaEnumAttr=component_enum_data.AxisEnum.x, 
        secondary_axis:component_enum_data.MayaEnumAttr=component_enum_data.AxisEnum.y, 
        **kwargs):

        kwargs[cls._KWG_PRMY_AXIS] = primary_axis
        kwargs[cls._KWG_SEC_AXIS] = secondary_axis
        kwargs[cls._KWG_CNTRL_CLR] = control_color
        component_inst = super().create(instance_name=instance_name, hier_side=hier_side, parent=parent, **kwargs)
        return component_inst
    
    def _override_build(self, **kwargs):
        control_color = kwargs[self._KWG_CNTRL_CLR]

        self.container_node[self._IN_PRMY_AXIS] = component_enum_data.get_index_of_item(kwargs[self._KWG_PRMY_AXIS])
        self.container_node[self._IN_SEC_AXIS] = component_enum_data.get_index_of_item(kwargs[self._KWG_SEC_AXIS])

        input_xforms = self._get_input_xform_attrs(utils.length_index_list(3))
        for index, input_xform in input_xforms.items():
            input_xform[self.HIER_DATA.INPUT_XFORM_NAME].set(f"xform{index}")

        # creating controls
        control_inst0 = control.Locator.create(
            instance_name=self.input_node[self.HIER_DATA.INPUT_XFORM][0][self.HIER_DATA.INPUT_XFORM_NAME], 
            parent=self, color=control_color)
        control_inst0.transform_node["ty"] = 8
        control_inst0.container_node[control_inst0._LOC_SCALE] << self.container_node[self._LOC_SCALE]
        for attr in ["rz","sx","sy","sz"]:
            control_inst0.transform_node[attr].set_locked(True)
            control_inst0.transform_node[attr].set_keyable(False)
        control_inst1 = control.Locator.create(
            instance_name=self.input_node[self.HIER_DATA.INPUT_XFORM][1][self.HIER_DATA.INPUT_XFORM_NAME], 
            parent=self, color=control_color)
        control_inst1.transform_node["tz"] = 1
        control_inst1.container_node[control_inst1._LOC_SCALE] << self.container_node[self._LOC_SCALE]
        for attr in ["ty","rx","ry","rz","sx","sy","sz"]:
            control_inst1.transform_node[attr].set_locked(True)
            control_inst1.transform_node[attr].set_keyable(False)
        control_inst2_translate = control.Sphere.create(
            instance_name=self.input_node[self.HIER_DATA.INPUT_XFORM][2][self.HIER_DATA.INPUT_XFORM_NAME], 
            parent=self, build_s=0.4, color=control_color)
        for attr in ["rx","ry","rz","sx","sy","sz"]:
            control_inst2_translate.transform_node[attr].set_locked(True)
            control_inst2_translate.transform_node[attr].set_keyable(False)
        control_inst2_orient = control.Locator.create(
            instance_name="xform2Orient", parent=self, 
            color=control_color)
        for attr in ["tx","ty","tz","sx","sy","sz"]:
            control_inst2_orient.transform_node[attr].set_locked(True)
            control_inst2_orient.transform_node[attr].set_keyable(False)
        control_inst2_orient.container_node[control_inst2_orient._LOC_SCALE] << self.container_node[self._LOC_SCALE]

        char_component = self.get_parent_type_component(component_enum_data.ComponentType.character)
        if char_component is None:
            raise ValueError("character component not found")
        # axis vectors
        primary_vec = char_component.axis_vec_choice_node(choice_node_name="primary_vec", enum_attr=self.container_node[self._IN_PRMY_AXIS])
        primary_vec["output"] >> self.container_node[self._PRM_VEC]
        secondary_vec = char_component.axis_vec_choice_node(choice_node_name="secondary_vec", enum_attr=self.container_node[self._IN_SEC_AXIS])
        secondary_vec["output"] >> self.container_node[self._SEC_VEC]
        tertiary_vec = nw.create_node("crossProduct", "tertiary_vec")
        tertiary_vec["input1"] << primary_vec["output"]
        tertiary_vec["input2"] << secondary_vec["output"]
        tertiary_vec["output"] >> self.container_node[self._TER_VEC]
        self.container_node.add_nodes(primary_vec, secondary_vec, tertiary_vec)

        # mid interp matrix
        mid_interp_matrix, xform2_translate = self.__create_mid_interp_matrix(
            control_inst0.container_node[base_comp.Control._OUT_WS_MAT], 
            control_inst2_translate.container_node[base_comp.Control._OUT_WS_MAT])
        control_inst1.container_node[base_comp.Control._IN_OFF_MAT] << mid_interp_matrix

        # xform0
        xform0_ws_mat_attr, xform0_inv_attr = self.__create_xform0(
            guide_transform0_ws_mat=control_inst0.container_node[base_comp.Control._OUT_WS_MAT], 
            guide_transform1_ws_mat=control_inst1.container_node[base_comp.Control._OUT_WS_MAT], 
            primary_vec=primary_vec["output"], 
            secondary_vec=secondary_vec["output"])

        # xform1
        xform1_ws_mat_attr, xform1_inv_attr = self.__create_xform1(
            guide_transform1_ws_mat=control_inst1.container_node[base_comp.Control._OUT_WS_MAT], 
            guide_transform2_ws_mat=control_inst2_translate.container_node[base_comp.Control._OUT_WS_MAT],
            xform0_ws_mat=xform0_ws_mat_attr,
            xform0_inv_mat=xform0_inv_attr,
            primary_vec=primary_vec["output"],
            tertiary_vec=tertiary_vec["output"])
        
        # xform2
        self.__create_xform2(
            xform1_ws_mat=xform1_ws_mat_attr, 
            xform2_translate=xform2_translate, 
            xform2_orient=control_inst2_orient.transform_node,
            xform1_inv_mat=xform1_inv_attr)
        
        #guide xform
        settings_cntrl_inst = control.Locator.create(instance_name="settingsGuide", parent=self, color=control_color)
        choice_node = nw.create_node("choice", "settings_cntrl_xform_choice")
        xform_attrs = self._get_output_xform_attrs()
        for index, attr in enumerate(xform_attrs.values()):
            matrix_src = attr[self.HIER_DATA.OUTPUT_INIT_MATRIX].get_src_connection()
            choice_node["input"][index] << matrix_src
        choice_node["selector"] << self.container_node[self._IN_SET_CNTRL_XFORM_FOLLOW]
        settings_cntrl_inst.transform_node["t"] = utils.list_mult(self.container_node[self._SEC_VEC].value, -2.5)
        rot_vec = utils.Vector([0, 1, 0]) ^ utils.Vector(self.container_node[self._TER_VEC].value)
        settings_cntrl_inst.transform_node["r"] = rot_vec * 90
        settings_cntrl_inst.transform_node["s"] = [0.7, 0.7, 0.7]
        settings_cntrl_inst.promote_attr_to_keyable(self.container_node[self._IN_SET_CNTRL_XFORM_FOLLOW])
        
        settings_cntrl_inst.container_node[base_comp.Control._IN_OFF_MAT] << choice_node["output"]
        settings_cntrl_inst.container_node[base_comp.Control._OUT_LOC_MAT] >> self.container_node[self._OUT_SET_CNTRL_LOC_MAT]
        self.container_node.add_nodes(choice_node)

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
        self._set_output_xform_attrs(
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
        self._set_output_xform_attrs(
            index = 1,
            output_init_matrix=pick_mat["outputMatrix"],
            output_init_inv_matrix=mat_inv["outputMatrix"],
            output_world_matrix=pick_mat["outputMatrix"],
            output_loc_matrix=mat_loc["matrixSum"]
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
        xform_matrix2_ws["output"] >> xform2_orient["offsetParentMatrix"]

        # xform2 loc
        xform_matrix2_loc = nw.create_node("multMatrix", "xform2_loc_mat")
        xform_matrix2_loc["matrixIn"][0] << xform2_orient["worldMatrix"][0]
        xform_matrix2_loc["matrixIn"][1] << xform1_inv_mat

        # xform2 connect to output xform
        self._set_output_xform_attrs(
            index = 2,
            output_init_matrix=xform2_orient["worldMatrix"][0],
            output_init_inv_matrix=xform2_orient["worldInverseMatrix"][0],
            output_world_matrix=xform2_orient["worldMatrix"][0],
            output_loc_matrix=xform_matrix2_loc["matrixSum"]
        )
        self.container_node.add_nodes(xform_matrix2_ws, xform_matrix2_loc)
