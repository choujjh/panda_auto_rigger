import system.component_enum_data as component_enum_data
import system.component_data as component_data
import maya.cmds as cmds
import system.base_component as base_comp
import utils.node_wrapper as nw
import component.enum_manager as enum_manager
import utils.utils as utils
from typing import Union

def swap_control(to_replace: Union[nw.Container, nw.Transform, base_comp.Control], replace_component:type):
    """Replaces the shape of one control with another

    Args:
        to_replace (Union[nw.Container, nw.Transform, base_component.Control]):
        replace_component (type):

    Raises:
        RuntimeError: if no control class detected for replace component
        RuntimeError: if to_replace is a transform and has no container
        RuntimeError: if no component found
    """
    if not issubclass(replace_component, base_comp.Control):
        raise RuntimeError(f"{replace_component} is not a control class")
        
    if isinstance(to_replace, nw.Container):
        to_replace = base_comp.get_component(to_replace)
    elif isinstance(to_replace, nw.Transform):
        container = to_replace.get_container_node()
        if container is None:
            raise RuntimeError(f"{to_replace} does not have component")
        to_replace = base_comp.get_component(container)
    if to_replace is None:
        raise RuntimeError(f"no source component found")
    
    # replace component class
    to_replace.container_node[replace_component._BLD_COMP_CLASS] = replace_component.get_class_name()
    # delete shapes
    cmds.delete([str(x) for x in to_replace.transform_node.get_shapes()])

    replace_inst = replace_component()
    replace_inst._apply_shape_to_cntrl(
        cntrl_transform=to_replace.transform_node, 
        component_container=to_replace.container_node)

class Circle(base_comp.Control):
    """A circle nurbs curve control"""
    
    def _create_shapes(self, axis_vec):
        return [cmds.circle(normal=axis_vec)[0]]
class Axis(base_comp.Control):
    """A axis nurbs curve control with a red, green, and blue axis pointers"""
    can_set_color = False
    
    def _create_shapes(self, axis_vec):
        x_axis = nw.wrap_node(cmds.curve(degree=1, point=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]))
        y_axis = nw.wrap_node(cmds.curve(degree=1, point=[[0.0, 0.0, 0.0], [0.0, 1.0, 0.0]]))
        z_axis = nw.wrap_node(cmds.curve(degree=1, point=[[0.0, 0.0, 0.0], [0.0, 0.0, 1.0]]))

        utils.apply_display_color(
            nodes=x_axis.get_shapes(), 
            color=utils.get_rgb_from_index(component_enum_data.Color.red))
        utils.apply_display_color(
            nodes=y_axis.get_shapes(), 
            color=utils.get_rgb_from_index(component_enum_data.Color.green))
        utils.apply_display_color(
            nodes=z_axis.get_shapes(), 
            color=utils.get_rgb_from_index(component_enum_data.Color.blue))
        
        return [x_axis, y_axis, z_axis]
class BoxControl(base_comp.Control):
    """A box nurbs curve control"""
    
    def _create_shapes(self, axis_vec):
        x = 1.0
        y = 1.0
        z = 1.0
        box = cmds.curve(degree=1, point=[
            [x, y, z],
            [-x, y, z], [-x, -y, z],  [-x, y, z],
            [-x, y, -z], [-x, -y, -z], [-x, y, -z],
            [x, y, -z], [x, -y, -z], [x, y, -z],
            [x, y, z], [x, -y, z],                      # going to other plane
            [-x, -y, z], [-x, -y, -z], [x, -y, -z], [x, -y, z]
        ])
        
        return [box]
class Diamond(base_comp.Control):
    """A diamond nurbs surface control"""
    
    def _create_shapes(self, axis_vec):
        diamond = cmds.sphere(axis=axis_vec, sections=4, spans=2, degree=1)[0]
        return [diamond]
class DiamondWire(base_comp.Control):
    """A diamond nurbs curve control"""
    
    def _create_shapes(self, axis_vec):
        diamond = cmds.curve(degree=1, point=[
            [0, 1, 0], [1, 0, 0], [0, -1, 0],
            [0, 0, 1], [0, 1, 0],
            [-1, 0, 0], [0, -1, 0],
            [0, 0, -1],
            [1, 0, 0], [0, 0, 1], [-1, 0, 0], [0, 0, -1],
            [0, 1, 0]
        ])
        return [diamond]
class Gear(base_comp.Control):
    """A gear nurbs curve control"""
    
    def _create_shapes(self, axis_vec):
        outer_shape = cmds.curve(degree=3, point=[
            [0.303359, 0, 0.940211], [0.662567, 0, 0.732822], [0.707107, 0, 0.720888], [0.751647, 0, 0.732822],
            [0.925336, 0, 0.833101], [0.973133, 0, 0.839394], [1.011381, 0, 0.810046], [1.20721, 0, 0.470859],
            [1.213503, 0, 0.423061], [1.184155, 0, 0.384813], [1.010466, 0, 0.284534], [0.97786, 0, 0.251929], 
            [0.965926, 0, 0.207388], [0.965926, 0, -0.207388], [0.97786, 0, -0.251929], [1.010466, 0, -0.284534], 
            [1.184155, 0, -0.384814], [1.213503, 0, -0.423061], [1.20721, 0, -0.470859], [1.011381, 0, -0.810045], 
            [0.973133, 0, -0.839394], [0.925336, 0, -0.833101], [0.751647, 0, -0.732822], [0.707107, 0, -0.720888], 
            [0.662567, 0, -0.732822], [0.303359, 0, -0.940211], [0.270754, 0, -0.972816], [0.258819, 0, -1.017356], 
            [0.258819, 0, -1.217915], [0.24037, 0, -1.262455], [0.19583, 0, -1.280904], [-0.19583, 0, -1.280904], 
            [-0.24037, 0, -1.262455], [-0.258819, 0, -1.217915], [-0.258819, 0, -1.017356], [-0.270754, 0, -0.972816], 
            [-0.303359, 0, -0.940211], [-0.662567, 0, -0.732822], [-0.707107, 0, -0.720888], [-0.751647, 0, -0.732822], 
            [-0.925336, 0, -0.833101], [-0.973133, 0, -0.839394], [-1.011381, 0, -0.810046], [-1.20721, 0, -0.470859], 
            [-1.213503, 0, -0.423061], [-1.184155, 0, -0.384813], [-1.010466, 0, -0.284534], [-0.97786, 0, -0.251929], 
            [-0.965926, 0, -0.207388], [-0.965926, 0, 0.207388], [-0.97786, 0, 0.251929], [-1.010466, 0, 0.284534], 
            [-1.184155, 0, 0.384814], [-1.213503, 0, 0.423061], [-1.20721, 0, 0.470859], [-1.011381, 0, 0.810045], 
            [-0.973133, 0, 0.839394], [-0.925336, 0, 0.833101], [-0.751647, 0, 0.732822], [-0.707107, 0, 0.720888], 
            [-0.662567, 0, 0.732822], [-0.303359, 0, 0.940211], [-0.270754, 0, 0.972816], [-0.258819, 0, 1.017356], 
            [-0.258819, 0, 1.217915], [-0.24037, 0, 1.262455], [-0.19583, 0, 1.280904], [0.19583, 0, 1.280904], 
            [0.24037, 0, 1.262455], [0.258819, 0, 1.217915], [0.258819, 0, 1.017356], [0.270754, 0, 0.972816], 
            [0.303359, 0, 0.940211],
        ])
        inner_shape = cmds.curve(degree=3, point=[ 
            [0.0942458, 0, 0.586178], [0.154925, 0, 0.578189], [0.21147, 0, 0.554768], [0.374708, 0, 0.460522], 
            [0.423264, 0, 0.423264], [0.460522, 0, 0.374708], [0.554768, 0, 0.21147], [0.578189, 0, 0.154925], 
            [0.586178, 0, 0.0942458], [0.586178, 0, -0.0942458], [0.578189, 0, -0.154925], [0.554768, 0, -0.21147], 
            [0.460522, 0, -0.374708], [0.423264, 0, -0.423264], [0.374708, 0, -0.460522], [0.21147, 0, -0.554768], 
            [0.154925, 0, -0.578189], [0.0942458, 0, -0.586178], [-0.0942458, 0, -0.586178], [-0.154925, 0, -0.578189], 
            [-0.21147, 0, -0.554768], [-0.374708, 0, -0.460522], [-0.423264, 0, -0.423264], [-0.460522, 0, -0.374708], 
            [-0.554768, 0, -0.21147], [-0.578189, 0, -0.154925], [-0.586178, 0, -0.0942458], [-0.586178, 0, 0.0942458], 
            [-0.578189, 0, 0.154925], [-0.554768, 0, 0.21147], [-0.460522, 0, 0.374708], [-0.423264, 0, 0.423264], 
            [-0.374708, 0, 0.460522], [-0.21147, 0, 0.554768], [-0.154925, 0, 0.578189], [-0.0942458, 0, 0.586178], 
            [0.0942458, 0, 0.586178],
        ])
        
        return [inner_shape, outer_shape]
class Gimbal(base_comp.Control):
    can_set_color = False
    
    def _create_shapes(self, axis_vec):
        circle1 = nw.wrap_node(cmds.circle(normal=[1.0, 0.0, 0.0])[0])
        circle2 = nw.wrap_node(cmds.circle(normal=[0.0, 1.0, 0.0])[0])
        circle3 = nw.wrap_node(cmds.circle(normal=[0.0, 0.0, 1.0])[0])

        utils.apply_display_color(
            nodes=circle1.get_shapes(), 
            color=utils.get_rgb_from_index(component_enum_data.Color.red))
        utils.apply_display_color(
            nodes=circle2.get_shapes(), 
            color=utils.get_rgb_from_index(component_enum_data.Color.green))
        utils.apply_display_color(
            nodes=circle3.get_shapes(), 
            color=utils.get_rgb_from_index(component_enum_data.Color.blue))
        
        return [circle1, circle2, circle3]
class Pyramid4(base_comp.Control):
    """A pyramid nurbs curve control"""
    
    def _create_shapes(self, axis_vec):
        pyramid = cmds.curve(degree=1, point=[
            [1, 0, 1], [1, 0, -1], [0, 1.4, 0], [1, 0, 1],
            [-1, 0, 1], [0, 1.4, 0], [-1, 0, -1], [-1, 0, 1], 
            [-1, 0, -1], [1, 0, -1]
        ])
        return [pyramid]
class Sphere(base_comp.Control):
    """A sphere nurbs surface control"""
    
    def _create_shapes(self, axis_vec):
        sphere = cmds.sphere(axis=axis_vec)[0]
        return [sphere]
class Locator(base_comp.Control):
    """A locator control"""

    _LOC_SCALE = "locScale_test"

    def _get_input_node_build_attr_data(self):
        node_data = super()._get_input_node_build_attr_data()
        node_data.extend_attr_data(
            component_data.AttrData(self._LOC_SCALE, type_="double", value=1.0, min=0.1, publish=True)
        )

        return node_data

    def _override_build(self, **kwargs):
        super()._override_build(**kwargs)

        loc_shape = self.transform_node.get_shapes()[0]
        loc_shape["localScaleX"] << self.input_node[self._LOC_SCALE]
        loc_shape["localScaleY"] << self.input_node[self._LOC_SCALE]
        loc_shape["localScaleZ"] << self.input_node[self._LOC_SCALE]

    def _create_shapes(self, axis_vec):
        return [cmds.spaceLocator()[0]]