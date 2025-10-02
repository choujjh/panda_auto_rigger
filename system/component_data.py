import utils.node_wrapper as nw
import system.component_enum_data as component_enum_data
from typing import Union
import utils.utils as utils

class NodeData():
    """Class to encapsulate node data to add attributes, publish attributes etc

    Attributes:
        node_attr_dict (list): node attribute list
    """

    def __init__(self, *args):
        """takes args and add them to node_attr_list

        Args:
            args (): list to add to node_attr_dict
        """
        self.node_attr_dict = {}

        self.extend_attr_data(*args)

    def extend_attr_data(self, *args):
        """Takes args and adds them to node_attr_dict checking for AttrData
        
        Args:
            args (): list to add to node_attr_dict
        """
        if len(args) > 0 and isinstance(args[0], NodeData):
            args_dict = {key: data for key, data in args[0].node_attr_dict.items()}
        else:
            
            args_dict = {data.name:data for data in args if isinstance(data, AttrData)}
        self.node_attr_dict.update(args_dict)

    def add_attrs_to_node(self, node:nw.Node):
        """Takes node_attr_list AttrData and processes data to add, set value, 
        and locked

        Args:
            node (nw.Node): node that the data will affect
        """
        # adding attrs
        num_children_dict = self.__get_num_children_dict()

        data_list = []
        for data in self.node_attr_dict.values():
            data_added = False
            for index, saved_data in enumerate(data_list):
                if "parent" in saved_data.add_attr_kwargs.keys() and saved_data.add_attr_kwargs["parent"] == data.name:
                    data_list.insert(index, data)
                    data_added = True
                    break
            if not data_added:
                data_list.append(data)

        for data in data_list:
            if data.do_add_attr:

                if data.name in num_children_dict.keys():
                    data.add_attr_kwargs["numberOfChildren"] = num_children_dict[data.name]

                if data.type_ == "compound" and not data.name in num_children_dict.keys():
                    continue

                node.add_attr(long_name=data.name, type=data.type_, **data.add_attr_kwargs)

        # setting attrs and locking
        for data in data_list:
            # dealing with attr value
            if data.value is not None:
                if isinstance(data.value, nw.Attr):
                    data.value >> node[data.name]
                else:
                    node[data.name] = data.value

        for data in data_list:
            # locking
            if data.locked:
                node[data.name].set_locked(True)

    def remove(self, *keys:str):
        """Given keys removes attrData

        Args:
            keys (list(str)):

        Raises:
            KeyError: if key not found
        """
        for key in keys:
            if key not in self.node_attr_dict.keys():
                raise KeyError(f"{key} not in node_attr_dict")
            self.node_attr_dict.pop(key)

    def modify_add_attr_kwargs(self, key:str, **add_attr_kwargs):
        """given a key modifies the add_attr_kwargs

        Args:
            key (str):
            add_attr_kwargs (dict)

        Raises:
            KeyError: if key not found
        """
        if key not in self.node_attr_dict.keys():
            raise KeyError(f"{key} not in node_attr_dict")
        self.node_attr_dict[key].add_attr_kwargs.update(add_attr_kwargs)

    def publish_attr_data_attributes(self, node:nw.Node):
        """Takes node_attr_list AttrData and publishes attributes to it's parent
        container

        Args:
            node (nw.Node): node that the data will affect
        """
        container_node = node.get_container_node()

        if container_node is None:
            return
        for data in self.node_attr_dict.values():
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
        for data in self.node_attr_dict.values():
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
        return "\n".join([str(x) for x in self.node_attr_dict.values()])
    
    def __iter__(self):
        """Iterates through AttrData

        Yields:
            AttrData:
        """
        for x in self.node_attr_dict:
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
        INPUT_WORLD_INV_MATRIX (str)
        INPUT_LOC_MATRIX (str):
        OUTPUT_XFORM (str):
        OUTPUT_XFORM_NAME (str):
        OUTPUT_INIT_MATRIX (str):
        OUTPUT_INIT_INV_MATRIX (str):
        OUTPUT_WORLD_MATRIX (str):
        OUTPUT_WORLD_INV_MATRIX (str):
        OUTPUT_LOC_MATRIX (str):
        HIER_DATA_NAMES (list(str)):
        INPUT_DATA_NAMES (list(str)):
        OUTPUT_DATA_NAMES (list(str)):
        """

    HIER_PARENT = "hierParent"
    HIER_PARENT_MATRIX = "hierParentMatrix" 
    HIER_PARENT_INV_MATRIX = "hierParentInvMatrix" 
    HIER_PARENT_INIT_INV_MATRIX = "hierParentInitInvMatrix"

    INPUT_XFORM = "inputXform"
    INPUT_XFORM_NAME = "inputXformName" 
    INPUT_INIT_MATRIX = "inputInitMatrix"
    INPUT_INIT_INV_MATRIX = "inputInitInvMatrix"
    INPUT_WORLD_MATRIX = "inputWorldMatrix"
    INPUT_WORLD_INV_MATRIX = "inputWorldInvMatrix"
    INPUT_LOC_MATRIX = "inputLocMatrix"

    OUTPUT_XFORM = "outputXform"
    OUTPUT_XFORM_NAME = "outputXformName"
    OUTPUT_INIT_MATRIX = "outputInitMatrix"
    OUTPUT_INIT_INV_MATRIX = "outputInitInvMatrix"
    OUTPUT_WORLD_MATRIX = "outputWorldMatrix"
    OUTPUT_WORLD_INV_MATRIX = "outputWorldInvMatrix"
    OUTPUT_LOC_MATRIX = "outputLocMatrix"

    HIER_PARENT_DATA_NAMES = [
        HIER_PARENT_MATRIX,
        HIER_PARENT_INV_MATRIX,
        HIER_PARENT_INIT_INV_MATRIX
    ]
    INPUT_DATA_NAMES = [
        INPUT_XFORM_NAME,
        INPUT_INIT_MATRIX,
        INPUT_INIT_INV_MATRIX,
        INPUT_WORLD_MATRIX,
        INPUT_WORLD_INV_MATRIX,
        INPUT_LOC_MATRIX
    ]
    OUTPUT_DATA_NAMES = [
        OUTPUT_XFORM_NAME,
        OUTPUT_INIT_MATRIX,
        OUTPUT_INIT_INV_MATRIX,
        OUTPUT_WORLD_MATRIX,
        OUTPUT_WORLD_INV_MATRIX,
        OUTPUT_LOC_MATRIX
    ]

    @classmethod
    def get_paired_names(cls, src:component_enum_data.IO, dest:component_enum_data.IO):
        """gives name pairs for hier names. src and dest are either input or output. has input init matricies removes Init matricies
        names

        Args:
            src (component_enum_data.IO): 
            dest (component_enum_data.IO): 
            has_input_init_matricies (bool, optional): Defaults to False.

        Returns:
            list(tuples(str)): 
        """
        input_names = cls.INPUT_DATA_NAMES
        output_names = cls.OUTPUT_DATA_NAMES
        src_names = input_names if cls.is_input_enum(src) else output_names
        dest_names = input_names if cls.is_input_enum(dest) else output_names
        return [(src_name, dest_name) for src_name, dest_name in zip(src_names, dest_names)]
    
    @classmethod
    def is_input_enum(cls, enum:component_enum_data.IO):
        """checks to see if it's input io

        Args:
            enum (component_enum_data.IO):

        Returns:
            bool:
        """
        if enum.value == component_enum_data.IO.input.value and enum.name == component_enum_data.IO.input.name:
            return True
        return False
    @classmethod
    def get_xform_names(cls, xform_type:component_enum_data.IO):
        if cls.is_input_enum(xform_type):
            return cls.INPUT_DATA_NAMES
        else:
            return cls.OUTPUT_DATA_NAMES
    @classmethod
    def get_xform_parent_name(cls, xform_type:component_enum_data.IO):
        if cls.is_input_enum(xform_type):
            return cls.INPUT_XFORM
        else:
            return cls.OUTPUT_XFORM

    @classmethod
    def is_hier_parent_attr(cls, attr:nw.Attr):
        """Checks if attribute is a hier attribute

        Args:
            attr (nw.Attr):

        Returns:
            bool:
        """
        hier_names = cls.HIER_PARENT_DATA_NAMES
        for attr_name in hier_names:
            if not attr.has_attr(attr_name):
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
        xform_names = cls.INPUT_DATA_NAMES
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
        xform_names = cls.OUTPUT_DATA_NAMES
        for attr_name in xform_names:
            if not attr.has_attr(attr_name):
                return False

        return True
    @classmethod
    def __gen_hier_node_data(cls, parent_name:str, attr_names, multi=True):
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
    def get_hier_parent_data(cls):
        """Returns NodeData for hier

        Returns:
            NodeData:
        """
        return cls.__gen_hier_node_data(cls.HIER_PARENT, cls.HIER_PARENT_DATA_NAMES, multi=False)
    @classmethod
    def get_input_xform_data(cls):
        """Returns NodeData for an input xform

        Args:
            input_matricies: has input matricies

        Returns:
            NodeData:
        """
        return cls.__gen_hier_node_data(cls.INPUT_XFORM, cls.INPUT_DATA_NAMES, multi=True)
    @classmethod
    def get_output_xform_data(cls):
        """Returns NodeData for an output xform

        Returns:
            NodeData:
        """
        return cls.__gen_hier_node_data(cls.OUTPUT_XFORM, cls.OUTPUT_DATA_NAMES, multi=True)

def xform_to_hier_parent(xform:"Xform"):
        """converts xform to hier_parent

        Args:
            xform (component_data.Xform): _description_

        Returns:
            _type_: _description_
        """
        return HierParent(matrix=xform.world_matrix, inv_matrix=xform.world_inv_matrix, init_inv_matrix=xform.init_inv_matrix)

class HierParent():
    """Encapsulates HierParent attribute"""
    def __init__(self, 
                 hier_parent_attr:nw.Attr=None, 
                 matrix:Union[utils.Matrix, nw.Attr]=None, 
                 inv_matrix:Union[utils.Matrix, nw.Attr]=None, 
                 init_inv_matrix:Union[utils.Matrix, nw.Attr]=None):
        """initializes hier parent. uses hier_parent first. otherwise uses given attributes

        Args:
            hier_parent_attr (nw.Attr, optional): _description_. Defaults to None.
            parent_matrix (Union[utils.Matrix, nw.Attr], optional): _description_. Defaults to None.
            parent_inv_matrix (Union[utils.Matrix, nw.Attr], optional): _description_. Defaults to None.
            parent_init_inv_matrix (Union[utils.Matrix, nw.Attr], optional): _description_. Defaults to None.
        """
        if hier_parent_attr is not None:
            if not HierData.is_hier_parent_attr(hier_parent_attr):
                raise RuntimeError(f"{hier_parent_attr} is not hier parent attribute")
            self.matrix = hier_parent_attr[HierData.HIER_PARENT_MATRIX]
            self.inv_matrix = hier_parent_attr[HierData.HIER_PARENT_INV_MATRIX]
            self.init_inv_matrix = hier_parent_attr[HierData.HIER_PARENT_INIT_INV_MATRIX]
        else:
            self.matrix = matrix
            self.inv_matrix = inv_matrix
            self.init_inv_matrix = init_inv_matrix

            not_none_list = [x for x in self.attrs if x is not None]
            if len(not_none_list) == 0:
                raise RuntimeError(f"{self.__repr__()} not all fields can be None")


    @property
    def attrs(self):
        """list of all attributes

        Returns:
            list:
        """
        return [self.matrix, self.inv_matrix, self.init_inv_matrix]

    def __iter__(self):
        for attr in self.attrs:
            yield attr
class Xform():
    """Encapsulates Xform attribute"""
    def __init__(self, 
                    xform_attr:nw.Attr=None, 
                    xform_type:component_enum_data.IO=component_enum_data.IO.input,
                    xform_name:Union[str, nw.Attr]=None, 
                    init_matrix:Union[utils.Matrix, nw.Attr]=None, 
                    init_inv_matrix:Union[utils.Matrix, nw.Attr]=None, 
                    world_matrix:Union[utils.Matrix, nw.Attr]=None, 
                    world_inv_matrix:Union[utils.Matrix, nw.Attr]=None, 
                    loc_matrix:Union[utils.Matrix, nw.Attr]=None):
        """Initializes Xform. tries to populate from xform_attr first, otherwise uses given attributes

        Args:
            xform_attr (nw.Attr, optional): _description_. Defaults to None.
            xform_type (component_enum_data.IO, optional): _description_. Defaults to component_enum_data.IO.input.
            xform_name (Union[str, nw.Attr], optional): _description_. Defaults to None.
            init_matrix (Union[utils.Matrix, nw.Attr], optional): _description_. Defaults to None.
            init_inv_matrix (Union[utils.Matrix, nw.Attr], optional): _description_. Defaults to None.
            world_matrix (Union[utils.Matrix, nw.Attr], optional): _description_. Defaults to None.
            world_inv_matrix (Union[utils.Matrix, nw.Attr], optional): _description_. Defaults to None.
            loc_matrix (Union[utils.Matrix, nw.Attr], optional): _description_. Defaults to None.

        Raises:
            RuntimeError: xform_attr is not an xform attribute
            RuntimeError: if all fields are none
        """
        if xform_attr is not None:
            if HierData.is_input_xform_attr(xform_attr):
                self.xform_type = component_enum_data.IO.input
            elif HierData.is_output_xform_attr(xform_attr):
                self.xform_type = component_enum_data.IO.output
            else:
                raise RuntimeError(f"{xform_attr} is not an xform attribute")
            
            if HierData.is_input_enum(self.xform_type):
                self.xform_name = xform_attr[HierData.INPUT_XFORM_NAME]
                self.init_matrix = xform_attr[HierData.INPUT_INIT_MATRIX]
                self.init_inv_matrix = xform_attr[HierData.INPUT_INIT_INV_MATRIX]
                self.world_matrix = xform_attr[HierData.INPUT_WORLD_MATRIX]
                self.world_inv_matrix = xform_attr[HierData.INPUT_WORLD_INV_MATRIX]
                self.loc_matrix = xform_attr[HierData.INPUT_LOC_MATRIX]
            else:
                self.xform_name = xform_attr[HierData.OUTPUT_XFORM_NAME]
                self.init_matrix = xform_attr[HierData.OUTPUT_INIT_MATRIX]
                self.init_inv_matrix = xform_attr[HierData.OUTPUT_INIT_INV_MATRIX]
                self.world_matrix = xform_attr[HierData.OUTPUT_WORLD_MATRIX]
                self.world_inv_matrix = xform_attr[HierData.OUTPUT_WORLD_INV_MATRIX]
                self.loc_matrix = xform_attr[HierData.OUTPUT_LOC_MATRIX]

        else:
            self.xform_type = xform_type
            self.xform_name = xform_name
            self.init_matrix = init_matrix
            self.init_inv_matrix = init_inv_matrix
            self.world_matrix = world_matrix
            self.world_inv_matrix = world_inv_matrix
            self.loc_matrix = loc_matrix

            not_none_list = [x for x in self.attrs if x is not None]
            if len(not_none_list) == 0:
                raise RuntimeError(f"{self.__repr__()} not all fields can be None")
    @property
    def attrs(self):
        """list of all attributes

        Returns:
            list:
        """
        return [self.xform_name, self.init_matrix, self.init_inv_matrix, self.world_matrix, self.world_inv_matrix, self.loc_matrix]

    def __iter__(self):
        for attr in self.attrs:
            yield attr