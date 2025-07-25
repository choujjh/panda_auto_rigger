import utils.node_wrapper as nw
import system.component_data as comp_data
import system.component_enum as component_enum
import re

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

def create_control_setup_node(name="controlSetup") -> nw.Node:
    """Creates control setup node

    Args:
        name (str, optional): name of control. Defaults to "controlSetup".

    Returns:
        nw.Node:
    """
    import component.control as control
    control_setup_node = nw.create_node("network", name)

    setup_node_data = comp_data.NodeData(
        comp_data.AttrData(name="containerNode", type="message"),
        comp_data.AttrData(name="controlComponent", type="message"),
        comp_data.AttrData(name="controlClass", type="enum", enum_name=":".join(utils.get_classes_from_package(control)[0])),
        comp_data.AttrData(name="instanceName", type="string"),
        comp_data.AttrData(name="shapeColor", type="enum", enum_name=component_enum.Colors.maya_enum_str()),
        comp_data.AttrData(
            name="nodeType", 
            type="enum", 
            enum_name=component_enum.ComponentTypes.maya_enum_str(), 
            value=component_enum.ComponentTypes.control_setup.value, 
            locked=True),
        comp_data.AttrData(name="attrInfo", type="compound", multi=True),
        comp_data.AttrData(name="attrMessage", type="message", parent="attrInfo"),
        comp_data.AttrData(name="attrName", type="string", parent="attrInfo"),
        comp_data.AttrData(name="lockAttrs", type="compound"),
        comp_data.AttrData(name="lockTX", type="bool", parent="lockAttrs"),
        comp_data.AttrData(name="lockTY", type="bool", parent="lockAttrs"),
        comp_data.AttrData(name="lockTZ", type="bool", parent="lockAttrs"),
        comp_data.AttrData(name="lockRX", type="bool", parent="lockAttrs"),
        comp_data.AttrData(name="lockRY", type="bool", parent="lockAttrs"),
        comp_data.AttrData(name="lockRZ", type="bool", parent="lockAttrs"),
        comp_data.AttrData(name="lockSX", type="bool", parent="lockAttrs"),
        comp_data.AttrData(name="lockSY", type="bool", parent="lockAttrs"),
        comp_data.AttrData(name="lockSZ", type="bool", parent="lockAttrs"),
        comp_data.AttrData(name="lockVis", type="bool", parent="lockAttrs", value=False),
        comp_data.AttrData(name="buildAxis", type="enum", enum_name=component_enum.AxisEnums.maya_enum_str(), value=1),
        comp_data.AttrData(name="buildTranslate", type="double3"),
        comp_data.AttrData(name="buildTranslateX", type="double", parent="buildTranslate"),
        comp_data.AttrData(name="buildTranslateY", type="double", parent="buildTranslate"),
        comp_data.AttrData(name="buildTranslateZ", type="double", parent="buildTranslate"),
        comp_data.AttrData(name="buildRotate", type="double3"),
        comp_data.AttrData(name="buildRotateX", type="double", parent="buildRotate"),
        comp_data.AttrData(name="buildRotateY", type="double", parent="buildRotate"),
        comp_data.AttrData(name="buildRotateZ", type="double", parent="buildRotate"),
        comp_data.AttrData(name="buildScale", type="double3"),
        comp_data.AttrData(name="buildScaleX", type="double", parent="buildScale", value=1),
        comp_data.AttrData(name="buildScaleY", type="double", parent="buildScale", value=1),
        comp_data.AttrData(name="buildScaleZ", type="double", parent="buildScale", value=1),
    )

    setup_node_data.add_attrs_to_node(control_setup_node)

    return control_setup_node

class Component():
    """A Base class for all autorigging components

    Attributes:
        component_type (component_enum.ComponentTypes): the component type
        root_transform_name (str): name of root transform. Defaults to None. 
        if true, the input node is a transform node instead of a network node
        class_namespace (str): gives the classes namespace
        has_hier_attrs (bool): creates hier attributes
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
    has_hier_attrs = False

    def __init__(self, container_node:nw.Node=None, parent_container_node:nw.Node=None):
        """initializes component with container nodes

        Args:
            container_node (nw.Node, optional): container to initialize with 
            (incase component is already existing). Defaults to None.
            parent_container_node (nw.Node, optional): container to be parented
            under. Defaults to None.
        """
        self.parent_container_node = parent_container_node
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
    def _get_input_node_attr_data(self) -> comp_data.NodeData:
        """Defines all the added, published, or modified attributes for the input node

        Returns:
            comp_data.NodeData:
        """
        node_data =  comp_data.NodeData(
            comp_data.AttrData(name="input", type="compound", publish=True),
            comp_data.AttrData(name="buildData", type="compound", publish=True),
            comp_data.AttrData(name="componentClass", type="string", value=self.class_name, locked=True, parent="buildData"),
            comp_data.AttrData(name="componentType", type=type(self).component_type, locked=True, parent="buildData"),
            comp_data.AttrData(name="instanceName", type="string", parent="buildData"),
        )
        
        if type(self).has_hier_attrs:
            node_data.extend_attr_data(comp_data.HierData.get_input_xform_data())
        return node_data
    def _get_output_node_attr_data(self) -> comp_data.NodeData:
        """Defines all the added, published, or modified attributes for the output node

        Returns:
            comp_data.NodeData:
        """
        node_data = comp_data.NodeData(
            comp_data.AttrData(name="output", type="compound", publish=True),
        )
        if type(self).has_hier_attrs:
            node_data.extend_attr_data(comp_data.HierData.get_output_xform_data())
        
        return node_data
    def _get_container_node_attr_data(self) -> comp_data.NodeData:
        """Defines all the added, published, or modified attributes for the container node

        Returns:
            comp_data.NodeData:
        """
        return comp_data.NodeData(
            comp_data.AttrData(name="built", type="bool", locked=True),
            comp_data.AttrData(name="controlSetups", type="message"),
            comp_data.AttrData(name="parentComponent", type="message"),
            comp_data.AttrData(name="childComponents", type="message", multi=True),
        )

    # creating nodes
    def create_component(self, **initial_attr_kwargs):
        """Creates component. initializes and builds component"""

        if self.container_node is None:
            self.initialize_component(**initial_attr_kwargs)
            self.build_component()
    def initialize_component(self, **initial_attr_kwargs):
        """Initializes component. sets everything up before the full build occurs.
        Used as a step to initialize so values can be modified before building"""

        if self.container_node is None:
            self.__create_base_nodes()
            initial_attr_kwargs = utils.unnest_dict(initial_attr_kwargs)
            
            attr_kwargs = initial_attr_kwargs

            # add non control setup data to container attributes
            control_setup_kwargs = nw.kwargs_set_attrs(self.container_node, ignore_data_types=[comp_data.ControlSetupData], **attr_kwargs)

            for key in list(control_setup_kwargs.keys()):
                if not isinstance(control_setup_kwargs[key], comp_data.ControlSetupData):
                    control_setup_kwargs.pop(key)
                    cmds.warning(f"{self.container_node}.{key} attr does not exist")       
            

            # Sort to have multiple promoted attributes together
            setup_control_filtered = {}
            for key in control_setup_kwargs:
                instance_name = ""
                kwargs = utils.unnest_dict(control_setup_kwargs[key].control_setup_dict)
                attrs = control_setup_kwargs[key].attrs

                if "instance_name" in kwargs:
                    instance_name = kwargs.pop("instance_name")
                elif "instanceName" in kwargs:
                    instance_name = kwargs.pop("instanceName")

                if instance_name == "":
                    instance_name = f"{key}_attr"

                kwargs["instance_name"] = utils.make_valid_maya_name(instance_name)

                if instance_name not in setup_control_filtered.keys():
                    setup_control_filtered[key] = comp_data.ControlSetupData(key, *attrs, **kwargs)
                else:
                    setup_control_filtered[key].add_attr(key)

            # promote to controls
            for key in setup_control_filtered:
                extra_kwargs = self.promote_attrs_to_cntrl_setup(setup_control_filtered[key])
                attr = self.container_node[key]
                extra_kwargs = nw.kwargs_set_attrs(attr, **extra_kwargs)
                for key in extra_kwargs:
                    cmds.warning(f"{attr}.{key} attr does not exist")

            #connecting parent and child components
            parent_container = self.container_node.get_container_node()
            if parent_container is not None:
                if parent_container.has_attr("childComponents"):
                    child_component_len = len(parent_container["childComponents"])
                    parent_container["childComponents"][child_component_len] >> self.container_node["parentComponent"]

            
            # renaming to nodes
            self.rename_nodes()
    def build_component(self):
        """Builds component after it has been initialized"""
        if type(self).has_hier_attrs:
            self.xform_output_function()
        self.container_node["built"] = True
        # renaming to nodes
        self.build_controls()
        self.rename_nodes()

    def __create_base_nodes(self):
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
        if self.parent_container_node is not None:
            self.parent_container_node.add_nodes(self.container_node)

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

    def xform_output_function(self):
        """Overriden function to connect up all output xforms
        """
        for index, attr in enumerate(self.input_node[comp_data.HierData.INPUT_XFORM]):
            attr[comp_data.HierData.INPUT_XFORM_NAME] >> self.output_node[comp_data.HierData.OUTPUT_XFORM][index][comp_data.HierData.OUTPUT_XFORM_NAME]
            attr[comp_data.HierData.INPUT_INIT_MATRIX] >> self.output_node[comp_data.HierData.OUTPUT_XFORM][index][comp_data.HierData.OUTPUT_INIT_MATRIX]
    
    # other functions
    def insert_component(self, component, transform_parent = None, **component_kwargs):
        """inserts a component into this component. uses may include adding controls
        and adding subcomponents

        Args:
            component (type):
            parent_transform (nw.Node, optional): Defaults to None.

        Returns:
            _type_: _description_
        """
        component_inst = component(parent_container_node=self.container_node)
        component_inst.create_component(**component_kwargs)

        if transform_parent is None and self.transform_node is not None:
            transform_parent = self.transform_node

        if component_inst.transform_node is not None and transform_parent is not None:
            cmds.parent(str(component_inst.transform_node), str(transform_parent), relative=True)

        return component_inst
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
            if node.type != "container":
                rename_node(node, full_namespace)

        # check if nothing else in namespace delete
        if utils.Namespace.empty(prev_namespace):
            utils.Namespace.delete(prev_namespace)

    def promote_attrs_to_cntrl_setup(self, setup_control_data:comp_data.ControlSetupData):
        """Connects up an attribute to setup control data so it can be promoted
        to an attribute on the control later

        Args:
            setup_control_data (comp_data.ControlSetupData):
        """
        def promote_check_attrs(*attrs):
            checked_attrs = []
            for attr_data in attrs:
                attr = None
                name = None
                # if it contains both the attribute and name
                if isinstance(attr_data, tuple):
                    attr = attr_data[0]
                    name = str(attr_data[1])
                # if attr is just by itself
                elif isinstance(attr_data, nw.Attr) or isinstance(attr_data, str):
                    attr = attr_data
                else:
                    cmds.warning(f"{attr} not of type {nw.Attr} or str")
                    continue
                # convert string to attr
                if isinstance(attr, str):
                    attr = nw._modify_kwargs_key(attr)
                    if self.container_node.has_attr(attr):
                        attr = self.container_node[attr]
                    else:
                        cmds.warning(f"{attr} attribute not found in {self.container_node}")
                        continue

                if name is None:
                    name = attr.short_name
                    name = utils.make_valid_maya_name(name)

                checked_attrs.append((attr, name))
            
            # checking for duplicates
            checked_dict = {}
            for attr, name in checked_attrs:
                gen_name = attr.attr_short_name.replace("[", "").replace("]", "").replace(".", "")
                if str(attr) not in checked_dict:
                    checked_dict[str(attr)] = [attr, name]
                else:
                    if checked_dict[str(attr)][1] == gen_name and name != gen_name:
                        checked_dict[str(attr)][1] = name

            connection_checked_list =[]
            for attr_key in checked_dict.keys():
                attr = checked_dict[attr_key][0]
                if attr.has_source_connection():
                    cmds.warning(f"{attr} has an incoming connection ... skipping promoting to control")
                else:
                    connection_checked_list.append(checked_dict[attr_key])

            return connection_checked_list

        attrs = promote_check_attrs(*setup_control_data.attrs)
        
        # using instance name
        instance_name = "controlSetup"
        if "instance_name" in setup_control_data.control_setup_dict:
            instance_name = setup_control_data.control_setup_dict["instance_name"]
            instance_name = f"{instance_name}_ControlSetup"
        elif "instanceName" in setup_control_data.control_setup_dict:
            instance_name = setup_control_data.control_setup_dict["instanceName"]
            instance_name = f"{instance_name}_ControlSetup"
        instance_name = utils.make_valid_maya_name(instance_name)
        control_kwargs = setup_control_data.control_setup_dict
        control_setup = create_control_setup_node(utils.make_valid_maya_name(instance_name))
        self.container_node.add_nodes(control_setup)

        #TODO
        # xform attrs

        # adding additional info to control_kwargs
        attr_info_curr_index = len(control_setup["attrInfo"])
        for attr, name in attrs:
            control_kwargs[control_setup["attrInfo"][attr_info_curr_index]["attrMessage"].attr_name] = attr
            control_kwargs[control_setup["attrInfo"][attr_info_curr_index]["attrName"].attr_name] = name

            attr_info_curr_index = attr_info_curr_index + 1

        control_kwargs[control_setup["containerNode"].attr_name] = self.container_node["controlSetups"]

        extra_kwargs = nw.kwargs_set_attrs(control_setup, **control_kwargs)

        # if already built 
        if self.container_node["built"].value:
            pass

        return extra_kwargs

    def build_controls(self, control_setup_node:nw.Node = None):
        """Given a control setup, builds a control according to it's specifications.
        used in the build step

        Args:
            control_setup_node (nw.Node, optional): Defaults to None. if None 
            finds all control setups in the component
            attr_indexs (list, optional): Defaults to [].
        """
        import component.control as control

        if control_setup_node is None:
            control_setup_node = [x.node for x in self.container_node["controlSetups"].get_dest_connections()]
            
        else:
            control_setup_node = [control_setup_node]

        class_dict = utils.get_classes_from_package(control)[1]

        for control_setup in control_setup_node:
            control_class = class_dict[control_setup["controlClass"].value]            
            
            control_inst = control_class(parent_container_node=self.container_node)
            control_inst.create_component(control_setup_node = control_setup)

            for promote_attr in control_setup["attrInfo"]:
                name = promote_attr["attrName"].value
                attr = promote_attr["attrMessage"].get_src_connections()[0]
                
                if comp_data.HierData.is_input_xform_attr(attr):
                    name = attr[comp_data.HierData.INPUT_XFORM_NAME].value
                    if name is not None:
                        # control_setup_node["instanceName"] = name
                        control_inst.container_node["instanceName"] = name
                        control_inst.rename_nodes()

                    attr[comp_data.HierData.INPUT_WORLD_MATRIX] >> control_inst.container_node["offsetMatrix"]
                    ~control_inst.container_node["offsetMatrix"]

                    control_inst.container_node["worldMatrix"] >> attr[comp_data.HierData.INPUT_WORLD_MATRIX]
                    control_inst.container_node["localMatrix"] >> attr[comp_data.HierData.INPUT_LOC_MATRIX]

                elif comp_data.HierData.is_hier_attr(attr):
                    name = attr[comp_data.HierData.HIER_NAME].value
                    if name is not None:
                        # control_setup_node["instanceName"] = name
                        control_inst.container_node["instanceName"] = name
                        control_inst.rename_nodes()
                    attr[comp_data.HierData.HIER_PARENT_MATRIX] >> control_inst.container_node["offsetMatrix"]
                    ~control_inst.container_node["offsetMatrix"]

                    control_inst.container_node["worldMatrix"] >> attr[comp_data.HierData.HIER_PARENT_MATRIX]

                elif attr.attr_type == "matrix":
                    attr >> control_inst.container_node["offsetMatrix"]
                    ~control_inst.container_node["offsetMatrix"]

                    control_inst.container_node["worldMatrix"] >> attr

                else:
                    control_inst.promote_attr_to_keyable(attr, name=name)


        # TODO
        # xforms
        # create control
        # connect it up
        # re publish if needs be

class Control(Component):
    """A Base class for all control autorigging components. Derived from Component

    Attributes:
        can_set_color (bool): can set color of component
    """
    component_type = component_enum.ComponentTypes.component
    root_transform_name = "control"
    class_namespace = "cntrl"
    has_hier_attrs = False
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
    def _get_input_node_attr_data(self) -> comp_data.NodeData:
        node_data = super()._get_input_node_attr_data()

        node_data.extend_attr_data(
            comp_data.AttrData(name="offsetParentMatrix", publish="offsetMatrix"),
            comp_data.AttrData(name="worldMatrix[0]", publish="worldMatrix"),
            comp_data.AttrData(name="matrix", publish="localMatrix"),
            comp_data.AttrData(name="worldInverseMatrix[0]", publish="worldInverseMatrix"),

            comp_data.AttrData(name="overrideEnabled", publish="hasColor", locked=not type(self).can_set_color),
            comp_data.AttrData(name="overrideColorRGB", publish="color", locked=not type(self).can_set_color),
            comp_data.AttrData(name="overrideRGBColors", value=1),
        )

        return node_data
    def _get_container_node_attr_data(self):
        node_data =  super()._get_container_node_attr_data()
    
        node_data.extend_attr_data(
            comp_data.AttrData(name="controlSetupNode", type="message"),
        )

        return node_data
    def create_component(self, control_setup_node:nw.Node = None, **initial_attr_kwargs):
        initial_attr_kwargs["control_setup_node"] = control_setup_node
        return super().create_component(**initial_attr_kwargs)
    def initialize_component(self, control_setup_node:nw.Node = None, **initial_attr_kwargs):
        if control_setup_node is not None:
            if control_setup_node.has_attr("instanceName"):
                initial_attr_kwargs["instanceName"] = control_setup_node["instanceName"].value

        super().initialize_component(**initial_attr_kwargs)

        if control_setup_node is not None and control_setup_node.has_attr("controlComponent"):
            self.container_node["controlSetupNode"] >> control_setup_node["controlComponent"]
    def build_component(self):
        shape_transforms = self._create_shapes()
        self._apply_shape_to_cntrl(shape_transforms)

        # apply control setup node info
        if self.control_setup_node is not None:
            # set build TRS
            translate = self.control_setup_node["buildTranslate"]
            rotate = self.control_setup_node["buildRotate"]
            scale = self.control_setup_node["buildScale"]

            self.transform_node["translate"] = translate
            self.transform_node["rotate"] = rotate
            self.transform_node["scale"] = scale

            utils.freeze_transform(self.transform_node)

            # set color
            if self.control_setup_node["shapeColor"].value != 0:
                if self.container_node["hasColor"].is_locked():
                    cmds.warning(f"color cannot be applied to {self.container_node} control")
                else:
                    self.container_node["hasColor"] = 1
                    shape_color_enum = self.control_setup_node["shapeColor"].value
                    rgb = utils.get_rgb_from_index(component_enum.Colors.get(shape_color_enum).value)
                    self.container_node["color"] = rgb
            
            # set lock attrs
            attribute_locked = {
                "tx":self.control_setup_node["lockTX"].value,
                "ty":self.control_setup_node["lockTY"].value,
                "tz":self.control_setup_node["lockTZ"].value,
                "rx":self.control_setup_node["lockRX"].value,
                "ry":self.control_setup_node["lockRY"].value,
                "rz":self.control_setup_node["lockRZ"].value,
                "sx":self.control_setup_node["lockSX"].value,
                "sy":self.control_setup_node["lockSY"].value,
                "sz":self.control_setup_node["lockSZ"].value,
                "visibility":self.control_setup_node["lockVis"].value,
            }
            for key in attribute_locked:
                value = attribute_locked[key]
                if value:
                    self.transform_node[key].set_locked(True)
                    self.transform_node[key].set_keyable(False)

        # promote anything on control setup 
        return super().build_component()
    
    # control specific functions
    def _create_shapes(self) -> list:
        """Creates shapes and returns a list of the shapes transforms. these 
        shapes will be parented to the transform node later

        Returns:
            list(nw.Node):
        """
        
    def _apply_shape_to_cntrl(self, shapes_transforms:list):
        """applys transform shapes to control

        Args:
            shapes_transforms (list):
        """
        for transform in shapes_transforms:
            if not isinstance(transform, nw.Node):
                transform = nw.Node(transform)

            # delete history
            cmds.delete(str(transform), constructionHistory=True)

            # freeze all controls
            utils.freeze_transform(transform)

            # apply to transform
            for x in cmds.listRelatives(str(transform), shapes=True):
                cmds.parent(x, str(self.transform_node), relative=True, shape=True)
        
        cmds.delete(shapes_transforms)

        shapes_list = [nw.Node(x) for x in cmds.listRelatives(str(self.transform_node), shapes=True)]

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
            attr_type = attr.type
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
                    transform_node.add_attr(child_name, parent=name, type=child_attr.type, **kwargs, **child_kwargs)
            
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
            if attr.has_source_connection():
                ~attr
            transform_node[name] >> attr
