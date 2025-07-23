import utils.utils as utils
import utils.node_wrapper as nw
import system.component_enum as component_enum
import system.component_data as comp_data
import system.component as sys_component
import component.control as control
import component.setup as setup
import component.motion as motion

import maya.cmds as cmds

import importlib

importlib.reload(utils)
importlib.reload(nw)
importlib.reload(component_enum)
importlib.reload(comp_data)
importlib.reload(sys_component)
importlib.reload(control)
importlib.reload(setup)
importlib.reload(motion)

def containerSainityCheck():
    """
    Run several checks to make sure maya is setup to work with containers.
    There are a couple 'gotcha's' to look out for
    """

    # set 'use assets' OFF in the node editor
    cmds.nodeEditor('nodeEditorPanel1NodeEditorEd', e=True, useAssets=False)

    # set 'show at top' OFF in the channel box editor
    cmds.channelBox('mainChannelBox', e=True, containerAtTop=False)

    # set asset display is to 'under parent' 
    outliners = cmds.getPanel(typ='outlinerPanel')
    for outlinerPanel in outliners:
        cmds.outlinerEditor(outlinerPanel, e=True, showContainerContents=1)
        cmds.outlinerEditor(outlinerPanel, e=True, showContainedOnly=0)

class TestComponent(sys_component.Component):
    """

    """
    component_type = component_enum.ComponentTypes.setup
    # root_transform_name = "newRoot"
    has_hier_attrs = True
    
    def _get_input_node_attr_data(self) -> comp_data.NodeData:
        node_data = super()._get_input_node_attr_data()
        node_data.extend_attr_data(
            comp_data.AttrData(attr_name="testEnum", attr_publish=True, attr_type=component_enum.AxisEnums),
            comp_data.AttrData(attr_name="testInt", attr_publish=True, attr_type="Int"),
        )
        return node_data
    
    def build_component(self):
        super().build_component()

        # self.promote_attrs_to_cntrl(
        #     component_data.ControlAttrAttrNameData(
        #         "testEnum", 
        #         3,
        #         self.container_node[component_data.HierData.input_xform][0])
        #     , **utils.kwargs_to_dict(controlClass=control.Control2))

        # self.add_nodes(sys_component.control_setup_node("attr_1"), sys_component.control_setup_node("attr_2"))
        # self.rename_nodes()

        # print(self.instance_namespace)
        # print(self.short_namespace)
        # print(self.full_namespace)
        # print(self.class_namespace)

class TestComponent2(sys_component.Component):
    component_type = component_enum.ComponentTypes.setup
    root_transform_name = "newRoot"
    class_namespace = "newNamespace"
    has_hier_attrs = False

def test():
    containerSainityCheck()
    cmds.file(new=True, force=True)


    loc1 = nw.Node(cmds.spaceLocator()[0])

    # motion.FK()
    setup_inst = setup.Setup()
    setup_inst.create_component(
        num_xforms = 3
    )
    setup_inst.container_node["numXforms"] = 3
    return

    component_inst = TestComponent()
    component_inst.create_component(
        test_int = comp_data.ControlSetupData(
            ("test_int", "test_int_new"),
            ("test_enum", "new_name"),
            build_axis = component_enum.AxisEnums.neg_y,
            controlClass = control.CircleControl,
            instance_name = "test_int_settings",
            buildTranslate = [0, 1, 3],
            shape_color = component_enum.Colors.purple,
            lockTX=True,
            lockVis=True
        ),
        input_xform = [
            comp_data.ControlSetupData(
                control_class = control.DiamondWireControl,
                shape_color = component_enum.Colors.green,
                input_xform_name = "hip",
                input_world_matrix = utils.translate_to_matrix([3, 10, 0]),
            ),
            comp_data.ControlSetupData(
                control_class = control.AxisControl,
                input_xform_name = "knee",
                input_world_matrix = utils.translate_to_matrix([3, 5.5, 1]),
            ),
            comp_data.ControlSetupData(
                control_class = control.SphereControl,
                input_xform_name = "ankle",
                input_world_matrix = utils.translate_to_matrix([3, 1, 0]),
            ),
            comp_data.ControlSetupData(
                control_class = control.GimbalControl,
                input_xform_name = "ball",
                input_world_matrix = utils.translate_to_matrix([3, 0, 3]),
            ),
        ],
    )
