# main.py - Pyton v3.9.13
from dataclasses import dataclass, field
from enum import Enum

class EqBandType(Enum):
    PEQ = "peq"
    LOW_SHELF = "low_shelf"
    HIGH_SHELF = "high_shelf"
    LOW_CUT = "low_cut"
    HIGH_CUT = "high_cut"

@dataclass
class EqualizerBand:
    type: EqBandType = EqBandType.PEQ
    frequency: float = 1000.0 #Hz
    gain: float = 0.0 #dB
    width: float = 2.0 #Q

@dataclass
class FourBandEqualizer:
    bands: tuple[EqualizerBand, EqualizerBand, EqualizerBand, EqualizerBand] = field(default_factory=lambda: (
        EqualizerBand(),
        EqualizerBand(),
        EqualizerBand(),
        EqualizerBand(),
    ))

@dataclass
class InputChannel:
    name: str = ""
    gain: float = 30.0 #dB
    low_cut_filter: bool = False
    low_cut_filter_frequency: float = 100.0 #Hz
    is_muted: bool = False
    equalizer: FourBandEqualizer = FourBandEqualizer()
    pan: float = 0.0 # -1.0 (left) to 1.0 (right)
    fader: float = 0.0 #dB
    
