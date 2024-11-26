import utils.utils as utils
import utils.node_wrapper as nw
import system.component_enum as component_enum
import system.component_data as component_data
import system.component as sys_component
import component.control as control

import maya.cmds as cmds

import importlib

importlib.reload(utils)
importlib.reload(nw)
importlib.reload(component_enum)
importlib.reload(component_data)
importlib.reload(sys_component)
importlib.reload(control)

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
    component_type = component_enum.ComponentTypes.setup
    root_transform_name = "newRoot"
    has_hier_attrs = True
    
    def _get_input_node_attr_data(self) -> component_data.NodeData:
        node_data = super()._get_input_node_attr_data()
        node_data.extend_attr_data(
            component_data.AttrData(attr_name="testEnum", attr_publish=True, attr_type=component_enum.AxisEnums)
        )
        return node_data
    
    def build_component(self):
        super().build_component()

        self.promote_attr(self.container_node["testEnum"], self.container_node[component_data.HierData.input_xform][0], **utils.kwarg_to_dict(controlClass=control.Control2))

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
    loc2 = nw.Node(cmds.spaceLocator()[0])
    loc3 = nw.Node(cmds.spaceLocator()[0])
    component_inst = TestComponent()
    component_inst.create_component(
        input_xform = [
            utils.kwarg_to_dict(
                input_xform_name = "hip",
                input_world_matrix = loc1["worldMatrix"][0],
                input_init_matrix = loc1["worldMatrix"][0],
            ),
            utils.kwarg_to_dict(
                input_xform_name = "knee",
                input_world_matrix = loc1["worldMatrix"][0],
                input_init_matrix = loc1["worldMatrix"][0],
            ),
            utils.kwarg_to_dict(
                input_xform_name = "ankle",
                input_world_matrix = loc1["worldMatrix"][0],
                input_init_matrix = loc1["worldMatrix"][0],
            ),
            utils.kwarg_to_dict(
                input_xform_name = "ball",
                input_world_matrix = loc1["worldMatrix"][0],
                input_init_matrix = loc1["worldMatrix"][0],
            ),
        ],
        test_enum = component_enum.AxisEnums.neg_z,
    )
    # component_inst.insert_component(
    #     TestComponent2
    # )
    component_inst.container_node[component_data.HierData.output_xform][0][component_data.HierData.output_world_matrix] >> loc2["offsetParentMatrix"]
    component_inst.container_node[component_data.HierData.output_xform][1][component_data.HierData.output_world_matrix] >> loc3["offsetParentMatrix"]

