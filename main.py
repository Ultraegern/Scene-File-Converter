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

    @classmethod
    def new(cls):
        return cls()

@dataclass
class FourBandEqualizer:
    bands: tuple[EqualizerBand, EqualizerBand, EqualizerBand, EqualizerBand] = field(default_factory=lambda: (
        EqualizerBand(),
        EqualizerBand(),
        EqualizerBand(),
        EqualizerBand(),
    ))

    @classmethod
    def new(cls):
        return cls(bands=(
            EqualizerBand.new(),
            EqualizerBand.new(),
            EqualizerBand.new(),
            EqualizerBand.new()
        ))

class InsertType(Enum):
    PRE_FADER = "pre_fader"
    POST_FADER = "post_fader"

@dataclass
class Send:
    is_muted: bool = False
    type: InsertType = InsertType.PRE_FADER
    level: float = -90.0 #dB

    @classmethod
    def new(cls):
        return cls()

@dataclass
class Sends:
    sends: list[Send] = field(default_factory=lambda: [Send() for _ in range(16)])

    @classmethod
    def new(cls):
        return cls(sends=[Send.new() for _ in range(16)])

@dataclass
class InputChannel:
    name: str = ""
    gain: float = 30.0 #dB
    low_cut_filter: bool = False
    low_cut_filter_frequency: float = 100.0 #Hz
    is_muted: bool = False
    equalizer: FourBandEqualizer = field(default_factory=FourBandEqualizer.new)
    equalizer_enabled: bool = False
    pan: float = 0.0 # -1.0 (left) to 1.0 (right)
    bus_sends: Sends = field(default_factory=Sends.new)
    fader: float = 0.0 #dB

@dataclass
class InputChannels:
    channels: list[InputChannel] = field(default_factory=lambda: [InputChannel() for _ in range(32)])

    @classmethod
    def new(cls):
        return cls(channels=[InputChannel() for _ in range(32)])

@dataclass
class MixerScene:
    name: str = ""
    input_channels: InputChannels = field(default_factory=InputChannels.new)

    @classmethod
    def new(cls):
        return cls(name="", input_channels=InputChannels.new())
