from lxml import etree
QMTag = etree._Element
from pcb_structure import *
import math

version = '1.2.1'
program = 'TopoR Lite 7.0.18707'

layers = [{'name': 'Paste Top', 'type': "Paste", 'thickness': "0"},
          {'name': 'Mask Top', 'type': "Mask", 'thickness': "0"},
          {'name': 'F.Cu outline', 'type': "Assy", 'compsOutline': "on"},
          {'name': 'F.Cu', 'type': "Signal", 'thickness': "0"},
          {'name': 'B.Cu', 'type': "Signal", 'thickness': "0"},
          {'name': 'B.Cu_outline', 'type': "Assy", 'compsOutline': "on"},
          {'name': 'Paste Bottom', 'type': "Paste", 'thickness': "0"},
          {'name': 'Mask Bottom', 'type': "Mask", 'thickness': "0"}]

used_fp = []


def get_end_point(arc: FpArc)->Coords:
    """
    gets end point for arc using center and angle
    :param arc: arc data
    :return: end point by x and y
    """
    x: float = arc.c.start[0]
    y: float = arc.start[1]
    ang: float = arc.angle
    x_c: float = arc.end[0]
    y_c: float = arc.end[1]
    r: float = math.sqrt((x - x_c) * (x - x_c) + (y - y_c) * (y - y_c))
    start_angle: float = math.atan2(y - y_c, x - x_c) / math.pi * 180
    stop_angle: float = start_angle + ang
    if ang > 0:
        da: float = 0.1
        cond = lambda a: a < stop_angle
    else:
        da = -delta
        cond = lambda a: a > stop_angle
    a = start_angle
    while cond(a):
        x = x_c + r * math.cos(a / 180 * math.pi)
        y = y_c + r * math.sin(a / 180 * math.pi)
        a += da
    return (x, y)

def create_topor(pcb: PCB):
    """
    creates pcb topor file
    :param pcb: structure with data
    :return:
    """
    topor = etree.Element('TopoR_PCB_File')
    header = etree.SubElement(topor, "Header")
    tag_format = etree.SubElement(header, 'Format', type="test")
    tag_format.text = 'TopoR PCB file'
    tag_version = etree.SubElement(header, 'Version')
    tag_version.text = version
    tag_program = etree.SubElement(header, 'Program')
    tag_program.text = "TopoR Lite 7.0.18707"
    tag_date = etree.SubElement(header, "Date")
    # to do add date
    tag_date.text = 'Monday, July 22, 2019 20:19'
    tag_original = etree.SubElement(header, 'OriginalFormat')
    tag_original.text = 'TopoR PCB'
    tag_original = etree.SubElement(header, "OriginalFile")
    tag_original.text = r"C:\Users\juice\Downloads\Ostranna\Scripts\topor\data\FireFly.kicad_pcb"
    _ = etree.SubElement(header, 'Units', dist='mm', time="ps")

    tag_layers = etree.SubElement(topor, 'Layers', version="1.1")
    stack = etree.SubElement(tag_layers, "StackUpLayers")
    for layer in layers:
        _ = etree.SubElement(stack, 'Layer', **layer)
    library = etree.SubElement(topor, 'LocalLibrary', version="1.1")
    footprints = etree.SubElement(library, "Footprints")

    for module in pcb.modules:
        if module.footprint not in used_fp:
            footprint = etree.SubElement(footprints, 'Footprint', name=module.footprint)
            details = etree.SubElement(footprint, "Details")
            for line in module.lines:
                detail = etree.SubElement(details, 'Detail', lineWidth=str(line.width))
                layer_name = 'F.Cu_outline' if line.layer == 'F.Silks' else 'B.Cu_outline'
                _ = etree.SubElement(detail, 'LayerRef', name=layer_name)
                tag_line = etree.SubElement(detail, 'Line')
                _ = etree.SubElement(tag_line, 'Dot', x=line.start[0], y=line.start[1])
                _ = etree.SubElement(tag_line, 'Dot', x=line.end[0], y=line.end[1])
            used_fp.append(module.footprint)




    xml_tree =etree.ElementTree(topor)
    xml_tree.write('test.fst', xml_declaration=True, encoding="UTF-8", pretty_print=True)







