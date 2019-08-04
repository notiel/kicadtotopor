from dataclasses import dataclass
from typing import Tuple, List, Union
from enum import Enum


Coords = Tuple[float, float]

class TextType(Enum):
    reference = 0
    value = 1
    user = 2
    simple = 3


class PadType(Enum):
    circle = 0
    rect = 1
    oval = 2


@dataclass
class Layer:
    name: str
    layer_type: str


@dataclass
class FpText:
    text_type: TextType
    text: str
    layer: Layer
    coords: Tuple[float, float]
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
    width: float
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


@dataclass
class Module:
    footprint: str
    layer: Layer
    coords: Coords
    smd: bool
    texts: List[FpText]
    figures: List[Union[FpLine, FpCircle, FpPoly, FpArc]]
    pads: List[FpPad]


@dataclass
class PCB:
    layers: List[Layer]
    modules: List[Module]
    edge: List[Union[FpLine, FpArc]]
    texts: List[FpText]
