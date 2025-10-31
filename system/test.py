import utils.om as om
import utils.utils as utils
import utils.node_wrapper as nw
import system.component_enum_data as component_enum_data
import system.component_data as component_data
import system.base_component as base_comp
import component.enum_manager as enum_manager
import component.control as control
import component.matrix as matrix
import component.setup as setup
import component.motion as motion
import component.misc as misc
import component.anim as anim
import component.character as character

import maya.cmds as cmds
import importlib

importlib.reload(om)
importlib.reload(utils)
importlib.reload(nw)
importlib.reload(component_enum_data)
importlib.reload(component_data)
importlib.reload(base_comp)
importlib.reload(enum_manager)
importlib.reload(control)
importlib.reload(matrix)
importlib.reload(setup)
importlib.reload(motion)
importlib.reload(misc)
importlib.reload(anim)
importlib.reload(character)


def containerSainityCheck():
    """
    Run several checks to make sure maya is setup to work with containers.
    There are a couple 'gotcha's' to look out for
    """

    # set 'use assets' OFF in the node editor
    cmds.nodeEditor("nodeEditorPanel1NodeEditorEd", e=True, useAssets=False)

    # set 'show at top' OFF in the channel box editor
    cmds.channelBox("mainChannelBox", e=True, containerAtTop=False)

    # set asset display is to 'under parent'
    outliners = cmds.getPanel(typ="outlinerPanel")
    for outlinerPanel in outliners:
        cmds.outlinerEditor(outlinerPanel, e=True, showContainerContents=1)
        cmds.outlinerEditor(outlinerPanel, e=True, showContainedOnly=0)


class TestAnim(anim._Anim):
    def _override_build(self, control_color=None, **kwargs):
        setup_inst = self._setup_component

        for index, xform in setup_inst.get_xform_attrs(
            xform_type=self.IO_ENUM.output
        ).items():
            self._set_xform_attrs(
                index=index, xform=xform, xform_type=self.IO_ENUM.output
            )

        clust_inst = misc.Cluster.create(parent=self)

        self.container_node.publish_attr(
            f"{clust_inst.container_node}.{self.HIER_DATA.IN_XFORM}", "inClustXform"
        )
        self.container_node.publish_attr(
            f"{clust_inst.container_node}.{self.HIER_DATA.OUT_XFORM}", "outClustXform"
        )


def test():
    containerSainityCheck()
    cmds.file(new=True, force=True)

    misc.Cluster.create()
    # t = nw.create_node("transform")
    # t.add_attr("new", type="string")
    # t["tx"] >> t["new"]

    # setup_inst = setup.Setup.create(input_xforms=4)
    # clust_inst = misc.Cluster.create()
    # print(setup_inst)
    # clust_inst.add_clust_xform(
    #     "arm", setup_inst.container_node[setup_inst.HIER_DATA.OUT_XFORM][0]
    # )
    # -------------------------------------------------------------------------
    # char_inst = character.SimpleBiped.create(instance_name="maleA")
    # -------------------------------------------------------------------------
    # l_leg = anim.SimpleLimb.create(
    #     instance_name="leg",
    #     hier_side=component_enum_data.CharacterSide.left,
    #     control_color=component_enum_data.Color.blue,
    #     setup_color=component_enum_data.Color.light_orange,
    #     input_xforms=[
    #         component_data.Xform(
    #             xform_name="hip", init_matrix=utils.Matrix.translate_matrix(3, 8, 0)
    #         ),
    #         component_data.Xform(xform_name="knee"),
    #         component_data.Xform(
    #             xform_name="ankle", init_matrix=utils.Matrix.translate_matrix(4, 0, 0)
    #         ),
    #     ],
    #     primary_axis=component_enum_data.AxisEnum.z,
    #     secondary_axis=component_enum_data.AxisEnum.x,
    #     add_settings_cntrl=True,
    # )

    # misc.VisualizeHier.create(instance_name="l_leg", source_component=l_leg)

    # r_leg = l_leg.mirror(control_color=component_enum_data.Color.red, setup_color=component_enum_data.Color.light_orange)
    # misc.VisualizeHier.create(instance_name="r_leg", source_component=r_leg)

    # for index in range(3):
    #     node = nw.wrap_node("|L_leg_anim:grp|L_leg_anim:setup_:setup")
    #     attr = node["inputXform"][index]
    #     new_xform = l_leg.get_hook_xform(xform=attr)
    #     print(new_xform.init_matrix.parent)
    # r_leg = l_leg.mirror(control_color=component_enum_data.Color.red , setup_color=component_enum_data.Color.light_orange)
    # r_leg_vis = misc.VisualizeHier.create(source_component=r_leg)
