from dataclasses import dataclass

from enum import Enum

class BandType(Enum):
    PEQ = "peq"
    LOW_SHELF = "low_shelf"
    HIGH_SHELF = "high_shelf"

@dataclass
class EqulizerBand:
    type: any # peq, low_shelf, high_shelf
    frequency: float
    gain: float
    width: float

@dataclass
class FourBandEqualizer:
    bands: tuple[EqulizerBand]

@dataclass
class InputChannel:
    name: str
    gain: float
    low_cut_filter: bool
    low_cut_filter_frequency: float
    is_muted: bool
    equalizer: FourBandEqualizer
