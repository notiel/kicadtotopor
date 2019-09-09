from pyparsing import OneOrMore, nestedExpr
from typing import Dict, Any, List, Union
import pprint
import math
import sys

from pcb_structure import *
import create_topor

layer_list = ['F.Cu', 'B.Cu', 'Edge.Cuts', 'F.SilkS', 'B.SilkS', 'F.Mask', 'B.Mask', 'Dwgs.User', 'F.Paste', 'B.Paste',
              'B.Fab', 'F.Fab', 'F.CrtYd', 'B.CrtYd', 'F.Adhes', 'B.Adhes']


def get_settings() -> Dict[str, Any]:
    """
    gets settings from config file
    :return:
    """
    settings = dict()
    with open("config,ini") as file_config:
        for line in file_config:
            try:
                key = line.split(":")[0]
                value = line.split(":")[1].strip().split() if key == 'invisible_manes' else line.split(":")[1].strip()
                settings[key] = value
            except IndexError:
                pass
    return settings


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
    return [str(x), str(y)]


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


def convert_to_layers(layer_data: Union[List[str], str])-> List[Layer]:
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


def create_module(module_dict: Dict[str, Any], nets: List[Net]) -> Module:
    """
    creates PCB Kicad module from data list
    :param nets: list of nets
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
    attr = get_dict_by_key(m_data, 'attr')
    smd: bool = True if (attr and attr['attr'] == 'smd') else False
    module_texts: List[FpText] = get_texts(m_data, 'fp_text')
    figures: List[Union[FpPoly, FpCircle, FpArc, FpLine]] = get_lines(m_data, 'fp_line')
    figures.extend(get_circles(m_data, 'fp_circle'))
    pads = get_pads(m_data, nets)
    ref = [text.text for text in module_texts if text.text_type ==TextType.reference][0]
    update_nets_with_pads(pads, nets, ref)
    figures.extend(get_polys(m_data, 'fp_poly'))
    figures.extend(get_arcs(m_data, 'fp_arc'))
    return Module(footprint=footprint, layer=layer, coords=coords, smd=smd,
                  texts=module_texts, pads=pads, figures=figures, extrapads=list())


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
    fp_texts: List[FpText] = list()
    for text_data in get_all_dicts_by_key(m_data, text_tag):
        fp_text = text_data[text_tag]
        if text_tag == 'fp_text':
            if fp_text[0] == 'reference':
                text_type = TextType.reference
            elif fp_text[0] == 'value':
                text_type = TextType.value
            else:
                text_type = TextType.user
            caption: str = fp_text[1].replace('"', "")
        else:
            text_type = TextType.simple
            caption: str = fp_text[0].replace('"', "")
        coords_data = get_dict_by_key(fp_text, 'at')['at']
        coords: Coords = [coords_data[0], str(-1*(float(coords_data[1])))]
        angle = coords_data[2] if len(coords_data) > 2 else '0'
        layer: Layer = convert_to_layers(get_dict_by_key(fp_text, 'layer')['layer'])[0]
        fp_texts.append(FpText(text_type=text_type, text=caption, coords=coords, layer=layer, angle=angle))
    return fp_texts


def create_line(line_data: Dict[str, Any], line_tag: str) -> FpLine:
    """
    create line
    :param line_tag: tag for line
    :param line_data: dict with line data
    :return: FpLine object
    """
    fp_line = line_data[line_tag]
    start: Coords = [get_dict_by_key(fp_line, 'start')['start'][0], get_dict_by_key(fp_line, 'start')['start'][1]]
    start[1] = str(-1 * float(start[1]))
    end: Coords = [get_dict_by_key(fp_line, 'end')['end'][0], get_dict_by_key(fp_line, 'end')['end'][1]]
    end[1] = str(-1 * float(end[1]))
    layer: Layer = convert_to_layers(get_dict_by_key(fp_line, 'layer')['layer'])[0]
    width: float = get_dict_by_key(fp_line, 'width')['width']
    new_line = FpLine(start=start, end=end, layer=layer, width=width)
    return new_line


def get_lines(m_data: List[Dict[str, Any]], line_tag: str) -> List[FpLine]:
    """
    get lines data for module
    :param line_tag: fp_line or gr_line
    :param m_data: module data
    :return: list of lines
    """
    lines: List[FpLine] = list()
    for line in get_all_dicts_by_key(m_data, line_tag):
        lines.append(create_line(line, line_tag))
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
        center: Coords = [get_dict_by_key(fp_circle, 'center')['center'][0],
                          get_dict_by_key(fp_circle, 'center')['center'][1]]
        center[1] = str(-1 * float(center[1]))
        end: Coords = [get_dict_by_key(fp_circle, 'end')['end'][0], get_dict_by_key(fp_circle, 'end')['end'][1]]
        end[1] = str(-1 * float(end[1]))
        layer: Layer = convert_to_layers(get_dict_by_key(fp_circle, 'layer')['layer'])[0]
        width: float = get_dict_by_key(fp_circle, 'width')['width']
        new_circle = FpCircle(center=center, end=end, layer=layer, width=width)
        circles.append(new_circle)
    # print(circles)
    return circles


def get_polys(m_data: List[Dict[str, Any]], poly_tag: str) -> List[FpPoly]:
    """
    get data of polygon
    :param m_data: data
    :param poly_tag: tag for poly
    :return:
    """
    polys = get_all_dicts_by_key(m_data, poly_tag)
    res_polys: List[FpPoly] = list()
    if polys:
        for poly in polys:
            poly_data = poly[poly_tag]
            layer: Layer = convert_to_layers(get_dict_by_key(poly_data, 'layer')['layer'])[0]
            width: str = get_dict_by_key(poly_data, 'width')['width']
            pts_data: List[Dict[str, Any]] = get_dict_by_key(poly_data, 'pts')['pts']
            points: List[Coords] = list()
            for p in pts_data:
                point = [p['xy'][0], str(-1*float(p['xy'][1]))]
                points.append(point)
            res_polys.append(FpPoly(layer=layer, width=width, points=points))
    return res_polys


def create_arc(arc_data: Dict[str, Any], arc_tag: str) -> FpArc:
    """
    create FpArc object from dict with arc data
    :param arc_data: dict with arc data
    :param arc_tag: arc tag
    :return: FpArc object
    """
    fp_arc = arc_data[arc_tag]
    # end in kicad is start point
    start: Coords = [get_dict_by_key(fp_arc, 'end')['end'][0], get_dict_by_key(fp_arc, 'end')['end'][1]]
    start[1] = str(-1 * float(start[1]))
    end: Coords = [get_dict_by_key(fp_arc, 'start')['start'][0],
                   get_dict_by_key(fp_arc, 'start')['start'][1]]  # start in kicad is center point
    end[1] = str(-1 * float(end[1]))
    angle: float = -1 * float(get_dict_by_key(fp_arc, 'angle')['angle'])
    layer: Layer = convert_to_layers(get_dict_by_key(fp_arc, 'layer')['layer'])[0]
    width: float = get_dict_by_key(fp_arc, 'width')['width']
    new_arc = FpArc(start=start, end=end, angle=angle, layer=layer, width=width)
    new_arc.end = get_end_point(new_arc)
    return new_arc


def get_arcs(m_data: List[Dict[str, Any]], arc_tag: str) -> List[FpArc]:
    """
    get lines data for module
    :param arc_tag: tag with arc key (gr_arc for example)
    :param m_data: module data
    :return: list of lines
    """
    arcs: List[FpArc] = list()
    for arc in get_all_dicts_by_key(m_data, arc_tag):
        arcs.append(create_arc(arc, arc_tag))
    return arcs


def get_pads(m_data: List[Dict[str, Any]], nets: List[Net]) -> List[FpPad]:
    """
    gets list of pads for module
    :param nets:
    :param m_data: dict with module
    :return: list of pads
    """
    layer = get_dict_by_key(m_data, 'layer')['layer']
    pads: List[FpPad] = list()
    used_pads = [""]
    for pad in get_all_dicts_by_key(m_data, 'pad'):
        fp_pad = pad['pad']
        pad_id = fp_pad[0].replace('"', "")
        if pad_id in used_pads:
            count = 1
            while pad_id+str(count) in used_pads:
                count += 1
            pad_id = pad_id+str(count)
        used_pads.append(pad_id)
        smd = (fp_pad[1] == 'smd')
        drill = 0 if smd else get_dict_by_key(fp_pad, "drill")['drill']
        if fp_pad[2] == 'rect':
            pad_type = PadType.rect
        elif fp_pad[2] == 'circle':
            pad_type = PadType.circle
        elif fp_pad[2] == 'oval':
            pad_type = PadType.oval
        else:
            pad_type = PadType.custom
        pos_data = get_dict_by_key(fp_pad, 'at')['at']
        pos = FpPos(pos=[pos_data[0], -1.0*float(pos_data[1])], rot=(pos_data[2]) if len(pos_data) == 3 else 0)
        if 'B.' in layer:
            pos.pos[1] = -1*pos.pos[1]
        size_data = get_dict_by_key(fp_pad, 'size')
        size = [size_data['size'][0], size_data['size'][1]] if size_data else [0, 0]
        pad_layers: List[Layer] = convert_to_layers(get_dict_by_key(fp_pad, 'layers')['layers'])
        net_data = get_dict_by_key(fp_pad, 'net')
        net_id = get_dict_by_key(fp_pad, 'net')['net'][0] if net_data else ""
        net_name = get_dict_by_key(fp_pad, 'net')['net'][1] if net_data else ""
        new_pad = FpPad(pad_id=pad_id, smd=smd, drill=drill, pad_type=pad_type, center=pos, size=size,
                        layers=pad_layers, net_id=net_id, net_name=net_name, extra_points=list())
        if pad_type == PadType.custom:
            pad_data = get_dict_by_key(fp_pad, 'primitives')['primitives']
            for extra_pad in pad_data:
                if isinstance(extra_pad, dict):
                    print(extra_pad)
                    if 'gr_poly' in extra_pad.keys():
                        points = get_dict_by_key(extra_pad['gr_poly'], 'pts')['pts']
                    elif 'pts' in extra_pad.keys():
                        points = extra_pad['pts']
                    else:
                        continue
                    for point in points:
                        new_pad.extra_points.append([point['xy'][0], str(-1*float(point['xy'][1]))])
            print(new_pad.extra_points)
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
            pcb_edges.append(create_line(elem, 'gr_line'))
        if isinstance(elem, dict) and 'gr_arc' in elem.keys():
            pcb_edges.append(create_arc(elem, 'gr_arc'))

    new_edges = [edge for edge in pcb_edges if edge.layer.name == 'Edge.Cuts']

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


def get_nets(data: List[Dict[str, Any]]) -> List[Net]:
    """
    get jusy list of nets with their id and name
    :param data: data of pcb
    :return: list of nets
    """
    nets_data = get_all_dicts_by_key(data, 'net')
    nets: List[Net] = list()
    for net in nets_data:
        new_net = Net(net_name=net['net'][1].replace('"', ''), net_id=net['net'][0], contacts=list(),
                      segments=list(), vias=list())
        nets.append(new_net)
    return nets


def get_net_groups(data: List[Dict[str, Any]], nets: List[Net]) -> List[NetGroup]:
    """
    get net groups data and assigns net groups to nets
    :param data: pcb data
    :param nets: list of nets
    :return: list of netgroups
    """
    group_data = get_all_dicts_by_key(data, 'net_class')
    groups: List[NetGroup] = list()
    for group in group_data:
        name = group['net_class'][0].replace('"', '')
        clearance = get_dict_by_key(group['net_class'], 'clearance')['clearance']
        width = get_dict_by_key(group['net_class'], 'trace_width')['trace_width']
        via_dia = get_dict_by_key(group['net_class'], 'via_dia')['via_dia']
        via_drill = get_dict_by_key(group['net_class'], 'via_drill')['via_drill']
        new_group = NetGroup(name=name, clearance=clearance, trace_width=width, via_dia=via_dia, via_drill=via_drill)
        groups.append(new_group)
        nets_data = get_all_dicts_by_key(group['net_class'], 'add_net')
        for add_net in nets_data:
            for net in nets:
                if net.net_name == add_net['add_net'].replace('"',''):
                    net.group = name
    return groups


def update_nets_with_pads(pads: List[FpPad], nets: List[Net], ref: str):
    """
    update net structure
    :param pads: list of module pads
    :param net: pcb nets
    :param ref: reference of module to find pad
    :return:
    """
    for pad in pads:
        if pad.net_name:
            net: Net = [net for net in nets if float(net.net_id) == float(pad.net_id)][0]
            net.contacts.append((ref, pad.pad_id))

def update_nets_with_segments(pcb_data: List[Dict[str, Any]], nets: List[Net]):
    """
    get segments of nets
    :param pcb_data: data of pcb to get nets
    :param nets: list of nets to update
    :return: 
    """
    segments = get_all_dicts_by_key(pcb_data, 'segment')
    for segment in segments:
        start: Coords = get_dict_by_key(segment['segment'], 'start')['start']
        start[1] = str(-1*float(start[1]))
        end: Coords = get_dict_by_key(segment['segment'], 'end')['end']
        end[1] = str(-1 * float(end[1]))
        width: str = get_dict_by_key(segment['segment'], 'width')['width']
        layer_data: str = get_dict_by_key(segment['segment'], 'layer')['layer']
        layers: List[Layer] = convert_to_layers(layer_data)
        new_segment: Segment = Segment(start=start, end=end, width=width, layers=layers)
        net_id: str = get_dict_by_key(segment['segment'], 'net')['net']
        for net in nets:
            if float(net.net_id) == float(net_id):
                net.segments.append(new_segment)


def update_nets_with_vias(pcb_data: List[Dict[str, Any]], nets: List[Net]):
    """
    get segments of nets
    :param pcb_data: data of pcb to get nets
    :param nets: list of nets to update
    :return:
    """
    vias = get_all_dicts_by_key(pcb_data, 'via')
    for via in vias:
        at: Coords = get_dict_by_key(via['via'], 'at')['at']
        at[1] = str(-1*float(at[1]))
        size: str = get_dict_by_key(via['via'], 'size')['size']
        layer_data: str  = get_dict_by_key(via['via'], 'layers')['layers']
        layers: List[Layer] = convert_to_layers(layer_data)
        new_via: Via = Via(center=at, size=size, layers=layers)
        net_id: str = get_dict_by_key(via['via'], 'net')['net']
        for net in nets:
            if float(net.net_id) == float(net_id):
                net.vias.append(new_via)


def main(filename):
    inputdata = open(filename).read()
    data_parse = OneOrMore(nestedExpr()).parseString(inputdata)
    data_list = data_parse.asList()
    data = list_to_dict(data_list[0])
    text: str = pprint.pformat(data, indent=0)
    with open("dump.txt", "w") as f:
        f.write(text)
    layers = get_layers(data)
    edges: List[Union[FpArc, FpLine]] = get_edges(data['kicad_pcb'])
    texts = get_texts(data['kicad_pcb'], 'gr_text')
    nets = get_nets(data['kicad_pcb'])
    net_groups = get_net_groups(data['kicad_pcb'], nets)
    update_nets_with_segments(data['kicad_pcb'], nets)
    update_nets_with_vias(data['kicad_pcb'], nets)
    extra_figures: List[Union[FpLine, FpCircle, FpPoly, FpArc]] = get_arcs(data['kicad_pcb'], 'gr_arc')
    extra_figures.extend((get_polys(data['kicad_pcb'], 'gr_poly')))
    extra_figures.extend(get_lines(data['kicad_pcb'], 'gr_line'))
    extra_figures.extend(get_circles(data['kicad_pcb'], 'gr_circle'))
    pcb = PCB(layers=layers, modules=list(), edge=edges, texts=texts, nets=nets, net_groups=net_groups  )
    for module in get_all_dicts_by_key(data['kicad_pcb'], 'module'):
        pcb.modules.append(create_module(module, nets))
    if extra_figures:
        extra_ref: FpText = FpText(TextType.reference, "ExtraSilks", Layer("F.SilkS", "user"), [0, 0], 0)
        extra_value: FpText = FpText(TextType.value, "ExtraSilks", Layer("F.SilkS", "user"), [0, 0], 0)
        extra_module: Module = Module("ExtraSilks", Layer("F.Silks", "user"), [0, 0], False, [extra_ref, extra_value],
                                      extra_figures, list(), list())
        pcb.modules.append(extra_module)
    create_topor.create_topor(filename, pcb, get_settings())


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("No PCB filename")
    else:
        main(sys.argv[1])
