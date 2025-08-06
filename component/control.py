import system.component_enum_data as component_enum_data
import maya.cmds as cmds
import system.component as component
import utils.node_wrapper as nw
import component.enum_manager as enum_manager

class Circle(component.Control):
    """A circle nurbs curve control"""
    def _create_shapes(self):
        return [cmds.circle(normal = self.axis_vec)[0]]
class Axis(component.Control):
    """A axis nurbs curve control with a red, green, and blue axis pointers"""
    can_set_color = False
    
    def _create_shapes(self):
        x_axis = nw.wrap_node(cmds.curve(degree=1, point=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]))
        y_axis = nw.wrap_node(cmds.curve(degree=1, point=[[0.0, 0.0, 0.0], [0.0, 1.0, 0.0]]))
        z_axis = nw.wrap_node(cmds.curve(degree=1, point=[[0.0, 0.0, 0.0], [0.0, 0.0, 1.0]]))

        # utils.set_color()
        enum_manager.Color.apply_color(x_axis.get_shapes()[0], component_enum_data.Color.red, connect=False)
        enum_manager.Color.apply_color(y_axis.get_shapes()[0], component_enum_data.Color.green, connect=False)
        enum_manager.Color.apply_color(z_axis.get_shapes()[0], component_enum_data.Color.blue, connect=False)
        
        return [x_axis, y_axis, z_axis]
class BoxControl(component.Control):
    """A box nurbs curve control"""
    def _create_shapes(self):
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
class DiamondControl(component.Control):
    """A diamond nurbs surface control"""
    def _create_shapes(self):
        diamond = cmds.sphere(axis=self.axis_vec, sections=4, spans=2, degree=1)[0]
        return [diamond]
class DiamondWireControl(component.Control):
    """A diamond nurbs curve control"""
    def _create_shapes(self):
        diamond = cmds.curve(degree=1, point=[
            [0, 1, 0], [1, 0, 0], [0, -1, 0],
            [0, 0, 1], [0, 1, 0],
            [-1, 0, 0], [0, -1, 0],
            [0, 0, -1],
            [1, 0, 0], [0, 0, 1], [-1, 0, 0], [0, 0, -1],
            [0, 1, 0]
        ])
        return [diamond]
class Gear(component.Control):
    """A gear nurbs curve control"""
    def _create_shapes(self):
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
class Gimbal(component.Control):
    can_set_color = False

    def _create_shapes(self):
        circle1 = nw.wrap_node(cmds.circle(normal=[1.0, 0.0, 0.0])[0])
        circle2 = nw.wrap_node(cmds.circle(normal=[0.0, 1.0, 0.0])[0])
        circle3 = nw.wrap_node(cmds.circle(normal=[0.0, 0.0, 1.0])[0])

        enum_manager.Color.apply_color(circle1.get_shapes()[0], component_enum_data.Color.red)
        enum_manager.Color.apply_color(circle2.get_shapes()[0], component_enum_data.Color.green)
        enum_manager.Color.apply_color(circle3.get_shapes()[0], component_enum_data.Color.blue)
        
        return [circle1, circle2, circle3]
class Pyramid4(component.Control):
    """A pyramid nurbs curve control"""
    def _create_shapes(self):
        pyramid = cmds.curve(degree=1, point=[
            [1, 0, 1], [1, 0, -1], [0, 1.4, 0], [1, 0, 1],
            [-1, 0, 1], [0, 1.4, 0], [-1, 0, -1], [-1, 0, 1], 
            [-1, 0, -1], [1, 0, -1]
        ])
        return [pyramid]
class Sphere(component.Control):
    """A sphere nurbs surface control"""
    def _create_shapes(self):
        sphere = cmds.sphere(axis=self.axis_vec)[0]
        return [sphere]
class Locator(component.Control):
    """A locator control"""
    def _create_shapes(self):
        return [cmds.spaceLocator()[0]]