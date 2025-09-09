import utils.node_wrapper as nw
import system.component_data as component_data
import system.component_enum_data as component_enum_data
from typing import Union

import utils.utils as utils
import maya.cmds as cmds

def get_component(container_node:nw.Container):
    """Gets component from a container

    Args:
        container_node (nw.Node):

    Returns:
        Component: 
    """
    if container_node is None:
        return None
    if container_node.has_attr("componentClass"):
        component_class = utils.string_to_class(container_node["componentClass"].value)
        return component_class(container_node)

class Component():
    """A Base class for all autorigging components

    Attributes:
        component_type (component_enum.ComponentTypes): the component type
        root_transform_name (str): name of root transform. Defaults to None. 
        if true, the input node is a transform node instead of a network node
        class_namespace (str): gives the classes namespace
        container_node (nw.Node): Container node that contains all component nodes
        input_node (nw.Node): Node that all incoming connections come through this node
        output_node (nw.Node): Node that all outgoing connections go through this node
        transform_node (nw.Node): Transform node (also input node). if no transform node 
        is created returns None

        _IN (str): str constant for input
        _BLD_DATA (str): str constant for buildData
        _BLD_COMP_CLASS (str): str constant for componentClass
        _BLD_COMP_TYPE (str): str constant for componentType
        _BLD_INST_NAME (str): str constant for instanceName
        _OUT (str): str constant for output
        _CNTNR_PAR_COMP (str): str constant for parentComponent
        _CNTNR_CHLD_COMP (str): str constant for childComponents
    """
    component_type = component_enum_data.ComponentType.component
    root_transform_name = None
    class_namespace = "component"

    _IN = "input"
    _BLD_DATA = "buildData"
    _BLD_COMP_CLASS = "componentClass"
    _BLD_COMP_TYPE = "componentType"
    _BLD_INST_NAME = "instanceName"
    _OUT = "output"
    _CNTNR_PAR_COMP = "parentComponent"
    _CNTNR_CHLD_COMP = "childComponents"
    _KWG_INST_NAME = "instance_name"
    _KWG_PARENT  = "parent"

    def __init__(self, container_node:nw.Node=None):
        """initializes component with container nodes

        Args:
            container_node (nw.Node, optional): container to initialize with 
            (incase component is already existing). Defaults to None.
        """
        self.__node_data_cache = {}
        if container_node is not None:
            self.__node_data_cache["container_node"] = container_node
    def _get_node_data_from_cache(self, key:str) -> nw.Node:
        """Caching function for all saved nodes so connections don't have to be 
        queried every time. if not cached yet, node is saved

        Args:
            key (str): node key

        Returns:
            nw.Node: node from cache
        """
        if key not in self.__node_data_cache.keys():
            if self.container_node.has_attr(key):
                self.__node_data_cache[key] = self.container_node[key].get_dest_connections()[0].node
            else:
                cmds.warning(f"{key} does not exist on component")
                return
        
        return self.__node_data_cache[key]

    # node attr
    @property 
    def container_node(self)->nw.Container:
        """Container node that contains all component nodes

        Returns:
            nw.Container:
        """
        if "container_node" in self.__node_data_cache.keys():
            return self.__node_data_cache["container_node"]
    @property 
    def input_node(self)->nw.Node:
        """Node that all incoming connections come through this node

        Returns:
            nw.Node:
        """
        if self.container_node is not None:
            return self._get_node_data_from_cache("input_node")
    @property 
    def output_node(self)->nw.Node:
        """Node that all outgoing connections go through this node

        Returns:
            nw.Node:
        """
        if self.container_node is not None:
            return self._get_node_data_from_cache("output_node")
    @property 
    def transform_node(self)->nw.Transform:
        """Transform node (also input node). if no transform node is created 
        returns None

        Returns:
            nw.Node:
        """
        if type(self).root_transform_name is not None:
            return self.input_node
    
    def child_components(self, component_type:component_enum_data.ComponentType=None)->list:
        """_summary_

        Args:
            component_type (component_enum_data.ComponentType): defaults to None

        Returns:
            list: _description_
        """
        containers = [attr.get_dest_connections()[0].node for attr in self.container_node[self._CNTNR_CHLD_COMP]]
        if component_type is not None:
            components = [get_component(container) for container in containers if container.has_attr(self._BLD_COMP_TYPE) and container[self._BLD_COMP_TYPE].value ==  component_type.value]
        else:
            components = [get_component(container) for container in containers]

        return components
    
    @classmethod
    def get_class_name(cls)->str:
        """Gets class name

        Returns:
            str:
        """
        return utils.class_type_to_str(cls)
    
    def get_namespace(self, instance_name:str=None):
        """Generates Namespace. instance_name used to check namespaces before adding them

        Args:
            instance_name (str, optional): replacement instance name. Defaults to None.

        Returns:
            str:
        """
        parent_container = self.container_node.get_container_node()
        if parent_container is not None:
            parent_namespace = utils.Namespace.get_namespace(name=parent_container.name)
        else:
            parent_namespace = ""

        if instance_name is None:
            instance_name = ""
            inst_name_attr = self.input_node[self._BLD_INST_NAME]
            if inst_name_attr.value is not None and inst_name_attr.value != "":
                instance_name = f"{inst_name_attr.value}_"
        else:
            instance_name = utils.strip_characters(instance_name, "_")
            instance_name = f"{instance_name}_"
        postfix = type(self).class_namespace

        return f"{parent_namespace}:{instance_name}{postfix}"

    def _input_attr_build_data(self) -> component_data.NodeData:
        """Defines all the added, published, or modified attributes for the 
        input node. Can be added onto by inherited classes

        Returns:
            comp_data.NodeData:
        """
        node_data =  component_data.NodeData(
            component_data.AttrData(name=self._IN, type_="compound", publish=True),
            component_data.AttrData(name=self._BLD_DATA, type_="compound", publish=True),
            component_data.AttrData(name=self._BLD_COMP_CLASS, type_="string", value=type(self).get_class_name(), locked=True, parent=self._BLD_DATA),
            component_data.AttrData(name=self._BLD_COMP_TYPE, type_=type(self).component_type, locked=True, parent=self._BLD_DATA),
            component_data.AttrData(name=self._BLD_INST_NAME, type_="string", parent=self._BLD_DATA),
        )
        return node_data
    def _output_attr_build_data(self) -> component_data.NodeData:
        """Defines all the added, published, or modified attributes for the 
        output node. Can be added onto by inherited classes

        Returns:
            comp_data.NodeData:
        """
        node_data = component_data.NodeData(
            component_data.AttrData(name=self._OUT, type_="compound", publish=True),
        )
        return node_data
    def _container_attr_build_data(self) -> component_data.NodeData:
        """Defines all the added, published, or modified attributes for the
        container node. Can be added onto by inherited classes

        Returns:
            comp_data.NodeData:
        """
        return component_data.NodeData(
            component_data.AttrData(name=self._CNTNR_PAR_COMP, type_="message"),
            component_data.AttrData(name=self._CNTNR_CHLD_COMP, type_="message", multi=True),
        )

    @classmethod
    def create(cls, instance_name:Union[str, nw.Attr]=None, parent=None):
        """class method to create component

        Args:
            instance_name (str, nw.Attr, optional): name of component. Defaults to None.
            parent (nw.Container, Component, optional): Defaults to None.

        Returns:
            cls: returns created 
        """

        pre_build_kwargs={cls._KWG_INST_NAME: instance_name, cls._KWG_PARENT:parent}
        build_kwargs={}
        post_build_kwargs={}

        return cls._filtered_create(pre_build_kwargs=pre_build_kwargs, build_kwargs=build_kwargs, post_build_kwargs=post_build_kwargs)
    @classmethod
    def _filtered_create(cls, pre_build_kwargs:dict, build_kwargs:dict, post_build_kwargs:dict):
        """creates with kwarg arguments

        Args:
            pre_build_kwargs (dict): 
            build_kwargs (dict): 
            post_build_kwargs (dict): 

        Returns:
            self: 
        """
        component_inst = cls()
        component_inst._pre_build(**pre_build_kwargs)
        component_inst._override_build(**build_kwargs)
        component_inst._post_build(**post_build_kwargs)

        return component_inst
    
    def _pre_build(self, instance_name:Union[str, nw.Attr]=None, parent:Union["Component", nw.Container]=None, **pre_build_kwargs):
        """handles creation and connection of initial nodes and 

        Args:
            instance_name (str, nw.Attr, optional): component instance name. Defaults to None.
            parent (nw.Container, Component, optional): Defaults to None.
        """
        if parent is not None and not isinstance(parent, nw.Container):
            parent = parent.container_node

        if self.container_node is None:
            self.__create_base_nodes(parent_container=parent)
            if instance_name is not None:
                if isinstance(instance_name, nw.Attr):
                    if instance_name.type_ != "string":
                        input_node_name = self.input_node[self._BLD_INST_NAME]
                        cmds.warning(f"{instance_name} is not a string attribute. Not connectiong to {input_node_name}")
                    else:
                        instance_name >> self.input_node[self._BLD_INST_NAME]
                else:
                    self.input_node[self._BLD_INST_NAME]=instance_name
            
            # connecting parent and child components
            if parent is not None:
                if parent.has_attr(self._CNTNR_CHLD_COMP):
                    child_component_len = len(parent[self._CNTNR_CHLD_COMP])
                    parent[self._CNTNR_CHLD_COMP][child_component_len] >> self.container_node[self._CNTNR_PAR_COMP]

                    # parenting transforms
                    parent_component = get_component(parent)
                    if parent_component is not None and parent_component.transform_node is not None and self.transform_node is not None:
                        cmds.parent(str(self.transform_node), str(parent_component.transform_node))
                        
            # renaming to nodes
            self.rename_nodes()
    def _override_build(self, **build_kwargs):
        """Takes care of derived component creation. must be implemented by child class

        Raises:
            NotImplementedError: must be implemented by child classes
        """
        raise NotImplementedError
    def _post_build(self, **post_build_kwargs):
        """Build cleanup. sets build to true and renames nodes
        """
        self.rename_nodes()
    
    def __create_base_nodes(self, parent_container:nw.Container=None):
        """Creates the base node (input, output, container) in the initialization
        phase
        """
        # input node
        if type(self).root_transform_name is not None:
            input_node = nw.create_node("transform", type(self).root_transform_name)
        else:
            input_node = nw.create_node("network", "input")
        input_node_attr_data = self._input_attr_build_data()
        input_node_attr_data.add_attrs_to_node(input_node)

        # output node
        output_node_attr_data = self._output_attr_build_data()
        has_output_node = len(output_node_attr_data.node_attr_dict) > 1
        if has_output_node:
            output_node = nw.create_node("network", "output")
            output_node_attr_data = self._output_attr_build_data()
            output_node_attr_data.add_attrs_to_node(output_node)

        # container node
        self.__node_data_cache["container_node"] = nw.create_node("container", "container")
        container_node_attr_data = self._container_attr_build_data()
        container_node_attr_data.add_attrs_to_node(self.container_node)
        if parent_container is not None:
            parent_container.add_nodes(self.container_node)

        # add to container -> map to container -> publish attributes
        # if output
        component_nodes = [input_node]
        if has_output_node:
            component_nodes.append(output_node)

        self.container_node.add_nodes(*component_nodes)

        utils.map_to_container(input_node, node_message_name="input_node")
        if has_output_node:
            utils.map_to_container(output_node, node_message_name="output_node")
            
            output_node_attr_data.publish_attr_data_attributes(output_node)

        input_node_attr_data.publish_attr_data_attributes(input_node)
        container_node_attr_data.publish_attr_data_attributes(self.container_node)
    def rename_nodes(self):
        """Renames all nodes found in the container with the component namespace"""

        NAME_CLS = utils.Namespace

        namespace = self.get_namespace()
        prev_namespace = NAME_CLS.get_namespace(self.container_node.name)

        # seeing if instance name needs to be changed
        if not NAME_CLS.equal_namespace(prev_namespace, namespace) and NAME_CLS.exists(namespace):

            inst_name_base = self.input_node[self._BLD_INST_NAME].value
            if inst_name_base == None or inst_name_base == "":
                inst_name_base = "temp"
            else:
                inst_name_base = utils.strip_trailing_numbers(inst_name_base)
            index = 1
            while NAME_CLS.exists(self.get_namespace(f"{inst_name_base}{index}")):
                index += 1
            self.input_node[self._BLD_INST_NAME] = f"{inst_name_base}{index}"
            namespace = self.get_namespace()

        # add namespace if it doesn't exist
        if NAME_CLS.exists(prev_namespace) and not NAME_CLS.exists(namespace) and prev_namespace!= ":":
            NAME_CLS.rename(prev_namespace, namespace)
        if not NAME_CLS.exists(namespace):
            NAME_CLS.add_namespace(namespace)

        # renames container
        if not self.container_node.name.startswith(namespace):
            strip_namespace_node = utils.Namespace.strip_namespace(self.container_node.name)
            self.container_node.rename(f"{namespace}:{strip_namespace_node}")

        # renaming nodes
        for node in [node for node in self.container_node.get_nodes() if node.type_!="container"]:
            if not node.name.startswith(namespace):
                strip_namespace_node = utils.Namespace.strip_namespace(node.name)
                node.rename(f"{namespace}:{strip_namespace_node}")

        # if prev namespace is empty, delete it
        if NAME_CLS.exists(prev_namespace) and NAME_CLS.empty(prev_namespace):
            NAME_CLS.delete(prev_namespace)
    def get_parent_type_component(self, parent_type:component_enum_data.ComponentType, disable_warning=False):
        """given a type gets the closest parent component of that type

        Args:
            parent_type (component_enum_data.ComponentType):
            disable_warning (bool):

        Returns:
            Component:
        """
        container = self.container_node
        while container is not None and container[self._BLD_COMP_TYPE].value != component_enum_data.ComponentType.index_of(parent_type):
            container = container.get_container_node()
        if container is not None:
            return get_component(container)
        else:
            if not disable_warning:
                cmds.warning(f"parent component of type {parent_type.name} not found")
            return None
class Control(Component):
    """A Base class for all control autorigging components. Derived from Component

    Attributes:
        can_set_color (bool): can set color of component
    """
    component_type = component_enum_data.ComponentType.control
    root_transform_name = "control"
    class_namespace = "cntrl"
    can_set_color = True

    _IN_OFF_MAT = "offsetMatrix"
    _IN_HAS_CLR = "hasColor"
    _IN_CLR = "color"
    _OUT_WS_MAT = "worldMatrix"
    _OUT_LOC_MAT = "localMatrix"
    _OUT_WS_INV_MAT = "worldInverseMatrix"
    _KWG_AXIS_VEC  = "axis_vec"
    _KWG_CLR = "color"
    _KWG_BUILD_T = "build_t"
    _KWG_BUILD_R = "build_r"
    _KWG_BUILD_S = "build_s"

    @classmethod
    def create(cls,
               instance_name:Union[str, nw.Attr]=None,
               parent=None,
               axis_vec=None,
               build_t=[0.0, 0.0, 0.0],
               build_r=[0.0, 0.0, 0.0],
               build_s=[1.0, 1.0, 1.0],
               color=None):
        pre_buid_kwargs = {
            cls._KWG_INST_NAME:instance_name,
            cls._KWG_PARENT:parent,
        }
        build_kwargs = {
            cls._KWG_AXIS_VEC:axis_vec,
            cls._KWG_CLR: color,
            cls._KWG_BUILD_T: build_t,
            cls._KWG_BUILD_R: build_r,
            cls._KWG_BUILD_S: build_s,
        }
        post_build_kwargs = {}

        return cls._filtered_create(pre_build_kwargs=pre_buid_kwargs, build_kwargs=build_kwargs, post_build_kwargs=post_build_kwargs)

    def _input_attr_build_data(self) -> component_data.NodeData:
        node_data = super()._input_attr_build_data()

        node_data.extend_attr_data(
            component_data.AttrData(name="offsetParentMatrix", publish=self._IN_OFF_MAT),
            component_data.AttrData(name="worldMatrix[0]", publish=self._OUT_WS_MAT),
            component_data.AttrData(name="matrix", publish=self._OUT_LOC_MAT),
            component_data.AttrData(name="worldInverseMatrix[0]", publish=self._OUT_WS_INV_MAT),

            component_data.AttrData(name="overrideEnabled", publish=self._IN_HAS_CLR, locked=not type(self).can_set_color),
            component_data.AttrData(name="overrideColorRGB", publish=self._IN_CLR, locked=not type(self).can_set_color),
            component_data.AttrData(name="overrideRGBColors", value=1),
        )
        return node_data
    def _override_build(self, axis_vec=None, color=None, build_t=[0.0, 0.0, 0.0], build_r=[0.0, 0.0, 0.0], build_s=[1.0, 1.0, 1.0],  **build_kwargs):
        # set visibility to hidden in channel box
        self.transform_node["visibility"].set_keyable(False)

        # add shapes
        self._apply_shape_to_cntrl(axis_vec=axis_vec)

        # add build transforms
        self.transform_node["translate"].set(utils.make_len(build_t, len_=3) if utils.is_iterable(build_t) else [build_t, build_t, build_t])
        self.transform_node["rotate"].set(utils.make_len(build_r, len_=3) if utils.is_iterable(build_r) else [build_r, build_r, build_r])
        self.transform_node["scale"].set(utils.make_len(build_s, len_=3, default=1.0) if utils.is_iterable(build_s) else [build_s, build_s, build_s])
        self.transform_node.freeze_transforms()
        if color is not None:
            self.apply_color(color)
    def _create_shapes(self, axis_vec) -> list:
        """Creates shapes and returns a list of the shapes transforms. these 
        shapes will be parented to the transform node later

        Args:
            axis_vec(vector, component_enum_data.AxisEnum):

        Returns:
            list(nw.Node):
        """
        raise NotImplementedError
    def _apply_shape_to_cntrl(self, cntrl_transform:nw.Transform=None, component_container:nw.Container=None, axis_vec=None):
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

        # axis vec
        if axis_vec is None:
            axis_vec = component_enum_data.AxisEnum.y.value
        elif component_enum_data.get_enum_item_class(axis_vec) == component_enum_data.AxisEnum:
            axis_vec = axis_vec.value

        # parenting to transform
        shape_transforms = self._create_shapes(axis_vec=axis_vec)
        for transform in shape_transforms:
            if not isinstance(transform, nw.Node):
                transform = nw.wrap_node(transform)

            # delete history
            cmds.delete(str(transform), constructionHistory=True)

            # freeze all controls
            transform.freeze_transforms()

            # apply to transform
            for x in cmds.listRelatives(str(transform), shapes=True, fullPath=True):
                cmds.parent(x, str(cntrl_transform), relative=True, shape=True)
        
        # deleting transforms
        if shape_transforms != []:
            cmds.delete(shape_transforms)

        shapes_list = cntrl_transform.get_shapes()
    
        # rename shapes
        transform_stripped_name = utils.Namespace.strip_namespace(str(cntrl_transform))
        for index, shape in enumerate(shapes_list):
            shape.rename(f"{transform_stripped_name}Shape{index+1}")

        # add shapes to container
        if component_container is not None:
            component_container.add_nodes(*shapes_list)
    
    def apply_color(self, color: Union[component_enum_data.Color, list, nw.Node]):
        """Applies color to control

        Args:
            color (Union[component_enum_data.Color, list, nw.Node]): 
        # """
        
        if self.container_node[self._IN_HAS_CLR].is_locked():
            return
        else:
            rgb = [1.0, 1.0, 1.0]
            shader = None
            surface_shapes = [shape for shape in self.transform_node.get_shapes() if shape.type_ == "mesh" or shape.type_ == "nurbsSurface"]
            if isinstance(color, nw.Node) and color.type_ == "lambert":
                shader = color
            elif isinstance(color, component_enum_data.Color):
                from component.enum_manager import Color
                shader = Color.get_shader(color)
            if isinstance(color, list):
                rgb = utils.make_len(color, len_=3, default=1.0)

            self.container_node[self._IN_HAS_CLR] = True
            if shader is not None:
                if len(surface_shapes) > 0:
                    utils.apply_shader_group(surface_shapes, shader)
                utils.apply_display_color(nodes=[self.transform_node], color=shader["color"])
            else:
                utils.apply_display_color(nodes=[self.transform_node], color=rgb)
    def promote_attr_to_keyable(self, attr:nw.Attr, name=None, **kwargs):
        """Turns attribute given into a controllable attribute by the control

        Args:
            attr (nw.Attr): attribute to be driven by control
            name (str, optional): new name of controllable attribute.
            Defaults to None.
        """
        
        def get_num_min_max_kwargs(attr:nw.Attr):
            # has max and mins
            kwargs={}
            if attr_type in ["double", "long"]:
                for attr_exists, attr_query_key, attr_add_key in zip(
                    ["softMaxExists", "softMinExists", "maxExists", "minExists"],
                    ["softMax", "softMin", "maximum", "minimum"],
                    ["softMaxValue", "softMinValue", "maxValue", "minValue"]):

                    if cmds.attributeQuery(attr.short_name, node=str(attr.node), **{attr_exists:True}):
                        kwargs[attr_add_key] = cmds.attributeQuery(attr.short_name, node=str(attr.node), **{attr_query_key:True})[0]

            return kwargs

        transform_node = self.transform_node
        if kwargs == {}:
            attr_type = attr.type_
            if attr_type == "compound":
                raise RuntimeError("{} of type compound. compound type not supported".format(attr))

            if name is None:
                name = attr.short_name

            # non settable
            if attr_type in ["string", "nurbsCurve", "nurbsSurface","mesh", "matrix", "message"]:
                warn_str = "{} of type {} is not keyable. attribute created without keyable".format(attr, attr_type)
                cmds.warning(warn_str)
            else:
                kwargs["keyable"] = True

            # has max and mins
            if attr_type in ["double", "long"]:
                kwargs.update(get_num_min_max_kwargs(attr))

            # enum
            if attr_type == "enum":
                enum_string = cmds.attributeQuery(attr.short_name, node=str(attr.node), listEnum=True)
                kwargs["enumName"] = enum_string[0]

            # compound attrs
            if attr_type in ["double3", "double2"]:
                transform_node.add_attr(name, type=attr_type, **kwargs)
                for child_attr in attr:
                    child_kwargs = get_num_min_max_kwargs(child_attr)
                    child_name = child_attr.attr_name.replace(attr.attr_name, name)
                    transform_node.add_attr(child_name, parent=name, type=child_attr.type_, **kwargs, **child_kwargs)
            
            else:
                transform_node.add_attr(name, type=attr_type, **kwargs)

            attr_connection = attr.get_connections(as_dest=True, as_src=False)
            if attr_connection == [] and attr_type not in ["nurbsCurve", "nurbsSurface","mesh", "message"]:
                try:
                    transform_node[name] = attr.value
                except:
                    pass
                transform_node[name] >> attr
            else:
                attr_connection[0] >> transform_node[name]
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

    def swap_control(self, replace_component:Union[type, "Control", nw.Transform]):
        if not isinstance(replace_component, nw.Transform):
            if isinstance(replace_component, type):
                replace_component = replace_component()

            self.pre_swap_cleanup()
            self.container_node[self._BLD_COMP_CLASS] = replace_component.get_class_name()

            cmds.delete([str(x) for x in self.transform_node.get_shapes()])
            replace_component._apply_shape_to_cntrl(
                cntrl_transform=self.transform_node,
                component_container=self.container_node
            )
            new_component = type(replace_component)(self.container_node)
            new_component.post_swap_cleanup()
            return new_component
        else:
            raise NotImplementedError("swap_control replace_component type \"Transform\" not implemented yet")
class SingletonComponent(Component):
    """Has instance method. only one of each singleton component exists in a character.
    usually used for enum conversion data (enum->vec)

    Attributes:
        __cls_instance (cls):
    """
    component_type = component_enum_data.ComponentType.manager
    __cls_instance = None

    @classmethod
    def instance(cls):
        """Gets the instance of class. create one of not created

        Returns:
            cls:
        """
        if cls.__cls_instance is None:
            cls.__cls_instance = cls.create()
            return cls.__cls_instance
        else:
            return cls.__cls_instance
class Hierarchy(Component):
    """A Class meant to be inherited for all hierarchy classes. hierarchy in this
    case is defined as a chain of matricies 

    Attributes:
        HIER_DATA (component_data.HierData): stores all Hier names and hier check
        functions
        IO_ENUM (component_enum_data.IO): stores input output enum
    """
    class_namespace = "hier"
    component_type = component_enum_data.ComponentType.hier

    HIER_DATA = component_data.HierData
    IO_ENUM = component_enum_data.IO
    _PRM_VEC = "primaryVec"
    _PRM_VEC_X = "primaryVecX"
    _PRM_VEC_Y = "primaryVecY"
    _PRM_VEC_Z = "primaryVecZ"
    _SEC_VEC = "secondaryVec"
    _SEC_VEC_X = "secondaryVecX"
    _SEC_VEC_Y = "secondaryVecY"
    _SEC_VEC_Z = "secondaryVecZ"
    _TER_VEC = "tertiaryVec"
    _TER_VEC_X = "tertiaryVecX"
    _TER_VEC_Y = "tertiaryVecY"
    _TER_VEC_Z = "tertiaryVecZ"
    _KWG_CNTRL_CLR = "control_color"
    _KWG_SRC_COMP = "source_component"
    _KWG_CONN_HIER = "connect_hierarchy"
    _KWG_CONN_AXS_VEC = "connect_axis_vec"
    _KWG_INIT_NUM_XFORMS = "init_num_xforms"
    _KWG_CNTR_CLR = "control_color"

    @classmethod
    def create(cls, 
               instance_name:Union[str, nw.Attr]=None, 
               parent:Component=None, 
               init_num_xforms:Union[int, tuple]=0, 
               source_component:Component=None, 
               connect_hierarchy:bool=True, 
               connect_axis_vecs:bool=True, 
               control_color=None):
        pre_build_kwargs={
            cls._KWG_INST_NAME: instance_name, 
            cls._KWG_PARENT:parent,
            cls._KWG_SRC_COMP:source_component,
            cls._KWG_CONN_HIER:connect_hierarchy,
            cls._KWG_CONN_AXS_VEC:connect_axis_vecs,
            cls._KWG_INIT_NUM_XFORMS:init_num_xforms}
        build_kwargs={
            cls._KWG_CNTR_CLR:control_color
        }
        post_build_kwargs={}
        
        return cls._filtered_create(pre_build_kwargs=pre_build_kwargs, build_kwargs=build_kwargs, post_build_kwargs=post_build_kwargs)
    def _pre_build(self, instance_name:Union[str, nw.Attr]=None, parent:Component=None, init_num_xforms:Union[int, tuple]=0, source_component:Component=None, connect_hierarchy:bool=None, connect_axis_vec:bool=True, **pre_build_kwargs):
        super()._pre_build(instance_name, parent)            
        init_num_xforms = self._check_init_num_xforms(init_num_xforms=init_num_xforms, source_component=source_component)

        #initialize
        for index, io in enumerate([self.IO_ENUM.input, self.IO_ENUM.output]):
            xforms = self.get_xform_attrs(xform_type=io , index=utils.length_index_list(init_num_xforms[index]))
            
            xform_name = self.HIER_DATA.INPUT_XFORM_NAME if io == self.IO_ENUM.input else self.HIER_DATA.OUTPUT_XFORM_NAME
            for xform_index, xform in xforms.items():
                xform[xform_name].set(f"xform{xform_index}")
        
        #connect source component
        if source_component is not None:
            self._connect_source_hier_component(source_component=source_component, connect_hierarchy=connect_hierarchy, connect_axis_vec=connect_axis_vec)
    def _override_build(self, control_color=None, **build_kwargs):
        return super()._override_build(**build_kwargs)
    def _post_build(self, **post_build_kwargs):
        super()._post_build()
        self.__populate_output_xforms()
        self.rename_nodes()
        self._check_output_xforms()
    
    def _input_attr_build_data(self):
        node_data = super()._input_attr_build_data()
        node_data.extend_attr_data(self.HIER_DATA.get_hier_data())
        node_data.extend_attr_data(self.HIER_DATA.get_input_xform_data())
        return node_data
    def _output_attr_build_data(self):
        node_data = super()._output_attr_build_data()
        node_data.extend_attr_data(self.HIER_DATA.get_output_xform_data())
        node_data.extend_attr_data(
            component_data.AttrData(self._PRM_VEC, type_="double3", parent=self._OUT, value=[1, 0, 0]),
            component_data.AttrData(self._PRM_VEC_X, type_="double", parent=self._PRM_VEC),
            component_data.AttrData(self._PRM_VEC_Y, type_="double", parent=self._PRM_VEC),
            component_data.AttrData(self._PRM_VEC_Z, type_="double", parent=self._PRM_VEC),
            component_data.AttrData(self._SEC_VEC, type_="double3", parent=self._OUT, value=[0, 1, 0]),
            component_data.AttrData(self._SEC_VEC_X, type_="double", parent=self._SEC_VEC),
            component_data.AttrData(self._SEC_VEC_Y, type_="double", parent=self._SEC_VEC),
            component_data.AttrData(self._SEC_VEC_Z, type_="double", parent=self._SEC_VEC),
            component_data.AttrData(self._TER_VEC, type_="double3", parent=self._OUT, value=[0, 0, 1]),
            component_data.AttrData(self._TER_VEC_X, type_="double", parent=self._TER_VEC),
            component_data.AttrData(self._TER_VEC_Y, type_="double", parent=self._TER_VEC),
            component_data.AttrData(self._TER_VEC_Z, type_="double", parent=self._TER_VEC),
        )
        return node_data
    def __populate_output_xforms(self):
        """Goes through the output xform attributes and tries to connect name, local matrix, and init matricies"""
        added_nodes = []
        HIER_DATA = self.HIER_DATA
        output_xforms = self.get_xform_attrs(xform_type=self.IO_ENUM.output)
        for index, output_xform in output_xforms.items():
            # init inverse matrix
            added_nodes.extend(self.__populate_world_matrix(
                index=index,
                world_matrix_attr=output_xform[HIER_DATA.OUTPUT_INIT_MATRIX],
                world_matrix_inv_attr=output_xform[HIER_DATA.OUTPUT_INIT_INV_MATRIX],
                is_init_matrix=True))
            self.__populate_name(index)
            added_nodes.extend(self.__populate_world_matrix(
                index=index,
                world_matrix_attr=output_xform[HIER_DATA.OUTPUT_WORLD_MATRIX],
                world_matrix_inv_attr=output_xform[HIER_DATA.OUTPUT_WORLD_INV_MATRIX]))
            added_nodes.extend(self.__populate_loc_matrix(index=index))

        # add nodes to container
        self.container_node.add_nodes(*added_nodes)
    def __populate_name(self, index:int):
        """Given the index tries to connect or set the output name

        Args:
            index (int): xform index
        """
        # set variables
        output_name = self.output_node[self.HIER_DATA.OUTPUT_XFORM][index][self.HIER_DATA.OUTPUT_XFORM_NAME]
        if output_name.has_src_connection():
            return
        input_name = self.input_node[self.HIER_DATA.INPUT_XFORM][index][self.HIER_DATA.INPUT_XFORM_NAME]
        output_ws_src = self.output_node[self.HIER_DATA.OUTPUT_XFORM][index][self.HIER_DATA.OUTPUT_WORLD_MATRIX].get_src_connection()
        
        # check if needs to be set
        if output_name.value is not None and output_name.value != "":
            pass

        # if input and output xform match
        elif (len(self.input_node[self.HIER_DATA.INPUT_XFORM]) ==
            len(self.output_node[self.HIER_DATA.OUTPUT_XFORM])):
            input_name >> output_name
        
        elif output_ws_src is not None:
            if output_ws_src.node.has_attr(self._BLD_INST_NAME):
                output_ws_src.node[self._BLD_INST_NAME] >> output_name
    def __populate_world_matrix(self, index:int, world_matrix_attr:nw.Attr, world_matrix_inv_attr:nw.Attr, is_init_matrix:bool=False):
        """Given the index tries to connect or set the output init matrix and output inverse init matrix

        Args:
            index (int): xform index
        """
        matrix_src = world_matrix_attr.get_src_connection()
        inv_matrix_src = world_matrix_inv_attr.get_src_connection()

        inverse_name = f"xform{index}_inverse"
        if is_init_matrix:
            inverse_name = f"xform{index}_init_inverse"

        input_xform = self.get_xform_attrs(xform_type=self.IO_ENUM.input, index=index)
        output_xform = self.get_xform_attrs(xform_type=self.IO_ENUM.output, index=index)

        added_nodes = []
        # pre check to see if it needs to return anything
        if inv_matrix_src is not None and matrix_src is not None:
            return []
        if inv_matrix_src is None and matrix_src is not None:
            if isinstance(matrix_src.node, nw.Transform):
                matrix_src.node["worldInverseMatrix"][0] >> world_matrix_inv_attr
            else:
                matrix_src_connections = [attr.node for attr in matrix_src.get_dest_connections() if attr.node.type_ == "inverseMatrix"]
                if matrix_src_connections == []:
                    inverse_node = nw.create_node("inverseMatrix", name=inverse_name)
                    inverse_node["inputMatrix"] << matrix_src
                    inverse_node["outputMatrix"] >> world_matrix_inv_attr
                    added_nodes.append(inverse_node)
                else:
                    matrix_src_connections[0]["outputMatrix"] >> world_matrix_inv_attr
        elif matrix_src is None and inv_matrix_src is not None:
            if isinstance(inv_matrix_src.node, nw.Transform):
                inv_matrix_src.node["worldMatrix"][0] >> world_matrix_attr
            elif inv_matrix_src.node.type_ == "inverseMatrix":
                new_matrix_src = inv_matrix_src.node["inputMatrix"].get_src_connection()
                if new_matrix_src is not None:
                    new_matrix_src >> world_matrix_attr

        elif is_init_matrix and len(input_xform.keys()) == len(output_xform.keys()):
            if matrix_src is None:
                input_xform[self.HIER_DATA.INPUT_INIT_MATRIX] >> world_matrix_attr
            if inv_matrix_src is None:
                input_xform[self.HIER_DATA.INPUT_INIT_INV_MATRIX] >> world_matrix_inv_attr
        return added_nodes
    def __populate_loc_matrix(self, index:int):
        """Given the index tries to connect or set the output local matrix

        Args:
            index (int): xform index
        """
        output_xform_attrs = self.get_xform_attrs(xform_type=self.IO_ENUM.output, index=index)
        output_loc_matrix = output_xform_attrs[self.HIER_DATA.OUTPUT_LOC_MATRIX]
        output_world_matrix_src = output_xform_attrs[self.HIER_DATA.OUTPUT_WORLD_MATRIX].get_src_connection()
        added_nodes = []

        if output_loc_matrix.has_src_connection():
            return []
        elif output_world_matrix_src is None:
            return []
        
        # connect to parent
        else:
            if index == 0:
                prev_world_inv_matrix_src = self.container_node[self.HIER_DATA.HIER_PARENT_INV_MATRIX]
            else:
                prev_world_inv_matrix_src = self.container_node[self.HIER_DATA.OUTPUT_XFORM][index-1][self.HIER_DATA.OUTPUT_WORLD_INV_MATRIX]
                prev_world_inv_matrix_src = prev_world_inv_matrix_src.get_src_connection()
            if prev_world_inv_matrix_src is None:
                return []

            # adding matrix mult
            mat_mult = nw.create_node("multMatrix", f"xform{index}_loc_output_mat_mult")
            mat_mult["matrixIn"][0] << output_world_matrix_src
            mat_mult["matrixIn"][1] << prev_world_inv_matrix_src
            mat_mult["matrixSum"] >> output_loc_matrix

            added_nodes.append(mat_mult)

            return added_nodes

    def _check_init_num_xforms(self, init_num_xforms:Union[int, tuple]=0, source_component:Component=None):
        """Checks  init_num_xforms before it builds the xforms. returns list of 2 for input and output num for initialization

        Args:
            init_num_xforms (Union[int, tuple], optional): Defaults to 0.
            source_component (Component, optional):  Defaults to None.

        Returns:
            list:
        """
        # initialize xforms
        if isinstance(init_num_xforms, tuple):
            init_num_xforms=utils.make_len(list(init_num_xforms), len_=2, default=0)
        else:
            init_num_xforms=[init_num_xforms, init_num_xforms]
        # limiting it to be as long as source component
        if source_component is not None and self._has_xforms(source_component=source_component, xform_type=self.IO_ENUM.output):
            src_output_len = len(source_component.container_node[self.HIER_DATA.OUTPUT_XFORM])
            if src_output_len > init_num_xforms[0]:
                init_num_xforms[0] = src_output_len
        # limiting output to be as long as input initialization
        if init_num_xforms[1] > init_num_xforms[0]:
            init_num_xforms[1] = init_num_xforms[0]

        return init_num_xforms
    def _check_output_xforms(self, check_len=True):
        """After component is built, checks to see if xforms were properly set"""
        if check_len:
            input_xform_len = len(self.input_node[self.HIER_DATA.INPUT_XFORM])
            output_xform_len = len(self.output_node[self.HIER_DATA.OUTPUT_XFORM])
            if output_xform_len == 0:
                cmds.warning(f"{self.container_node} component has no xform output")

            if input_xform_len > output_xform_len:
                cmds.warning(f"input xform (len {input_xform_len}) longer than output xform (len {output_xform_len})")

        for xform_attr in self.output_node[self.HIER_DATA.OUTPUT_XFORM]:
            for xform_sub_attr in xform_attr:
                if xform_sub_attr.type_ == "string":
                    if xform_sub_attr.value == None or xform_sub_attr.value == "":
                        cmds.warning(f"{xform_sub_attr} not set")
                elif not xform_sub_attr.has_src_connection():
                    cmds.warning(f"{xform_sub_attr} does not have connection")
    def get_xform_attrs(self, xform_type:component_enum_data.IO, index:Union[int, list]=None):
        """Gets a dict of xforms given indicies and type of xform. returns all if index is None

        Args:
            xform_type (component_enum_data.IO): selects input or output xform
            index (int, list):
        Returns:
            dict: 
        """
        
        if index is None:
            if self.container_node.has_attr(self.HIER_DATA.INPUT_XFORM):
                indicies = range(len(self.container_node[self.HIER_DATA.INPUT_XFORM]))
            else:
                indicies = range(len(self.container_node[self.HIER_DATA.OUTPUT_XFORM]))
                
        else:
            indicies = utils.make_iterable(index)
        xform_names = self.HIER_DATA.get_xform_names(xform_type=xform_type)
        xform_parent_name = self.HIER_DATA.get_xform_parent_name(xform_type=xform_type)
        xform_data = {index:{key: self.container_node[xform_parent_name][index][key] for key in xform_names} for index in indicies}
        if isinstance(index, int) and index is not None:
            return list(xform_data.values())[0]
        else:
            return xform_data
    def _set_xform_attrs(
            self, 
            index:int, 
            xform_type:component_enum_data.IO,
            xform_name:Union[nw.Attr, str]=None, 
            init_matrix:nw.Attr=None, 
            init_inv_matrix:nw.Attr=None, 
            world_matrix:nw.Attr=None,
            world_inv_matrix:nw.Attr=None,
            loc_matrix:nw.Attr=None,
            disable_warning:bool=False,
        ):
        """Connects up attributes to output xform

        Args:
            index (int):
            input_name (Union[nw.Attr, str], optional): Defaults to None.
            input_init_matrix (nw.Attr, optional): Defaults to None.
            input_init_inv_matrix (nw.Attr, optional): Defaults to None.
            input_world_matrix (nw.Attr, optional): Defaults to None.
            input_world_inv_matrix (nw.Attr, optional): Defaults to None.
            input_loc_matrix (nw.Attr, optional): Defaults to None.
            disable_warning (bool):disables warnings
        """
        xform_matricies = self.get_xform_attrs(xform_type=xform_type, index=index)
        src_attr_list = [xform_name, init_matrix, init_inv_matrix, world_matrix, world_inv_matrix, loc_matrix]
        xform_names = self.HIER_DATA.get_xform_names(xform_type=xform_type)
        if len(src_attr_list) != len(xform_names):
            raise RuntimeError("source_attr_list and xform_names mismatched lengths")
        for src_attr, dest_attr in zip(src_attr_list, xform_names):
            if not xform_matricies[dest_attr].has_src_connection():
                if isinstance(src_attr, str):
                    xform_matricies[dest_attr].set(src_attr)
                elif src_attr is not None:
                    src_attr >> xform_matricies[dest_attr]
            elif not disable_warning:
                cmds.warning(f"{xform_matricies[dest_attr]} has connection. unable to connect {src_attr} to it")
    def _has_xforms(self, source_component:Component=None, xform_type:component_enum_data.IO=component_enum_data.IO.output):
        """checks to see if component has xforms
        
        Args:
            source_component (Component): component to check
        Returns:
            bool:
        """
        if source_component is None:
            return False
        if source_component.container_node.has_attr(self.HIER_DATA.get_xform_parent_name(xform_type=xform_type)):
            if xform_type == self.IO_ENUM.output and self.HIER_DATA.is_output_xform_attr(source_component.container_node[self.HIER_DATA.OUTPUT_XFORM][0]):
                return True
            elif xform_type == self.IO_ENUM.input and self.HIER_DATA.is_input_xform_attr(source_component.container_node[self.HIER_DATA.INPUT_XFORM][0]):
                return True
        return False
    def _initialize_xforms(self, xform_type:component_enum_data.IO, len_:int):
        """initializes xform with xform{index} for names to len len_

        Args:
            xform_type (component_enum_data.IO):
            len_ (int):
        """
        pass

    def _connect_source_hier_component(self, source_component:Component, connect_hierarchy:bool=True, connect_axis_vec:bool=True):
        """Given a source Hier component connects it's hier output to this component's hier input
        

        Args:
            source_component (Component):
            connect_hierarchy (bool): connects hierarchy from source
            connect_axis_vec (bool): connects axis vec from source
        """
        if self._has_xforms(source_component=source_component, xform_type=self.IO_ENUM.output):
            HIER_DATA = self.HIER_DATA

            # getting both containers
            self_container = self.container_node
            source_container = source_component.container_node
            parent_component_as_source = True if source_container == self_container.get_container_node() else False
            if parent_component_as_source and not self._has_xforms(xform_type=self.IO_ENUM.input, source_component=source_component):
                raise RuntimeError(f"source parent component ({source_component.container_node}) does not have input xforms")

            src_type = self.IO_ENUM.input if parent_component_as_source else self.IO_ENUM.output
            src_xforms =  source_component.get_xform_attrs(src_type)
            self_input_xforms = self.get_xform_attrs(xform_type=self.IO_ENUM.input, index=utils.length_index_list(len(src_xforms.keys())))
            for index, src_xform in src_xforms.items():

                input_xform = self_input_xforms[index]
                # for loop through attributes to connect
                for src_name, self_input_name in HIER_DATA.get_paired_names(src=src_type, dest=self.IO_ENUM.input):
                    src_xform[src_name] >> input_xform[self_input_name]

            # if connect_hierarchy
            if connect_hierarchy:
                for hier_attr_name in HIER_DATA.HIER_DATA_NAMES:
                    if source_container.has_attr(hier_attr_name):
                        source_container[hier_attr_name] >> self_container[hier_attr_name]   

            # connecting axis vectors
            if connect_axis_vec:
                for attr in [self._PRM_VEC, self._SEC_VEC, self._TER_VEC]:
                    if source_container.has_attr(attr) and self_container.has_attr(attr):
                        source_container[attr] >> self_container[attr]
            
        else:
            raise RuntimeError(f"{source_component} does not have output xforms")
    def _create_orient_translate_blend(self, name:str, matrix_attr:nw.Attr, tx_attr:nw.Attr=None, ty_attr:nw.Attr=None, tz_attr:nw.Attr=None, tw_attr:nw.Attr=None):
        """Creates a blended matrix where the translate values are overriden

        Args:
            name (str): 
            matrix_attr (nw.Attr): matrix to blend from
            tx_attr (nw.Attr): translate X attr. Defaults to None.
            ty_attr (nw.Attr): translate Y attr. Defaults to None.
            tz_attr (nw.Attr): translate Z attr. Defaults to None.
            tw_attr (nw.Attr, optional): translate W attr. Defaults to None.
        """
        row_nodes = []
        matrix_4x4 = nw.create_node("fourByFourMatrix", f"{name}_4x4_mat")
        # translate matrix
        for index, t_attr in enumerate([tx_attr, ty_attr, tz_attr, tw_attr]):
            if t_attr is not None:
                matrix_4x4[f"in3{index}"] << t_attr

        # orient part of the matrix
        for row_index in range(3):
            row_node = nw.create_node("rowFromMatrix", f"{name}_row{row_index}")
            row_node["input"] = row_index
            row_node["matrix"] << matrix_attr

            for col_index, axis in enumerate(["X", "Y", "Z", "W"]):
                matrix_4x4[f"in{row_index}{col_index}"] << row_node[f"output{axis}"]
            row_nodes.append(row_node)
        
        self.container_node.add_nodes(matrix_4x4, *row_nodes)
        return matrix_4x4
class Motion(Hierarchy):
    """Base class for motion autorigging components. Derived from Hierarchy"""
    component_type = component_enum_data.ComponentType.motion
    root_transform_name = "grp"
    class_namespace = "motion"

class Anim(Hierarchy):
    """Base class for anim autorigging components. Derived from Hierarchy"""
    component_type = component_enum_data.ComponentType.anim
    _setup_component_type = utils.string_to_class("component.setup.Setup")
    root_transform_name = "grp"
    class_namespace = "anim"
    
    _IN_PRM_AXIS = "primaryAxis"
    _IN_SEC_AXIS = "secondaryAxis"
    _HIER_SIDE = "hierSide"
    _IN_SET_XFORM_FOLLOW_INDEX = "settingXformFollowIndex"
    _IN_SET_CNTRL_LOC_MAT = "inputSettingCntrlLocMatrix"
    _OUT_SET_CNTRL_LOC_MAT = "outputSettingCntrlLocMatrix"

    _KWG_HIER_SIDE = "hier_side"
    _KWG_SETUP_CLR = "setup_color"
    _KWG_PRM_AXIS = "primary_axis"
    _KWG_SEC_AXIS = "secondary_axis"
    _KWG_ADD_SETTINGS_CNTRL = "add_settings_cntrl"
    _KWG_MIRROR_SRC = "mirror_source"
    
    import component.setup as setup
    @property
    def setup_component_type(self):
        """Returns class specific _setup_component_type. works for inherited classes"""
        return type(self)._setup_component_type
    @property
    def setup_component(self)->setup.Setup:
        """Returns setup component

        Returns:
            setup.Setup:
        """
        if self.container_node is not None:
            if self.container_node.has_attr("setup_container"):
                return get_component(self._get_node_data_from_cache("setup_container"))
    @property
    def settings_component(self)->Control:
        """Returns settings component (if one exists)

        Returns:
            Control:
        """
        if self.container_node is not None:
            if self.container_node.has_attr("settings_container"):
                return get_component(self._get_node_data_from_cache("settings_container"))
    @property
    def settings_guide_component(self)->Control:
        """Returns settings guide component (if one exists)

        Returns:
            Control:
        """
        if self.container_node is not None:
            if self.container_node.has_attr("settings_guide_container"):
                return get_component(self._get_node_data_from_cache("settings_guide_container"))

    def _input_attr_build_data(self):
        node_data = super()._input_attr_build_data()
        node_data.extend_attr_data(
            component_data.AttrData(self._IN_PRM_AXIS, type_=component_enum_data.AxisEnum.x, publish=True),
            component_data.AttrData(self._IN_SEC_AXIS, type_=component_enum_data.AxisEnum.y, publish=True),
            component_data.AttrData(self._HIER_SIDE, type_=component_enum_data.CharacterSide.none, publish=True),
            component_data.AttrData(self._IN_SET_XFORM_FOLLOW_INDEX, type_="long", parent=self._IN, min=0),
            component_data.AttrData(self._IN_SET_CNTRL_LOC_MAT, type_="matrix", parent=self._IN),
        )
        return node_data 
    def _output_attr_build_data(self):
        node_data = super()._output_attr_build_data()
        node_data.extend_attr_data(
            component_data.AttrData(self._OUT_SET_CNTRL_LOC_MAT, type_="matrix", parent=self._OUT)
        )
        return node_data

    def get_namespace(self, instance_name = None):
        namespace = super().get_namespace(instance_name)
        prefix = f"{component_enum_data.CharacterSide.get(self.input_node['hierSide'].value).value}_"
        if prefix == f"{component_enum_data.CharacterSide.none.value}_":
            prefix = ""
        parent_namespace, curr_namespace = namespace.rsplit(":", 1)
        return f"{parent_namespace}:{prefix}{curr_namespace}"

    @classmethod
    def create(cls, 
               instance_name:Union[str, nw.Attr]=None, 
               parent:Component=None, 
               init_num_xforms:Union[int, tuple]=0, 
               primary_axis:component_enum_data.AxisEnum=component_enum_data.AxisEnum.x,
               secondary_axis:component_enum_data.AxisEnum=component_enum_data.AxisEnum.y,
               add_settings_cntrl:bool=True,
               mirror_source:"Anim"=None,
               source_component:Component=None, 
               connect_hierarchy:bool=True, 
               connect_axis_vecs:bool=True, 
               control_color=None,
               setup_color=None,
               hier_side:component_enum_data.CharacterSide=component_enum_data.CharacterSide.none):
        pre_build_kwargs={
            cls._KWG_INST_NAME: instance_name, 
            cls._KWG_PARENT:parent,
            cls._KWG_SRC_COMP:source_component,
            cls._KWG_HIER_SIDE: hier_side,
            cls._KWG_PRM_AXIS: primary_axis,
            cls._KWG_SEC_AXIS: secondary_axis,
            cls._KWG_CONN_HIER:connect_hierarchy,
            cls._KWG_CONN_AXS_VEC:connect_axis_vecs,
            cls._KWG_INIT_NUM_XFORMS:init_num_xforms,
            cls._KWG_ADD_SETTINGS_CNTRL:add_settings_cntrl,
            cls._KWG_MIRROR_SRC:mirror_source,
            cls._KWG_SETUP_CLR:setup_color,
            cls._KWG_CNTR_CLR:control_color,}
        build_kwargs={
            cls._KWG_CNTR_CLR:control_color,
        }
        post_build_kwargs={}
        
        return cls._filtered_create(pre_build_kwargs=pre_build_kwargs, build_kwargs=build_kwargs, post_build_kwargs=post_build_kwargs)
    
    def mirror(self, control_color=None, setup_color=None):
        pass

    def __set_vectors(self, mirror_source:"Anim"=None):
        """Creates nodes for primary, secondary, and tertiary vectors

        Args:
            mirror_source (Anim, optional): Defaults to None.

        Raises:
            NotImplementedError: mirror not currently implemented
        """
        char_component = self.get_parent_type_component(component_enum_data.ComponentType.character, disable_warning=True)
        # adding prim, sec, ter vectors
        axis_vec_choice_node = None
        if char_component is not None and char_component:
            axis_vec_choice_node = char_component.axis_vec_choice_node
        else:
            import component.enum_manager as enum_manager
            axis_vec_choice_node = enum_manager.axis_vec_choice_node

        primary_choice_node = axis_vec_choice_node(choice_node_name="primary_vec_choice", enum_attr=self.container_node[self._IN_PRM_AXIS])
        secondary_choice_node = axis_vec_choice_node(choice_node_name="primary_vec_choice", enum_attr=self.container_node[self._IN_SEC_AXIS])
        primary_axis_attr = primary_choice_node["output"]
        secondary_axis_attr = secondary_choice_node["output"]
        if mirror_source:
            raise NotImplementedError("mirror not implemented yet")
        tertiary_vec = nw.create_node("crossProduct", "tertiary_vec_prod")
        tertiary_vec["input1"] << primary_axis_attr
        tertiary_vec["input2"] << secondary_axis_attr
        tertiary_vec["output"] >> self.container_node[self._TER_VEC]

        self.container_node[self._PRM_VEC] << primary_axis_attr
        self.container_node[self._SEC_VEC] << secondary_axis_attr

        self.container_node.add_nodes(primary_choice_node, secondary_choice_node, tertiary_vec)
    def __create_setup_component(self, init_num_xforms:Union[int, tuple]=0, setup_color=None, mirror_source:"Anim"=None):
        """Creates setup component and maps it to container

        Args:
            init_num_xforms (Union[int, tuple], optional): . Defaults to 0.
            setup_color (Any, optional): . Defaults to None.
            mirror_source (Anim, optional): . Defaults to None.
        """
        if mirror_source is None:
            build_setup = self.setup_component_type
        else:
            build_setup = utils.string_to_class("component.setup.Mirror")

        setup_inst = build_setup.create(init_num_xforms=init_num_xforms, control_color=setup_color, parent=self, source_component=self)
        setup_inst.container_node[setup_inst._IN_SET_XFORM_FOLLOW_INDEX] << self.container_node[self._IN_SET_XFORM_FOLLOW_INDEX]
        setup_inst.container_node[setup_inst._IN_SET_CNTRL_LOC_MAT] << self.container_node[self._IN_SET_CNTRL_LOC_MAT]
        setup_inst.container_node[setup_inst._OUT_SET_CNTRL_LOC_MAT] >> self.container_node[self._OUT_SET_CNTRL_LOC_MAT]
        utils.map_to_container(setup_inst.container_node, "setup_container")
        self.container_node[self._IN_SET_XFORM_FOLLOW_INDEX].set(len(self.get_xform_attrs(self.IO_ENUM.input)) - 1)
    def __create_settings_cntrls(self, setup_color=None, control_color=None):
        settings_init_choice = nw.create_node("choice", "settings_init_choice")
        settings_choice = nw.create_node("choice", "settings_choice")
        settings_init_choice["selector"] << self.container_node[self._IN_SET_XFORM_FOLLOW_INDEX]
        settings_choice["selector"] << self.container_node[self._IN_SET_XFORM_FOLLOW_INDEX]
        settings_mult = nw.create_node("multMatrix", "settings_ws_mult")
        
        # setting up controls
        import component.control as control
        settings_init = control.Locator.create(instance_name="settings_guide", parent=self, color=setup_color)
        settings_init.promote_attr_to_keyable(self.container_node[self._IN_SET_XFORM_FOLLOW_INDEX])
        settings_init.transform_node["translate"] = [1, 1, 1]
        settings = control.Gear.create(instance_name="settings", parent=self, color=control_color)
        utils.map_to_container(settings_init.container_node, "settings_guide_container")
        utils.map_to_container(settings.container_node, "settings_container")
        for attr in ["t", "r", "s"]:
            for axis in ["x", "y", "z"]:
                settings.transform_node[f"{attr}{axis}"].set_locked(True)
                settings.transform_node[f"{attr}{axis}"].set_keyable(False)
        self.setup_component.container_node[self.setup_component._OUT_SET_CNTRL_LOC_MAT] << settings.container_node[settings._OUT_LOC_MAT]

        # inserting offset matrix to control
        settings_init.container_node[settings_init._IN_OFF_MAT] << settings_init_choice["output"]
        settings.container_node[settings_init._IN_OFF_MAT] << settings_mult["matrixSum"]
        settings_mult["matrixIn"][0] << settings_init.container_node[settings_init._OUT_LOC_MAT]
        settings_mult["matrixIn"][1] << settings_choice["output"]

        anim_output_xforms = self.container_node[self.HIER_DATA.OUTPUT_XFORM]
        for index, output_xform in enumerate(anim_output_xforms):
            settings_init_choice["input"][index] << output_xform[self.HIER_DATA.OUTPUT_INIT_MATRIX]
            settings_choice["input"][index] << output_xform[self.HIER_DATA.OUTPUT_WORLD_MATRIX]

        self.container_node.add_nodes(settings_init_choice, settings_choice)

    def _pre_build(self, 
                   instance_name:Union[str, nw.Attr]=None, 
                   parent:Component=None, 
                   init_num_xforms:Union[int, tuple]=0, 
                   hier_side:component_enum_data.CharacterSide=component_enum_data.CharacterSide.none, 
                   primary_axis:component_enum_data.AxisEnum=component_enum_data.AxisEnum.x,
                   secondary_axis:component_enum_data.AxisEnum=component_enum_data.AxisEnum.y,
                   add_settings_cntrl:bool=True,
                   mirror_source:"Anim"=None,
                   setup_color=None,
                   control_color=None,
                   source_component:Component=None, 
                   connect_hierarchy:bool=None, 
                   connect_axis_vec:bool=True, 
                   **pre_build_kwargs):
        # calling super
        super()._pre_build(
            instance_name=instance_name, 
            parent=parent, 
            init_num_xforms=init_num_xforms, 
            source_component=source_component, 
            connect_hierarchy=connect_hierarchy, 
            connect_axis_vec=connect_axis_vec, 
            **pre_build_kwargs)
        # setting values
        self.container_node[self._HIER_SIDE]=hier_side.name
        self.container_node[self._IN_PRM_AXIS]=primary_axis.name
        self.container_node[self._IN_SEC_AXIS]=secondary_axis.name

        # populating primary, secondary, and tertiary vectors
        self.__set_vectors(mirror_source=mirror_source)

        # create setup component
        self.__create_setup_component(init_num_xforms=init_num_xforms, setup_color=setup_color, mirror_source=mirror_source)

        # adding settings cntrl
        if add_settings_cntrl:
            self.__create_settings_cntrls(setup_color=setup_color, control_color=control_color)
            
        self.rename_nodes()
    def _override_build(self, control_color=None, **build_kwargs):
        return super()._override_build(control_color, **build_kwargs)