import system.component_enum_data as component_enum_data
import system.component_data as component_data
import maya.cmds as cmds
import system.base_component as base_comp
import utils.utils as utils
import utils.node_wrapper as nw
from typing import Union
from component.enum_manager import Color


class _Control(base_comp._Component):
    """A Base class for all control autorigging components. Derived from Component

    Attributes:
        can_set_color (bool): can set color of component
        lock_transform (bool): locks transform of control

        _IN_OFF_MAT (str): str constant "offsetMatrix"
        _IN_HAS_CLR (str): str constant "hasColor"
        _IN_CLR (str): str constant "color"
        _OUT_WS_MAT (str): str constant "worldMatrix"
        _OUT_LOC_MAT (str): str constant "localMatrix"
        _OUT_WS_INV_MAT (str): str constant "worldInverseMatrix"
        _CNTNR_CNTRL_MAP (str): str constant "controlMap"
    """

    component_type = component_enum_data.ComponentType.control
    input_node_name = "cntrl"
    input_node_type = "transform"
    class_namespace = "cntrl"
    can_set_color = True
    lock_transform = False

    _IN_OFF_MAT = "offsetMatrix"
    _IN_HAS_CLR = "hasColor"
    _IN_CLR = "color"
    _OUT_WS_MAT = "worldMatrix"
    _OUT_LOC_MAT = "localMatrix"
    _OUT_WS_INV_MAT = "worldInverseMatrix"
    _CNTNR_CNTRL_MAP = "controlMap"

    @classmethod
    def create(
        cls,
        instance_name: Union[str, nw.Attr] = None,
        parent: Union[base_comp._Component, nw.Container] = None,
        axis_vec: component_enum_data.AxisEnum = None,
        build_t: Union[list, utils.Vector, float] = [0.0, 0.0, 0.0],
        build_r: Union[list, utils.Vector, float] = [0.0, 0.0, 0.0],
        build_s: Union[list, utils.Vector, float] = [1.0, 1.0, 1.0],
        color: Union[
            list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node
        ] = None,
        xform_map_index: int = None,
    ):
        """Class method to create component

        Args:
            instance_name (Union[str, nw.Attr], optional): name of component. Defaults to None.
            parent (Union[base_comp._Component, nw.Container], optional): Defaults to None.
            axis_vec (component_enum_data.AxisEnum, optional): vector by which the control will be pointed. Defaults to None.
            build_t (Union[list, utils.Vector, float], optional): build translate will have freeze applied to it. Defaults to [0.0, 0.0, 0.0].
            build_r (Union[list, utils.Vector, float], optional): build translate will have freeze applied to it. Defaults to [0.0, 0.0, 0.0].
            build_s (Union[list, utils.Vector, float], optional): build translate will have freeze applied to it. Defaults to [1.0, 1.0, 1.0].
            color (Union[ list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node ], optional): Defaults to None.
            xform_map_index (int, optional): map index connected to parent container. Defaults to None.

        Returns:
            _Control:
        """
        return cls._kwarg_create(**cls._process_locals(kwarg_dict=locals()))

    def _input_attr_build_data(self) -> component_data.NodeData:
        """Defines all the added, published, or modified attributes for the
        input node. inherits all input node data from _Component.

        Returns:
            comp_data.NodeData:
        """
        node_data = super()._input_attr_build_data()

        node_data.extend_attr_data(
            component_data.AttrData(
                name="offsetParentMatrix", publish=self._IN_OFF_MAT
            ),
            component_data.AttrData(name="worldMatrix[0]", publish=self._OUT_WS_MAT),
            component_data.AttrData(name="matrix", publish=self._OUT_LOC_MAT),
            component_data.AttrData(
                name="worldInverseMatrix[0]", publish=self._OUT_WS_INV_MAT
            ),
            component_data.AttrData(
                name="overrideEnabled",
                publish=self._IN_HAS_CLR,
                locked=not type(self).can_set_color,
            ),
            component_data.AttrData(
                name="overrideColorRGB",
                publish=self._IN_CLR,
                locked=not type(self).can_set_color,
            ),
            component_data.AttrData(name="overrideRGBColors", value=1),
        )
        return node_data

    def _container_attr_build_data(self):
        """Defines all the added, or modified attributes for the
        container node. inherits all container node data from _Component.

        Returns:
            comp_data.NodeData:
        """
        node_data = super()._container_attr_build_data()
        node_data.extend_attr_data(
            component_data.AttrData(name=self._CNTNR_CNTRL_MAP, type_="message"),
        )
        return node_data

    def _override_build(
        self,
        axis_vec: component_enum_data.AxisEnum = None,
        color: Union[
            list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node
        ] = None,
        build_t: Union[list, utils.Vector, float] = [0.0, 0.0, 0.0],
        build_r: Union[list, utils.Vector, float] = [0.0, 0.0, 0.0],
        build_s: Union[list, utils.Vector, float] = [1.0, 1.0, 1.0],
        xform_map_index: int = None,
        **kwargs,
    ):
        """Creates control, shapes for control, and applies the build t r s then
        freezes control. maps it to parent container using xform_map_index

        Args:
            axis_vec (component_enum_data.AxisEnum, optional): _description_. Defaults to None.
            color (Union[ list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node ], optional): Defaults to None.
            build_t (Union[list, utils.Vector, float], optional): Defaults to [0.0, 0.0, 0.0].
            build_r (Union[list, utils.Vector, float], optional): Defaults to [0.0, 0.0, 0.0].
            build_s (Union[list, utils.Vector, float], optional): Defaults to [1.0, 1.0, 1.0].
            xform_map_index (int, optional): _description_. Defaults to None.
        """
        # set visibility to hidden in channel box
        self.transform_node["visibility"].set_keyable(False)

        # add shapes
        self._apply_shape_to_cntrl(axis_vec=axis_vec)

        parent_container = self.container_node.get_container_node()
        if (
            parent_container is not None
            and xform_map_index is not None
            and xform_map_index >= 0
        ):
            (
                parent_container[self._CNTNR_CNTRL_CHLDRN][xform_map_index]
                >> self.container_node[self._CNTNR_CNTRL_MAP]
            )

        # add build transforms
        self.transform_node["translate"].set(
            utils.make_len(build_t, len_=3)
            if utils.is_iterable(build_t)
            else [build_t, build_t, build_t]
        )
        self.transform_node["rotate"].set(
            utils.make_len(build_r, len_=3)
            if utils.is_iterable(build_r)
            else [build_r, build_r, build_r]
        )
        self.transform_node["scale"].set(
            utils.make_len(build_s, len_=3, default=1.0)
            if utils.is_iterable(build_s)
            else [build_s, build_s, build_s]
        )
        self.transform_node.freeze_transforms()
        if color is not None:
            self.apply_color(color)

    def _create_shapes(self) -> list[nw.Transform]:
        """Creates shapes and returns a list of the shapes transforms. these
        shapes will be parented to the transform node later

        Returns:
            list[nw.Transform]:
        """
        raise NotImplementedError

    def _apply_shape_to_cntrl(
        self,
        cntrl_transform: nw.Transform = None,
        component_container: nw.Container = None,
        axis_vec=None,
    ):
        """Takes create shape function and adds all shapes to transform node

        Args:
            cntrl_transform (nw.Transform):
            component_container (nw.Container):
            axis_vec (vector, component_enum_data.AxisEnum, None):
        """
        if cntrl_transform is None:
            cntrl_transform = self.transform_node
        if component_container is None:
            component_container = self.container_node

        # parenting to transform
        shape_transforms = self._create_shapes()
        for transform in shape_transforms:
            if not isinstance(transform, nw.Node):
                transform = nw.wrap_node(transform)

            # delete history
            cmds.delete(str(transform), constructionHistory=True)

            # freeze all controls
            transform.freeze_transforms()

            # apply to transform
            for shape in transform.get_shapes():
                cmds.parent(str(shape), str(cntrl_transform), relative=True, shape=True)

        # deleting transforms
        if shape_transforms != []:
            cmds.delete(shape_transforms)

        shapes_list = cntrl_transform.get_shapes()

        # rename shapes
        transform_stripped_name = utils.Namespace.strip_namespace(str(cntrl_transform))
        for index, shape in enumerate(shapes_list):
            shape.rename(f"{transform_stripped_name}Shape{index + 1}")

        # add shapes to container
        if component_container is not None:
            component_container.add_nodes(*shapes_list)

        # axis vec
        if (
            axis_vec is not None
            and axis_vec
            and component_enum_data.get_enum_item_class(axis_vec)
            == component_enum_data.AxisEnum
        ):
            axis_vec = utils.Vector(axis_vec.value)
        if axis_vec is not None and axis_vec != utils.Vector(
            component_enum_data.AxisEnum.y.value
        ):
            if axis_vec == utils.Vector(component_enum_data.AxisEnum.neg_y.value):
                rot_vec = utils.Vector(1, 0, 0) * 180
            else:
                y_vec = utils.Vector(component_enum_data.AxisEnum.y.value)
                rot_vec = (y_vec ^ axis_vec).normalize() * 90
            self.transform_node["rotate"] = rot_vec
            self.transform_node.freeze_transforms()

    def apply_color(self, color: Union[component_enum_data.Color, list, nw.Node]):
        """Applies color to control

        Args:
            color (Union[component_enum_data.Color, list, nw.Node]):
        #"""

        if self.container_node[self._IN_HAS_CLR].is_locked():
            return
        else:
            rgb = [1.0, 1.0, 1.0]
            shader = None
            surface_shapes = [
                shape
                for shape in self.transform_node.get_shapes()
                if shape.type_ == "mesh" or shape.type_ == "nurbsSurface"
            ]
            if isinstance(color, nw.Node) and color.type_ == "lambert":
                shader = color
            elif isinstance(color, component_enum_data.Color):
                shader = Color.get_shader(color)
            if isinstance(color, list):
                rgb = utils.make_len(color, len_=3, default=1.0)

            self.container_node[self._IN_HAS_CLR] = True
            if shader is not None:
                if len(surface_shapes) > 0:
                    utils.apply_shader_group(surface_shapes, shader)
                utils.apply_display_color(
                    nodes=[self.transform_node], color=shader["color"]
                )
            else:
                utils.apply_display_color(nodes=[self.transform_node], color=rgb)

    def promote_attr_to_keyable(self, attr: nw.Attr, name: str = None, **kwargs):
        """Turns attribute given into a controllable attribute by the control

        Args:
            attr (nw.Attr): attribute to be driven by control
            name (str, optional): new name of controllable attribute.
            Defaults to None.
        """

        def get_num_min_max_kwargs(attr: nw.Attr):
            """get min and max kwargs

            Args:
                attr (nw.Attr): _description_

            Returns:
                _type_: _description_
            """
            # has max and mins
            kwargs = {}
            if attr_type in ["double", "long"]:
                for attr_exists, attr_query_key, attr_add_key in zip(
                    ["softMaxExists", "softMinExists", "maxExists", "minExists"],
                    ["softMax", "softMin", "maximum", "minimum"],
                    ["softMaxValue", "softMinValue", "maxValue", "minValue"],
                ):
                    if cmds.attributeQuery(
                        attr.short_name, node=str(attr.node), **{attr_exists: True}
                    ):
                        kwargs[attr_add_key] = cmds.attributeQuery(
                            attr.short_name,
                            node=str(attr.node),
                            **{attr_query_key: True},
                        )[0]

            return kwargs

        transform_node = self.transform_node
        if kwargs == {}:
            attr_type = attr.type_
            if attr_type == "compound":
                raise RuntimeError(
                    "{} of type compound. compound type not supported".format(attr)
                )

            if name is None:
                name = attr.short_name

            # non settable
            if attr_type in [
                "string",
                "nurbsCurve",
                "nurbsSurface",
                "mesh",
                "matrix",
                "message",
            ]:
                warn_str = "{} of type {} is not keyable. attribute created without keyable".format(
                    attr, attr_type
                )
                cmds.warning(warn_str)
            else:
                kwargs["keyable"] = True

            # has max and mins
            if attr_type in ["double", "long"]:
                kwargs.update(get_num_min_max_kwargs(attr))

            # enum
            if attr_type == "enum":
                enum_string = cmds.attributeQuery(
                    attr.short_name, node=str(attr.node), listEnum=True
                )
                kwargs["enumName"] = enum_string[0]

            # compound attrs
            if attr_type in ["double3", "double2"]:
                transform_node.add_attr(name, type=attr_type, **kwargs)
                for child_attr in attr:
                    child_kwargs = get_num_min_max_kwargs(child_attr)
                    child_name = child_attr.attr_name.replace(attr.attr_name, name)
                    transform_node.add_attr(
                        child_name,
                        parent=name,
                        type=child_attr.type_,
                        **kwargs,
                        **child_kwargs,
                    )

            else:
                transform_node.add_attr(name, type=attr_type, **kwargs)

            attr_connection = attr.get_connections(as_dest=True, as_src=False)
            if attr_connection == [] and attr_type not in [
                "nurbsCurve",
                "nurbsSurface",
                "mesh",
                "message",
            ]:
                utils.set_connect_attr_data(attr=attr, data=transform_node[name])
            else:
                attr_connection[0] << transform_node[name]
                transform_node[name] >> ~attr

        # has add attr kwargs
        else:
            if name is not None:
                kwargs["long_name"] = name
            kwargs["keyable"] = True

            transform_node.add_attr(**kwargs)
            if attr.has_src_connection():
                ~attr
            transform_node[name] >> attr

    def pre_swap_cleanup(self):
        """This code is ran before the control is swapped. meant to be overriden"""

    def post_swap_cleanup(self):
        """This code is ran after the control is swapped. meant to be overriden"""

    def replace_control(
        self,
        replace_component: Union[type, "_Control", nw.Transform],
        color: Union[component_enum_data.Color, list, nw.Node] = None,
    ):
        """Replaces control with replace_component. could be component type, control, and transform

        Args:
            replace_component (Union[type, Control, nw.Transform]): _description_
            color ( Union[component_enum_data.Color, list, nw.Node], optional): Defaults to None.

        Raises:
            RuntimeError: no replacement transform found

        Returns:
            Control:
        """

        self.pre_swap_cleanup()
        cmds.delete([str(x) for x in self.transform_node.get_shapes()])
        replace_component_class = None
        transform_node = None
        if isinstance(replace_component, type):
            replace_component = replace_component()

            self.container_node[self._BLD_COMP_CLASS] = (
                replace_component.get_class_name()
            )

            replace_component._apply_shape_to_cntrl(
                cntrl_transform=self.transform_node,
                component_container=self.container_node,
            )
            replace_component_class = type(replace_component)

        if isinstance(replace_component, nw.Transform):
            transform_node = replace_component
        elif replace_component_class is None:
            transform_node = replace_component.transform_node
            if transform_node is None:
                raise RuntimeError(
                    f"no replace transform found in {replace_component.container_node}"
                )
            replace_component_class = type(replace_component)

        # renaming shapes
        if transform_node is not None:
            mirror_transform = nw.wrap_node(cmds.duplicate(str(transform_node))[0])
            for index, shape in enumerate(mirror_transform.get_shapes()):
                cmds.parent(
                    str(shape), str(self.transform_node), relative=True, shape=True
                )
                shape.rename(f"{self.transform_node}Shape{index + 1}")
            cmds.delete(str(mirror_transform))

        # adding shapes to container
        self.container_node.add_nodes(*self.transform_node.get_shapes())
        self.rename_nodes()

        if replace_component_class is not None:
            new_component = type(replace_component)(self.container_node)
            new_component.container_node[self._BLD_COMP_CLASS] = (
                new_component.get_class_name()
            )
            new_component.post_swap_cleanup()
        else:
            new_component = self

        # apply color
        if color is not None:
            self.apply_color(color=color)

        return new_component


class Circle(_Control):
    """A circle nurbs curve control"""

    def _create_shapes(self):
        """Creates circle wire shape

        Returns:
            list[mw.Transform]:
        """
        return [cmds.circle(normal=component_enum_data.AxisEnum.y.value)[0]]


class Axis(_Control):
    """A axis nurbs curve control with a red, green, and blue axis pointers"""

    can_set_color = False

    def _create_shapes(self):
        """Creates axis wire shapes

        Returns:
            list[nw.Transform]:
        """
        x_axis = nw.wrap_node(
            cmds.curve(degree=1, point=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
        )
        y_axis = nw.wrap_node(
            cmds.curve(degree=1, point=[[0.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
        )
        z_axis = nw.wrap_node(
            cmds.curve(degree=1, point=[[0.0, 0.0, 0.0], [0.0, 0.0, 1.0]])
        )

        utils.apply_display_color(
            nodes=x_axis.get_shapes(),
            color=utils.get_rgb_from_index(component_enum_data.Color.red),
        )
        utils.apply_display_color(
            nodes=y_axis.get_shapes(),
            color=utils.get_rgb_from_index(component_enum_data.Color.green),
        )
        utils.apply_display_color(
            nodes=z_axis.get_shapes(),
            color=utils.get_rgb_from_index(component_enum_data.Color.blue),
        )

        return [x_axis, y_axis, z_axis]


class Box(_Control):
    """A box nurbs curve control"""

    def _create_shapes(self):
        """Creates box wire shapes

        Returns:
            list[nw.Transform]:
        """
        x = 1.0
        y = 1.0
        z = 1.0
        box = cmds.curve(
            degree=1,
            point=[
                [x, y, z],
                [-x, y, z],
                [-x, -y, z],
                [-x, y, z],
                [-x, y, -z],
                [-x, -y, -z],
                [-x, y, -z],
                [x, y, -z],
                [x, -y, -z],
                [x, y, -z],
                [x, y, z],
                [x, -y, z],  # going to other plane
                [-x, -y, z],
                [-x, -y, -z],
                [x, -y, -z],
                [x, -y, z],
            ],
        )

        return [box]


class Diamond(_Control):
    """A diamond nurbs surface control"""

    def _create_shapes(self):
        """Creates diamond nurbs surface shape

        Returns:
            list[nw.Transform]:
        """
        diamond = cmds.sphere(sections=4, spans=2, degree=1)[0]
        return [diamond]


class DiamondWire(_Control):
    """A diamond nurbs curve control"""

    def _create_shapes(self):
        """Creates diamond wire shape

        Returns:
            list[nw.Transform]:
        """
        diamond = cmds.curve(
            degree=1,
            point=[
                [0, 1, 0],
                [1, 0, 0],
                [0, -1, 0],
                [0, 0, 1],
                [0, 1, 0],
                [-1, 0, 0],
                [0, -1, 0],
                [0, 0, -1],
                [1, 0, 0],
                [0, 0, 1],
                [-1, 0, 0],
                [0, 0, -1],
                [0, 1, 0],
            ],
        )
        return [diamond]


class Gear(_Control):
    """A gear nurbs curve control"""

    def _create_shapes(self):
        """Creates gear wire shapes

        Returns:
            list[nw.Transform]:
        """
        outer_shape = cmds.curve(
            degree=3,
            point=[
                [0.303359, 0, 0.940211],
                [0.662567, 0, 0.732822],
                [0.707107, 0, 0.720888],
                [0.751647, 0, 0.732822],
                [0.925336, 0, 0.833101],
                [0.973133, 0, 0.839394],
                [1.011381, 0, 0.810046],
                [1.20721, 0, 0.470859],
                [1.213503, 0, 0.423061],
                [1.184155, 0, 0.384813],
                [1.010466, 0, 0.284534],
                [0.97786, 0, 0.251929],
                [0.965926, 0, 0.207388],
                [0.965926, 0, -0.207388],
                [0.97786, 0, -0.251929],
                [1.010466, 0, -0.284534],
                [1.184155, 0, -0.384814],
                [1.213503, 0, -0.423061],
                [1.20721, 0, -0.470859],
                [1.011381, 0, -0.810045],
                [0.973133, 0, -0.839394],
                [0.925336, 0, -0.833101],
                [0.751647, 0, -0.732822],
                [0.707107, 0, -0.720888],
                [0.662567, 0, -0.732822],
                [0.303359, 0, -0.940211],
                [0.270754, 0, -0.972816],
                [0.258819, 0, -1.017356],
                [0.258819, 0, -1.217915],
                [0.24037, 0, -1.262455],
                [0.19583, 0, -1.280904],
                [-0.19583, 0, -1.280904],
                [-0.24037, 0, -1.262455],
                [-0.258819, 0, -1.217915],
                [-0.258819, 0, -1.017356],
                [-0.270754, 0, -0.972816],
                [-0.303359, 0, -0.940211],
                [-0.662567, 0, -0.732822],
                [-0.707107, 0, -0.720888],
                [-0.751647, 0, -0.732822],
                [-0.925336, 0, -0.833101],
                [-0.973133, 0, -0.839394],
                [-1.011381, 0, -0.810046],
                [-1.20721, 0, -0.470859],
                [-1.213503, 0, -0.423061],
                [-1.184155, 0, -0.384813],
                [-1.010466, 0, -0.284534],
                [-0.97786, 0, -0.251929],
                [-0.965926, 0, -0.207388],
                [-0.965926, 0, 0.207388],
                [-0.97786, 0, 0.251929],
                [-1.010466, 0, 0.284534],
                [-1.184155, 0, 0.384814],
                [-1.213503, 0, 0.423061],
                [-1.20721, 0, 0.470859],
                [-1.011381, 0, 0.810045],
                [-0.973133, 0, 0.839394],
                [-0.925336, 0, 0.833101],
                [-0.751647, 0, 0.732822],
                [-0.707107, 0, 0.720888],
                [-0.662567, 0, 0.732822],
                [-0.303359, 0, 0.940211],
                [-0.270754, 0, 0.972816],
                [-0.258819, 0, 1.017356],
                [-0.258819, 0, 1.217915],
                [-0.24037, 0, 1.262455],
                [-0.19583, 0, 1.280904],
                [0.19583, 0, 1.280904],
                [0.24037, 0, 1.262455],
                [0.258819, 0, 1.217915],
                [0.258819, 0, 1.017356],
                [0.270754, 0, 0.972816],
                [0.303359, 0, 0.940211],
            ],
        )
        inner_shape = cmds.curve(
            degree=3,
            point=[
                [0.0942458, 0, 0.586178],
                [0.154925, 0, 0.578189],
                [0.21147, 0, 0.554768],
                [0.374708, 0, 0.460522],
                [0.423264, 0, 0.423264],
                [0.460522, 0, 0.374708],
                [0.554768, 0, 0.21147],
                [0.578189, 0, 0.154925],
                [0.586178, 0, 0.0942458],
                [0.586178, 0, -0.0942458],
                [0.578189, 0, -0.154925],
                [0.554768, 0, -0.21147],
                [0.460522, 0, -0.374708],
                [0.423264, 0, -0.423264],
                [0.374708, 0, -0.460522],
                [0.21147, 0, -0.554768],
                [0.154925, 0, -0.578189],
                [0.0942458, 0, -0.586178],
                [-0.0942458, 0, -0.586178],
                [-0.154925, 0, -0.578189],
                [-0.21147, 0, -0.554768],
                [-0.374708, 0, -0.460522],
                [-0.423264, 0, -0.423264],
                [-0.460522, 0, -0.374708],
                [-0.554768, 0, -0.21147],
                [-0.578189, 0, -0.154925],
                [-0.586178, 0, -0.0942458],
                [-0.586178, 0, 0.0942458],
                [-0.578189, 0, 0.154925],
                [-0.554768, 0, 0.21147],
                [-0.460522, 0, 0.374708],
                [-0.423264, 0, 0.423264],
                [-0.374708, 0, 0.460522],
                [-0.21147, 0, 0.554768],
                [-0.154925, 0, 0.578189],
                [-0.0942458, 0, 0.586178],
                [0.0942458, 0, 0.586178],
            ],
        )

        return [inner_shape, outer_shape]


class Gimbal(_Control):
    can_set_color = False

    def _create_shapes(self):
        """Creates gimbal wire shapes

        Returns:
            list[nw.Transform]:
        """
        circle1 = nw.wrap_node(cmds.circle(normal=[1.0, 0.0, 0.0])[0])
        circle2 = nw.wrap_node(cmds.circle(normal=[0.0, 1.0, 0.0])[0])
        circle3 = nw.wrap_node(cmds.circle(normal=[0.0, 0.0, 1.0])[0])

        utils.apply_display_color(
            nodes=circle1.get_shapes(),
            color=utils.get_rgb_from_index(component_enum_data.Color.red),
        )
        utils.apply_display_color(
            nodes=circle2.get_shapes(),
            color=utils.get_rgb_from_index(component_enum_data.Color.green),
        )
        utils.apply_display_color(
            nodes=circle3.get_shapes(),
            color=utils.get_rgb_from_index(component_enum_data.Color.blue),
        )

        return [circle1, circle2, circle3]


class Pyramid4(_Control):
    """A pyramid nurbs curve control"""

    def _create_shapes(self):
        """Creates pyramid wire shape

        Returns:
            list[nw.Transform]:
        """
        pyramid = cmds.curve(
            degree=1,
            point=[
                [1, 0, 1],
                [1, 0, -1],
                [0, 1.4, 0],
                [1, 0, 1],
                [-1, 0, 1],
                [0, 1.4, 0],
                [-1, 0, -1],
                [-1, 0, 1],
                [-1, 0, -1],
                [1, 0, -1],
            ],
        )
        return [pyramid]


class Sphere(_Control):
    """A sphere nurbs surface control"""

    def _create_shapes(self):
        """Creates sphere nurbs surface shape

        Returns:
            list[nw.Transform]:
        """
        sphere = cmds.sphere(axis=component_enum_data.AxisEnum.y.value)[0]
        return [sphere]


class Locator(_Control):
    """A locator control"""

    _LOC_SCALE = "locScale"

    def _override_build(
        self,
        axis_vec=None,
        color=None,
        build_t=[0, 0, 0],
        build_r=[0, 0, 0],
        build_s=[1, 1, 1],
        xform_map_index=None,
        **kwargs,
    ):
        """Creates control, shapes for control, and applies the build t r s then
        freezes control. maps it to parent container using xform_map_index. also calls post_swap_cleanup to setup scaling

        Args:
            axis_vec (component_enum_data.AxisEnum, optional): _description_. Defaults to None.
            color (Union[ list, utils.Vector, component_enum_data.Color, nw.Attr, nw.Node ], optional): Defaults to None.
            build_t (Union[list, utils.Vector, float], optional): Defaults to [0.0, 0.0, 0.0].
            build_r (Union[list, utils.Vector, float], optional): Defaults to [0.0, 0.0, 0.0].
            build_s (Union[list, utils.Vector, float], optional): Defaults to [1.0, 1.0, 1.0].
            xform_map_index (int, optional): _description_. Defaults to None.
        """
        super()._override_build(
            axis_vec, color, build_t, build_r, build_s, xform_map_index, **kwargs
        )
        self.post_swap_cleanup()

    def _create_shapes(self):
        """Creates locator shape

        Returns:
            list[nw.Transform]:
        """
        return [cmds.spaceLocator()[0]]

    def pre_swap_cleanup(self):
        """unpublishes local scale attribute"""
        self.container_node.unpublish_attr(self.container_node[self._LOC_SCALE])

    def post_swap_cleanup(self):
        """publishes locator.localScaleX attribute and connects it to y and z"""
        loc_shape = self.transform_node.get_shapes()[0]
        loc_shape["localScaleX"] >> loc_shape["localScaleY"]
        loc_shape["localScaleX"] >> loc_shape["localScaleZ"]
        self.container_node.publish_attr(
            loc_shape["localScaleX"], attr_bind_name=self._LOC_SCALE
        )


class DebugMirror(_Control):
    """Debugging used to check mirroring of controls"""

    def _create_shapes(self):
        """Creates debug wire shape

        Returns:
            list[nw.Transform]:
        """
        shape = cmds.curve(
            degree=1, point=[[0, 0, 0], [1, 0, 0], [2, 1, 1], [0, 0, 1], [0, 0, 0]]
        )
        return [shape]
