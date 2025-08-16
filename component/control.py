import system.component_enum_data as component_enum_data
import system.component_data as component_data
import maya.cmds as cmds
import system.base_component as base_component
import utils.node_wrapper as nw
import component.enum_manager as enum_manager
from typing import Union

def swap_control(to_replace: Union[nw.Container, nw.Transform, base_component.Control], replace_component:type):
    """Replaces the shape of one control with another

    Args:
        to_replace (Union[nw.Container, nw.Transform, base_component.Control]):
        replace_component (type):

    Raises:
        RuntimeError: if no control class detected for replace component
        RuntimeError: if to_replace is a transform and has no container
        RuntimeError: if no component found
    """
    if not issubclass(replace_component, base_component.Control):
        raise RuntimeError(f"{replace_component} is not a control class")
        
    if isinstance(to_replace, nw.Container):
        to_replace = base_component.get_component(to_replace)
    elif isinstance(to_replace, nw.Transform):
        container = to_replace.get_container_node()
        if container is None:
            raise RuntimeError(f"{to_replace} does not have component")
        to_replace = base_component.get_component(container)
    if to_replace is None:
        raise RuntimeError(f"no source component found")
    
    # replace component class
    to_replace.container_node["componentClass"] = replace_component.get_class_name()
    # delete shapes
    cmds.delete([str(x) for x in to_replace.transform_node.get_shapes()])

    replace_component._apply_shape_to_cntrl(to_replace.transform_node, to_replace.container_node)

class Circle(base_component.Control):
    """A circle nurbs curve control"""
    @classmethod
    def create(cls, instance_name=None, parent=None, axis_vec=None, build_tx=0, build_ty=0, build_tz=0, build_rx=0, build_ry=0, build_rz=0, build_sx=1, build_sy=1, build_sz=1, **kwargs):
        return super().create(instance_name, parent, axis_vec, build_tx, build_ty, build_tz, build_rx, build_ry, build_rz, build_sx, build_sy, build_sz, **kwargs)
    @classmethod
    def _create_shapes(cls, axis_vec):
        return [cmds.circle(normal=axis_vec)[0]]
class Axis(base_component.Control):
    """A axis nurbs curve control with a red, green, and blue axis pointers"""
    can_set_color = False
    
    @classmethod
    def _create_shapes(cls, axis_vec):
        x_axis = nw.wrap_node(cmds.curve(degree=1, point=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]))
        y_axis = nw.wrap_node(cmds.curve(degree=1, point=[[0.0, 0.0, 0.0], [0.0, 1.0, 0.0]]))
        z_axis = nw.wrap_node(cmds.curve(degree=1, point=[[0.0, 0.0, 0.0], [0.0, 0.0, 1.0]]))

        # utils.set_color()
        enum_manager.Color.apply_color(x_axis.get_shapes()[0], component_enum_data.Color.red, connect=False)
        enum_manager.Color.apply_color(y_axis.get_shapes()[0], component_enum_data.Color.green, connect=False)
        enum_manager.Color.apply_color(z_axis.get_shapes()[0], component_enum_data.Color.blue, connect=False)
        
        return [x_axis, y_axis, z_axis]
class BoxControl(base_component.Control):
    """A box nurbs curve control"""
    @classmethod
    def _create_shapes(cls, axis_vec):
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
class DiamondControl(base_component.Control):
    """A diamond nurbs surface control"""
    @classmethod
    def _create_shapes(cls, axis_vec):
        diamond = cmds.sphere(axis=axis_vec, sections=4, spans=2, degree=1)[0]
        return [diamond]
class DiamondWireControl(base_component.Control):
    """A diamond nurbs curve control"""
    @classmethod
    def _create_shapes(cls, axis_vec):
        diamond = cmds.curve(degree=1, point=[
            [0, 1, 0], [1, 0, 0], [0, -1, 0],
            [0, 0, 1], [0, 1, 0],
            [-1, 0, 0], [0, -1, 0],
            [0, 0, -1],
            [1, 0, 0], [0, 0, 1], [-1, 0, 0], [0, 0, -1],
            [0, 1, 0]
        ])
        return [diamond]
class Gear(base_component.Control):
    """A gear nurbs curve control"""
    @classmethod
    def _create_shapes(cls, axis_vec):
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
class Gimbal(base_component.Control):
    can_set_color = False
    @classmethod
    def _create_shapes(cls, axis_vec):
        circle1 = nw.wrap_node(cmds.circle(normal=[1.0, 0.0, 0.0])[0])
        circle2 = nw.wrap_node(cmds.circle(normal=[0.0, 1.0, 0.0])[0])
        circle3 = nw.wrap_node(cmds.circle(normal=[0.0, 0.0, 1.0])[0])

        enum_manager.Color.apply_color(circle1.get_shapes()[0], component_enum_data.Color.red)
        enum_manager.Color.apply_color(circle2.get_shapes()[0], component_enum_data.Color.green)
        enum_manager.Color.apply_color(circle3.get_shapes()[0], component_enum_data.Color.blue)
        
        return [circle1, circle2, circle3]
class Pyramid4(base_component.Control):
    """A pyramid nurbs curve control"""
    @classmethod
    def _create_shapes(cls, axis_vec):
        pyramid = cmds.curve(degree=1, point=[
            [1, 0, 1], [1, 0, -1], [0, 1.4, 0], [1, 0, 1],
            [-1, 0, 1], [0, 1.4, 0], [-1, 0, -1], [-1, 0, 1], 
            [-1, 0, -1], [1, 0, -1]
        ])
        return [pyramid]
class Sphere(base_component.Control):
    """A sphere nurbs surface control"""
    @classmethod
    def _create_shapes(cls, axis_vec):
        sphere = cmds.sphere(axis=axis_vec)[0]
        return [sphere]
class Locator(base_component.Control):
    """A locator control"""
    def _get_input_node_build_attr_data(self):
        node_data = super()._get_input_node_build_attr_data()
        node_data.extend_attr_data(
            component_data.AttrData("locScale", type_="double", value=1.0, min=0.1, publish=True)
        )

        return node_data

    def _override_build(self, **kwargs):
        super()._override_build(**kwargs)

        loc_shape = self.transform_node.get_shapes()[0]
        loc_shape["localScaleX"] << self.input_node["locScale"]
        loc_shape["localScaleY"] << self.input_node["locScale"]
        loc_shape["localScaleZ"] << self.input_node["locScale"]

    @classmethod
    def _create_shapes(cls, axis_vec):
        return [cmds.spaceLocator()[0]]