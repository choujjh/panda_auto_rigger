import utils.node_wrapper as nw
import system.component_data as component_data
import system.component_enum_data as component_enum_data
from typing import Union

import utils.utils as utils
import maya.cmds as cmds

from inspect import signature


def get_component(container_node: nw.Container) -> "_Component":
    """Gets component from a container

    Args:
        container_node (nw.Node):

    Returns:
        Component:
    """
    if container_node is None:
        return None
    if container_node.has_attr("componentClass") and isinstance(
        container_node, nw.Container
    ):
        component_class = utils.string_to_class(container_node["componentClass"].value)
        return component_class(container_node)


class _Component:
    """A Base class for all autorigging components

    Attributes:
        component_type (component_enum.ComponentTypes): the component type
        input_node_name (str): name of input node
        input_node_type (str)L input node type
        if true, the input node is a transform node instead of a network node
        class_namespace (str): gives the classes namespace
        lock_transform (bool): locks transform on root transform
        container_node (nw.Node): Container node that contains all component nodes
        input_node (nw.Node): Node that all incoming connections come through this node
        output_node (nw.Node): Node that all outgoing connections go through this node
        transform_node (nw.Node): Transform node (also input node). if no transform node
        is created returns None

        _IN (str): str constant "input"
        _BLD_DATA (str): str constant "buildData"
        _BLD_COMP_CLASS (str): str constant "componentClass"
        _BLD_COMP_TYPE (str): str constant "componentType"
        _BLD_INST_NAME (str): str constant "instanceName"
        _BLD_COMP_NAMESPC (str): str constant "componentNamespace"
        _BLD_COMP_NAME (str): str constant "componentName"
        _BLD_COMP_MESS (str): str constant "componentMessage"
        _OUT (str): str constant "output"
        _CNTNR_PAR_COMP (str): str constant "parentComponent"
        _CNTNR_CHLD_COMP (str): str constant "childComponents"
        _CNTNR_CNTRL_CHLDRN (str): str constant "controlChildren"
        _MIRROR_SRC (str): str constant "mirrorSource"
        _MIRROR_DEST (str): str constant "mirrorDest"
    """

    component_type = component_enum_data.ComponentType.component
    input_node_name = "input"
    input_node_type = "network"
    class_namespace = "component"
    lock_transform = True

    _IN = "input"
    _BLD_DATA = "buildData"
    _BLD_COMP_CLASS = "componentClass"
    _BLD_COMP_TYPE = "componentType"
    _BLD_INST_NAME = "instanceName"
    _BLD_COMP_NAMESPC = "componentNamespace"
    _BLD_COMP_NAME = "componentName"
    _BLD_COMP_MESS = "componentMessage"
    _OUT = "output"
    _CNTNR_PAR_COMP = "parentComponent"
    _CNTNR_CHLD_COMP = "childComponents"
    _CNTNR_CNTRL_CHLDRN = "controlChildren"
    _MIRROR_SRC = "mirrorSource"
    _MIRROR_DEST = "mirrorDest"

    def __init__(self, container_node: nw.Node = None):
        """initializes component with container nodes

        Args:
            container_node (nw.Node, optional): container to initialize with
            (incase component is already existing). Defaults to None.
        """
        self._node_data_cache = {}
        if container_node is not None:
            self._node_data_cache["container_node"] = container_node

    def _get_node_from_cache(self, key: str) -> nw.Node:
        """Caching function for all saved nodes so connections don't have to be
        queried every time. if not cached yet, node is saved

        Args:
            key (str): node key

        Returns:
            nw.Node: node from cache
        """
        if key not in self._node_data_cache.keys():
            if self.container_node.has_attr(key):
                self._node_data_cache[key] = (
                    self.container_node[key].get_dest_connections()[0].node
                )
            else:
                cmds.warning(f"{key} does not exist on component")
                return

        return self._node_data_cache[key]

    def _get_node_from_key(self, key: str, as_component: bool = False) -> nw.Node:
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
    def container_node(self) -> nw.Container:
        """Container node that contains all component nodes

        Returns:
            nw.Container:
        """
        if "container_node" in self._node_data_cache.keys():
            return self._node_data_cache["container_node"]

    @property
    def input_node(self) -> nw.Node:
        """Node that all incoming connections come through this node

        Returns:
            nw.Node:
        """
        return self._get_node_from_key("input_node")

    @property
    def output_node(self) -> nw.Node:
        """Node that all outgoing connections go through this node

        Returns:
            nw.Node:
        """
        return self._get_node_from_key("output_node")

    @property
    def transform_node(self) -> nw.Transform:
        """Transform node (also input node). if no transform node is created
        returns None

        Returns:
            nw.Node:
        """
        if type(self).input_node_type == "transform":
            return self.input_node

    def child_components(
        self, component_type: component_enum_data.ComponentType = None
    ) -> list["_Component"]:
        """Gets child components

        Args:
            component_type (component_enum_data.ComponentType): defaults to None

        Returns:
            list:
        """
        containers = [
            attr.get_dest_connections()[0].node
            for attr in self.container_node[self._CNTNR_CHLD_COMP]
        ]
        if component_type is not None:
            components = [
                get_component(container)
                for container in containers
                if container.has_attr(self._BLD_COMP_TYPE)
                and container[self._BLD_COMP_TYPE].value == component_type.value
            ]
        else:
            components = [get_component(container) for container in containers]

        return components

    def get_all_descendants(
        self, component_type: component_enum_data.ComponentType = None
    ) -> list["_Component"]:
        """Gets all descendent components

        Args:
            component_type (component_enum_data.ComponentType, optional): filters to component type. Defaults to None.

        Returns:
            list:
        """
        descendants = self.child_components()

        index = 0
        while index < len(descendants):
            curr_children = descendants[index].child_components()
            descendants.extend(curr_children)
            index += 1
        if component_type is not None:
            descendants = [
                component
                for component in descendants
                if component.container_node.has_attr(self._BLD_COMP_TYPE)
                and component.container_node[self._BLD_COMP_TYPE].value
                == component_type.value
            ]
        return descendants

    # namespaces
    @classmethod
    def get_class_name(cls) -> str:
        """Gets class name

        Returns:
            str:
        """
        return utils.class_type_to_str(cls)

    def get_short_namespace(self, instance_name: str = None):
        """Generates namespace without parented namespace attached

        Args:
            instance_name (str, optional): Defaults to None.
        """

        def __get_comp_name(attr: nw.Attr):
            """Generates part of the namespace from attr. only used internally from get_short_namespace

            Args:
                attr (nw.Attr):

            Returns:
                str:
            """
            name_value = attr[self._BLD_COMP_NAME].value
            if name_value is not None and name_value != "":
                return name_value
            mess_conn_attr = attr[self._BLD_COMP_MESS].get_src_connection()
            if mess_conn_attr is None:
                return None
            if mess_conn_attr.type_ == "enum":
                enum_names = utils.get_enum_names(mess_conn_attr)
                enum_str = utils.get_enum_string(mess_conn_attr)

                # checking within component enum data
                _, packages = utils.get_classes_from_package(component_enum_data)
                for package in packages:
                    if hasattr(package, "maya_enum_str"):
                        package_enum_names = getattr(package, "maya_enum_str")
                        if package_enum_names() == enum_names:
                            if hasattr(package, enum_str):
                                enum_obj = getattr(package, enum_str)
                                if isinstance(enum_obj.value, str):
                                    return enum_obj.value
                return enum_str

            else:
                return mess_conn_attr.value

        namespace_list = [
            __get_comp_name(name)
            for name in self.container_node[self._BLD_COMP_NAMESPC]
        ]
        if instance_name is not None:
            instance_name_indicies = [
                attr.parent.index
                for attr in self.container_node[
                    self._BLD_INST_NAME
                ].get_dest_connections()
                if attr.parent is not None
                and attr.parent.parent == self.container_node[self._BLD_COMP_NAMESPC]
            ]

            for index in instance_name_indicies:
                namespace_list[index] = instance_name

        namespace_list = [
            name for name in namespace_list if name is not None and name != "none"
        ]

        return "_".join(namespace_list[::-1])

    def insert_component_namespace_data(
        self, index: int, name: str = None, message_connection: nw.Attr = None
    ):
        """Inserts and sets data in component namespace attribute

        Args:
            index (int, optional): Defaults to None.
            name (str, optional): Defaults to None.
            message_connection (nw.Attr, optional): Defaults to None.
        """
        if index == 0:
            cmds.warning(
                "component namespace cannot insert at 0. component class type must be last in component namespace"
            )
            return
        comp_namespc_attr = self.container_node[self._BLD_COMP_NAMESPC]
        attr_index = len(comp_namespc_attr) - 1
        while attr_index >= index:
            comp_index_attr = comp_namespc_attr[attr_index]
            name_data = comp_index_attr[self._BLD_COMP_NAME].value
            message_data = comp_index_attr[self._BLD_COMP_MESS].get_src_connection()

            ~comp_index_attr[self._BLD_COMP_MESS]

            # set for next index
            utils.set_connect_attr_data(
                comp_namespc_attr[attr_index + 1][self._BLD_COMP_NAME], name_data
            )
            utils.set_connect_attr_data(
                comp_namespc_attr[attr_index + 1][self._BLD_COMP_MESS], message_data
            )

            if attr_index == index:
                comp_index_attr[self._BLD_COMP_NAME] = ""

            attr_index -= 1

        utils.set_connect_attr_data(comp_namespc_attr[index][self._BLD_COMP_NAME], name)
        utils.set_connect_attr_data(
            comp_namespc_attr[index][self._BLD_COMP_MESS], message_connection
        )

        self.rename_nodes()

    def get_namespace(self, instance_name: str = None):
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
            component_data.AttrData(
                name=self._BLD_DATA, type_="compound", publish=True
            ),
            component_data.AttrData(
                name=self._BLD_COMP_CLASS,
                type_="string",
                value=type(self).get_class_name(),
                locked=True,
                parent=self._BLD_DATA,
            ),
            component_data.AttrData(
                name=self._BLD_COMP_TYPE,
                type_=type(self).component_type,
                locked=True,
                parent=self._BLD_DATA,
            ),
            component_data.AttrData(
                name=self._BLD_INST_NAME, type_="string", parent=self._BLD_DATA
            ),
            component_data.AttrData(
                name=self._BLD_COMP_NAMESPC,
                type_="compound",
                parent=self._BLD_DATA,
                multi=True,
            ),
            component_data.AttrData(
                name=self._BLD_COMP_NAME,
                type_="string",
                parent=self._BLD_COMP_NAMESPC,
            ),
            component_data.AttrData(
                name=self._BLD_COMP_MESS,
                type_="message",
                parent=self._BLD_COMP_NAMESPC,
            ),
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
            component_data.AttrData(
                name=self._CNTNR_CHLD_COMP, type_="message", multi=True
            ),
            component_data.AttrData(
                name=self._CNTNR_CNTRL_CHLDRN, type_="message", multi=True
            ),
        )

    @classmethod
    def create(
        cls,
        instance_name: Union[str, nw.Attr] = None,
        parent: Union["_Component", nw.Container] = None,
        **kwargs,
    ):
        """Class method to create component

        Args:
            instance_name (str, nw.Attr, optional): name of component. Defaults to None.
            parent (nw.Container, Component, optional): Defaults to None.

        Returns:
            cls: returns created
        """
        return cls._kwarg_create(**cls._process_locals(kwarg_dict=locals()))

    @classmethod
    def _process_locals(cls, kwarg_dict_name="kwargs", kwarg_dict={}):
        """Takes a kwarg dict and makes sure that the kwarg_dict (kwarg_dict_name)
        is not a nested dictionary. also removes cls and self from dictionary.
        used to sort local() function

        Args:
            kwarg_dict_name (str, optional): Defaults to "kwargs".
            kwarg_dict (dict, optional): Defaults to {}.

        Returns:
            dict:

        Example:
            >>> cls._process_locals(kwarg_dict_name="kwargs", kwarg_dict=locals())
        """
        if kwarg_dict_name in kwarg_dict.keys():
            back_kwargs = kwarg_dict.pop(kwarg_dict_name)
            kwarg_dict.update(back_kwargs)
        for key in ["cls", "self"]:
            if key in kwarg_dict.keys():
                kwarg_dict.pop(key)

        return kwarg_dict

    @classmethod
    def _kwarg_create(cls, **kwargs):
        """Creates with kwarg arguments. also takes the signatures to make sure all kwargs are used

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
            cmds.warning(
                f'{component_inst.container_node} create method did not use "{parm_name}" parameter'
            )

        return component_inst

    def _pre_build(
        self,
        instance_name: Union[str, nw.Attr] = None,
        parent: Union["_Component", nw.Container] = None,
        **kwargs,
    ):
        """Handles creation and connection of initial nodes

        Args:
            instance_name (str, nw.Attr, optional): component instance name. Defaults to None.
            parent (nw.Container, Component, optional): Defaults to None.
        """
        if parent is not None and not isinstance(parent, nw.Container):
            parent = parent.container_node

        if self.container_node is None:
            self.__create_base_nodes(parent_container=parent)
            if instance_name is not None:
                utils.set_connect_attr_data(
                    self.input_node[self._BLD_INST_NAME], instance_name
                )

            # connecting parent and child components
            if parent is not None:
                if parent.has_attr(self._CNTNR_CHLD_COMP):
                    child_component_len = len(parent[self._CNTNR_CHLD_COMP])
                    (
                        parent[self._CNTNR_CHLD_COMP][child_component_len]
                        >> self.container_node[self._CNTNR_PAR_COMP]
                    )

                    # parenting transforms
                    parent_component = get_component(parent)
                    if (
                        parent_component is not None
                        and parent_component.transform_node is not None
                        and self.transform_node is not None
                    ):
                        cmds.parent(
                            str(self.transform_node),
                            str(parent_component.transform_node),
                        )

            # renaming to nodes
            self.rename_nodes()

    def _override_build(self, **kwargs):
        """Takes care of derived component creation. must be implemented by child class

        Raises:
            NotImplementedError: must be implemented by child classes
        """
        raise NotImplementedError

    def _post_build(self, **kwargs):
        """Build cleanup. sets build to true and renames nodes"""
        self.rename_nodes()

    def __create_base_nodes(self, parent_container: nw.Container = None):
        """Creates the base node (input, output, container) in the initialization
        phase

        Args:
            parent_container (nw.Container, optional): Defaults to None.
        """
        # input node
        input_node = nw.create_node(
            type(self).input_node_type, type(self).input_node_name
        )

        # see if transform trs is locked
        if type(self).input_node_type == "transform" and type(self).lock_transform:
            for attr in ["t", "r", "s"]:
                input_node[attr].set_locked(True)
                for axis in ["x", "y", "z"]:
                    input_node[f"{attr}{axis}"].set_keyable(False)

        input_node_attr_data = self._input_attr_build_data()
        input_node_attr_data.add_attrs_to_node(input_node)

        # connecting instance name
        input_node[self._BLD_COMP_NAMESPC][0][self._BLD_COMP_NAME] = type(
            self
        ).class_namespace
        input_node[self._BLD_COMP_NAMESPC][0].set_locked(True)
        (
            input_node[self._BLD_COMP_NAMESPC][1][self._BLD_COMP_MESS]
            << input_node[self._BLD_INST_NAME]
        )

        # output node
        output_node_attr_data = self._output_attr_build_data()
        has_output_node = len(output_node_attr_data.node_attr_dict) > 1
        if has_output_node:
            output_node = nw.create_node("network", "output")
            output_node_attr_data = self._output_attr_build_data()
            output_node_attr_data.add_attrs_to_node(output_node)

        # container node
        self._node_data_cache["container_node"] = nw.create_node(
            "container", "container"
        )
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
        if not NAME_CLS.equal_namespace(prev_namespace, namespace) and NAME_CLS.exists(
            namespace
        ):
            inst_name_base = self.input_node[self._BLD_INST_NAME].value
            if inst_name_base is None or inst_name_base == "":
                inst_name_base = "temp"
            else:
                inst_name_base = utils.strip_trailing_numbers(inst_name_base)
            index = 1
            while NAME_CLS.exists(self.get_namespace(f"{inst_name_base}{index}")):
                index += 1
            self.input_node[self._BLD_INST_NAME] = f"{inst_name_base}{index}"
            namespace = self.get_namespace()

        # add namespace if it doesn't exist
        if (
            NAME_CLS.exists(prev_namespace)
            and not NAME_CLS.exists(namespace)
            and prev_namespace != ":"
        ):
            NAME_CLS.rename(prev_namespace, namespace)
        if not NAME_CLS.exists(namespace):
            NAME_CLS.add_namespace(namespace)

        # renames container
        if not self.container_node.name.startswith(namespace):
            strip_namespace_node = utils.Namespace.strip_namespace(
                self.container_node.name
            )
            self.container_node.rename(f"{namespace}:{strip_namespace_node}")

        # renaming nodes
        for node in [
            node
            for node in self.container_node.get_nodes()
            if node.type_ != "container"
        ]:
            if not node.name.startswith(namespace):
                strip_namespace_node = utils.Namespace.strip_namespace(node.name)
                node.rename(f"{namespace}:{strip_namespace_node}")

        # if prev namespace is empty, delete it
        if NAME_CLS.exists(prev_namespace) and NAME_CLS.empty(prev_namespace):
            NAME_CLS.delete(prev_namespace)

        for child_comp in self.child_components():
            child_comp.rename_nodes()

    def get_parent_type_component(
        self, parent_type: component_enum_data.ComponentType, disable_warning=False
    ) -> "_Component":
        """Given a type gets the closest parent component of that type

        Args:
            parent_type (component_enum_data.ComponentType):
            disable_warning (bool):

        Returns:
            Component:
        """
        container = self.container_node
        while container is not None and container[
            self._BLD_COMP_TYPE
        ].value != component_enum_data.ComponentType.index_of(parent_type):
            container = container.get_container_node()
        if container is not None:
            return get_component(container)
        else:
            if not disable_warning:
                cmds.warning(f"parent component of type {parent_type.name} not found")
            return None

    def get_mirror_component(self, container: nw.Container = None) -> "_Component":
        """Gets mirror component. Returns None if not found

        Returns:
            Component:
        """

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
                mirror_container = (
                    curr_container[self._MIRROR_SRC].get_dest_connections()[0].node
                )
                break
            elif curr_container.has_attr(self._MIRROR_DEST):
                mirror_container = (
                    curr_container[self._MIRROR_DEST].get_src_connection().node
                )
                break
            if curr_container.has_attr(self._CNTNR_PAR_COMP):
                par_comp_attr = curr_container[self._CNTNR_PAR_COMP]
                connection = par_comp_attr.get_src_connection()
                if connection is None:
                    break

                component_data.append(
                    {
                        COMP_LEN: len(connection.parent),
                        COMP_INDEX: connection.index,
                        COMP_NAMESPC: get_component(curr_container).get_short_namespace,
                    }
                )
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
                mirror_container = (
                    child_attrs[mirror_data[COMP_INDEX]].get_dest_connections()[0].node
                )
                continue
            else:
                mirror_container = None
                for attr in child_attrs:
                    new_cntnr = attr.get_dest_connections()[0].node
                    new_cntnr_namespace = get_component(new_cntnr).get_short_namespace
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
