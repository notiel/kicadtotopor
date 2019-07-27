from pyparsing import OneOrMore, nestedExpr, Dict
from typing import Dict, Any, List
import pprint

from pcb_structure import *

def list_to_dict(data: list) -> dict:
    """

    :param data:
    :return:
    """
    res = {}
    if not data or len(data) < 2:
        return res
    if len(data) == 2:
        res[data[0]] = data[1]
        if not isinstance(res[data[0]], list):
            try:
                res[data[0]] = float(res[data[0]])
            except ValueError:
                pass
    else:
        res[data[0]] = data[1:]
    current_data = res[data[0]]
    if isinstance(current_data, list):
        for word in current_data:
            if isinstance(word, list):
                i = current_data.index(word)
                current_data[i] = list_to_dict(word)

    return res


def get_dict_by_key(data: List[Dict[str, Any]], key: str) -> Dict[str, Any]:
    """
    find a dict in a list with selected key
    :param key: key to find
    :param data: list with dicts
    :return: dict with given key
    """
    for d in data:
        if key in d.keys():
            return d
    return {}

# def upgrade_lists_in_dict(data: Dict[str, any]):
#     """
#
#    :param data:
#    :return:
#    """
#    for key in data.keys():
#        if isinstance(data[key], list):
#            new = {}


def get_layers(data: Dict[str, Any]) -> List[Layer]:
    """
    get layers from kicad pcb file
    :param data:
    :return:
    """
    try:
        layers = data['kicad_pcb']
        layers = get_dict_by_key(layers, 'layers')
        res: List[Layer] = list()
        for layer in layers['layers']:
            layer_data = list(layer.values())[0]
            new_layer = Layer(name=layer_data[0], layer_type=layer_data[1])
            res.append(new_layer)
        print(res)
        return res

    except KeyError:
        print("Wrong file structure, unable to get layers")


if __name__ == '__main__':
    inputdata = open("data/FireFly.kicad_pcb").read()
    data_parse = OneOrMore(nestedExpr()).parseString(inputdata)
    data_list = data_parse.asList()
    data = list_to_dict(data_list[0])
    text: str = pprint.pformat(data, indent=0)
    with open("dump.txt", "w") as f:
        f.write(text)
    print(data)
    layers = get_layers(data)
    pcb = PCB(layers, list())

    pass

