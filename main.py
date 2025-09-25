# main.py - Pyton v3.9.13
from dataclasses import dataclass, field
from enum import Enum
import re

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

class M32:
    @staticmethod
    def decode(file_path: str) -> MixerScene:
        # Helper parsers
        def parse_frequency(s: str) -> float:
            # support formats like '124.7', '1k97' (=>1970), '10k02' (=>10020)
            if not s:
                return 0.0
            s = s.strip()
            s_low = s.lower()
            if 'k' in s_low:
                # replace the first 'k' with '.' then multiply by 1000
                s2 = s_low.replace('k', '.', 1)
                try:
                    return float(s2) * 1000.0
                except ValueError:
                    pass
            try:
                return float(s)
            except ValueError:
                return 0.0

        def parse_level(s: str) -> float:
            if not s:
                return -90.0
            s = s.strip()
            if s in ('-oo', '-inf', '-\u221E'):
                return -90.0
            # remove + for numeric parse
            try:
                return float(s.replace('+', ''))
            except ValueError:
                # try to extract a number from the string
                m = re.search(r'[-+]?[0-9]*\.?[0-9]+', s)
                if m:
                    return float(m.group(0))
            return -90.0

        def map_eq_type(s: str) -> EqBandType:
            if not s:
                return EqBandType.PEQ
            t = s.lower()
            if t.startswith('peq') or t.startswith('veq'):
                return EqBandType.PEQ
            if 'h' in t and ('sh' in t or 'shv' in t or 'shelf' in t):
                return EqBandType.HIGH_SHELF
            if 'l' in t and ('sh' in t or 'shelf' in t):
                return EqBandType.LOW_SHELF
            if 'lcut' in t or t.startswith('lcut'):
                return EqBandType.LOW_CUT
            if 'hcut' in t or t.startswith('hcut'):
                return EqBandType.HIGH_CUT
            # fallback
            return EqBandType.PEQ

        def map_insert_type(s: str) -> InsertType:
            if not s:
                return InsertType.PRE_FADER
            t = s.upper()
            if 'PRE' in t or 'IN' in t:
                return InsertType.PRE_FADER
            return InsertType.POST_FADER

        scene = MixerScene.new()
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        for line in lines:
            s = line.strip()
            if not s:
                continue
            # header line with scene name usually starts with '#'
            if s.startswith('#'):
                m = re.search(r'"([^"]+)"', s)
                if m:
                    scene.name = m.group(1)
                continue

            if not s.startswith('/ch/'):
                continue

            tokens = s.split()
            path = tokens[0]
            path_parts = path.strip('/').split('/')
            if len(path_parts) < 3 or path_parts[0] != 'ch':
                continue
            try:
                channel_index = int(path_parts[1]) - 1
            except ValueError:
                continue
            if channel_index < 0 or channel_index >= len(scene.input_channels.channels):
                continue
            channel = scene.input_channels.channels[channel_index]

            prop = path_parts[2]
            rest = s[len(path):].strip()

            # config: contains quoted channel name
            if prop == 'config':
                m = re.search(r'config\s+"([^"]+)"', s)
                if m:
                    channel.name = m.group(1)
                else:
                    # fallback: take next token without quotes
                    if len(tokens) > 1:
                        channel.name = tokens[1].strip('"')

            elif prop == 'preamp':
                # try to find first numeric = gain, last numeric = low_cut_freq (if any)
                nums = re.findall(r'[-+]?[0-9]*\.?[0-9]+', s)
                if nums:
                    try:
                        channel.gain = float(nums[0])
                    except Exception:
                        pass
                    # last numeric value often corresponds to low-cut frequency
                    try:
                        channel.low_cut_filter_frequency = float(nums[-1])
                    except Exception:
                        pass
                # whether any ON appears after preamp likely indicates low_cut present
                channel.low_cut_filter = 'ON' in s

            elif prop == 'eq':
                # top-level eq on/off
                if len(path_parts) == 3:
                    channel.equalizer_enabled = ('ON' in rest)
                # specific band: /ch/01/eq/1 ...
                elif len(path_parts) == 4:
                    try:
                        band_index = int(path_parts[3]) - 1
                    except ValueError:
                        continue
                    if band_index < 0 or band_index >= 4:
                        continue
                    tokens_rest = rest.split()
                    if not tokens_rest:
                        continue
                    typ = tokens_rest[0]
                    freq = tokens_rest[1] if len(tokens_rest) > 1 else ''
                    gain = tokens_rest[2] if len(tokens_rest) > 2 else ''
                    width = tokens_rest[3] if len(tokens_rest) > 3 else ''
                    band = channel.equalizer.bands[band_index]
                    band.type = map_eq_type(typ)
                    band.frequency = parse_frequency(freq) if freq else band.frequency
                    band.gain = parse_level(gain) if gain else band.gain
                    try:
                        band.width = float(width)
                    except Exception:
                        pass

            elif prop == 'pan':
                tokens_rest = rest.split()
                if tokens_rest:
                    p = parse_level(tokens_rest[0])
                    # assume pan is -100..100 -> convert to -1..1
                    channel.pan = max(-1.0, min(1.0, p / 100.0))

            elif prop == 'mix':
                # either a summary line (/ch/01/mix) or a send (/ch/01/mix/01)
                if len(path_parts) == 4:
                    try:
                        send_index = int(path_parts[3]) - 1
                    except ValueError:
                        continue
                    if send_index < 0 or send_index >= len(channel.bus_sends.sends):
                        continue
                    tokens_rest = rest.split()
                    if not tokens_rest:
                        continue
                    is_muted = tokens_rest[0] == 'OFF'
                    fader = parse_level(tokens_rest[1]) if len(tokens_rest) > 1 else -90.0
                    insert_token = tokens_rest[3] if len(tokens_rest) > 3 else ''
                    send = channel.bus_sends.sends[send_index]
                    send.is_muted = is_muted
                    send.level = fader
                    send.type = map_insert_type(insert_token)

            elif prop == 'fader':
                tokens_rest = rest.split()
                if tokens_rest:
                    channel.fader = parse_level(tokens_rest[0])

        return scene


if __name__ == '__main__':
    # simple smoke test/demo using bundled sample file
    try:
        scene = M32.decode('m32Exsample.scn')
        print('Scene name:', scene.name)
        ch0 = scene.input_channels.channels[0]
        print('Channel 1 name:', ch0.name)
        print('Channel 1 gain:', ch0.gain)
        print('Channel 1 low cut enabled:', ch0.low_cut_filter)
        print('Channel 1 low cut freq:', ch0.low_cut_filter_frequency)
        print('Channel 1 EQ enabled:', ch0.equalizer_enabled)
        for i, b in enumerate(ch0.equalizer.bands, start=1):
            print(f'  EQ band {i}: type={b.type}, freq={b.frequency}, gain={b.gain}, q={b.width}')
    except Exception as e:
        print('Error running demo:', e)