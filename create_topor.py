from lxml import etree
from pcb_structure import *
import math
import random
import string

QMTag = etree._Element

version = '1.2.1'
program = 'TopoR Lite 7.0.18707'

layers = [{'name': 'Paste Top', 'type': "Paste", 'thickness': "0"},
          {'name': 'Mask Top', 'type': "Mask", 'thickness': "0"},
          {'name': 'F.Cu_outline', 'type': "Assy", 'compsOutline': "on"},
          {'name': 'F.Cu', 'type': "Signal", 'thickness': "0"},
          {'name': 'B.Cu', 'type': "Signal", 'thickness': "0"},
          {'name': 'B.Cu_outline', 'type': "Assy", 'compsOutline': "on"},
          {'name': 'Paste Bottom', 'type': "Paste", 'thickness': "0"},
          {'name': 'Mask Bottom', 'type': "Mask", 'thickness': "0"}]

used_fp = []


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

    textstyles = etree.SubElement(topor, "TextStyles", version="1.0")
    _ = etree.SubElement(textstyles, "TextStyle", name="Default", fontName="", height="1")
    _ = etree.SubElement(textstyles, "TextStyle", name="President", fontName="", height="1")


    library = etree.SubElement(topor, 'LocalLibrary', version="1.1")
    footprints = etree.SubElement(library, "Footprints")

    for module in pcb.modules:
        if module.footprint not in used_fp:
            footprint = etree.SubElement(footprints, 'Footprint', name=module.footprint)
            details = etree.SubElement(footprint, "Details")
            for line in module.lines:
                detail = etree.SubElement(details, 'Detail', lineWidth=str(line.width))
                layer_name = 'F.Cu_outline' # if line.layer.name == 'F.SilkS'  else 'B.Cu_outline'
                _ = etree.SubElement(detail, 'LayerRef', name=layer_name)
                tag_line = etree.SubElement(detail, 'Line')
                _ = etree.SubElement(tag_line, 'Dot', x=line.start[0], y=line.start[1])
                _ = etree.SubElement(tag_line, 'Dot', x=line.end[0], y=line.end[1])
            for circle in module.circles:
                detail = etree.SubElement(details, 'Detail', lineWidth=str(circle.width))
                layer_name = 'F.Cu_outline'  # if line.layer.name == 'F.SilkS' else 'B.Cu_outline'
                _ = etree.SubElement(detail, 'LayerRef', name=layer_name)
                diameter = 2*((float(circle.end[0]) - float(circle.center[0]))**2 + (float(circle.end[1]) - float(circle.center[1])**2))**0.5
                tag_circle = etree.SubElement(detail, "Circle", diameter=str(diameter))
                _ = etree.SubElement(tag_circle, "Center", x=str(circle.center[0]), y=str(circle.center[1]))

            used_fp.append(module.footprint)

    components = etree.SubElement(library, "Components")
    for module in pcb.modules:
        ref = [text.text for text in module.texts if text.text_type == TextType.reference][0]
        component = etree.SubElement(components, 'Component', name=ref)
        pins = etree.SubElement(component, 'Pins')
        pin = etree.SubElement(pins,
                               "Pin", pinNum="1", name="1", pinSymName="1", pinEqual="0", gate="-1", gateEqual="0")

    packages = etree.SubElement(library, "Packages")
    for module in pcb.modules:
        ref = [text.text for text in module.texts if text.text_type == TextType.reference][0]
        package = etree.SubElement(packages, 'Package')
        _ = etree.SubElement(package, 'ComponentRef', name=ref)
        _ = etree.SubElement(package, 'FootprintRef', name=module.footprint)
        _ = etree.SubElement(package, 'Pinpack', pinNum="1", padNum="1")

    constr = etree.SubElement(topor, "Constructive", version='1.2')
    board = etree.SubElement(constr, 'BoardOutline')
    contour = etree.SubElement(board, 'Contour')
    shape = etree.SubElement(contour, 'Shape')
    polyline = etree.SubElement(shape, 'Polyline')
    _ = etree.SubElement(polyline, "Start", x=str(pcb.edge[0].start[0]), y=str(pcb.edge[0].start[1]))
    for edge in pcb.edge:
        if isinstance(edge, FpLine):
            line = etree.SubElement(polyline, "SegmentLine")
            _ = etree.SubElement(line, 'End', x=edge.end[0], y=edge.end[1])
        if isinstance(edge, FpArc):
            arc = etree.SubElement(polyline, "SegmentArcByAngle", angle=str(edge.angle))
            _ = etree.SubElement(arc, 'End',  x=str(edge.end[0]), y=str(edge.end[1]))

    components_on_board = etree.SubElement(topor, 'ComponentsOnBoard', version='1.3')
    components = etree.SubElement(components_on_board, "Components")
    for module in pcb.modules:
        ref = [text.text for text in module.texts if text.text_type == TextType.reference][0]
        comp_inst = etree.SubElement(components, 'CompInstance', name=ref,
                                     uniqueId=''.join(random.choice(string.ascii_letters) for x in range(7)),
                                     side='Top' if 'F.Cu' in module.layer.name else 'Bottom',
                                     angle=str(module.coords[2]) if len(module.coords) > 2 else '0',
                                     )
        _ = etree.SubElement(comp_inst, "ComponentRef", name=ref)
        _ = etree.SubElement(comp_inst, 'FootprintRef', name=module.footprint)
        _ = etree.SubElement(comp_inst, 'Org', x=str(module.coords[0]), y=str(module.coords[1]))

        attributes = etree.SubElement(comp_inst, 'Attributes')
        attribute = etree.SubElement(attributes, 'Attribute', type="RefDes")
        visible = 'off' if any([text in ref for text in ['Logo', 'RP', 'Test', 'HOLE']]) else 'on'
        label = etree.SubElement(attribute, "Label", mirror='on' if'B.Cu' in module.layer.name else 'off', visible=visible)
        ref_coords = [text.coords for text in module.texts if text.text_type == TextType.reference][0]
        _ = etree.SubElement(label, "LayerRef", name='F.Cu_outline' if 'F.Cu' in module.layer.name else 'B.Cu_outline')
        _ = etree.SubElement(label, "TextStyleRef", name="Default")
        _ = etree.SubElement(label, 'Org', x=str(ref_coords[0]), y=str(ref_coords[1]))

    xml_tree = etree.ElementTree(topor)
    xml_tree.write('test.fst', xml_declaration=True, encoding="UTF-8", pretty_print=True)







