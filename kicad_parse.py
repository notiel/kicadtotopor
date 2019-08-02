from pyparsing import OneOrMore, nestedExpr
from typing import Dict, Any, List, Union
import pprint

from pcb_structure import *
import create_topor

def list_to_dict(pcb_data: List) -> Dict[str, Any]:
    """

    :param pcb_data:
    :return:
    """
    res = {}
    if not pcb_data or len(pcb_data) < 2:
        return res
    if len(pcb_data) == 2:
        res[pcb_data[0]] = pcb_data[1]
        if not isinstance(res[pcb_data[0]], list):
            try:
                res[pcb_data[0]] = float(res[pcb_data[0]])
            except ValueError:
                pass
    else:
        res[pcb_data[0]] = pcb_data[1:]
    current_data = res[pcb_data[0]]
    if isinstance(current_data, list):
        for word in current_data:
            if isinstance(word, list):
                i = current_data.index(word)
                current_data[i] = list_to_dict(word)

    return res


def get_dict_by_key(pcb_data: List[Dict[str, Any]], key: str) -> Dict[str, Any]:
    """
    find a dict in a list with selected key
    :param key: key to find
    :param pcb_data: list with dicts
    :return: dict with given key
    """
    for d in pcb_data:
        if isinstance(d, dict) and key in d.keys():
            return d
    return {}


def get_all_dicts_by_key(pcb_data: List[Dict[str, Any]], key: str) -> List[Dict[str, Any]]:
    """
    find all dicts in a list with selected key
    :param key: key to find
    :param pcb_data: list with dicts
    :return: dicts with given key
    """
    res: List[Dict[str, Any]] = list()
    for d in pcb_data:
        if isinstance(d, dict) and key in d.keys():
            res.append(d)
    return res


def create_module(module_dict: Dict[str, Any]) -> Module:
    """
    creates PCB Kicad module from data list
    :param module_dict: list with module fields
    :return:
    """
    m_data = module_dict['module']
    footprint = m_data[0]
    layer = get_dict_by_key(m_data, 'layer')['layer']
    coords = get_dict_by_key(m_data, 'at')['at']
    # coords[0] = float(coords[0])
    # coords[1] = float(coords[1])
    attr = get_dict_by_key(m_data, 'attr')
    smd: bool = True if (attr and attr['attr'] == 'smd') else False
    texts = get_texts(m_data)
    lines = get_lines(m_data, 'fp_line')
    pads = get_pads(m_data)
    return Module(footprint=footprint, layer=layer, coords=coords, smd=smd, texts=texts, lines=lines, pads=pads)


def get_layers(layer_data: Dict[str, Any]) -> List[Layer]:
    """
    get layers from kicad pcb file
    :param layer_data:
    :return:
    """
    try:
        l_data = layer_data['kicad_pcb']
        l_data = get_dict_by_key(l_data, 'layers')
        res: List[Layer] = list()
        for layer in l_data['layers']:
            layer_data = list(layer.values())[0]
            new_layer = Layer(name=layer_data[0], layer_type=layer_data[1])
            res.append(new_layer)
        print(res)
        return res

    except KeyError:
        print("Wrong file structure, unable to get layers")


def get_texts(m_data: List[Dict[str, Any]]) -> List[FpText]:
    """
    gets texts for module
    :param m_data: module data
    :return: list of FpText
    """
    texts: List[FpText] = list()
    for text_data in get_all_dicts_by_key(m_data, 'fp_text'):
        fp_text = text_data['fp_text']
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


def get_lines(m_data: List[Dict[str, Any]], line_tag: str) -> List[FpLine]:
    """
    get lines data for module
    :param line_tag: fp_line or gr_line
    :param m_data: module data
    :return: list of lines
    """
    lines: List[FpLine] = list()
    for line in get_all_dicts_by_key(m_data, line_tag):
        fp_line = line[line_tag]
        start: Coords = get_dict_by_key(fp_line, 'start')['start']
        end: Coords = get_dict_by_key(fp_line, 'end')['end']
        layer: str = get_dict_by_key(fp_line, 'layer')['layer']
        width: float = get_dict_by_key(fp_line, 'width')['width']
        new_line = FpLine(start=start, end=end, layer=layer, width=width)
        lines.append(new_line)
    return lines


def get_arcs(m_data: List[Dict[str, Any]], arc_tag: str) -> List[FpArc]:
    """
    get lines data for module
    :param line_tag: fp_line or gr_line
    :param m_data: module data
    :return: list of lines
    """
    arcs: List[FpArc] = list()
    for arc in get_all_dicts_by_key(m_data, arc_tag):
        fp_arc = arc[arc_tag]
        start: Coords = get_dict_by_key(fp_arc, 'start')['start']
        end: Coords = get_dict_by_key(fp_arc, 'end')['end']
        angle: float = get_dict_by_key(fp_arc)
        layer: str = get_dict_by_key(fp_arc, 'layer')['layer']
        width: float = get_dict_by_key(fp_arc, 'width')['width']
        new_arc = FpArc(start=start, end=end, angle=angle, layer=layer, width=width)
        arcs.append(new_arc)
    return arcs


def get_pads(m_data: List[Dict[str, Any]]) -> List[FpPad]:
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
            pad_type = PadType.rect
        elif fp_pad[ind] == 'circle':
            pad_type = PadType.circle
        else:
            pad_type = PadType.oval
        pos_data = get_dict_by_key(fp_pad, 'at')['at']
        pos = FpPos(pos=(pos_data[0], pos_data[1]), rot=pos_data[2] if len(pos_data) == 3 else -1)
        size_data = get_dict_by_key(fp_pad, 'size')
        size = (size_data['size'][0], size_data['size'][1]) if size_data else (0, 0)
        pad_layers = get_dict_by_key(fp_pad, 'layers')['layers']
        net = get_dict_by_key(fp_pad, 'net')
        net_id = get_dict_by_key(fp_pad, 'net')['net'][0] if net else ""
        net_name = get_dict_by_key(fp_pad, 'net')['net'][1] if net else ""
        new_pad = FpPad(pad_id=pad_id, smd=smd, drill=drill, pad_type=pad_type, center=pos, size=size,
                        layers=pad_layers, net_id=net_id, net_name=net_name)
        pads.append(new_pad)
    return pads


def get_edges(pcb_data: List[Dict[str, Any]]) -> List[Union[FpLine, FpArc]]:
    """
    get edge data
    :param rcb_data: list with arcs
    :return: FpLine and FpArc list
    """
    edges: List[Union[FpLine, FpArc]] = list()
    for elem in pcb_data:
        if isinstance(elem, dict) and 'gr_line' in elem.keys():
            fp_line = elem['gr_line']
            start: Coords = get_dict_by_key(fp_line, 'start')['start']
            end: Coords = get_dict_by_key(fp_line, 'end')['end']
            layer: str = get_dict_by_key(fp_line, 'layer')['layer']
            width: float = get_dict_by_key(fp_line, 'width')['width']
            new_line = FpLine(start=start, end=end, layer=layer, width=width)
            edges.append(new_line)
        if isinstance(elem, dict) and 'gr_arc' in elem.keys():
            fp_arc = elem['gr_arc']
            start: Coords = get_dict_by_key(fp_arc, 'start')['start']
            end: Coords = get_dict_by_key(fp_arc, 'end')['end']
            angle: float = get_dict_by_key(fp_arc, 'angle')
            layer: str = get_dict_by_key(fp_arc, 'layer')['layer']
            width: float = get_dict_by_key(fp_arc, 'width')['width']
            new_arc = FpArc(start=start, end=end, angle=angle, layer=layer, width=width)
            edges.append(new_arc)

    edges = [edge for edge in edges if edge.layer == '"Edge.Cuts"']
    print(edges)
    return edges


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
    edges: List[Union[FpArc, FpLine]] = get_edges(data['kicad_pcb'])
    pcb = PCB(layers=layers, modules=list(), edge=edges)
    for module in get_all_dicts_by_key(data['kicad_pcb'], 'module'):
        pcb.modules.append(create_module(module))
    create_topor.create_topor(pcb)