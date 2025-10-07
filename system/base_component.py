import utils.node_wrapper as nw
import system.component_data as component_data
import system.component_enum_data as component_enum_data
from typing import Union

import utils.utils as utils
import maya.cmds as cmds

def get_component(container_node:nw.Container) -> "Component":
    """Gets component from a container

    Args:
        container_node (nw.Node):

    Returns:
        Component: 
    """
    if container_node is None:
        return None
    if container_node.has_attr("componentClass") and isinstance(container_node, nw.Container):
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
    lock_transform = True

    _IN = "input"
    _BLD_DATA = "buildData"
    _BLD_COMP_CLASS = "componentClass"
    _BLD_COMP_TYPE = "componentType"
    _BLD_INST_NAME = "instanceName"
    _BLD_INST_FORM = "instanceFormat"
    _OUT = "output"
    _CNTNR_PAR_COMP = "parentComponent"
    _CNTNR_CHLD_COMP = "childComponents"
    _CNTNR_CNTRL_CHLDRN = "controlChildren"
    _MIRROR_SRC = "mirrorSource"
    _MIRROR_DEST = "mirrorDest"
    _KWG_INST_NAME = "instance_name"
    _KWG_PARENT  = "parent"


    def __init__(self, container_node:nw.Node=None):
        """initializes component with container nodes

        Args:
            container_node (nw.Node, optional): container to initialize with 
            (incase component is already existing). Defaults to None.
        """
        self._node_data_cache = {}
        if container_node is not None:
            self._node_data_cache["container_node"] = container_node
    def _get_node_from_cache(self, key:str) -> nw.Node:
        """Caching function for all saved nodes so connections don't have to be 
        queried every time. if not cached yet, node is saved

        Args:
            key (str): node key

        Returns:
            nw.Node: node from cache
        """
        if key not in self._node_data_cache.keys():
            if self.container_node.has_attr(key):
                self._node_data_cache[key] = self.container_node[key].get_dest_connections()[0].node
            else:
                cmds.warning(f"{key} does not exist on component")
                return
        
        return self._node_data_cache[key]
    def _get_node_from_key(self, key:str, as_component:bool=False) ->nw.Node:
        """Check for container before returning cached node

        Args:
            key (str):
            as_component (bool): tries to cast node to component

        Returns:
            nw.Node:
        """
        if self.container_node is not None:
            node = self._get_node_from_cache(key)
            if as_component:
                curr_component = get_component(node)
                if curr_component is None:
                    return node
                return curr_component
            return node    

    # node attr
    @property 
    def container_node(self)->nw.Container:
        """Container node that contains all component nodes

        Returns:
            nw.Container:
        """
        if "container_node" in self._node_data_cache.keys():
            return self._node_data_cache["container_node"]
    @property 
    def input_node(self)->nw.Node:
        """Node that all incoming connections come through this node

        Returns:
            nw.Node:
        """
        return self._get_node_from_key("input_node")
    @property 
    def output_node(self)->nw.Node:
        """Node that all outgoing connections go through this node

        Returns:
            nw.Node:
        """
        return self._get_node_from_key("output_node")
    @property 
    def transform_node(self)->nw.Transform:
        """Transform node (also input node). if no transform node is created 
        returns None

        Returns:
            nw.Node:
        """
        if type(self).root_transform_name is not None:
            return self.input_node
    
    def child_components(self, component_type:component_enum_data.ComponentType=None)->list["Component"]:
        """gets child components

        Args:
            component_type (component_enum_data.ComponentType): defaults to None

        Returns:
            list:
        """
        containers = [attr.get_dest_connections()[0].node for attr in self.container_node[self._CNTNR_CHLD_COMP]]
        if component_type is not None:
            components = [get_component(container) for container in containers if container.has_attr(self._BLD_COMP_TYPE) and container[self._BLD_COMP_TYPE].value ==  component_type.value]
        else:
            components = [get_component(container) for container in containers]

        return components
    def get_all_descendants(self, component_type:component_enum_data.ComponentType=None)->list["Component"]:
        """Gets all descendent components

        Args:
            component_type (component_enum_data.ComponentType, optional): filters to component type. Defaults to None.

        Returns:
            list:
        """
        descendants = self.child_components()

        index = 0
        while(index < len(descendants)):
            curr_children = descendants[index].child_components()
            descendants.extend(curr_children)
            index += 1
        if component_type is not None:
            descendants = [component for component in descendants if component.container_node.has_attr(self._BLD_COMP_TYPE) and component.container_node[self._BLD_COMP_TYPE].value ==  component_type.value]
        return descendants
    
    # namespaces
    @classmethod
    def get_class_name(cls)->str:
        """Gets class name

        Returns:
            str:
        """
        return utils.class_type_to_str(cls)
    def get_short_namespace(self, instance_name:str=None):
        """Generates namespace without parentent namespace attached

        Args:
            instance_name (str, optional): Defaults to None.
        """
        format_str = self.container_node[self._BLD_INST_FORM].value
        if instance_name is None:
            instance_name = self.container_node[self._BLD_INST_NAME].value
        
        if instance_name is None:
            instance_name = ""

        return utils.strip_characters(format_str.format(instance_name), "_", leading=True, trailing=False)
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

        return f"{parent_namespace}:{self.get_short_namespace(instance_name)}"

    # build attributes
    def _input_attr_build_data(self) -> component_data.NodeData:
        """Defines all the added, published, or modified attributes for the 
        input node. Can be added onto by inherited classes

        Returns:
            comp_data.NodeData:
        """
        node_data = component_data.NodeData(
            component_data.AttrData(name=self._IN, type_="compound", publish=True),
            component_data.AttrData(name=self._BLD_DATA, type_="compound", publish=True),
            component_data.AttrData(name=self._BLD_COMP_CLASS, type_="string", value=type(self).get_class_name(), locked=True, parent=self._BLD_DATA),
            component_data.AttrData(name=self._BLD_COMP_TYPE, type_=type(self).component_type, locked=True, parent=self._BLD_DATA),
            component_data.AttrData(name=self._BLD_INST_NAME, type_="string", parent=self._BLD_DATA),
            component_data.AttrData(name=self._BLD_INST_FORM, type_="string", parent=self._BLD_DATA, value=f"{{}}_{type(self).class_namespace}"),
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
            component_data.AttrData(name=self._CNTNR_CNTRL_CHLDRN, type_="message", multi=True)
        )

    @classmethod
    def create(cls, instance_name:Union[str, nw.Attr]=None, parent:Union["Component", nw.Container]=None):
        """Class method to create component

        Args:
            instance_name (str, nw.Attr, optional): name of component. Defaults to None.
            parent (nw.Container, Component, optional): Defaults to None.

        Returns:
            cls: returns created 
        """
        pre_build_kwargs, build_kwargs, post_build_kwargs = cls._process_kwargs(instance_name=instance_name, parent=parent)

        return cls._filtered_create(pre_build_kwargs=pre_build_kwargs, build_kwargs=build_kwargs, post_build_kwargs=post_build_kwargs)
    @classmethod
    def _process_kwargs(cls, instance_name:Union[str, nw.Attr]=None, parent:Union["Component", nw.Container]=None):
        """Process the different args to be sorted into pre, post, and override build. 

        Args:
            instance_name (Union[str, nw.Attr], optional): _description_. Defaults to None.
            parent (Union[&quot;Component&quot;, nw.Container], optional): _description_. Defaults to None.

        Returns:
            list[dict]:
        """
        pre_build_kwargs={
            cls._KWG_INST_NAME: instance_name,
            cls._KWG_PARENT:parent
        }
        build_kwargs={}
        post_build_kwargs={}

        return pre_build_kwargs, build_kwargs, post_build_kwargs
    @classmethod
    def _filtered_create(cls, pre_build_kwargs:dict, build_kwargs:dict, post_build_kwargs:dict):
        """Creates with kwarg arguments

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
                utils.set_connect_attr_data(self.input_node[self._BLD_INST_NAME], instance_name)
            
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
            
            # see if transform trs is locked
            if type(self).lock_transform:
                for attr in ["t", "r", "s"]:
                    input_node[attr].set_locked(True)
                    for axis in ["x", "y", "z"]:
                        input_node[f"{attr}{axis}"].set_keyable(False)
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
        self._node_data_cache["container_node"] = nw.create_node("container", "container")
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

        for child_comp in self.child_components():
            child_comp.rename_nodes()

    def get_parent_type_component(self, parent_type:component_enum_data.ComponentType, disable_warning=False)->"Component":
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
    def mirror_component(self)->"Component":
        """Gets mirror component. Returns None if none found
        
        Returns:
            Component:
        """
        def get_container_namespace(container:nw.Container):
            """gets short namespace from container

            Args:
                container (nw.Container):

            Returns:
                str:
            """
            format_str = container[self._BLD_INST_FORM].value
            inst_name = container[self._BLD_INST_NAME].value
            format_args = [inst_name if inst_name is not None else ""]

            if format_str.count("{}") > 1:
                hier_side = component_enum_data.CharacterSide.get(container['hierSide'].value).value
                if hier_side == f"{component_enum_data.CharacterSide.none.value}":
                    hier_side = ""
                format_args.insert(0, hier_side)

            return utils.strip_characters(format_str.format(*format_args), "_", leading=True, trailing=False)
            
        # stack data constants
        COMP_LEN = "comp_len"
        COMP_INDEX = "comp_index"
        COMP_NAMESPC = "comp_namespace"

        # getting source component data
        curr_container = self.container_node
        mirror_container = None
        component_data = []
        while curr_container is not None:
            if curr_container.has_attr(self._MIRROR_SRC):
                curr_container[self._MIRROR_SRC]
                mirror_container = curr_container[self._MIRROR_SRC].get_dest_connections()[0].node
                break
            elif curr_container.has_attr(self._MIRROR_DEST):
                mirror_container = curr_container[self._MIRROR_DEST].get_src_connection().node
                break
            if curr_container.has_attr(self._CNTNR_PAR_COMP):
                par_comp_attr = curr_container[self._CNTNR_PAR_COMP]
                connection = par_comp_attr.get_src_connection()
                if connection is None:
                    break

                component_data.append({
                    COMP_LEN: len(connection.parent),
                    COMP_INDEX: connection.index,
                    COMP_NAMESPC: get_container_namespace(curr_container),
                })
                curr_container = curr_container.get_container_node()
            else:
                break

        # if no mirror root component found
        if mirror_container is None:
            return None

        # getting mirror component
        for mirror_data in component_data[::-1]:
            child_attrs = mirror_container[self._CNTNR_CHLD_COMP]
            if len(child_attrs) == mirror_data[COMP_LEN]:
                mirror_container = child_attrs[mirror_data[COMP_INDEX]].get_dest_connections()[0].node
                continue
            else:
                mirror_container = None
                for attr in child_attrs:
                    new_cntnr = attr.get_dest_connections()[0].node
                    new_cntnr_namespace = get_container_namespace(new_cntnr)
                    if new_cntnr_namespace == mirror_data[COMP_NAMESPC]:
                        mirror_container = new_cntnr
                        break
                if mirror_container is not None:
                    continue
            return None
        if mirror_container is None:
            return None
        else:
            return get_component(mirror_container)
        
class Control(Component):
    """A Base class for all control autorigging components. Derived from Component

    Attributes:
        can_set_color (bool): can set color of component
    """
    component_type = component_enum_data.ComponentType.control
    root_transform_name = "control"
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
    _KWG_AXIS_VEC  = "axis_vec"
    _KWG_CLR = "color"
    _KWG_BUILD_T = "build_t"
    _KWG_BUILD_R = "build_r"
    _KWG_BUILD_S = "build_s"
    _KWG_XFORM_MAP_INDEX = "xform_map_index"

    @classmethod
    def create(cls,
               instance_name:Union[str, nw.Attr]=None,
               parent:Union["Component", nw.Container]=None,
               axis_vec:component_enum_data.AxisEnum=None,
               build_t=[0.0, 0.0, 0.0],
               build_r=[0.0, 0.0, 0.0],
               build_s=[1.0, 1.0, 1.0],
               color=None,
               xform_map_index:int=None):
        pre_buid_kwargs, build_kwargs, post_build_kwargs = cls._process_kwargs(instance_name=instance_name, parent=parent, axis_vec=axis_vec, build_t=build_t, build_r=build_r, build_s=build_s, color=color, xform_map_index=xform_map_index)
        return cls._filtered_create(pre_build_kwargs=pre_buid_kwargs, build_kwargs=build_kwargs, post_build_kwargs=post_build_kwargs)
    @classmethod
    def _process_kwargs(cls, 
                        instance_name:Union[str, nw.Attr]=None,
                        parent:Union["Component", nw.Container]=None,
                        axis_vec:component_enum_data.AxisEnum=None,
                        build_t=[0.0, 0.0, 0.0],
                        build_r=[0.0, 0.0, 0.0],
                        build_s=[1.0, 1.0, 1.0],
                        color=None,
                        xform_map_index:int=None):
        pre_build_kwargs, build_kwargs, post_build_kwargs = super()._process_kwargs(instance_name, parent)
        build_kwargs.update({
            cls._KWG_AXIS_VEC:axis_vec,
            cls._KWG_CLR: color,
            cls._KWG_BUILD_T: build_t,
            cls._KWG_BUILD_R: build_r,
            cls._KWG_BUILD_S: build_s,
            cls._KWG_XFORM_MAP_INDEX: xform_map_index
        })
        return pre_build_kwargs, build_kwargs, post_build_kwargs

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
    def _container_attr_build_data(self):
        node_data = super()._container_attr_build_data()
        node_data.extend_attr_data(
            component_data.AttrData(name=self._CNTNR_CNTRL_MAP, type_="message"),
        )
        return node_data
    def _pre_build(self, instance_name = None, parent = None, **pre_build_kwargs):
        super()._pre_build(instance_name, parent, **pre_build_kwargs)
    
    def _override_build(self, axis_vec:component_enum_data.AxisEnum=None, color=None, build_t=[0.0, 0.0, 0.0], build_r=[0.0, 0.0, 0.0], build_s=[1.0, 1.0, 1.0], xform_map_index:int=None, **build_kwargs):
        # set visibility to hidden in channel box
        self.transform_node["visibility"].set_keyable(False)

        # add shapes
        self._apply_shape_to_cntrl(axis_vec=axis_vec)

        parent_container = self.container_node.get_container_node()
        if parent_container is not None and xform_map_index is not None and xform_map_index >= 0:
            parent_container[self._CNTNR_CNTRL_CHLDRN][xform_map_index] >> self.container_node[self._CNTNR_CNTRL_MAP]

        # add build transforms
        self.transform_node["translate"].set(utils.make_len(build_t, len_=3) if utils.is_iterable(build_t) else [build_t, build_t, build_t])
        self.transform_node["rotate"].set(utils.make_len(build_r, len_=3) if utils.is_iterable(build_r) else [build_r, build_r, build_r])
        self.transform_node["scale"].set(utils.make_len(build_s, len_=3, default=1.0) if utils.is_iterable(build_s) else [build_s, build_s, build_s])
        self.transform_node.freeze_transforms()
        if color is not None:
            self.apply_color(color)
    def _create_shapes(self) -> list:
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
            shape.rename(f"{transform_stripped_name}Shape{index+1}")

        # add shapes to container
        if component_container is not None:
            component_container.add_nodes(*shapes_list)

        # axis vec
        if axis_vec is not None and axis_vec and component_enum_data.get_enum_item_class(axis_vec) == component_enum_data.AxisEnum:
            axis_vec = utils.Vector(axis_vec.value)
        if axis_vec is not None and axis_vec != utils.Vector(component_enum_data.AxisEnum.y.value):
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

    def replace_control(self, replace_component:Union[type, "Control", nw.Transform], color=None):
        """Replaces control with replace_component. could be component type, control, and transform

        Args:
            replace_component (Union[type, Control, nw.Transform]): _description_
            color (any, optional): Defaults to None.

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

            self.container_node[self._BLD_COMP_CLASS] = replace_component.get_class_name()

            replace_component._apply_shape_to_cntrl(
                cntrl_transform=self.transform_node,
                component_container=self.container_node
            )
            replace_component_class = type(replace_component)

        if isinstance(replace_component, nw.Transform):
            transform_node = replace_component
        elif replace_component_class is None:
            transform_node = replace_component.transform_node
            if transform_node is None:
                raise RuntimeError(f"no replace transform found in {replace_component.container_node}")
            replace_component_class = type(replace_component)
        
        # renaming shapes
        if transform_node is not None:
            mirror_transform = nw.wrap_node(cmds.duplicate(str(transform_node))[0])
            for index, shape in enumerate(mirror_transform.get_shapes()):
                cmds.parent(str(shape), str(self.transform_node), relative=True, shape=True)
                shape.rename(f"{self.transform_node}Shape{index+1}")
            cmds.delete(str(mirror_transform))

        # adding shapes to container
        self.container_node.add_nodes(*self.transform_node.get_shapes())
        self.rename_nodes()
        
        if replace_component_class is not None:
            new_component = type(replace_component)(self.container_node)
            new_component.container_node[self._BLD_COMP_CLASS] = new_component.get_class_name()
            new_component.post_swap_cleanup()
        else:
            new_component = self

        

        # apply color
        if color is not None:
            self.apply_color(color=color)

        return new_component
        

        # else:
        #     raise NotImplementedError("swap_control replace_component type \"Transform\" not implemented yet")
class Singleton(Component):
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
class Matrix(Component):
    component_type = component_enum_data.ComponentType.matrix
    class_namespace = "matrix"
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
    _max_num_xforms = (-1, -1)

    HIER_DATA = component_data.HierData
    IO_ENUM = component_enum_data.IO
    XFORM = component_data.Xform
    HIER_PARENT = component_data.HierParent
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
    _KWG_SRC_COMP = "source_component"
    _KWG_CONN_HIER = "connect_hierarchy"
    _KWG_CONN_AXS_VEC = "connect_axis_vec"
    _KWG_INPUT_XFORMS = "input_xforms"
    _KWG_CNTR_CLR = "control_color"

    @classmethod
    def create(cls, 
               instance_name:Union[str, nw.Attr]=None, 
               parent:Component=None, 
               input_xforms:Union[list[component_data.Xform], int]=None, 
               source_component:Component=None, 
               connect_hierarchy:bool=True, 
               connect_axis_vecs:bool=True, 
               control_color=None):
        pre_build_kwargs, build_kwargs, post_build_kwargs=cls._process_kwargs(
            instance_name=instance_name, 
            parent=parent, 
            input_xforms=input_xforms, 
            source_component=source_component, 
            connect_hierarchy=connect_hierarchy, 
            connect_axis_vecs=connect_axis_vecs, 
            control_color=control_color)
        
        return cls._filtered_create(pre_build_kwargs=pre_build_kwargs, build_kwargs=build_kwargs, post_build_kwargs=post_build_kwargs)
    @classmethod
    def _process_kwargs(cls, 
                        instance_name:Union[str, nw.Attr]=None, 
                        parent:Component=None, 
                        input_xforms:Union[list[component_data.Xform], int]=[], 
                        source_component:Component=None, 
                        connect_hierarchy:bool=True, 
                        connect_axis_vecs:bool=True, 
                        control_color=None):
        pre_build_kwargs, build_kwargs, post_build_kwargs = super()._process_kwargs(instance_name, parent)
        pre_build_kwargs.update({
            cls._KWG_INST_NAME: instance_name, 
            cls._KWG_PARENT:parent,
            cls._KWG_SRC_COMP:source_component,
            cls._KWG_CONN_HIER:connect_hierarchy,
            cls._KWG_CONN_AXS_VEC:connect_axis_vecs,
            cls._KWG_INPUT_XFORMS:input_xforms})
        build_kwargs.update({
            cls._KWG_CNTR_CLR:control_color
        })
        return pre_build_kwargs, build_kwargs, post_build_kwargs

    def _pre_build(self, instance_name:Union[str, nw.Attr]=None, parent:Component=None, input_xforms:Union[list[component_data.Xform], int]=None,  source_component:Component=None, connect_hierarchy:bool=None, connect_axis_vec:bool=True, **pre_build_kwargs):
        super()._pre_build(instance_name, parent)            

        source_xforms = None
        if source_component is not None and hasattr(source_component, "get_as_source_xforms"):
            source_xforms = source_component.get_as_source_xforms(is_parent_component=utils.if_container_is_ancestor(child=self.container_node, ancestor=source_component.container_node))
        
        self.__initialize_input_xform(input_xforms=input_xforms, source_xforms=source_xforms)
        
        #connect source component
        if source_xforms is not None:
            self._connect_source_component(source_component=source_component, source_xforms=source_xforms, connect_hierarchy=connect_hierarchy, connect_axis_vec=connect_axis_vec)
    def _override_build(self, control_color=None, **build_kwargs):
        return super()._override_build(**build_kwargs)
    def _post_build(self, **post_build_kwargs):
        super()._post_build()
        self.__populate_output_xforms()
        self.rename_nodes()
        self._check_output_xforms()
    
    def _input_attr_build_data(self):
        node_data = super()._input_attr_build_data()
        node_data.extend_attr_data(self.HIER_DATA.get_hier_parent_data())
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
    #pre build
    def __initialize_input_xform(self, input_xforms:Union[list[component_data.Xform], int]=None, source_xforms:list=None):
        """initializes input xform

        Args:
            input_xforms (Union[list[component_data.Xform], int], optional): Defaults to [].
            source_xforms (list, optional): Defaults to None.

        Raises:
            RuntimeError: if list contains item that is not component_data
        """
        max_input_len, max_output_len = type(self)._max_num_xforms
        input_xforms_len = 0
        if max_input_len == -1 and source_xforms is not None:
            max_input_len = len(source_xforms)
        elif max_input_len == -1 and isinstance(input_xforms, int):
            max_input_len = input_xforms
        elif max_input_len == -1 and isinstance(input_xforms, list):
            input_xforms_len = len(input_xforms)
            max_input_len = input_xforms_len
        elif max_input_len == -1:
            max_input_len = -1
            cmds.warning(f"{self.container_node} xforms not initialized")
        elif isinstance(input_xforms, list):
            input_xforms_len = len(input_xforms)
        
        if max_output_len < max_input_len:
            max_output_len = max_input_len

        for index in range(max_output_len):
            # input
            init_xform = self.XFORM(xform_name=f"xform{index}")
            if index < max_input_len:
                input_xform = init_xform
                if index < input_xforms_len:
                    input_xform=input_xforms[index]
                self._set_xform_attrs(
                    index=index,
                    xform_type=self.IO_ENUM.input,
                    xform=input_xform,
                    set_when_data_is_attr=True
                )
            self._set_xform_attrs(
                index=index,
                xform_type=self.IO_ENUM.output,
                xform=init_xform,
                set_when_data_is_attr=True
            )
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
        elif (len(self.input_node[self.HIER_DATA.INPUT_XFORM]) >=
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
        input_xform = self.get_xform_attrs(xform_type=self.IO_ENUM.input)
        output_xform = self.get_xform_attrs(xform_type=self.IO_ENUM.output)

        inverse_name = f"xform{index}_inverse"
        if is_init_matrix:
            inverse_name = f"xform{index}_init_inverse"

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

        elif world_matrix_attr.attr_name.find("Init") >= 0 and len(input_xform.keys()) == len(output_xform.keys()):
            if matrix_src is None:
                input_xform[index].init_matrix >> world_matrix_attr
            if inv_matrix_src is None:
                input_xform[index].init_inv_matrix >> world_matrix_inv_attr

        return added_nodes
    def __populate_loc_matrix(self, index:int):
        """Given the index tries to connect or set the output local matrix

        Args:
            index (int): xform index
        """
        output_xform = self.get_xform_attrs(xform_type=self.IO_ENUM.output, index=index)
        output_loc_matrix = output_xform.loc_matrix
        output_world_matrix_src = output_xform.world_matrix.get_src_connection()
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
    def __populate_output_xforms(self):
        """Goes through the output xform attributes and tries to connect name, local matrix, and init matricies"""
        added_nodes = []
        output_xforms = self.get_xform_attrs(xform_type=self.IO_ENUM.output)
        for index, output_xform in output_xforms.items():
            self.__populate_name(index)
            added_nodes.extend(self.__populate_world_matrix(
                index=index,
                world_matrix_attr=output_xform.init_matrix,
                world_matrix_inv_attr=output_xform.init_inv_matrix,
                is_init_matrix=True))
            added_nodes.extend(self.__populate_world_matrix(
                index=index,
                world_matrix_attr=output_xform.world_matrix,
                world_matrix_inv_attr=output_xform.world_inv_matrix))
            added_nodes.extend(self.__populate_loc_matrix(index=index))
            
        # add nodes to container
        self.container_node.add_nodes(*added_nodes)
    def _connect_source_component(self, source_component:Component, source_xforms:list[component_data.Xform], connect_hierarchy:bool=True, connect_axis_vec:bool=True):
        """Given a source Hier component connects it's hier output to this component's hier input
        
        Args:
            source_component (Component):
            connect_hierarchy (bool): connects hierarchy from source
            connect_axis_vec (bool): connects axis vec from source
        """
        # getting both containers
        self_container = self.container_node
        source_container = source_component.container_node

        max_input_xform = type(self)._max_num_xforms[0]
        if max_input_xform >= 0 and max_input_xform < len(source_xforms):
            source_xforms = source_xforms[:max_input_xform]
        for index, xform in enumerate(source_xforms):
            self._set_xform_attrs(
                index=index,
                xform_type=self.IO_ENUM.input,
                xform=xform,
            )

        # if connect_hierarchy
        if connect_hierarchy:
            if hasattr(source_component, "get_hier_parent_attrs"):
                self._set_hier_parent_attrs(source_component.get_hier_parent_attrs())

        # connecting axis vectors
        if connect_axis_vec:
            for attr in [self._PRM_VEC, self._SEC_VEC, self._TER_VEC]:
                if source_container.has_attr(attr) and self_container.has_attr(attr):
                    source_container[attr] >> self_container[attr]
    #post build
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
    def get_as_source_xforms(self, is_parent_component=True):
        """When it is the source component returns xforms to be plugged in

        Args:
            is_parent_component (bool, optional): _description_. Defaults to True.

        Returns:
            list(component_data.Xform):
        """
        xform_type = self.IO_ENUM.input if is_parent_component else self.IO_ENUM.output
        return [x for x in self.get_xform_attrs(xform_type=xform_type).values()]
    #xform and hierarchy
    def get_xform_attrs(self, xform_type:component_enum_data.IO, index:Union[int, list]=None):
        """Gets a dict of xforms given indicies and type of xform. returns all if index is None

        Args:
            xform_type (component_enum_data.IO): selects input or output xform
            index (int, list):
        Returns:
            dict:
        """
        if index is None:
            input_len = 0
            if self.container_node.has_attr(self.HIER_DATA.INPUT_XFORM):
                input_len = len(self.container_node[self.HIER_DATA.INPUT_XFORM])
            if self.HIER_DATA.is_input_enum(xform_type):
                indicies = utils.length_index_list(input_len)
            else:
                output_len = len(self.container_node[self.HIER_DATA.OUTPUT_XFORM])
                if output_len > input_len:
                    indicies = utils.length_index_list(output_len)
                else:
                    indicies = utils.length_index_list(input_len)
        else:
            indicies = utils.make_iterable(index)
        xform_parent_name = self.HIER_DATA.get_xform_parent_name(xform_type=xform_type)
        xform_data = {index: self.XFORM(self.container_node[xform_parent_name][index]) for index in indicies}
        if isinstance(index, int) and index is not None:
            return list(xform_data.values())[0]
        else:
            return xform_data
    def _set_xform_attrs(self, index:int, xform:component_data.Xform, xform_type:component_enum_data.IO, set_when_data_is_attr:bool=False):
        """Sets xform

        Args:
            index (int): 
            xform (component_data.Xform): 
            xform_type (component_enum_data.IO): 
            set_when_data_is_attr (bool, optional): only sets and not connects if it's an attribute. Defaults to False.
        """
        set_xform = self.get_xform_attrs(xform_type=xform_type, index=index)
        for xform_attr, set_xform_attr in zip(xform, set_xform):
            if xform_attr is not None:
                utils.set_connect_attr_data(attr=set_xform_attr, data=xform_attr, set_when_data_is_attr=set_when_data_is_attr)
    def get_hier_parent_attrs(self):
        """gets hier parent attr and wraps it in HierParent class

        Returns:
            component_data.HierParent:
        """
        return self.HIER_PARENT(self.container_node[self.HIER_DATA.HIER_PARENT])
    def _set_hier_parent_attrs(self, hier_parent:component_data.HierParent, set_when_data_is_attr:bool=False):
        """Sets HierParent

        Args:
            hier_parent (component_data.HierParent): 
            set_when_data_is_attr (bool, optional): Defaults to False.
            disable_warning (bool, optional): Defaults to False.
        """
        for hier_parent, set_hier_parent in zip(hier_parent, self.get_hier_parent_attrs()):
            if hier_parent is not None:
                utils.set_connect_attr_data(attr=set_hier_parent, data=hier_parent, set_when_data_is_attr=set_when_data_is_attr)
    # hooking
    def hook(self, hook_src_data):
        """Hooks xform to hier parent

        Args:
            hook_src_data (any): _description_
        """
        # get parent hier that can be hooked first
        hier_parent = self.unhook()

        # convert hook data (go from highest level hier)
        hier_src_data = self.get_hook_source_data(hook_src_data=hook_src_data)

        for hook_src, hook_hier_parent in zip(hier_src_data, hier_parent):
            hook_src >> hook_hier_parent
    def unhook(self):
        """Unhooks Hierarchy

        Returns:
            component_data.HierParent:
        """
        hier_parent = self.get_hook_hier_parent()
        
        for attr in hier_parent:
            if attr.has_src_connection():
                ~attr
        return hier_parent

    def __get_hier_parent_source(self, hier_parent:component_data.HierParent):
        """Gets hier parent source and casts it to hier parent. returns none if source is not hier parent

        Args:
            hier_parent (component_data.HierParent):

        Returns:
            component_data.HierParent:
        """
        hier_parent_attr = None
        for attr in hier_parent.attrs:
            # has source connection
            if attr.has_src_connection():
                src_connection = attr.get_src_connection()
                if src_connection.parent is not None:
                    connection_parent = src_connection.parent
                    hier_parent_attr = connection_parent
                    if self.HIER_DATA.is_hier_parent_attr(connection_parent):
                        continue
            return None
        return self.HIER_PARENT(hier_parent_attr=hier_parent_attr)
    def get_hook_hier_parent(self):
        """gets setable hier parent meaning hier parent isn't connected to another hier parent

        Returns:
            component_data.HierParent:
        """
        curr_hier_parent = self.get_hier_parent_attrs()
        while True:
            next_hier_parent = self.__get_hier_parent_source(curr_hier_parent)
            if next_hier_parent is None:
                return curr_hier_parent
            curr_hier_parent = next_hier_parent
    def get_hook_source_data(self, hook_src_data):
        """converts hook_src_data to component_data.hierParent

        Args:
            hook_src_data (any):

        Returns:
            component_data.hierParent:
        """
        control_inst=None
        if isinstance(hook_src_data, nw.Transform) and hook_src_data.get_container_node() is not None:
            control_inst = get_component(hook_src_data.get_container_node())
        elif isinstance(hook_src_data, nw.Transform):
            return self.HIER_PARENT(
                matrix=hook_src_data["worldMatrix"][0],
                inv_matrix=hook_src_data["worldInverseMatrix"][0],
                init_inv_matrix=hook_src_data["worldInverseMatrix"][0].value)
    
        if issubclass(type(hook_src_data), Hierarchy):
            hook_xform = self.get_hook_xform(hook_src_data.container_node[self.HIER_DATA.INPUT_XFORM][0])
            return component_data.xform_to_hier_parent(hook_xform)

        if issubclass(type(hook_src_data), Control):
            control_inst = hook_src_data

        if control_inst is not None:
            cntrl_map_attr = control_inst.container_node[control_inst._CNTNR_CNTRL_MAP]
            parent_component = get_component(control_inst.container_node.get_container_node())
            if parent_component is not None:
                if cntrl_map_attr.has_src_connection():
                    connection = cntrl_map_attr.get_src_connection()
                    if issubclass(type(parent_component), Hierarchy):
                        hook_xform = self.get_hook_xform(parent_component.container_node[self.HIER_DATA.INPUT_XFORM][connection.index])
                        return component_data.xform_to_hier_parent(hook_xform)
                else:
                    hook_xform = self.get_hook_xform(parent_component.container_node[self.HIER_DATA.INPUT_XFORM][0])
                    return component_data.xform_to_hier_parent(hook_xform)
            else:
                return self.HIER_PARENT(
                    matrix=control_inst.transform_node["worldMatrix"][0],
                    inv_matrix=control_inst.transform_node["worldInverseMatrix"][0],
                    init_inv_matrix=control_inst.transform_node["worldInverseMatrix"][0].value)
    def get_hook_xform(self, xform:nw.Attr):
        """Gets hook xform at the end of chain that can be used to set hook data

        Args:
            xform (nw.Attr): 

        Raises:
            RuntimeError: not an xform attribute
            RuntimeError: xform not part of a hierarchy component
            RuntimeError: xform has more than one connection to output node

        Returns:
            component_data.Xform:
        """
        if not self.HIER_DATA.is_input_xform_attr(xform) and self.HIER_DATA.is_output_xform_attr(xform):
            raise RuntimeError(f"{xform} is not xform attribute")
        if not issubclass(utils.string_to_class(xform.node.get_container_node()[self._BLD_COMP_CLASS].value), Hierarchy):
            raise RuntimeError(f"xform not attached to hierarchy component")
        
        ancestor_hier = self.__get_ancestor_hierarchy()
        HIER_DATA = self.HIER_DATA

        curr_xform = xform
        xform_container = xform.node.get_container_node()
        xform_index = xform.index
        io_len = [len(xform_container[HIER_DATA.INPUT_XFORM]), len(xform_container[HIER_DATA.OUTPUT_XFORM])]
        
        while True:
            # input to output
            if io_len[0] == io_len[1]:
                curr_xform = xform_container[HIER_DATA.OUTPUT_XFORM][xform_index]
            else:
                check_func = lambda attr: attr.parent is not None and (HIER_DATA.is_output_xform_attr(attr.parent) or HIER_DATA.is_input_xform_attr(attr.parent))
                dest_attrs = curr_xform[HIER_DATA.INPUT_INIT_MATRIX].get_dest_connections()
                if dest_attrs == []:
                    dest_attrs = curr_xform[HIER_DATA.INPUT_XFORM_NAME].get_dest_connections()
                dest_attrs = [attr.parent for attr in dest_attrs if check_func(attr=attr)]

                if len(dest_attrs) > 1:
                    raise RuntimeError(f"{curr_xform} does not only have one connection to output node")
                if len(dest_attrs) < 1:
                    raise RuntimeError(f"{curr_xform} does not one connection to xform")
                if HIER_DATA.is_input_xform_attr(dest_attrs[0]):
                    curr_xform = dest_attrs[0]
                    xform_container = curr_xform.node.get_container_node()
                    xform_index = curr_xform.index
                    io_len[0] = len(curr_xform.parent)
                    io_len[1] = len(xform_container[HIER_DATA.OUTPUT_XFORM])
                    continue
                curr_xform = dest_attrs[0]                
            # updating index
            xform_index = curr_xform.index

            # updating input len
            io_len[0] = len(curr_xform.parent)

            # get connection
            check_func = lambda attr: attr.parent is not None and attr.parent.index != -1
            connection = [attr.parent for attr in curr_xform[HIER_DATA.OUTPUT_LOC_MATRIX].get_dest_connections() if check_func(attr=attr)]

            if len(connection) <= 0:
                return self.XFORM(curr_xform)
            
            #updating other things
            curr_xform = connection[0]
            xform_container = curr_xform.node.get_container_node()
            io_len[1] = len(xform_container[HIER_DATA.OUTPUT_XFORM])
            # get output_len

            if xform_container == ancestor_hier.container_node:
                return self.XFORM(curr_xform)
    def __get_ancestor_hierarchy(self):
        """Gets highest ancestor that's of Hierarchy class/subclass

        Returns:
            Hierarchy:
        """
        parent_component_class = None
        ancestor_container = self.container_node
        while True:
            parent_container = ancestor_container.get_container_node()
            if parent_container is None or not parent_container.has_attr(self._BLD_COMP_CLASS):
                break
            parent_component_class = utils.string_to_class(parent_container[self._BLD_COMP_CLASS].value)
            if issubclass(parent_component_class, Hierarchy):
                ancestor_container = ancestor_container.get_container_node()
            else:
                break

        if parent_component_class is None:
            return self
        return parent_component_class(ancestor_container)
        
    #other functionality
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
    _IN_HAS_PARENT_HIER = "hasHierParent"
    _OUT_SET_CNTRL_LOC_MAT = "outputSettingCntrlLocMatrix"
    _MIRROR_AXIS = "mirrorAxis"

    _KWG_HIER_SIDE = "hier_side"
    _KWG_SETUP_CLR = "setup_color"
    _KWG_PRM_AXIS = "primary_axis"
    _KWG_SEC_AXIS = "secondary_axis"
    _KWG_ADD_SETTINGS_CNTRL = "add_settings_cntrl"
    _KWG_MIRROR_SRC = "mirror_source"
    _KWG_MIRROR_AXIS = "mirror_axis"
    
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
        return self._get_node_from_key("setup_container", as_component=True)
    @property
    def settings_component(self)->Control:
        """Returns settings component (if one exists)

        Returns:
            Control:
        """
        if not self.container_node.has_attr("settings_container"):
            return
        return self._get_node_from_key("settings_container", as_component=True)
    @property
    def settings_guide_component(self)->Control:
        """Returns settings guide component (if one exists)

        Returns:
            Control:
        """
        if not self.container_node.has_attr("settings_guide_container"):
            return
        return self._get_node_from_key("settings_guide_container", as_component=True)
    @property
    def mirror_dest_component(self)->"Anim":
        """Get mirror destination component

        Returns:
            Anim:
        """
        return self._get_node_from_key(self._MIRROR_SRC, as_component=True)
    @property
    def mirror_src_component(self)->"Anim":
        """Get mirror source component

        Returns:
            Anim:
        """
        if self.container_node is not None:
            if self._MIRROR_DEST not in self._node_data_cache.keys():
                if self.container_node.has_attr(self._MIRROR_DEST):
                    if self.container_node[self._MIRROR_DEST].has_src_connection():
                        node = self.container_node[self._MIRROR_DEST].get_src_connection().node
                        self._node_data_cache[self._MIRROR_DEST] = node
        if self._MIRROR_DEST in self._node_data_cache.keys():
            node = self._node_data_cache[self._MIRROR_DEST]
            component = get_component(node)
            if component is not None:
                return component
            return node

    def _input_attr_build_data(self):
        node_data = super()._input_attr_build_data()
        node_data.extend_attr_data(
            component_data.AttrData(self._IN_PRM_AXIS, type_=component_enum_data.AxisEnum.x, publish=True),
            component_data.AttrData(self._IN_SEC_AXIS, type_=component_enum_data.AxisEnum.y, publish=True),
            component_data.AttrData(self._HIER_SIDE, type_=component_enum_data.CharacterSide.none, publish=True),
            component_data.AttrData(self._IN_SET_XFORM_FOLLOW_INDEX, type_="long", parent=self._IN, min=0),
            component_data.AttrData(self._IN_SET_CNTRL_LOC_MAT, type_="matrix", parent=self._IN),
            component_data.AttrData(self._IN_HAS_PARENT_HIER, type_="bool", parent=self._IN, value=False)
        )
        node_data.modify_add_attr_kwargs(self._BLD_INST_FORM, value=f"{{}}_{{}}_{type(self).class_namespace}")
        return node_data 
    def _output_attr_build_data(self):
        node_data = super()._output_attr_build_data()
        node_data.extend_attr_data(
            component_data.AttrData(self._OUT_SET_CNTRL_LOC_MAT, type_="matrix", parent=self._OUT)
        )
        return node_data
    def get_short_namespace(self, instance_name = None):
        format_str = self.container_node[self._BLD_INST_FORM].value

        # instance_name
        if instance_name is None:
            instance_name = self.container_node[self._BLD_INST_NAME].value
        
        if instance_name is None:
            instance_name = ""

        # hier sode
        hier_side = component_enum_data.CharacterSide.get(self.input_node['hierSide'].value).value
        if hier_side == f"{component_enum_data.CharacterSide.none.value}":
            hier_side = ""

        return utils.strip_characters(format_str.format(hier_side, instance_name), "_", leading=True, trailing=False)
    
    @classmethod
    def create(cls, 
               instance_name:Union[str, nw.Attr]=None, 
               parent:Component=None, 
               input_xforms:Union[int, tuple]=0, 
               primary_axis:component_enum_data.AxisEnum=component_enum_data.AxisEnum.x,
               secondary_axis:component_enum_data.AxisEnum=component_enum_data.AxisEnum.y,
               add_settings_cntrl:bool=True,
               mirror_source:"Anim"=None,
               mirror_axis:component_enum_data.AxisEnum=component_enum_data.AxisEnum.x,
               source_component:Component=None, 
               connect_hierarchy:bool=True, 
               connect_axis_vecs:bool=True, 
               control_color=None,
               setup_color=None,
               hier_side:component_enum_data.CharacterSide=component_enum_data.CharacterSide.none):
        pre_build_kwargs, build_kwargs, post_build_kwargs = cls._process_kwargs(
            instance_name=instance_name,
            parent=parent, 
            input_xforms=input_xforms,
            primary_axis=primary_axis,
            secondary_axis=secondary_axis,
            add_settings_cntrl=add_settings_cntrl,
            mirror_source=mirror_source,
            mirror_axis=mirror_axis,
            source_component=source_component,
            connect_hierarchy=connect_hierarchy,
            connect_axis_vecs=connect_axis_vecs,
            control_color=control_color,
            setup_color=setup_color,
            hier_side=hier_side)
        return cls._filtered_create(pre_build_kwargs=pre_build_kwargs, build_kwargs=build_kwargs, post_build_kwargs=post_build_kwargs)
    @classmethod
    def _process_kwargs(cls, 
               instance_name:Union[str, nw.Attr]=None, 
               parent:Component=None, 
               input_xforms:Union[int, tuple]=0, 
               primary_axis:component_enum_data.AxisEnum=component_enum_data.AxisEnum.x,
               secondary_axis:component_enum_data.AxisEnum=component_enum_data.AxisEnum.y,
               add_settings_cntrl:bool=True,
               mirror_source:"Anim"=None,
               mirror_axis:component_enum_data.AxisEnum=component_enum_data.AxisEnum.x,
               source_component:Component=None, 
               connect_hierarchy:bool=True, 
               connect_axis_vecs:bool=True, 
               control_color=None,
               setup_color=None,
               hier_side:component_enum_data.CharacterSide=component_enum_data.CharacterSide.none):
        pre_build_kwargs, build_kwargs, post_build_kwargs = super()._process_kwargs(instance_name, parent, input_xforms, source_component, connect_hierarchy, connect_axis_vecs, control_color)
        pre_build_kwargs.update({
            cls._KWG_HIER_SIDE: hier_side,
            cls._KWG_PRM_AXIS: primary_axis,
            cls._KWG_SEC_AXIS: secondary_axis,
            cls._KWG_ADD_SETTINGS_CNTRL:add_settings_cntrl,
            cls._KWG_MIRROR_SRC:mirror_source,
            cls._KWG_SETUP_CLR:setup_color,
            cls._KWG_CNTR_CLR:control_color,
            cls._KWG_MIRROR_AXIS:mirror_axis,
        })
        return pre_build_kwargs, build_kwargs, post_build_kwargs

    def _pre_build(self, 
                   instance_name:Union[str, nw.Attr]=None, 
                   parent:Component=None, 
                   input_xforms:Union[int, tuple]=0, 
                   hier_side:component_enum_data.CharacterSide=component_enum_data.CharacterSide.none, 
                   primary_axis:component_enum_data.AxisEnum=component_enum_data.AxisEnum.x,
                   secondary_axis:component_enum_data.AxisEnum=component_enum_data.AxisEnum.y,
                   add_settings_cntrl:bool=True,
                   mirror_source:"Anim"=None,
                   mirror_axis:component_enum_data.AxisEnum=component_enum_data.AxisEnum.x,
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
            input_xforms=input_xforms, 
            source_component=source_component, 
            connect_hierarchy=connect_hierarchy, 
            connect_axis_vec=connect_axis_vec, 
            **pre_build_kwargs)
        # setting values
        self.container_node[self._HIER_SIDE]=hier_side.name
        self.container_node[self._IN_PRM_AXIS]=primary_axis.name
        self.container_node[self._IN_SEC_AXIS]=secondary_axis.name

        # if mirror source connect other attrs from last time
        if mirror_source is not None:
            self._connect_mirror_source(mirror_source=mirror_source)
            self.input_node.add_attr(self._MIRROR_AXIS, type="enum", enumName=component_enum_data.AxisEnum.maya_enum_str())
            self.container_node.publish_attr(self.input_node[self._MIRROR_AXIS], attr_bind_name=self._MIRROR_AXIS)
            self.container_node[self._MIRROR_AXIS] = component_enum_data.AxisEnum.index_of(mirror_axis)

            # setting correct input xform
            setup_xforms = mirror_source.setup_component.get_xform_attrs(self.IO_ENUM.input)
            setup_xforms = {index: mirror_source.get_hook_xform(xform.init_matrix.parent) for index, xform in setup_xforms.items()}
            
            input_xforms = self.get_xform_attrs(xform_type=self.IO_ENUM.input)
            for input_xform in input_xforms.values():
                for attr in input_xform.attrs:
                    if isinstance(attr, nw.Attr):
                        ~attr
            for index, xform in setup_xforms.items():                
                self._set_xform_attrs(xform_type=self.IO_ENUM.input, index=index, xform=xform)

        # populating primary, secondary, and tertiary vectors
        self.__set_vectors()
        
        # create setup component
        self.__create_setup_component(input_xforms=input_xforms, setup_color=setup_color, mirror_source=mirror_source, mirror_axis=mirror_axis)

        # adding settings cntrl
        if add_settings_cntrl:
            self.__create_settings_cntrls(setup_color=setup_color, control_color=control_color)
            
        self.rename_nodes()
    def _post_build(self, **post_build_kwargs):
        super()._post_build(**post_build_kwargs)
        if self.mirror_src_component is not None:
            self.__mirror_controls_from_source()
        self._attach_output_xforms_to_settings_controls()
 
    # settings controls
    def __create_settings_cntrls(self, setup_color=None, control_color=None):
        """Creates settings control. creates settings guide if not mirrored

        Args:
            setup_color (component_enum_data.Color, optional): Defaults to None.
            control_color (component_enum_data.Color, optional): Defaults to None.
        """
        has_mirror_src  = self.mirror_src_component is not None

        import component.control as control
        #settings init
        settings_init_choice = None
        settings_init = None
        if not has_mirror_src:
            settings_init_choice = nw.create_node("choice", "settings_init_choice")
            settings_init_choice["selector"] << self.container_node[self._IN_SET_XFORM_FOLLOW_INDEX]
            settings_init = control.Locator.create(instance_name="settings_guide", parent=self, color=setup_color)
            settings_init.promote_attr_to_keyable(self.container_node[self._IN_SET_XFORM_FOLLOW_INDEX])
            settings_init.transform_node["translate"] = [1, 1, 1]
            utils.map_to_container(settings_init.container_node, "settings_guide_container")

            self.container_node.add_nodes(settings_init_choice)

        settings_choice = nw.create_node("choice", "settings_choice")
        settings_choice["selector"] << self.container_node[self._IN_SET_XFORM_FOLLOW_INDEX]
        settings_mult = nw.create_node("multMatrix", "settings_ws_mult")
        
        # setting up controls
        settings = control.Gear.create(instance_name="settings", parent=self, color=control_color)
        utils.map_to_container(settings.container_node, "settings_container")
        for attr in ["t", "r", "s"]:
            for axis in ["x", "y", "z"]:
                settings.transform_node[f"{attr}{axis}"].set_locked(True)
                settings.transform_node[f"{attr}{axis}"].set_keyable(False)

        # inserting offset matrix to control
        if not has_mirror_src:
            settings_init.container_node[settings_init._IN_OFF_MAT] << settings_init_choice["output"]
            settings_init.container_node[settings_init._OUT_LOC_MAT] >> self.container_node[self._IN_SET_CNTRL_LOC_MAT]
        settings.container_node[settings._IN_OFF_MAT] << settings_mult["matrixSum"]
        settings_mult["matrixIn"][0] << self.setup_component.container_node[self._OUT_SET_CNTRL_LOC_MAT]
        settings_mult["matrixIn"][1] << settings_choice["output"]

        self.container_node.add_nodes(settings_choice, settings_mult)
    def _attach_output_xforms_to_settings_controls(self):
        """Takes finished output xforms and applies it to settings init choice"""
        output_xforms = self.get_xform_attrs(xform_type=self.IO_ENUM.output)
        settings_guide = self.settings_guide_component
        if settings_guide is not None:
            settings_guide_choice = settings_guide.container_node[settings_guide._IN_OFF_MAT].get_src_connection().node
            for index, output_xform in output_xforms.items():
                if not settings_guide_choice["input"][index].has_src_connection():
                    if output_xform.init_matrix.has_src_connection():
                        output_xform.init_matrix.get_src_connection() >> settings_guide_choice["input"][index]
                    else:
                        output_xform.init_matrix >> settings_guide_choice["input"][index]

            # reset max
            max = len(output_xforms.keys()) - 1
            cmds.addAttr(str(settings_guide.transform_node[self._IN_SET_XFORM_FOLLOW_INDEX]), edit=True, max=max)
            
            # set to max
            settings_guide.transform_node[self._IN_SET_XFORM_FOLLOW_INDEX] = max

        settings = self.settings_component
        if settings is not None:
            settings_choice = settings.container_node[settings._IN_OFF_MAT].get_src_connection().node["matrixIn"][1].get_src_connection().node
            for index, output_xform in output_xforms.items():
                if not settings_choice["input"][index].has_src_connection():
                    if output_xform.world_matrix.has_src_connection():
                        output_xform.world_matrix.get_src_connection() >> settings_choice["input"][index]
                    else:
                        output_xform.world_matrix >> settings_choice["input"][index]

        # do it for settings

    # mirroring
    def mirror(self, control_color:component_enum_data.Color=None, setup_color:component_enum_data.Color=None, mirror_axis:component_enum_data.AxisEnum=component_enum_data.AxisEnum.x):
        """Mirrors component. returns new mirrored componenet

        Args:
            control_color (component_enum_data.Color, optional): Defaults to None.
            setup_color (component_enum_data.Color, optional): Defaults to None.
            mirror_axis (component_enum_data.AxisEnum, optional): Defaults to component_enum_data.AxisEnum.x.

        Returns:
            Hierarchy:
        """
        parent = self.container_node.get_container_node()
        add_settings_cntrl = self.settings_component is not None
        mirror_component = type(self).create(
            parent=parent, 
            source_component=self, 
            mirror_source=self, 
            mirror_axis=mirror_axis, 
            control_color=control_color, 
            setup_color=setup_color, 
            connect_hierarchy=False, 
            connect_axis_vecs=False, 
            add_settings_cntrl=add_settings_cntrl)

        return mirror_component
    def _connect_mirror_source(self, mirror_source:"Anim"):
        """Connects all necessary attributes from mirror source

        Args:
            mirror_source (Anim): _description_
        """
        mirror_src_container = mirror_source.container_node
        self_container = self.container_node

        # add source and dest mirror attributes and connect it up
        mirror_src_container.add_attr(self._MIRROR_SRC, type="message")
        self_container.add_attr(self._MIRROR_DEST, type="message")

        mirror_src_container[self._MIRROR_SRC] >> self_container[self._MIRROR_DEST]

        # connect remap attrs
        primary_axis_remap = component_enum_data.AxisEnum.create_remap("mirrorPrimaryAxisRemap")
        secondary_axis_remap = component_enum_data.AxisEnum.create_remap("mirrorSecondaryAxisRemap")
        char_side_remap = component_enum_data.CharacterSide.create_remap("mirrorHierSideRemap")

        primary_axis_remap["inputValue"] << mirror_src_container[mirror_source._IN_PRM_AXIS]
        primary_axis_remap["outValue"] >> self_container[self._IN_PRM_AXIS]

        secondary_axis_remap["inputValue"] << mirror_src_container[mirror_source._IN_SEC_AXIS]
        secondary_axis_remap["outValue"] >> self_container[self._IN_SEC_AXIS]
        
        char_side_remap["inputValue"] << mirror_src_container[mirror_source._HIER_SIDE]
        char_side_remap["outValue"] >> self_container[self._HIER_SIDE]

        self.container_node.add_nodes(primary_axis_remap, secondary_axis_remap, char_side_remap)

        # connecting up other mirro source attributes
        self_container[self._BLD_INST_NAME] << mirror_src_container[mirror_source._BLD_INST_NAME]
        self_container[self._IN_SET_XFORM_FOLLOW_INDEX] << mirror_src_container[mirror_source._IN_SET_XFORM_FOLLOW_INDEX]
        self_container[self._IN_SET_CNTRL_LOC_MAT] << mirror_src_container[mirror_source._OUT_SET_CNTRL_LOC_MAT]

        self.rename_nodes()
    def __mirror_controls_from_source(self, color=None):
        """Mirrors the controls (to have the same shape as the other source)

        Args:
            color (Any, optional): Defaults to None.

        Raises:
            RuntimeError: can only be called from mirror destination component
        """
        
        if self.mirror_src_component is None:
            raise RuntimeError("__mirror_controls can only be called if component is mirror dest")
        for control in self.get_all_descendants(component_enum_data.ComponentType.control):
            mirror_control = control.mirror_component()
            if isinstance(control, Control):
                replace_control = control.replace_control(mirror_control, color=color)
                
                if replace_control.container_node[replace_control._IN_OFF_MAT].value.det4x4() > 0:

                    scale_attr = replace_control.transform_node["scale"]
                    
                    locked_attrs = [attr for attr in scale_attr if attr.is_locked()]
                    [attr.set_locked(False) for attr in locked_attrs]

                    scale_attr.set([-1, -1, -1])
                    replace_control.transform_node.freeze_transforms()

                    [attr.set_locked(True) for attr in locked_attrs]
        
    # hooking
    def hook(self, hook_src_data):
        super().hook(hook_src_data)
        if not self.container_node[self._IN_HAS_PARENT_HIER].has_src_connection():
            self.container_node[self._IN_HAS_PARENT_HIER] = True
    def unhook(self):
        hier_parent = super().unhook()
        if not self.container_node[self._IN_HAS_PARENT_HIER].has_src_connection():
            self.container_node[self._IN_HAS_PARENT_HIER] = False
        return hier_parent
                
   # other
    def __set_vectors(self):
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
        tertiary_vec = nw.create_node("crossProduct", "tertiary_vec_prod")
        tertiary_vec["input1"] << primary_axis_attr
        tertiary_vec["input2"] << secondary_axis_attr
        tertiary_vec["output"] >> self.container_node[self._TER_VEC]

        self.container_node[self._PRM_VEC] << primary_axis_attr
        self.container_node[self._SEC_VEC] << secondary_axis_attr

        self.container_node.add_nodes(primary_choice_node, secondary_choice_node, tertiary_vec)
    def __create_setup_component(self, input_xforms:Union[int, tuple]=0, setup_color=None, mirror_source:"Anim"=None, mirror_axis:component_enum_data.AxisEnum=component_enum_data.AxisEnum.x):
        """Creates setup component and maps it to container

        Args:
            init_num_xforms (Union[int, tuple], optional): . Defaults to 0.
            setup_color (Any, optional): . Defaults to None.
            mirror_source (Anim, optional): . Defaults to None.
        """
        import component.setup as setup
        if mirror_source is None:
            setup_inst = self.setup_component_type.create(input_xforms=input_xforms, control_color=setup_color, parent=self, source_component=self)
        else:
            setup_inst = setup.Mirror.create(input_xforms=input_xforms, control_color=setup_color, parent=self, source_component=self, mirror_axis=mirror_axis)

        setup_inst.container_node[setup_inst._IN_SET_XFORM_FOLLOW_INDEX] << self.container_node[self._IN_SET_XFORM_FOLLOW_INDEX]
        setup_inst.container_node[setup_inst._IN_SET_CNTRL_LOC_MAT] << self.container_node[self._IN_SET_CNTRL_LOC_MAT]
        setup_inst.container_node[setup_inst._OUT_SET_CNTRL_LOC_MAT] >> self.container_node[self._OUT_SET_CNTRL_LOC_MAT]
        setup_inst.container_node[setup_inst._IN_HAS_PARENT_HIER] << self.container_node[self._IN_HAS_PARENT_HIER]
        utils.map_to_container(setup_inst.container_node, "setup_container")
        if self.mirror_src_component is None:
            self.container_node[self._IN_SET_XFORM_FOLLOW_INDEX] = len(self.get_xform_attrs(self.IO_ENUM.input)) - 1
