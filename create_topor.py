from lxml import etree
from pcb_structure import *
import random
import string
from typing import Dict, Any

FstTag = etree._Element

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
exclude_names = ['Logo', 'RP', 'TEST', 'HOLE', "CONN", "BUTTON", "EEPROM", "ANT", "REF", "LED", "HOLDER", "SWITCH"]


def create_detail(details: FstTag, figure: FpFigure):
    """
    creates tag structure for detail
    :param details: parent tag
    :param figure: figure for detail
    :return:
    """
    detail = etree.SubElement(details, 'Detail', lineWidth=str(figure.width))
    layer_name = 'F.Cu_outline'  # if line.layer.name == 'F.SilkS'  else 'B.Cu_outline'
    _ = etree.SubElement(detail, 'LayerRef', name=layer_name)
    if isinstance(figure, FpLine):
        tag_line = etree.SubElement(detail, 'Line')
        _ = etree.SubElement(tag_line, 'Dot', x=figure.start[0], y=figure.start[1])
        _ = etree.SubElement(tag_line, 'Dot', x=figure.end[0], y=figure.end[1])
    elif isinstance(figure, FpCircle):
        diameter = round(2 * ((float(figure.end[0]) - float(figure.center[0])) ** 2 +
                              (float(figure.end[1]) - float(figure.center[1])) ** 2) ** 0.5, 2)
        tag_circle = etree.SubElement(detail, "Circle", diameter=str(diameter))
        _ = etree.SubElement(tag_circle, "Center", x=str(figure.center[0]), y=str(figure.center[1]))
    elif isinstance(figure, FpPoly):
        poly_tag = etree.SubElement(detail, "Polygon")
        for point in figure.points:
            _ = etree.SubElement(poly_tag, "Dot", x=point[0], y=point[1])
    elif isinstance(figure, FpArc):
        arc = etree.SubElement(detail, "ArcByAngle", angle=figure.angle)
        _ = etree.SubElement(arc, "Start", x=figure.start[0], y=figure.start[1])
        _ = etree.SubElement(arc, "End", x=figure.end[0], y=figure.end[1])


def get_label_angle(module: Module, label_type: TextType) -> float:
    """
    get angle for label using label and footprint angles
    :param label_type: reference or value label
    :param module: module with data
    :return:
    """
    ref_angle = float([text.angle for text in module.texts if text.text_type == label_type][0])
    angle = float(module.coords[2]) if len(module.coords) > 2 else 0
    if angle == 90:
        label_angle = 0
    elif angle == 180:
        label_angle = angle + ref_angle
    else:
        label_angle = (angle + ref_angle) % 180
    return label_angle


def create_header(topor: FstTag):
    """
    creates header
    :param topor:
    :return:
    """
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
    # to do add filename
    tag_original.text = r"C:\Users\juice\Downloads\Ostranna\Scripts\topor\data\FireFly.kicad_pcb"
    _ = etree.SubElement(header, 'Units', dist='mm', time="ps")


def create_layers(topor: FstTag):
    """
    creates layers tags
    :param topor: tag to add layers
    :return:
    """
    tag_layers = etree.SubElement(topor, 'Layers', version="1.1")
    stack = etree.SubElement(tag_layers, "StackUpLayers")
    for layer in layers:
        _ = etree.SubElement(stack, 'Layer', **layer)

def create_textstyles(topor: FstTag, settings: Dict[str, Any]):
    """
    creates text styles
    :param topor: tag to add styles
    :param settings: config fonts settings
    :return:
    """
    textstyles = etree.SubElement(topor, "TextStyles", version="1.0")
    _ = etree.SubElement(textstyles, "TextStyle", name="Default", fontName=settings.setdefault("font_default", ""),
                         height=settings.setdefault("font_size", "1"))
    _ = etree.SubElement(textstyles, "TextStyle", name="Logo", fontName=settings.setdefault("font_logo", ""),
                         height=settings.setdefault("logo_size", "3"))


def create_extra_pads(padstacks: FstTag, module: Module, ref: str, used_extra_pads: List[str]):
    """
    creates extra pads from .Cu
    :param used_extra_pads: list of also used names for extra pads
    :param ref: name of module
    :param module: module with pad data
    :param padstacks: tag to add info
    :return:
    """
    for figure in module.figures:
        if "Cu" in figure.layer.name:
            if isinstance(figure, FpPoly):
                name: str = ref
                if name in used_extra_pads:
                    count = 2
                    while name + str(count) in used_extra_pads:
                        count += 1
                    name = name + str(count)
                padstack = etree.SubElement(padstacks, "Padstack", name=name, type="SMD", metallized="on")
                _ = etree.SubElement(padstack, "Thermal", spokeNum='4', minSpokeNum='4', angle='45',
                                     spokeWidth='0.381', backoff='0.381')
                pads_tag = etree.SubElement(padstack, "Pads")
                pad_tag = etree.SubElement(pads_tag, "PadPoly")
                _ = etree.SubElement(pad_tag, "LayerTypeRef", type="Signal")
                for point in figure.points:
                    _ = etree.SubElement(pad_tag, "Dot", x=point[0], y=point[1])
                module.extrapads.append(name)
                used_extra_pads.append(name)


def create_pads(library: FstTag, pcb: PCB):
    """
    creates padsstack tags
    :param library: tag to add padstacks
    :param pcb: pcb data
    :return:
    """
    padstacks = etree.SubElement(library, "Padstacks")
    used_extra_pads = list()
    for module in pcb.modules:
        ref = [text.text for text in module.texts if text.text_type == TextType.reference][0]
        for pad in module.pads:
            if pad.smd:
                padstack = etree.SubElement(padstacks, "Padstack", name=ref + ' ' + pad.pad_id, type="SMD",
                                            metallized="on")
            else:
                padstack = etree.SubElement(padstacks, "Padstack", name=ref + ' ' + pad.pad_id,
                                            holeDiameter=str(pad.drill), metallized="on")
                pad.layers.append(Layer(name='Plane', layer_type='Plane'))
            _ = etree.SubElement(padstack, "Thermal", spokeNum='4', minSpokeNum='4', angle='45', spokeWidth='0.381',
                                 backoff='0.381')
            pads_tag = etree.SubElement(padstack, "Pads")
            used_layers = list()
            for layer in pad.layers:
                if layer.layer_type not in used_layers:
                    layer_type = layer.layer_type.title().replace("User", "Mask")
                    if pad.pad_type == PadType.circle:
                        pad_tag = etree.SubElement(pads_tag, "PadCircle", diameter=pad.size[0])
                        _ = etree.SubElement(pad_tag, "LayerTypeRef", type=layer_type)
                    if pad.pad_type == PadType.oval:
                        diameter = min(float(pad.size[0]), float(pad.size[1]))
                        x = str(diameter - float(pad.size[0]))
                        y = str(diameter - float(pad.size[1]))
                        pad_tag = etree.SubElement(pads_tag, "PadOval", diameter=str(diameter))
                        _ = etree.SubElement(pad_tag, "LayerTypeRef", type=layer_type)
                        _ = etree.SubElement(pad_tag, "Stretch", x=x, y=y)
                    if pad.pad_type == PadType.rect:
                        width = pad.size[0]
                        height = pad.size[1]
                        pad_tag = etree.SubElement(pads_tag, "PadRect", width=width, height=height)
                        _ = etree.SubElement(pad_tag, "LayerTypeRef", type=layer_type)
                    if pad.pad_type == PadType.custom:
                        print(pad.extra_points)
                        pad_tag = etree.SubElement(pads_tag, "PadPoly")
                        _ = etree.SubElement(pad_tag, "LayerTypeRef", type="Signal")
                        for point in pad.extra_points:
                            _ = etree.SubElement(pad_tag, "Dot", x=point[0], y=point[1])

                    used_layers.append(layer_type)
        create_extra_pads(padstacks, module, ref, used_extra_pads)


def create_topor(pcb: PCB, settings: Dict[str, Any]):
    """
    creates pcb topor file
    :param settings: data with config settings
    :param pcb: structure with data
    :return:
    """
    topor = etree.Element('TopoR_PCB_File')
    create_header(topor)
    create_layers(topor)
    create_textstyles(topor, settings)
    library = etree.SubElement(topor, 'LocalLibrary', version="1.1")
    create_pads(library, pcb)

    footprints = etree.SubElement(library, "Footprints")
    for module in pcb.modules:
        ref = [text.text for text in module.texts if text.text_type == TextType.reference][0]
        footprint = etree.SubElement(footprints, 'Footprint', name=module.footprint + ' ' + ref)
        pads = etree.SubElement(footprint, "Pads")
        for pad in module.pads:
            angle = str(pad.center.rot) if (pad.pad_type != PadType.custom and int(pad.center.rot) % 90 == 0) else '0'
            pad_tag = etree.SubElement(pads, "Pad", padNum=str(module.pads.index(pad)), name=pad.pad_id, angle=angle)
            _ = etree.SubElement(pad_tag, "PadstackRef", name=ref+' ' + pad.pad_id)
            _ = etree.SubElement(pad_tag, "Org", x=str(pad.center.pos[0]), y=str(pad.center.pos[1]))
        for pad in module.extrapads:
            pad_tag = etree.SubElement(pads, "Pad", padNum=str(module.extrapads.index(pad)+len(module.pads)),
                                       name=str(module.extrapads.index(pad)+len(module.pads)))
            _ = etree.SubElement(pad_tag, "PadstackRef", name=pad)
            _ = etree.SubElement(pad_tag, "Org", x='0', y='0')

        details = etree.SubElement(footprint, "Details")
        for figure in module.figures:
            if 'SilkS' in figure.layer.name:
                create_detail(details, figure)
        used_fp.append(module.footprint)

    components = etree.SubElement(library, "Components")
    for module in pcb.modules:
        ref = [text.text for text in module.texts if text.text_type == TextType.reference][0]
        component = etree.SubElement(components, 'Component', name=ref)
        pins = etree.SubElement(component, 'Pins')
        for pad in module.pads:
            _ = etree.SubElement(pins, "Pin", pinNum=str(module.pads.index(pad)), name=pad.pad_id,
                                 pinSymName=pad.pad_id, pinEqual="0", gate="-1", gateEqual="0")

    packages = etree.SubElement(library, "Packages")
    for module in pcb.modules:
        ref = [text.text for text in module.texts if text.text_type == TextType.reference][0]
        package = etree.SubElement(packages, 'Package')
        _ = etree.SubElement(package, 'ComponentRef', name=ref)
        _ = etree.SubElement(package, 'FootprintRef', name=module.footprint + ' ' + ref)
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
    texts = etree.SubElement(constr, "Texts")
    for text in pcb.texts:
        text_tag = etree.SubElement(texts, "Text", text=text.text, angle=text.angle)
        _ = etree.SubElement(text_tag, 'LayerRef', name='F.Cu_outline' if 'F.' in text.layer.name else 'B.Cu_outline')
        name = "Logo" if 'Ostranna' in text.text else "Default"
        _ = etree.SubElement(text_tag, "TextStyleRef", name=name)
        _ = etree.SubElement(text_tag, 'Org', x=text.coords[0], y=text.coords[1])

    components_on_board = etree.SubElement(topor, 'ComponentsOnBoard', version='1.3')
    components = etree.SubElement(components_on_board, "Components")
    used_names = list()
    for module in pcb.modules:
        name = [text.text for text in module.texts if text.text_type == TextType.value][0]
        ref = [text.text for text in module.texts if text.text_type == TextType.reference][0]
        while name in used_names:
            name += " "
        used_names.append(name)
        comp_inst = etree.SubElement(components, 'CompInstance', name=name,
                                     uniqueId=''.join(random.choice(string.ascii_letters) for x in range(7)),
                                     side='Top' if 'F.' in module.layer.name else 'Bottom',
                                     angle=str(module.coords[2]) if len(module.coords) > 2 else '0',
                                     )
        _ = etree.SubElement(comp_inst, "ComponentRef", name=ref)
        _ = etree.SubElement(comp_inst, 'FootprintRef', name=module.footprint + ' ' + ref)
        _ = etree.SubElement(comp_inst, 'Org', x=str(module.coords[0]), y=str(module.coords[1]))

        attributes = etree.SubElement(comp_inst, 'Attributes')

        attribute = etree.SubElement(attributes, 'Attribute', type="RefDes")
        visible = 'off' if any([text in name for text in settings.setdefault("invisible_names", "")])else 'on'
        label = etree.SubElement(attribute, "Label", mirror='on' if'B.Cu' in module.layer.name else 'off',
                                 visible=visible, angle=str(get_label_angle(module, TextType.value)))
        ref_coords = [text.coords for text in module.texts if text.text_type == TextType.value][0]
        _ = etree.SubElement(label, "LayerRef", name='F.Cu_outline' if 'F.' in module.layer.name else 'B.Cu_outline')
        _ = etree.SubElement(label, "TextStyleRef", name="Default")
        _ = etree.SubElement(label, 'Org', x=str(ref_coords[0]), y=str(ref_coords[1]))

        attribute = etree.SubElement(attributes, 'Attribute', type="PartName")
        visible = 'off' if any([text in ref for text in settings.setdefault("invisible_names", "")]) else 'on'
        label = etree.SubElement(attribute, "Label", mirror='on' if 'B.Cu' in module.layer.name else 'off',
                                 visible=visible, angle=str(get_label_angle(module, TextType.reference)))
        ref_coords = [text.coords for text in module.texts if text.text_type == TextType.reference][0]
        _ = etree.SubElement(label, "LayerRef", name='F.Cu_outline' if 'F.' in module.layer.name else 'B.Cu_outline')
        _ = etree.SubElement(label, "TextStyleRef", name="Default")
        _ = etree.SubElement(label, 'Org', x=str(ref_coords[0]), y=str(ref_coords[1]))

    xml_tree = etree.ElementTree(topor)
    xml_tree.write('test.fst', xml_declaration=True, encoding="UTF-8", pretty_print=True)
