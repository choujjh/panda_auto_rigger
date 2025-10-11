import utils.node_wrapper as nw
import system.component_data as component_data
import system.component_enum_data as component_enum_data
from typing import Union

import utils.utils as utils
import maya.cmds as cmds

from inspect import signature

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
    def create(cls, instance_name:Union[str, nw.Attr]=None, parent:Union["Component", nw.Container]=None, **kwargs):
        """Class method to create component

        Args:
            instance_name (str, nw.Attr, optional): name of component. Defaults to None.
            parent (nw.Container, Component, optional): Defaults to None.

        Returns:
            cls: returns created 
        """
        return cls._kwarg_create(**cls._local_kwargs(kwarg_dict=locals()))
    @classmethod
    def _local_kwargs(cls, kwarg_property_name="kwargs", kwarg_dict={}):
        if kwarg_property_name in kwarg_dict.keys():
            back_kwargs = kwarg_dict.pop(kwarg_property_name)
            kwarg_dict.update(back_kwargs)
        for key in ["cls", "self"]:
            if key in kwarg_dict.keys():
                kwarg_dict.pop(key)

        return kwarg_dict
    @classmethod
    def _kwarg_create(cls, **kwargs):
        """Creates with kwarg arguments

        Args:
            kwargs_dict (dict):

        Returns:
            self:
        """
        kwarg_keys = set(kwargs.keys())
        
        # creating
        component_inst = cls()
        component_inst._pre_build(**kwargs)
        component_inst._override_build(**kwargs)
        component_inst._post_build(**kwargs)

        # parm checking
        pre_parm = set(signature(component_inst._pre_build).parameters.keys())
        override_parm = set(signature(component_inst._override_build).parameters.keys())
        post_parm = set(signature(component_inst._post_build).parameters.keys())
        override_parm.update(pre_parm)
        override_parm.update(post_parm)

        kwarg_keys = kwarg_keys - override_parm

        for parm_name in kwarg_keys:
            cmds.warning(f"{component_inst.container_node} create method did not use \"{parm_name}\" parameter")

        return component_inst
    
    def _pre_build(self, instance_name:Union[str, nw.Attr]=None, parent:Union["Component", nw.Container]=None, **kwargs):
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
    def _override_build(self, **kwargs):
        """Takes care of derived component creation. must be implemented by child class

        Raises:
            NotImplementedError: must be implemented by child classes
        """
        raise NotImplementedError
    def _post_build(self, **kwargs):
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
    def get_mirror_component(self, container:nw.Container=None)->"Component":
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
        if container is not None:
            curr_container = container
        else:
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
class _Hierarchy(Component):
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

    @classmethod
    def create(cls, 
               instance_name:Union[str, nw.Attr]=None, 
               parent:Component=None, 
               input_xforms:Union[list[component_data.Xform], int]=None, 
               source_component:Component=None, 
               connect_parent_hier:bool=True, 
               connect_axis_vecs:bool=True, 
               control_color=None):        
        return cls._kwarg_create(**cls._local_kwargs(kwarg_dict=locals()))
    def _pre_build(self, instance_name:Union[str, nw.Attr]=None, parent:Component=None, input_xforms:Union[list[component_data.Xform], int]=None,  source_component:Component=None, connect_parent_hier:bool=None, connect_axis_vecs:bool=True, **kwargs):
        super()._pre_build(instance_name, parent)            

        source_xforms = None
        if source_component is not None and hasattr(source_component, "get_as_source_xforms"):
            source_xforms = source_component.get_as_source_xforms(is_parent_component=utils.if_container_is_ancestor(child=self.container_node, ancestor=source_component.container_node))
        
        self.__initialize_input_xform(input_xforms=input_xforms, source_xforms=source_xforms)
        
        #connect source component
        if source_xforms is not None:
            self._connect_source_component(source_component=source_component, source_xforms=source_xforms, connect_hierarchy=connect_parent_hier, connect_axis_vec=connect_axis_vecs)
    def _override_build(self, control_color=None, **kwargs):
        return super()._override_build(**kwargs)
    def _post_build(self, **kwargs):
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
    def hook(self, hook_src_data, hook_mirror_component:bool=True):
        """Hooks xform to hier parent

        Args:
            hook_src_data (any): hook data that will be setting the hier parent
            hook_mirror(bool): also hooks mirror to it's corresponding source

        """
        # get parent hier that can be hooked first
        hier_parent = self.get_hook_hier_parent()
        
        self.unhook(False)
        # convert hook data (go from highest level hier)
        hier_src_data = self.get_hook_source_data(hook_src_data=hook_src_data)
        
        for hook_src, hook_hier_parent in zip(hier_src_data, hier_parent):
            hook_src >> hook_hier_parent

        if hook_mirror_component:
            self._hook_mirror_component()
    def unhook(self, unhook_mirror_component:bool=True):
        """Unhooks Hierarchy

        Returns:
            component_data.HierParent:
        """
        hier_parent = self.get_hook_hier_parent()
        
        for attr in hier_parent:
            if attr.has_src_connection():
                ~attr
        if unhook_mirror_component:
            self.__unhook_mirror_component()

    def _hook_mirror_component(self):
        """Hooking the mirror component"""
        mirror_component = self.get_mirror_component()
        if mirror_component is None:
            return
        
        hook_src = self.get_hook_hier_parent()
        hook_src.matrix = hook_src.matrix.get_src_connection()
        hook_src.inv_matrix = hook_src.inv_matrix.get_src_connection()
        hook_src.init_inv_matrix = hook_src.init_inv_matrix.get_src_connection()

        if hook_src.matrix is not None:
            hook_src_cntnr = hook_src.matrix.node.get_container_node()
            if hook_src_cntnr is not None:
                mirror_hook_src_cntnr = get_component(hook_src_cntnr)
                mirror_hook_src_cntnr = mirror_hook_src_cntnr.get_mirror_component()
                # TODO rather find the node of each attribute then try to find it in the published container_nodes
                if mirror_hook_src_cntnr is not None:
                    hook_src.matrix = mirror_hook_src_cntnr.container_node[hook_src.matrix.attr_name]
                    hook_src.inv_matrix = mirror_hook_src_cntnr.container_node[hook_src.inv_matrix.attr_name]
                    hook_src.init_inv_matrix = mirror_hook_src_cntnr.container_node[hook_src.init_inv_matrix.attr_name]

        if [x for x in hook_src.attrs if x is not None] == []:
            return

        mirror_component.hook(hook_src, hook_mirror_component=False)
    def __unhook_mirror_component(self):
        """Unhook Mirror component"""
        mirror_component = self.get_mirror_component()
        if mirror_component is not None:
            mirror_component.unhook(unhook_mirror_component=False)
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
        if isinstance(hook_src_data, self.HIER_PARENT):
            return hook_src_data
        if isinstance(hook_src_data, nw.Attr) and (
            self.HIER_DATA.is_input_xform_attr(hook_src_data) or 
            self.HIER_DATA.is_output_xform_attr(hook_src_data)):
            return component_data.xform_to_hier_parent(self.get_hook_xform(hook_src_data))
        if isinstance(hook_src_data, nw.Transform) and hook_src_data.get_container_node() is not None:
            control_inst = get_component(hook_src_data.get_container_node())
        elif isinstance(hook_src_data, nw.Transform):
            return self.HIER_PARENT(
                matrix=hook_src_data["worldMatrix"][0],
                inv_matrix=hook_src_data["worldInverseMatrix"][0],
                init_inv_matrix=hook_src_data["worldInverseMatrix"][0].value)
    
        if issubclass(type(hook_src_data), _Hierarchy):
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
                    if issubclass(type(parent_component), _Hierarchy):
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
        if not issubclass(utils.string_to_class(xform.node.get_container_node()[self._BLD_COMP_CLASS].value), _Hierarchy):
            raise RuntimeError(f"xform not attached to hierarchy component")
        
        
        HIER_DATA = self.HIER_DATA

        curr_xform = xform
        xform_container = xform.node.get_container_node()
        ancestor_hier = self.__get_ancestor_hierarchy(xform_container)
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
    def __get_ancestor_hierarchy(self, container:nw.Container):
        """Gets highest ancestor that's of Hierarchy class/subclass

        Returns:
            Hierarchy:
        """
        if container is None:
            return None
        parent_component_class = None
        ancestor_container = container
        while True:
            parent_container = ancestor_container.get_container_node()
            if parent_container is None or not parent_container.has_attr(self._BLD_COMP_CLASS):
                break
            parent_component_class = utils.string_to_class(parent_container[self._BLD_COMP_CLASS].value)
            if issubclass(parent_component_class, _Hierarchy):
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