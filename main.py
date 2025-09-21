# main.py - Pyton v3.9.13
from dataclasses import dataclass
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
    
    def set_band(self, index: int, *, type: EqBandType = None,
     frequency: float = None, gain: float = None, width: float = None):
        """Update parameters of one EQ band by index (0–3)."""
        if not (0 <= index < 4):
            raise IndexError("Band index out of range (0–3)")

        band = self.bands[index]

        if type is not None: band.type = type
        if frequency is not None: band.frequency = frequency
        if gain is not None: band.gain = gain
        if width is not None: band.width = width

@dataclass
class InputChannel:
    name: str = ""
    gain: float = 30.0 #dB
    low_cut_filter: bool = False
    low_cut_filter_frequency: float = 100.0 #Hz
    is_muted: bool = False
    equalizer: FourBandEqualizer = FourBandEqualizer((
        EqulizerBand(),
    pan: float = 0.0 # -1.0 (left) to 1.0 (right)
    fader: float = 0.0 #dB
    
