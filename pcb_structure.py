from dataclasses import dataclass
from typing import Tuple, List
from enum import Enum


Layer = str
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
class FpText:
    text_type: TextType
    layer: Layer
    coords: Tuple[float, float]


@dataclass
class FpLine:
    start: Coords
    End: Coords
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
    pad_type: PadType
    center: FpPos
    size: Coords
    drill: int
    layers: List[Layer]
    net_id: int
    net_name: str


@dataclass
class Module:
    name: str
    layer: Layer
    coords: Coords
    descr: str
    smd: bool
    texts: List[FpText]
    lines: List[FpLine]
    pads: List[FpPad]



