from dataclasses import dataclass
from typing import Tuple, List
from enum import Enum


Coords = Tuple[int, int]


class TextType(Enum):
    reference = 0
    value = 1
    user = 2


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


@dataclass
class FpLine:
    start: Coords
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
    lines: List[FpLine]
    pads: List[FpPad]


@dataclass
class PCB:
    layers: List[Layer]
    modules: List[Module]
    edge: List[Union[FpLine, FpArc]]
