from dataclasses import dataclass
from typing import Tuple, List, Union
from enum import Enum


Coords = List[str]
FpFigure = Union['FpArc', 'FpPoly', 'FpLine', 'FpCircle']


class TextType(Enum):
    reference = 0
    value = 1
    user = 2
    simple = 3


class PadType(Enum):
    circle = 0
    rect = 1
    oval = 2
    custom = 3


@dataclass
class Layer:
    name: str
    layer_type: str


@dataclass
class FpText:
    text_type: TextType
    text: str
    layer: Layer
    coords: List[str]
    angle: float


@dataclass
class FpLine:
    start: Coords
    end: Coords
    layer: Layer
    width: float


@dataclass
class FpPoly:
    layer: Layer
    width: str
    points: List[Coords]


@dataclass
class FpCircle:
    center: Coords
    end: Coords
    layer: Layer
    width: float


@dataclass
class FpArc:
    start: Coords
    end: Coords
    angle: float
    layer: Layer
    width: float


@dataclass
class FpPos:
    pos: Coords
    rot: int


@dataclass
class FpPad:
    pad_id: str
    smd: bool
    drill: float
    pad_type: PadType
    center: FpPos
    size: Coords
    layers: List[Layer]
    net_id: int
    net_name: str
    extra_points: List[Coords]


@dataclass
class Module:
    footprint: str
    layer: Layer
    coords: Coords
    smd: bool
    texts: List[FpText]
    figures: List[FpFigure]
    pads: List[FpPad]
    extrapads: List[str]


@dataclass
class NetGroup:
    name: str
    clearance: float
    trace_width: float
    via_dia: float
    via_drill: float


@dataclass
class Segment:
    start: Coords
    end: Coords
    layers: List[Layer]
    width: str


@dataclass
class Via:
    center: Coords
    layers: List[Layer]
    size: str


@dataclass
class Net:
    net_id: int
    net_name: str
    contacts: List[Tuple[str, str]]
    segments: List[Segment]
    vias: List[Via]
    group: str = ""


@dataclass
class PCB:
    layers: List[Layer]
    modules: List[Module]
    edge: List[Union[FpLine, FpArc]]
    texts: List[FpText]
    nets: List[Net]
    net_groups: List[NetGroup]

