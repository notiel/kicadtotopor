from pyparsing import OneOrMore, nestedExpr
from typing import Dict, Any, List, Union
import pprint
import math

from pcb_structure import *
import create_topor

layer_list = ['F.Cu', 'B.Cu', 'Edge.Cuts', 'F.SilkS', 'B.SilkS', 'F.Mask', 'B.Mask', 'Dwgs.User', 'F.Paste', 'B.Paste',
              'B.Fab', 'F.Fab']


def get_end_point(arc: FpArc)->Coords:
    """
    gets end point for arc using center and angle
    :param arc: arc data
    :return: end point by x and y
    """
    x: float = float(arc.start[0])
    y: float = float(arc.start[1])
    ang: float = float(arc.angle)
    x_c: float = float(arc.end[0])
    y_c: float = float(arc.end[1])
    r: float = math.sqrt((x - x_c) * (x - x_c) + (y - y_c) * (y - y_c))
    start_angle: float = math.atan2(y - y_c, x - x_c) / math.pi * 180
    stop_angle: float = start_angle + ang
    if ang > 0:
        da: float = 0.1
        cond = lambda a: a < stop_angle
    else:
        da = - 0.1
        cond = lambda a: a > stop_angle
    a = start_angle
    while cond(a):
        x = x_c + r * math.cos(a / 180 * math.pi)
        y = y_c + r * math.sin(a / 180 * math.pi)
        a += da
    return x, y


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


def convert_to_layers(layer_data: Union [List[str], str])-> List[Layer]:
    """
    converts str layer data to layer list
    :param layer_data: data with layers
    :return:
    """
    if not isinstance(layer_data, List):
        layer_data = [layer_data]
    # change *. to F. and B.
    star_layer = [layer for layer in layer_data if "*." in layer]
    b_stars = [layer.replace("*", "B") for layer in star_layer]
    f_stars = [layer.replace("*", "F") for layer in star_layer]
    layer_data = [layer for layer in layer_data if "*." not in layer]
    layer_data.extend(b_stars)
    layer_data.extend(f_stars)
    result: List[Layer] = list()
    for layer in layer_data:
        layer = layer.replace('"', '')
        if layer in layer_list:
            layer_type = "signal" if layer in ['F.Cu', 'B.Cu'] else "user"
            result.append(Layer(name=layer, layer_type=layer_type))
        else:
            print('Unknown layer %s' % layer)
    return result


def create_module(module_dict: Dict[str, Any]) -> Module:
    """
    creates PCB Kicad module from data list
    :param module_dict: list with module fields
    :return:
    """
    m_data = module_dict['module']
    footprint = m_data[0].replace('"',  "")
    layer = convert_to_layers(get_dict_by_key(m_data, 'layer')['layer'])[0]
    coords = get_dict_by_key(m_data, 'at')['at']
    if len(coords) == 3 and "B." in layer.name:
        coords[2] = (float(coords[2]) + 180) % 360
    coords[1] = str(-1*float(coords[1]))
    # coords[0] = float(coords[0])
    # coords[1] = float(coords[1])
    attr = get_dict_by_key(m_data, 'attr')
    smd: bool = True if (attr and attr['attr'] == 'smd') else False
    texts = get_texts(m_data)
    lines = get_lines(m_data, 'fp_line')
    circles = get_circles(m_data, 'fp_circle')
    pads = get_pads(m_data)
    return Module(footprint=footprint, layer=layer, coords=coords, smd=smd, texts=texts, lines=lines, pads=pads,
                  circles=circles)


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


def get_texts(m_data: List[Dict[str, Any]], text_tag: str) -> List[FpText]:
    """
    gets texts for module
    :param text_tag: tag for find text
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
        caption: str = fp_text[1].replace('"', "")
        coords: Coords = (fp_text[2]['at'][0], str(-1*(float(fp_text[2]['at'][1]))))
        layer: Layer = convert_to_layers(fp_text[3]['layer'])[0]
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
        start[1] = str(-1 * float(start[1]))
        end: Coords = get_dict_by_key(fp_line, 'end')['end']
        end[1] = str(-1 * float(end[1]))
        layer: Layer = convert_to_layers(get_dict_by_key(fp_line, 'layer')['layer'])[0]
        width: float = get_dict_by_key(fp_line, 'width')['width']
        new_line = FpLine(start=start, end=end, layer=layer, width=width)
        lines.append(new_line)
    return lines


def get_circles(m_data: List[Dict[str, Any]], circle_tag: str) -> List[FpCircle]:
    """
    get lines data for module
    :param circle_tag: fp_line or gr_line
    :param m_data: module data
    :return: list of lines
    """
    circles: List[FpCircle] = list()
    for circle in get_all_dicts_by_key(m_data, circle_tag):
        fp_circle = circle[circle_tag]
        center: Coords = get_dict_by_key(fp_circle, 'center')['center']
        center[1] = str(-1 * float(center[1]))
        end: Coords = get_dict_by_key(fp_circle, 'end')['end']
        end[1] = str(-1 * float(end[1]))
        layer: Layer = convert_to_layers(get_dict_by_key(fp_circle, 'layer')['layer'])[0]
        width: float = get_dict_by_key(fp_circle, 'width')['width']
        new_circle = FpCircle(center=center, end=end, layer=layer, width=width)
        circles.append(new_circle)
    return circles


def get_arcs(m_data: List[Dict[str, Any]], arc_tag: str) -> List[FpArc]:
    """
    get lines data for module
    :param arc_tag: tag with arc key (gr_arc for example)
    :param m_data: module data
    :return: list of lines
    """
    arcs: List[FpArc] = list()
    for arc in get_all_dicts_by_key(m_data, arc_tag):
        fp_arc = arc[arc_tag]
        start: Coords = get_dict_by_key(fp_arc, 'start')['start']
        start[1] = str(-1 * float(start[1]))
        end: Coords = get_dict_by_key(fp_arc, 'end')['end']
        end[1] = str(-1 * float(end[1]))
        angle: float = -1*float(get_dict_by_key(fp_arc, "angle"))
        layer: Layer = convert_to_layers(get_dict_by_key(fp_arc, 'layer')['layer'])[0]
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
        pos = FpPos(pos=(pos_data[0], -1*float(pos_data[1])), rot=pos_data[2] if len(pos_data) == 3 else -1)
        size_data = get_dict_by_key(fp_pad, 'size')
        size = (size_data['size'][0], size_data['size'][1]) if size_data else (0, 0)
        pad_layers: List[Layer] = convert_to_layers(get_dict_by_key(fp_pad, 'layers')['layers'])
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
    :param pcb_data: list with arcs
    :return: FpLine and FpArc list
    """
    pcb_edges: List[Union[FpLine, FpArc]] = list()
    for elem in pcb_data:
        if isinstance(elem, dict) and 'gr_line' in elem.keys():
            fp_line = elem['gr_line']
            start: Coords = get_dict_by_key(fp_line, 'start')['start']
            start[1] = str(-1 * float(start[1]))
            end: Coords = get_dict_by_key(fp_line, 'end')['end']
            end[1] = str(-1 * float(end[1]))
            layer: Layer= convert_to_layers(get_dict_by_key(fp_line, 'layer')['layer'])[0]
            width: float = get_dict_by_key(fp_line, 'width')['width']
            new_line = FpLine(start=start, end=end, layer=layer, width=width)
            pcb_edges.append(new_line)
        if isinstance(elem, dict) and 'gr_arc' in elem.keys():
            fp_arc = elem['gr_arc']
            start: Coords = get_dict_by_key(fp_arc, 'end')['end']   # end in kicaad is _starting_ point
            start[1] = str(-1 * float(start[1]))
            end: Coords = get_dict_by_key(fp_arc, 'start')['start']     # start in kicad is center point
            end[1] = str(-1 * float(end[1]))
            angle: float = -1*float(get_dict_by_key(fp_arc, 'angle')['angle'])
            layer: Layer = convert_to_layers(get_dict_by_key(fp_arc, 'layer')['layer'])[0]
            width: float = get_dict_by_key(fp_arc, 'width')['width']
            new_arc = FpArc(start=start, end=end, angle=angle, layer=layer, width=width)
            pcb_edges.append(new_arc)

    new_edges = [edge for edge in pcb_edges if edge.layer.name == 'Edge.Cuts']
    for edge in new_edges:
        if isinstance(edge, FpArc):
            edge.end = get_end_point(edge)

    sorted_edges = [new_edges[0]]
    new_edges.pop(0)
    current = sorted_edges[0]
    while new_edges:
        for edge in new_edges:
            dx = abs(float(edge.start[0]) - float(current.end[0]))
            dy = abs(float(edge.start[1]) - float(current.end[1]))
            if dx + dy < 0.5:
                sorted_edges.append(edge)
                new_edges.remove(edge)
                current = edge
    return sorted_edges


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