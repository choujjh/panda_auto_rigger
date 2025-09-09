import utils.om as om
import utils.utils as utils
import utils.node_wrapper as nw
import system.component_enum_data as component_enum_data
import system.component_data as component_data
import system.base_component as base_comp
import component.enum_manager as enum_manager
import component.control as control
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
    cmds.nodeEditor('nodeEditorPanel1NodeEditorEd', e=True, useAssets=False)

    # set 'show at top' OFF in the channel box editor
    cmds.channelBox('mainChannelBox', e=True, containerAtTop=False)

    # set asset display is to 'under parent' 
    outliners = cmds.getPanel(typ='outlinerPanel')
    for outlinerPanel in outliners:
        cmds.outlinerEditor(outlinerPanel, e=True, showContainerContents=1)
        cmds.outlinerEditor(outlinerPanel, e=True, showContainedOnly=0)

def test():
    containerSainityCheck()
    cmds.file(new=True, force=True)