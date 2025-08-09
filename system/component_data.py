import utils.node_wrapper as nw
import system.component_enum_data as component_enum_data

class NodeData():
    """Class to encapsulate node data to add attributes, publish attributes etc

    Attributes:
        node_attr_list (list): node attribute list
    """

    def __init__(self, *args):
        """takes args and add them to node_attr_list

        Args:
            args (): list to add to node_attr_list
        """
        self.node_attr_list = []

        self.extend_attr_data(*args)

    def extend_attr_data(self, *args):
        """Takes args and adds them to node_attr_list checking for AttrData
        
        Args:
            args (): list to add to node_attr_list
        """
        if len(args) > 0 and isinstance(args[0], NodeData):
            args = args[0].node_attr_list
        else:
            args = [data for data in args if isinstance(data, AttrData)]
        self.node_attr_list.extend(args)

    def add_attrs_to_node(self, node:nw.Node):
        """Takes node_attr_list AttrData and processes data to add, set value, 
        and locked

        Args:
            node (nw.Node): node that the data will affect
        """
        # adding attrs
        num_children_dict = self.__get_num_children_dict()

        for data in self.node_attr_list:
            if data.do_add_attr:

                if data.name in num_children_dict.keys():
                    data.add_attr_kwargs["numberOfChildren"] = num_children_dict[data.name]

                if data.type_ == "compound" and not data.name in num_children_dict.keys():
                    continue

                node.add_attr(long_name=data.name, type=data.type_, **data.add_attr_kwargs)

        # setting attrs and locking
        for data in self.node_attr_list:
            # dealing with attr value
            if data.value is not None:
                if isinstance(data.value, nw.Attr):
                    data.value >> node[data.name]
                else:
                    node[data.name] = data.value

            # locking
            if data.locked:
                node[data.name].set_locked(True)

    def publish_attr_data_attributes(self, node:nw.Node):
        """Takes node_attr_list AttrData and publishes attributes to it's parent
        container

        Args:
            node (nw.Node): node that the data will affect
        """
        container_node = node.get_container_node()

        if container_node is None:
            return
        for data in self.node_attr_list:
            if data.publish != False:
                if node.has_attr(data.name):
                    if isinstance(data.publish, str):
                        container_node.publish_attr(node[data.name], data.publish)
                    else:
                        container_node.publish_attr(node[data.name], data.name)

    def __get_num_children_dict(self):
        """Takes the attribute data and adds up how many children each attribute
        has (the child will have a parent:"{parent}" entry that is checked). used
        to set the numberOfChildren field when adding the attribute

        Returns:
            dict:
        """
        num_children_dict = {}
        for data in self.node_attr_list:
            attr_kwargs = data.add_attr_kwargs
            if "parent" in attr_kwargs.keys():
                parent_name = attr_kwargs["parent"]
                if parent_name not in num_children_dict.keys():
                    num_children_dict[parent_name] = 1
                else:
                    num_children_dict[parent_name] = num_children_dict[parent_name] + 1

        return num_children_dict

    def __str__(self):
        """Returns string list of all data in list

        Returns:
            str:
        """
        return "\n".join([str(x) for x in self.node_attr_list])
    
    def __iter__(self):
        """Iterates through AttrData

        Yields:
            AttrData:
        """
        for x in self.node_attr_list:
            yield x

class AttrData:
    """Class to define attributes

    Attributes:
        name (str): attribute name
        type (str): attribute type
        publish (bool, str): publish to container. if string publishes with new name
        value (Any): value of the attribute
        locked (bool): lock attribute
        keyable (bool): keyable attribute
        alias (str): new attribute alias
        add_attr_kwargs (): kwarg of all addAttr fields
        do_add_attr(bool): variable to see if attr should be added
    """
    def __init__(self, name:str, type_:str=None, value=None, publish=False, locked:bool=False, keyable:bool=False, alias:str=None, **add_attr_kwargs):
        """Initializes AttrData

        Args:
            name (str): attribute name
            type (str, optional):  Defaults to None.
            value (Any, optional): Defaults to None.
            publish (bool, optional): Defaults to False.
            locked (bool, optional): Defaults to False.
            keyable (bool, optional): Defaults to False.
            alias (str, optional): Defaults to None.
        """
        self.name = name
        self.type_ = type_
        self.publish = publish
        self.value = value
        self.locked = locked
        self.keyable = keyable
        self.alias = alias
        self.do_add_attr = self.type_ is not None

        self.add_attr_kwargs = add_attr_kwargs
        
        if not isinstance(self.type_, str) and self.type_ is not None:
            enum_class = component_enum_data.get_enum_item_class(self.type_)
            if enum_class is not None:
                enum_data = self.type_
                self.type_ = "enum"
                


                self.add_attr_kwargs["enumName"] = enum_class.maya_enum_str()

                index = component_enum_data.get_index_of_item(enum_data)
                if index is not None:
                    self.value = index
            
    def __str__(self):
        """Str of all the data and their values

        Returns:
            str:
        """
        return f"name-\"{self.name}\" | type-{self.type_} | publish-{self.publish} | value-{self.value} | locked-{self.locked} | keyable-{self.keyable} | alias-{self.alias} | attr_kwargs-{self.add_attr_kwargs}"

class HierData:
    """Class with constants and checks for Hierarchy in Autorigger
    
    Attributes:
        HIERARCHY (str):
        HIER_NAME (str):
        HIER_PARENT_MATRIX (str):
        HIER_PARENT_INIT_MATRIX (str):
        INPUT_XFORM (str):
        INPUT_XFORM_NAME (str):
        INPUT_INIT_MATRIX (str):
        INPUT_INIT_INV_MATRIX (str):
        INPUT_WORLD_MATRIX (str):
        INPUT_LOC_MATRIX (str):
        OUTPUT_XFORM (str):
        OUTPUT_XFORM_NAME (str):
        OUTPUT_INIT_MATRIX (str):
        OUTPUT_INIT_INV_MATRIX (str):
        OUTPUT_WORLD_MATRIX (str):
        OUTPUT_LOC_MATRIX (str):
        __HIER_DATA_NAMES (list(str)):
        __INPUT_DATA_NAMES (list(str))
        __OUTPUT_DATA_NAMES (list(str))
        """

    HIERARCHY = "hierarchy"
    HIER_PARENT_MATRIX = "hierParentMatrix"
    HIER_PARENT_INIT_MATRIX = "hierParentInitMatrix"

    INPUT_XFORM = "inputXform"
    INPUT_XFORM_NAME = "inputXformName" 
    INPUT_INIT_MATRIX = "inputInitMatrix"
    INPUT_INIT_INV_MATRIX = "inputInitInvMatrix"
    INPUT_WORLD_MATRIX = "inputWorldMatrix"
    INPUT_LOC_MATRIX = "inputLocMatrix"

    OUTPUT_XFORM = "outputXform"
    OUTPUT_XFORM_NAME = "outputXformName"
    OUTPUT_INIT_MATRIX = "outputInitMatrix"
    OUTPUT_INIT_INV_MATRIX = "outputInitInvMatrix"
    OUTPUT_WORLD_MATRIX = "outputWorldMatrix"
    OUTPUT_LOC_MATRIX = "outputLocMatrix"

    HIER_DATA_NAMES = [
        HIER_PARENT_MATRIX,
        HIER_PARENT_INIT_MATRIX
    ]
    INPUT_DATA_NAMES = [
        INPUT_XFORM_NAME,
        INPUT_INIT_MATRIX,
        INPUT_INIT_INV_MATRIX,
        INPUT_WORLD_MATRIX,
        INPUT_LOC_MATRIX
    ]
    OUTPUT_DATA_NAMES = [
        OUTPUT_XFORM_NAME,
        OUTPUT_INIT_MATRIX,
        OUTPUT_INIT_INV_MATRIX,
        OUTPUT_WORLD_MATRIX,
        OUTPUT_LOC_MATRIX
    ]

    @classmethod
    def is_hier_attr(cls, attr:nw.Attr):
        """Checks if attribute is a hier attribute

        Args:
            attr (nw.Attr):

        Returns:
            bool:
        """
        hier_names = cls.HIER_DATA_NAMES()
        for attr_name in hier_names:
            if not attr.has_attr(attr_name):
                return False

        attr = attr[cls.INPUT_XFORM][0]

        if not cls.is_input_xform_attr(attr[cls.INPUT_XFORM][0]):
            return False
        return True
    @classmethod
    def is_input_xform_attr(cls, attr:nw.Attr):
        """Checks to see if attribute is an input xform attribute

        Args:
            attr (nw.Attr):

        Returns:
            bool:
        """
        xform_names = cls.INPUT_DATA_NAMES()
        for attr_name in xform_names:
            if not attr.has_attr(attr_name):
                return False

        return True
    @classmethod
    def is_output_xform_attr(cls, attr:nw.Attr):
        """Checks to see if attribute is an output xform attribute

        Args:
            attr (nw.Attr):

        Returns:
            bool:
        """
        xform_names = cls.OUTPUT_DATA_NAMES()
        for attr_name in xform_names:
            if not attr.has_attr(attr_name):
                return False

        return True
    
    @classmethod
    def __gen_hier_nodeData(cls, parent_name:str, attr_names, multi=True):
        """Given a parent name and attribute names generates the Node Data to build
        it. only sets attributes to string or matrix. (string if "Name" is in the 
        name)

        Args:
            parent_name (str):
            attr_names (list(str)):

        Returns:
            component_data.NodeData:
        """
        attr_data = [AttrData(parent_name, type_="compound", publish=True, multi=multi)]
        for attr_name in attr_names:
            attr_type = "matrix"
            if attr_name.find("Name") >= 0:
                attr_type ="string"
            attr_data.append(AttrData(attr_name, type_=attr_type, parent=parent_name))

        return NodeData(*attr_data)
    
    @classmethod
    def get_hier_data(cls):
        """Returns NodeData for hier

        Returns:
            NodeData:
        """
        return cls.__gen_hier_nodeData(cls.HIERARCHY, cls.HIER_DATA_NAMES, multi=False)

    @classmethod
    def get_input_xform_data(cls):
        """Returns NodeData for an input xform

        Returns:
            NodeData:
        """
        return cls.__gen_hier_nodeData(cls.INPUT_XFORM, cls.INPUT_DATA_NAMES, multi=True)
    
    @classmethod
    def get_output_xform_data(cls):
        """Returns NodeData for an output xform

        Returns:
            NodeData:
        """
        return cls.__gen_hier_nodeData(cls.OUTPUT_XFORM, cls.OUTPUT_DATA_NAMES, multi=True)
        
class ControlSetupData():
    """A class that takes Control data and saves it to be inputed into a control
    setup node

    Attributes:
        attrs (list): attributes to be promoted on this control and the override names accompanying them
        control_setup (dict): dict to apply to control setup node later
    """

    def __init__(self, *attrs, control_class = None, **control_setup):
        """_summary_

        Args:
            attrs (list(set)): [("attr_name", "control_attr_name")]
            control_class (type, optional): _description_. Defaults to None.
            control_setup (dict): control setup kwargs to apply data to later
        """
        import component.control as control
        self.control_setup_dict = control_setup
        if "controlClass" not in control_setup.keys():
            if control_class is None:
                control_setup["controlClass"] = control.Circle
            else:
                control_setup["controlClass"] = control_class
        self.attrs = list(attrs)

    def add_attr(self, *attrs):
        """Adds attrs to the attrs list

        Args:
            attrs (): attrs to add

        """
        self.attrs.extend(attrs)