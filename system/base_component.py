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
        full_namespace (str): namespace with all parent namespaces included
        short_namespace (str): components full namespace (without parent namespaces)
        instance_namespace (str): instance name + side

        _IN (str): str constant for input
        _BLD_DATA (str): str constant for buildData
        _BLD_COMP_CLASS (str): str constant for componentClass
        _BLD_COMP_TYPE (str): str constant for componentType
        _BLD_INST_NAME (str): str constant for instanceName
        _OUT (str): str constant for output
        _CONTR_PAR_COMP (str): str constant for parentComponent
        _CONTR_CHLD_COMP (str): str constant for childComponents
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
    _CONTR_PAR_COMP = "parentComponent"
    _CONTR_CHLD_COMP = "childComponents"

    def __init__(self, container_node:nw.Node=None):
        """initializes component with container nodes

        Args:
            container_node (nw.Node, optional): container to initialize with 
            (incase component is already existing). Defaults to None.
        """
        self.__node_data_cache = {}
        self.__namespace_cache = {"full_namespace":"", "short_namespace":"", "instance_namespace":"", "hier_side":"", "instance_name":""}
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
    @classmethod
    def get_class_name(cls)->str:
        return utils.class_type_to_str(cls)

    #namespace functions
    @property
    def full_namespace(self):
        """namespace with all parent namespaces included

        Returns:
            str:
        """
        self.__update_full_namespace()
        return self.__namespace_cache["full_namespace"]
    @property
    def short_namespace(self):
        """components full namespace (without parent namespaces)

        Returns:
            str:
        """
        self.__update_short_namespace()
        return self.__namespace_cache["short_namespace"]
    @property
    def instance_namespace(self):
        """instance name + side

        Returns:
            str:
        """
        self.__update_instance_namespace()
        return self.__namespace_cache["instance_namespace"]
    def __update_full_namespace(self):
        """Updates full_namespace"""

        parent_container = None
        if self.container_node is not None:
            parent_container = self.container_node.get_container_node()
        short_namespace = self.short_namespace
        full_namespace = ""
        cached_full_namespace = self.__namespace_cache["full_namespace"]
        if parent_container is None:
            if cached_full_namespace.find(short_namespace) != 1:
                full_namespace = f":{short_namespace}"
        else:
            parent_namespace = utils.Namespace.get_namespace(str(parent_container))
            if cached_full_namespace.find(parent_namespace) != 0:
                full_namespace = f"{utils.Namespace.get_namespace(str(parent_container))}:{short_namespace}"
            else:
                cached_full_namespace = cached_full_namespace.replace(parent_namespace, "", 1)
                if cached_full_namespace.find(short_namespace) != 1:
                    full_namespace = f"{utils.Namespace.get_namespace(str(parent_container))}:{short_namespace}"
                    
        if full_namespace != "":
            self.__namespace_cache["full_namespace"] = full_namespace
    def __update_short_namespace(self):
        """Updates short_namespace"""

        instance_namespace = self.instance_namespace
        short_namespace = ""

        if instance_namespace is not None and instance_namespace != "":
            if not self.__namespace_cache["short_namespace"].startswith(f"{instance_namespace}__"):
                short_namespace = f"{instance_namespace}__{type(self).class_namespace}"
        else:
            if self.__namespace_cache["short_namespace"] != type(self).class_namespace:
                short_namespace = type(self).class_namespace

        if short_namespace != "":
            self.__namespace_cache["short_namespace"] = short_namespace
        if type(self).class_namespace == None or type(self).class_namespace == "":
            self.__namespace_cache["short_namespace"] = short_namespace.replace("__", "")
    def __update_instance_namespace(self):
        """Update instance namespace"""

        instance_namespace = ""

        if self.input_node is None:
            return

        side = None
        if self.input_node.has_attr("hierSide"):
            side = self.input_node["hierSide"].value
            if side != self.__namespace_cache["hier_side"]:
                self.__namespace_cache["hier_side"] = side
                
                if side is not None and side != "":
                    instance_namespace = f"{component_enum_data.CharacterSide.get(side).value}_"

        instance_name = None
        if self.input_node.has_attr(self._BLD_INST_NAME):
            instance_name = self.input_node[self._BLD_INST_NAME].value
            if instance_name != self.__namespace_cache["instance_name"]:
                self.__namespace_cache["instance_name"] = instance_name
                
                if instance_name is not None and instance_name!= "":
                    instance_namespace = f"{instance_namespace}{instance_name}"

        if instance_namespace != "":
            self.__namespace_cache["instance_namespace"] = instance_namespace

    # node add attr data
    def _get_input_node_build_attr_data(self) -> component_data.NodeData:
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
    def _get_output_node_build_attr_data(self) -> component_data.NodeData:
        """Defines all the added, published, or modified attributes for the 
        output node. Can be added onto by inherited classes

        Returns:
            comp_data.NodeData:
        """
        node_data = component_data.NodeData(
            component_data.AttrData(name=self._OUT, type_="compound", publish=True),
        )        
        return node_data
    def _get_container_node_build_attr_data(self) -> component_data.NodeData:
        """Defines all the added, published, or modified attributes for the
        container node. Can be added onto by inherited classes

        Returns:
            comp_data.NodeData:
        """
        return component_data.NodeData(
            component_data.AttrData(name=self._CONTR_PAR_COMP, type_="message"),
            component_data.AttrData(name=self._CONTR_CHLD_COMP, type_="message", multi=True),
        )

    @classmethod
    def create(cls, instance_name:Union[str, nw.Attr]=None, parent=None, **kwargs):
        """class method to create component

        Args:
            instance_name (str, nw.Attr, optional): name of component. Defaults to None.
            parent (nw.Container, Component, optional): Defaults to None.

        Returns:
            cls: returns created 
        """
        component_inst = cls()
        component_inst._pre_build(instance_name=instance_name, parent=parent)
        component_inst._override_build(**kwargs)
        component_inst._post_build()

        return component_inst
    def _pre_build(self, instance_name:Union[str, nw.Attr]=None, parent=None):
        """handles creation and connection of initial nodes and 

        Args:
            instance_name (str, nw.Attr, optional): component instance name. Defaults to None.
            parent (nw.Container, Component, optional): Defaults to None.
        """
        if parent is not None and isinstance(parent, Component):
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
                if parent.has_attr(self._CONTR_CHLD_COMP):
                    child_component_len = len(parent[self._CONTR_CHLD_COMP])
                    parent[self._CONTR_CHLD_COMP][child_component_len] >> self.container_node[self._CONTR_PAR_COMP]

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
    def _post_build(self):
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
        input_node_attr_data = self._get_input_node_build_attr_data()
        input_node_attr_data.add_attrs_to_node(input_node)

        # output node
        output_node_attr_data = self._get_output_node_build_attr_data()
        has_output_node = len(output_node_attr_data.node_attr_dict) > 1
        if has_output_node:
            output_node = nw.create_node("network", "output")
            output_node_attr_data = self._get_output_node_build_attr_data()
            output_node_attr_data.add_attrs_to_node(output_node)

        # container node
        self.__node_data_cache["container_node"] = nw.create_node("container", "container")
        container_node_attr_data = self._get_container_node_build_attr_data()
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

        def rename_node(node, full_namespace):
            if not node.name.startswith(full_namespace):
                strip_namespace_node = utils.Namespace.strip_namespace(node.name)
                node.rename(f"{full_namespace}:{strip_namespace_node}")
        full_namespace = self.full_namespace
        prev_namespace = utils.Namespace.get_namespace(self.container_node.name)

        # if you need to add the namespace
        if not utils.Namespace.equal_namespace(full_namespace, prev_namespace):
            # if namespace doesn't exist
            if utils.Namespace.exists(full_namespace):
                parent_namespace = utils.Namespace.get_namespace(full_namespace)
                child_namespaces = [utils.Namespace.strip_namespace(x) for x in utils.Namespace.child_namespaces(parent_namespace)]
                # add something to instance namespace if it's none
                if (self.input_node[self._BLD_INST_NAME].value == "" or self.input_node[self._BLD_INST_NAME].value is None):
                    self.input_node[self._BLD_INST_NAME] = "temp"
                # getting just the instance_namespace portion of children namespaces
                child_namespaces = [x.split("__", 1)[0] for x in child_namespaces if x.startswith(utils.strip_trailing_numbers(self.instance_namespace))]
                if child_namespaces != []:
                    highest_trailing_number = utils.get_max_trailing_number(child_namespaces)
                    instance_name = utils.strip_trailing_numbers(self.input_node[self._BLD_INST_NAME].value)
                    self.input_node[self._BLD_INST_NAME] = f"{instance_name}{int(highest_trailing_number + 1)}"

                # give it a unique namespace by giving instance_namespace a new value
                full_namespace = self.full_namespace
            
            utils.Namespace.add_namespace(full_namespace)
        rename_node(self.container_node, full_namespace)
        for node in self.container_node.get_nodes():
            # TODO replace later with if it's a component not just a container
            if node.type_ != "container":
                rename_node(node, full_namespace)
        # check if nothing else in namespace delete
        if utils.Namespace.empty(prev_namespace):
            utils.Namespace.delete(prev_namespace)

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
    _has_input_init_matricies = False

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

    @property
    def has_input_init_matricies(self):
        return type(self)._has_input_init_matricies

    @classmethod
    def create(cls, source_component:Component, connect_hierarchy:bool=True, instance_name = None, parent=None, **kwargs):
        kwargs[cls._KWG_SRC_COMP] = source_component
        kwargs[cls._KWG_CONN_HIER] = connect_hierarchy
        return super().create(instance_name, parent, **kwargs)

    def _get_input_node_build_attr_data(self):
        node_data = super()._get_input_node_build_attr_data()
        node_data.extend_attr_data(self.HIER_DATA.get_hier_data())
        node_data.extend_attr_data(self.HIER_DATA.get_input_xform_data(self.has_input_init_matricies))
        return node_data
    def _get_output_node_build_attr_data(self):
        node_data = super()._get_output_node_build_attr_data()
        node_data.extend_attr_data(self.HIER_DATA.get_output_xform_data())
        return node_data
    def _post_build(self):
        super()._post_build()
        self._populate_output_xforms()
        self.rename_nodes()
        self._check_xforms()
    def _populate_output_xforms(self):
        """Goes through the output xform attributes and tries to connect name, local matrix, and init matricies"""
        added_nodes = []
        HIER_DATA = self.HIER_DATA
        output_xforms = self._get_output_xform_attrs()
        for index, output_xform in output_xforms.items():
            # init inverse matrix
            self.__populate_name(index)
            if self.has_input_init_matricies:
                added_nodes.extend(self.__populate_world_matrix(
                    index=index,
                    world_matrix_attr=output_xform[HIER_DATA.OUTPUT_INIT_MATRIX],
                    world_matrix_inv_attr=output_xform[HIER_DATA.OUTPUT_INIT_INV_MATRIX],
                    is_init_matrix=True))
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

        input_xform = self._get_input_xform_attrs(index=index)[index]
        output_xform = self._get_output_xform_attrs(index=index)[index]

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
            if matrix_src is None and self.has_input_init_matricies:
                input_xform[self.HIER_DATA.INPUT_INIT_MATRIX] >> world_matrix_attr
            if inv_matrix_src is None and self.has_input_init_matricies:
                input_xform[self.HIER_DATA.INPUT_INIT_INV_MATRIX] >> world_matrix_inv_attr
        return added_nodes
    def __populate_loc_matrix(self, index:int):
        """Given the index tries to connect or set the output local matrix

        Args:
            index (int): xform index
        """
        output_xform_attrs = self._get_output_xform_attrs(index)[index]
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
        return added_nodes

    def _check_xforms(self, check_len=True):
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
    def _get_input_xform_attrs(self, index:Union[int, list]=None):
        """Gets a dict of input xforms given indicies. returns all if index is None

        Returns:
            dict: 
        """
        
        if index is None:
            indicies = range(len(self.input_node[self.HIER_DATA.INPUT_XFORM]))
        else:
            indicies = utils.make_iterable(index)
        return {index:{key: self.input_node[self.HIER_DATA.INPUT_XFORM][index][key] for key in self.HIER_DATA.get_input_data_names(self.has_input_init_matricies)} for index in indicies}
    def _get_output_xform_attrs(self, index:Union[int, list]=None):
        """Gets a dict of output xforms given indicies. returns all if index is None

        Returns:
            list:
        """
        if index is None:
            indicies = range(len(self.output_node[self.HIER_DATA.OUTPUT_XFORM]))
        else:
            indicies = utils.make_iterable(index)
        return {index:{key: self.output_node[self.HIER_DATA.OUTPUT_XFORM][index][key] for key in self.HIER_DATA.get_output_data_names()} for index in indicies}
    def _set_input_xform_attrs(
            self, 
            index:int, 
            input_xform_name:Union[nw.Attr, str]=None, 
            input_init_matrix:nw.Attr=None, 
            input_init_inv_matrix:nw.Attr=None, 
            input_world_matrix:nw.Attr=None,
            input_world_inv_matrix:nw.Attr=None,
            input_loc_matrix:nw.Attr=None
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
        """
        input_xform_matricies = self._get_input_xform_attrs(index=index)[index]
        if self.has_input_init_matricies:
            source_attr_list = [input_xform_name, input_init_matrix, input_init_inv_matrix, input_world_matrix, input_world_inv_matrix, input_loc_matrix]
        else:
            source_attr_list = [input_xform_name, input_world_matrix, input_world_inv_matrix, input_loc_matrix]
        input_data_names = self.HIER_DATA.get_input_data_names(self.has_input_init_matricies)
        if len(source_attr_list) != len(input_data_names):
            raise RuntimeError("source_attr_list and OUPUT_DATA_NAMES mismatched lengths")
        for source_attr, input_attr in zip(source_attr_list, input_data_names):
            if isinstance(source_attr, str):
                input_xform_matricies[input_attr].set(source_attr)
            elif source_attr is not None:
                source_attr >> input_xform_matricies[input_attr]
    def _set_output_xform_attrs(
        self, 
        index:int, 
        output_xform_name:Union[nw.Attr, str]=None, 
        output_init_matrix:nw.Attr=None, 
        output_init_inv_matrix:nw.Attr=None, 
        output_world_matrix:nw.Attr=None, 
        output_world_inv_matrix:nw.Attr=None,
        output_loc_matrix:nw.Attr=None
    ):
        """Connects up attributes to output xform

        Args:
            index (int):
            output_name (Union[nw.Attr, str], optional): Defaults to None.
            output_init_matrix (nw.Attr, optional): Defaults to None.
            output_init_inv_matrix (nw.Attr, optional): Defaults to None.
            output_world_matrix (nw.Attr, optional): Defaults to None.
            output_world_inv_matrix (nw.Attr, optional): Defaults to None.
            output_loc_matrix (nw.Attr, optional): Defaults to None.
        """
        output_xform = self._get_output_xform_attrs(index)[index]
        source_attr_list = [output_xform_name, output_init_matrix, output_init_inv_matrix, output_world_matrix, output_world_inv_matrix, output_loc_matrix]
        output_data_names = self.HIER_DATA.get_output_data_names()
        if len(source_attr_list) != len(output_data_names):
            raise RuntimeError("source_attr_list and OUPUT_DATA_NAMES mismatched lengths")
        for source_attr, output_attr in zip(source_attr_list, output_data_names):
            if isinstance(source_attr, str):
                output_xform[output_attr].set(source_attr)
            elif source_attr is not None:
                source_attr >> output_xform[output_attr]
    
    def _has_output_xforms(self, source_component):
        """checks to see if component has output xforms"""
        if source_component.container_node.has_attr(self.HIER_DATA.OUTPUT_XFORM):
            if self.HIER_DATA.is_output_xform_attr(source_component.container_node[self.HIER_DATA.OUTPUT_XFORM][0]):
                return True
        return False
    def _has_input_xforms(self, source_component):
        """checks to see if component has input xforms"""
        if source_component.container_node.has_attr(self.HIER_DATA.INPUT_XFORM):
            if self.HIER_DATA.is_input_xform_attr(source_component.container_node[self.HIER_DATA.INPUT_XFORM][0]):
                return True
        return False
    
    def _connect_source_hier_component(self, source_component, connect_hierarchy):
        """Given a source Hier component connects it's hier output to this component's hier input

        Args:
            source_component (Hierarchy):
        """


        if self._has_output_xforms(source_component=source_component):
            HIER_DATA = self.HIER_DATA

            # getting both containers
            self_container = self.container_node
            source_container = source_component.container_node
            parent_component_as_source = True if source_container == self_container.get_container_node() else False
            if parent_component_as_source and not self._has_input_xforms(source_component=source_component):
                raise RuntimeError("source parent component does not have input xforms")

            if connect_hierarchy:
                for hier_attr_name in HIER_DATA.get_hier_data_names():
                    if source_container.has_attr(hier_attr_name):
                        source_container[hier_attr_name] >> self_container[hier_attr_name]

            src_type = self.IO_ENUM.input if parent_component_as_source else self.IO_ENUM.output
            src_xforms =  source_component._get_input_xform_attrs() if parent_component_as_source else source_component._get_output_xform_attrs()
            self_input_xforms = self._get_input_xform_attrs(utils.length_index_list(len(src_xforms.keys())))
            for index, src_xform in src_xforms.items():

                input_xform = self_input_xforms[index]
                # for loop through attributes to connect
                for src_name, self_input_name in HIER_DATA.get_paired_names(src=src_type, dest=self.IO_ENUM.input):
                    src_xform[src_name] >> input_xform[self_input_name]

                # connecting up the init matricies
                if self.has_input_init_matricies:
                    self_xform = self.container_node[HIER_DATA.INPUT_XFORM][index]
                    self_init_mat = self_xform[HIER_DATA.INPUT_INIT_MATRIX]
                    self_init_inv_mat = self_xform[HIER_DATA.INPUT_INIT_INV_MATRIX]
                else:
                    self_xform = self.container_node[HIER_DATA.OUTPUT_XFORM][index]
                    self_init_mat = self_xform[HIER_DATA.OUTPUT_INIT_MATRIX]
                    self_init_inv_mat = self_xform[HIER_DATA.OUTPUT_INIT_INV_MATRIX]

                source_container[HIER_DATA.OUTPUT_XFORM][index][HIER_DATA.OUTPUT_INIT_MATRIX] >> self_init_mat
                source_container[HIER_DATA.OUTPUT_XFORM][index][HIER_DATA.OUTPUT_INIT_INV_MATRIX] >> self_init_inv_mat
                    
            # connecting axis vectors
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

    def _get_input_node_build_attr_data(self):
        node_data = super()._get_input_node_build_attr_data()
        node_data.extend_attr_data(
            component_data.AttrData(self._PRM_VEC, type_="double3", parent=self._IN),
            component_data.AttrData(self._PRM_VEC_X, type_="double", parent=self._PRM_VEC),
            component_data.AttrData(self._PRM_VEC_Y, type_="double", parent=self._PRM_VEC),
            component_data.AttrData(self._PRM_VEC_Z, type_="double", parent=self._PRM_VEC),
            component_data.AttrData(self._SEC_VEC, type_="double3", parent=self._IN),
            component_data.AttrData(self._SEC_VEC_X, type_="double", parent=self._SEC_VEC),
            component_data.AttrData(self._SEC_VEC_Y, type_="double", parent=self._SEC_VEC),
            component_data.AttrData(self._SEC_VEC_Z, type_="double", parent=self._SEC_VEC),
            component_data.AttrData(self._TER_VEC, type_="double3", parent=self._IN),
            component_data.AttrData(self._TER_VEC_X, type_="double", parent=self._TER_VEC),
            component_data.AttrData(self._TER_VEC_Y, type_="double", parent=self._TER_VEC),
            component_data.AttrData(self._TER_VEC_Z, type_="double", parent=self._TER_VEC),
        )
        return node_data

    @classmethod
    def create(cls, source_component, connect_hierarchy=True, control_color=None, instance_name=None, parent=None, **kwargs):
        kwargs[cls._KWG_CNTRL_CLR]=control_color
        return super().create(source_component, connect_hierarchy, instance_name, parent, **kwargs)

class Anim(Motion):
    """Base class for anim autorigging components. Derived from Hierarchy"""
    component_type = component_enum_data.ComponentType.anim
    root_transform_name = "grp"
    class_namespace = "anim"

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
    _KWG_BUILD_T = "build_t"
    _KWG_BUILD_R = "build_r"
    _KWG_BUILD_S = "build_s"
    _KWG_CLR = "color"

    @classmethod
    def create(cls, instance_name = None, parent=None, axis_vec=None, 
               build_t=[0.0, 0.0, 0.0],
               build_r=[0.0, 0.0, 0.0],
               build_s=[1.0, 1.0, 1.0], 
               color=None, **kwargs):
        kwargs[cls._KWG_AXIS_VEC] = axis_vec
        kwargs[cls._KWG_BUILD_T] = utils.make_len(build_t, len_=3) if utils.is_iterable(build_t) else [build_t, build_t, build_t]
        kwargs[cls._KWG_BUILD_R] = utils.make_len(build_r, len_=3) if utils.is_iterable(build_r) else [build_r, build_r, build_r]
        kwargs[cls._KWG_BUILD_S] = utils.make_len(build_s, len_=3, default=1.0) if utils.is_iterable(build_s) else [build_s, build_s, build_s]
        kwargs[cls._KWG_CLR] = color

        return super().create(instance_name, parent, **kwargs)

    def _get_input_node_build_attr_data(self) -> component_data.NodeData:
        node_data = super()._get_input_node_build_attr_data()

        node_data.extend_attr_data(
            component_data.AttrData(name="offsetParentMatrix", publish=self._IN_OFF_MAT),
            component_data.AttrData(name="worldMatrix[0]", publish=self._OUT_WS_MAT),
            component_data.AttrData(name="matrix", publish=self._OUT_LOC_MAT),
            component_data.AttrData(name="worldInverseMatrix[0]", publish=self._OUT_WS_INV_MAT),

            component_data.AttrData(name="overrideEnabled", publish=self._IN_HAS_CLR, locked=not type(self).can_set_color),
            component_data.AttrData(name="overrideColorRGB", publish=self._IN_HAS_CLR, locked=not type(self).can_set_color),
            component_data.AttrData(name="overrideRGBColors", value=1),
        )
        return node_data

    def _override_build(self, **kwargs):
        axis_vec = kwargs[self._KWG_AXIS_VEC]
        color = kwargs[self._KWG_CLR]
        # set visibility to hidden in channel box
        self.transform_node["visibility"].set_keyable(False)

        # add shapes
        self._apply_shape_to_cntrl(axis_vec=axis_vec)

        # add build transforms
        self.transform_node["translate"] = kwargs[self._KWG_BUILD_T]
        self.transform_node["rotate"] = kwargs[self._KWG_BUILD_R]
        self.transform_node["scale"] = kwargs[self._KWG_BUILD_S]
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
            for x in cmds.listRelatives(str(transform), shapes=True):
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
        """
        import component.enum_manager as enum_manager
        
        if self.container_node[self._IN_HAS_CLR].is_locked():
            return
        else:
            rgb = [1.0, 1.0, 1.0]
            shader = None
            surface_shapes = [shape for shape in self.transform_node.get_shapes() if shape.type_ == "mesh" or shape.type_ == "nurbsSurface"]
            if isinstance(color, nw.Node) and color.type_ == "lambert":
                shader = color
            elif isinstance(color, component_enum_data.Color):
                shader = enum_manager.Color.get_shader(color)
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