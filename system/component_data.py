import utils.node_wrapper as nw

class NodeData(list):
    def __init__(self, node:nw.Node, *args):
        self.node_add_attr_list = []
        self.node = node

        self.add_attr_data(*args)

    def add_attr_data(self, *args):
        args = [data for data in args if isinstance(data, AddAttrData)]
        self.node_add_attr_list.extend(args)

    def add_node_attrs(self):
        for data in self.node_add_attr_list:
            
            self.node.add_attr(long_name=data.name, type=data.attr_type, **data.add_attr_kwargs)

            # dealing with attr value
            if data.value is not None:
                if isinstance(data.value, nw.Attr):
                    data.value >> self.node[data.name]
                else:
                    self.node[data.name] = data.value

            # locking
            if data.locked:
                self.node[data.name].set_locked(True)

class AddAttrData:
    def __init__(self, attr_name, attr_type, attr_value=None, attr_publish=False, attr_locked=False, attr_keyable=False, attr_alias=None, **add_attr_kwargs):
        for key in add_attr_kwargs:
            print(f"{key}:{add_attr_kwargs[key]}")
        self.name = attr_name
        self.attr_type = attr_type
        self.publish = attr_publish
        self.value = attr_value
        self.locked = attr_locked
        self.keyable = attr_keyable
        self.alias = attr_alias

        self.add_attr_kwargs = add_attr_kwargs



    