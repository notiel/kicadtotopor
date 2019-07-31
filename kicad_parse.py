from pyparsing import OneOrMore, nestedExpr
from typing import Dict, Any, List, Union
import pprint

from pcb_structure import *


def list_to_dict(data: List) -> Dict[str, Any]:
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
        if isinstance(d, dict) and key in d.keys():
            return d
    return {}


def get_all_dicts_by_key(data: List[Dict[str, Any]], key: str) -> List[Dict[str, Any]]:
    """
    find all dicts in a list with selected key
    :param key: key to find
    :param data: list with dicts
    :return: dicts with given key
    """
    res: List[Dict[str, Any]] = list()
    for d in data:
        if isinstance(d, dict) and key in d.keys():
            res.append(d)
    return res


def create_module(module: List[Union[str, Dict[str, Any]]]) -> Module:
    """
    creates PCB Kicad module from data list
    :param data: list with module fields
    :return:
    """
    m_data = module['module']
    footprint = m_data[0]
    layer = get_dict_by_key(m_data, 'layer')['layer']
    coords = get_dict_by_key(m_data, 'at')['at']
    # coords[0] = float(coords[0])
    # coords[1] = float(coords[1])
    attr = get_dict_by_key(m_data, 'attr')
    smd: bool = True if (attr and attr['attr'] == 'smd') else False
    texts = get_texts(m_data)
    lines = get_lines(m_data)
    pads = get_pads(m_data)
    return Module(footprint=footprint, layer=layer, coords=coords, smd=smd, texts=texts, lines=lines, pads=pads)


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


def get_texts(m_data: Dict[str, Any]) -> List[FpText]:
    """
    gets texts for module
    :param data: module data
    :return: list of FpText
    """
    texts: List[FpText] = list()
    for text in get_all_dicts_by_key(m_data, 'fp_text'):
        fp_text = text['fp_text']
        if fp_text[0] == 'reference':
            text_type = TextType.reference
        elif fp_text[0] == 'value':
            text_type = TextType.value
        else:
            text_type = TextType.user
        caption: str = fp_text[1]
        coords: Coords = (fp_text[2]['at'][0], fp_text[2]['at'][1])
        layer: str = fp_text[3]['layer']
        texts.append(FpText(text_type=text_type, text=caption, coords=coords, layer=layer))
    return texts


def get_lines(m_data: Dict[str, Any]) -> List[FpLine]:
    """
    get lines data for module
    :param m_data: module data
    :return: list of lines
    """
    lines: List[FpLine] = list()
    for line in get_all_dicts_by_key(m_data, 'fp_line'):
        fp_line = line['fp_line']
        start: Coords = get_dict_by_key(fp_line, 'start')['start']
        end: Coords = get_dict_by_key(fp_line, 'end')['end']
        layer: str = get_dict_by_key(fp_line, 'layer')['layer']
        width: float = get_dict_by_key(fp_line, 'width')['width']
        new_line = FpLine(start=start, end=end, layer=layer, width=width)
        lines.append(new_line)
    return lines


def get_pads(m_data: Dict[str, Any]) -> List[FpPad]:
    """
    gets list of pads for module
    :param m_data: dict with module
    :return: list of pads
    """
    pads: List[FpPad] = list()
    for pad in get_all_dicts_by_key(m_data, 'pad'):
        fp_pad = pad['pad']
        pad_id = fp_pad[0]
        smd = fp_pad[1] == 'smd'
        drill = 0 if smd else fp_pad[2]
        ind = 2 if smd else 3
        if fp_pad[ind] == 'rect':
            pad_type =PadType.rect
        elif fp_pad[ind] == 'circle':
            pad_type = PadType.circle
        else:
            pad_type = PadType.oval
        pos = FpPos(pos=(fp_pad[ind+1][0], fp_pad[ind+1][1]), rot=fp_pad[ind+1][2])
        size = (fp_pad[ind+2][0], fp_pad[ind+2][1])
        layers = fp_pad[ind+3]
        net_id = fp_pad[ind+4][0]
        net_name = fp_pad[ind+4][1]
        new_pad = FpPad(pad_id=pad_id, smd=smd, drill=drill, pad_type=pad_type, pos=pos, size=size, layers=layers,
                        net_id=net_id, net_name=net_name)
        pads.append(new_pad)
    return pads


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
    for module in get_all_dicts_by_key(data['kicad_pcb'], 'module'):

        print(footprint, coords, layer, smd, texts)
    pass

