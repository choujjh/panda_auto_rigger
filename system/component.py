import utils.node_wrapper as nw
import system.component_data as component_data
import system.component_enum as component_enum
from typing import Union

import utils.utils as utils

import maya.cmds as cmds

def get_component(container_node:nw.Node):
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
        is_built (bool): True if the component is already built
        full_namespace (str): namespace with all parent namespaces included
        short_namespace (str): components full namespace (without parent namespaces)
        instance_namespace (str): instance name + side
    """
    component_type = component_enum.ComponentTypes.component
    root_transform_name = None
    class_namespace = "component"

    def __init__(self, container_node:nw.Node=None):
        """initializes component with container nodes

        Args:
            container_node (nw.Node, optional): container to initialize with 
            (incase component is already existing). Defaults to None.
        """
        self.__node_data_cache = {}
        self.__namespace_cache = {"full_namespace":"", "short_namespace":"", "instance_namespace":"", "hier_side":"", "instance_name":""}
        self.class_name = utils.class_type_to_str(type(self))
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
    def transform_node(self)->nw.Node:
        """Transform node (also input node). if no transform node is created 
        returns None

        Returns:
            nw.Node:
        """
        if type(self).root_transform_name is not None:
            return self.input_node
    @property
    def is_built(self):
        """True if the component is already built

        Returns:
            _type_: _description_
        """
        return self.container_node["built"].value

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
                    instance_namespace = f"{component_enum.CharacterSide.get(side).value}_"

        instance_name = None
        if self.input_node.has_attr("instanceName"):
            instance_name = self.input_node["instanceName"].value
            if instance_name != self.__namespace_cache["instance_name"]:
                self.__namespace_cache["instance_name"] = instance_name
                
                if instance_name is not None and instance_name!= "":
                    instance_namespace = f"{instance_namespace}{instance_name}"

        if instance_namespace != "":
            self.__namespace_cache["instance_namespace"] = instance_namespace

    # node add attr data
    def _get_input_node_attr_data(self) -> component_data.NodeData:
        """Defines all the added, published, or modified attributes for the 
        input node. Can be added onto by inherited classes

        Returns:
            comp_data.NodeData:
        """
        node_data =  component_data.NodeData(
            component_data.AttrData(name="input", type_="compound", publish=True),
            component_data.AttrData(name="buildData", type_="compound", publish=True),
            component_data.AttrData(name="componentClass", type_="string", value=self.class_name, locked=True, parent="buildData"),
            component_data.AttrData(name="componentType", type_=type(self).component_type, locked=True, parent="buildData"),
            component_data.AttrData(name="instanceName", type_="string", parent="buildData"),
        )
        return node_data
    def _get_output_node_attr_data(self) -> component_data.NodeData:
        """Defines all the added, published, or modified attributes for the 
        output node. Can be added onto by inherited classes

        Returns:
            comp_data.NodeData:
        """
        node_data = component_data.NodeData(
            component_data.AttrData(name="output", type_="compound", publish=True),
        )        
        return node_data
    def _get_container_node_attr_data(self) -> component_data.NodeData:
        """Defines all the added, published, or modified attributes for the
        container node. Can be added onto by inherited classes

        Returns:
            comp_data.NodeData:
        """
        return component_data.NodeData(
            component_data.AttrData(name="built", type_="bool", locked=True),
            component_data.AttrData(name="controlSetups", type_="message"),
            component_data.AttrData(name="parentComponent", type_="message"),
            component_data.AttrData(name="childComponents", type_="message", multi=True),
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
                        input_node_name = self.input_node["instanceName"]
                        cmds.warning(f"{instance_name} is not a string attribute. Not connectiong to {input_node_name}")
                    else:
                        instance_name >> self.input_node["instanceName"]
                else:
                    self.input_node["instanceName"]=instance_name
            
            # connecting parent and child components
            if parent is not None:
                if parent.has_attr("childComponents"):
                    child_component_len = len(parent["childComponents"])
                    parent["childComponents"][child_component_len] >> self.container_node["parentComponent"]

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
        self.container_node["built"] = True
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
        input_node_attr_data = self._get_input_node_attr_data()
        input_node_attr_data.add_attrs_to_node(input_node)

        # output node
        output_node_attr_data = self._get_output_node_attr_data()
        has_output_node = len(output_node_attr_data.node_attr_list) > 1
        if has_output_node:
            output_node = nw.create_node("network", "output")
            output_node_attr_data = self._get_output_node_attr_data()
            output_node_attr_data.add_attrs_to_node(output_node)

        # container node
        self.__node_data_cache["container_node"] = nw.create_node("container", "component_container")
        container_node_attr_data = self._get_container_node_attr_data()
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
        self.rename_nodes()

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
                if self.input_node["instanceName"].value == "" or self.input_node["instanceName"].value is None:
                    self.input_node["instanceName"] = "temp"
                # getting just the instance_namespace portion of children namespaces
                child_namespaces = [x.split("__", 1)[0] for x in child_namespaces if x.startswith(utils.strip_trailing_numbers(self.instance_namespace))]
                if child_namespaces != []:
                    highest_trailing_number = utils.get_max_trailing_number(child_namespaces)
                    instance_name = utils.strip_trailing_numbers(self.input_node["instanceName"].value)
                    self.input_node["instanceName"] = f"{instance_name}{int(highest_trailing_number + 1)}"

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

        # TODO
        # connect it up
        # re publish if needs be

class Hierarchy(Component):
    """A Class meant to be inherited for all hierarchy classes. hierarchy in this
    case is defined as a chain of matricies 

    Attributes:
        HIER_DATA (component_data.HierData): stores all Hier names and hier check
        functions
    """
    HIER_DATA = component_data.HierData
    class_namespace = "hier"
    component_type = component_enum.ComponentTypes.hier

    def _get_input_node_attr_data(self):
        node_data = super()._get_input_node_attr_data()
        node_data.extend_attr_data(self.HIER_DATA.get_hier_data())
        node_data.extend_attr_data(self.HIER_DATA.get_input_xform_data())
        return node_data
    def _get_output_node_attr_data(self):
        node_data = super()._get_output_node_attr_data()
        node_data.extend_attr_data(self.HIER_DATA.get_output_xform_data())
        return node_data
    
    def _post_build(self):
        super()._post_build()
        self.__populate_output_xforms()
        self.rename_nodes()
        self.__check_xforms()
    
    def __populate_output_xforms(self):
        """Goes through the output xform attributes and tries to connect name, local matrix, and init matricies"""
        added_nodes = []
        for index in range(len(self.output_node[self.HIER_DATA.OUTPUT_XFORM])):
            # init inverse matrix
            self.__populate_name(index)
            added_nodes.extend(self.__populate_init_matrix(index))
            added_nodes.extend(self.__populate_loc_matrix(index))

        # add nodes to container
        self.container_node.add_nodes(*added_nodes)

    def __populate_name(self, index:int):
        """Given the index tries to connect or set the output name

        Args:
            index (int): xform index
        """
        # set variables
        input_name = self.input_node[self.HIER_DATA.INPUT_XFORM][index][self.HIER_DATA.INPUT_XFORM_NAME]
        output_name = self.output_node[self.HIER_DATA.OUTPUT_XFORM][index][self.HIER_DATA.OUTPUT_XFORM_NAME]
        output_ws_src = self.output_node[self.HIER_DATA.OUTPUT_XFORM][index][self.HIER_DATA.OUTPUT_WORLD_MATRIX].get_src_connection()
        
        # check if needs to be set
        if output_name.value is not None and output_name.value != "":
            pass

        # if input and output xform match
        elif (len(self.input_node[self.HIER_DATA.INPUT_XFORM]) ==
            len(self.output_node[self.HIER_DATA.OUTPUT_XFORM])):
            input_name >> output_name
        
        elif output_ws_src is not None:
            if output_ws_src.node.has_attr("instanceName"):
                output_ws_src.node["instanceName"] >> output_name
    def __populate_init_matrix(self, index:int):
        """Given the index tries to connect or set the output init matrix and output inverse init matrix

        Args:
            index (int): xform index
        """
        input_xform_dict = self._get_input_xform_attrs(index)
        output_xform_dict = self._get_output_xform_attrs(index)

        # storing matrix attributes
        input_init_matrix = input_xform_dict[self.HIER_DATA.INPUT_INIT_MATRIX]
        input_init_inv_matrix = input_xform_dict[self.HIER_DATA.INPUT_INIT_INV_MATRIX]
        output_init_matrix = output_xform_dict[self.HIER_DATA.OUTPUT_INIT_MATRIX]
        output_init_inv_matrix = output_xform_dict[self.HIER_DATA.OUTPUT_INIT_INV_MATRIX]

        # output src  connection
        output_init_src = output_init_matrix.get_src_connection()

        # if output init inverse matrix is connected then return
        if output_init_inv_matrix.get_src_connection() is not None:
            return []

        # if connected to transform
        if (output_init_src.attr_name == "worldMatrix[0]" and 
            output_init_src.node.has_attr("worldInverseMatrix[0]")):
            output_init_src.node["worldInverseMatrix[0]"] >> output_init_inv_matrix

        # if output init connected to input init
        elif output_init_src == input_init_matrix:
            input_init_inv_matrix >> output_init_inv_matrix

        # if output init is connected to
        elif output_init_src is not None:
            inverse_matrix_node = nw.create_node("inverseMatrix", f"xform{index}_inverse_mat")
            output_init_src >> inverse_matrix_node["inputMatrix"]
            inverse_matrix_node["outputMatrix"] >> output_init_inv_matrix
            return [inverse_matrix_node]
        
        # if lengths match
        elif len(input_init_matrix.parent) == len(output_init_matrix.parent):
            input_init_matrix >> output_init_matrix
            input_init_inv_matrix >> output_init_inv_matrix

        return []
    def __populate_loc_matrix(self, index:int):
        """Given the index tries to connect or set the output local matrix

        Args:
            index (int): xform index
        """
        output_xform_attrs = self._get_output_xform_attrs(index)
        output_loc_matrix = output_xform_attrs[self.HIER_DATA.OUTPUT_LOC_MATRIX]
        output_world_matrix_src = output_xform_attrs[self.HIER_DATA.OUTPUT_WORLD_MATRIX].get_src_connection()
        
        added_nodes = []

        # if world matrix isn't connected return
        if output_world_matrix_src is None:
            return []
        # has no parent
        elif index <= 0:
            output_world_matrix_src >> output_loc_matrix
        
        # connect to parent
        else:
            prev_world_matrix_src = self.output_node[self.HIER_DATA.OUTPUT_XFORM][index-1][self.HIER_DATA.OUTPUT_WORLD_MATRIX]
            prev_world_matrix_src = prev_world_matrix_src.get_src_connection()
            if prev_world_matrix_src is None:
                return []
            inverse_attr = None
            # of connected ws are translates
            if (prev_world_matrix_src.node.has_attr("worldInverseMatrix[0]") and 
                  output_world_matrix_src.attr_name == "worldMatrix[0]"
                  ):
                inverse_attr = prev_world_matrix_src.node["worldInverseMatrix"][0]
            # if inverse node needed
            if inverse_attr is None:
                inverse_matrix_node = nw.create_node("inverseMatrix", f"xform{index-1}_out_world_inverse_mat")
                prev_world_matrix_src >> inverse_matrix_node["inputMatrix"]
                inverse_attr = inverse_matrix_node["outputMatrix"]

                added_nodes = [inverse_attr]

            # adding matrix mult
            mat_mult = nw.create_node("multMatrix", f"xform{index}_loc_output_mat_mult")
            output_world_matrix_src >> mat_mult["matrixIn"][0]
            inverse_attr >> mat_mult["matrixIn"][1]
            mat_mult["matrixSum"] >> output_loc_matrix

            added_nodes.append(mat_mult)

            return added_nodes
        return added_nodes

    def __check_xforms(self):
        """After component is built, checks to see if xforms were properly set"""
        input_xform_len = len(self.input_node[self.HIER_DATA.INPUT_XFORM])
        output_xform_len = len(self.output_node[self.HIER_DATA.OUTPUT_XFORM])
        if output_xform_len == 0:
            cmds.warning(f"{self.container_node} component has no xform output")

        if input_xform_len > output_xform_len:
            cmds.warning(f"input xform (len {input_xform_len}) longer than output xform (len {output_xform_len})")
        
        for attr in self.output_node[self.HIER_DATA.OUTPUT_XFORM]:
            for sub_attr in self.HIER_DATA.OUTPUT_DATA_NAMES:
                if attr[sub_attr].type_ == "string":
                    if attr[sub_attr].value == None or attr[sub_attr].value == "":
                        cmds.warning(f"{attr[sub_attr]} not set")
                elif not attr[sub_attr].has_src_connection():
                    cmds.warning(f"{attr[sub_attr]} does not have connection")
    def _get_input_xform_attrs(self, index:int):
        """Gets the input attributes of an index

        Args:
            index (int):

        Returns:
            dict: dict of input attributes
        """
        return {key: self.input_node[self.HIER_DATA.INPUT_XFORM][index][key] for key in self.HIER_DATA.INPUT_DATA_NAMES}
    def _get_output_xform_attrs(self, index:int):
        """Gets the output attributes of an index

        Args:
            index (int):

        Returns:
            dict: dict of output attributes
        """
        return {key: self.output_node[self.HIER_DATA.OUTPUT_XFORM][index][key] for key in self.HIER_DATA.OUTPUT_DATA_NAMES}
    def _set_output_xform_attrs(
            self, 
            index:int, 
            output_xform_name:Union[nw.Attr, str]=None, 
            output_init_matrix:nw.Attr=None, 
            output_init_inv_matrix:nw.Attr=None, 
            output_world_matrix:nw.Attr=None, 
            output_loc_matrix:nw.Attr=None
        ):
        """Connects up attributes to output xform

        Args:
            index (int):
            output_name (Union[nw.Attr, str], optional): Defaults to None.
            output_init_matrix (nw.Attr, optional): Defaults to None.
            output_init_inv_matrix (nw.Attr, optional): Defaults to None.
            output_world_matrix (nw.Attr, optional): Defaults to None.
            output_loc_matrix (nw.Attr, optional): Defaults to None.
        """
        output_xform_matricies = self._get_output_xform_attrs(index)
        source_attr_list = [output_xform_name, output_init_matrix, output_init_inv_matrix, output_world_matrix, output_loc_matrix]
        for source_attr, output_attr in zip(source_attr_list, self.HIER_DATA.OUTPUT_DATA_NAMES):
            if isinstance(source_attr, str):
                output_xform_matricies[output_attr].set(source_attr)
            elif source_attr is not None:
                source_attr >> output_xform_matricies[output_attr]
        

class Control(Component):
    """A Base class for all control autorigging components. Derived from Component

    Attributes:
        can_set_color (bool): can set color of component
    """
    component_type = component_enum.ComponentTypes.control
    root_transform_name = "cntrl"
    class_namespace = ""
    can_set_color = True

    @ property
    def control_setup_node(self):
        """control setup node used to create this control

        Returns:
            nw.Node:
        """
        if self.container_node is not None:
            return self._get_node_data_from_cache("controlSetupNode")
    @property
    def axis_vec(self):
        """axis to build control on

        Returns:
            str:
        """
        axis_vec = component_enum.AxisEnums.y.value
        if self.control_setup_node is not None:
            axis_vec = component_enum.AxisEnums.get(self.control_setup_node["buildAxis"].value).value
        return axis_vec
    def _get_input_node_attr_data(self) -> component_data.NodeData:
        node_data = super()._get_input_node_attr_data()

        node_data.extend_attr_data(
            component_data.AttrData(name="offsetParentMatrix", publish="offsetMatrix"),
            component_data.AttrData(name="worldMatrix[0]", publish="worldMatrix"),
            component_data.AttrData(name="matrix", publish="localMatrix"),
            component_data.AttrData(name="worldInverseMatrix[0]", publish="worldInverseMatrix"),

            component_data.AttrData(name="overrideEnabled", publish="hasColor", locked=not type(self).can_set_color),
            component_data.AttrData(name="overrideColorRGB", publish="color", locked=not type(self).can_set_color),
            component_data.AttrData(name="overrideRGBColors", value=1),
        )

        return node_data
    def _override_build(self, **kwargs):
        # set visibility to hidden in channel box
        self.transform_node["visibility"].set_keyable(False)

        # add shapes
        self._apply_shape_to_cntrl()

    def _create_shapes(self) -> list:
        """Creates shapes and returns a list of the shapes transforms. these 
        shapes will be parented to the transform node later

        Returns:
            list(nw.Node):
        """
        raise NotImplementedError
        
    def _apply_shape_to_cntrl(self):
        """Takes create shape function and adds all shapes to transform node"""

        # parenting to transform
        shape_transforms = self._create_shapes()
        for transform in shape_transforms:
            if not isinstance(transform, nw.Node):
                transform = nw.wrap_node(transform)

            # delete history
            cmds.delete(str(transform), constructionHistory=True)

            # freeze all controls
            utils.freeze_transform(transform)

            # apply to transform
            for x in cmds.listRelatives(str(transform), shapes=True):
                cmds.parent(x, str(self.transform_node), relative=True, shape=True)
        
        # deleting transforms
        if shape_transforms != []:
            cmds.delete(shape_transforms)

        shapes_list = self.transform_node.get_shapes()
    
        # rename shapes
        transform_stripped_name = utils.Namespace.strip_namespace(str(self.transform_node))
        for index, shape in enumerate(shapes_list):
            shape.rename(f"{transform_stripped_name}Shape{index+1}")

        # add shapes to container
        self.container_node.add_nodes(*shapes_list)

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

            attr_connection = attr.get_src_connections()
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