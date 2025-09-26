# main.py - Pyton v3.9.13
from dataclasses import dataclass, field, asdict
from enum import Enum
import re
import json
from typing import Any, Dict, List, Optional, Tuple, cast

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
    
    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable dict representation of the MixerScene.

        Enums are converted to their values and tuples are converted to lists.
        """
        def _convert(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {k: _convert(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_convert(v) for v in obj]
            if isinstance(obj, tuple):
                return [_convert(v) for v in obj]
            if isinstance(obj, Enum):
                return obj.value
            return obj

        raw: Dict[str, Any] = asdict(self)
        return cast(Dict[str, Any], _convert(raw))

    def save_json(self, file_path: str, *, indent: int = 2) -> None:
        """Save the scene as JSON to the given file path.

        Uses UTF-8 and writes human-friendly indented JSON.
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MixerScene':
        """Reconstruct a MixerScene from a dict (produced by to_dict)."""
        name = data.get('name', '')

        # Input channels
        channels: List[InputChannel] = []
        ic_any = data.get('input_channels')
        ic: Optional[Dict[str, Any]] = ic_any if isinstance(ic_any, dict) else None

        ch_list: Optional[List[Any]] = None
        if ic is not None:
            ch_list_any = ic.get('channels')
            if isinstance(ch_list_any, list):
                ch_list = ch_list_any

        if ch_list is not None:
            for chd_any in ch_list:
                if not isinstance(chd_any, dict):
                    continue
                chd = cast(Dict[str, Any], chd_any)

                # initialize defaults so static analysis knows variables exist
                ch_name: str = ''
                gain: float = 30.0
                low_cut_filter: bool = False
                low_cut_filter_frequency: float = 100.0
                is_muted: bool = False
                equalizer_enabled: bool = False
                pan: float = 0.0
                fader: float = 0.0
                sends: Sends = Sends.new()
                bands_objs: List[EqualizerBand] = []

                name_val = chd.get('name', '')
                if isinstance(name_val, str):
                    ch_name = name_val

                # safe numeric conversions with fallbacks
                try:
                    gain = float(chd.get('gain', 30.0))
                except Exception:
                    gain = 30.0
                low_cut_filter = bool(chd.get('low_cut_filter', False))
                try:
                    low_cut_filter_frequency = float(chd.get('low_cut_filter_frequency', 100.0))
                except Exception:
                    low_cut_filter_frequency = 100.0
                is_muted = bool(chd.get('is_muted', False))
                equalizer_enabled = bool(chd.get('equalizer_enabled', False))
                try:
                    pan = float(chd.get('pan', 0.0))
                except Exception:
                    pan = 0.0
                try:
                    fader = float(chd.get('fader', 0.0))
                except Exception:
                    fader = 0.0

                # bus sends
                sends_objs: List[Send] = []
                bus_sends = chd.get('bus_sends')
                if isinstance(bus_sends, dict):
                    bus_sends = cast(Dict[str, Any], bus_sends)
                    s_list = bus_sends.get('sends')
                else:
                    s_list = None
                if isinstance(s_list, list):
                    for sd in s_list:
                        if not isinstance(sd, dict):
                            continue
                        sd = cast(Dict[str, Any], sd)
                        s_muted = bool(sd.get('is_muted', False))
                        try:
                            s_level = float(sd.get('level', -90.0))
                        except Exception:
                            s_level = -90.0
                        s_type_raw = sd.get('type', InsertType.PRE_FADER.value)
                        try:
                            s_type = InsertType(s_type_raw)
                        except Exception:
                            s_type = InsertType.PRE_FADER
                        sends_objs.append(Send(is_muted=s_muted, type=s_type, level=s_level))
                sends = Sends(sends=sends_objs + [Send.new() for _ in range(max(0, 16 - len(sends_objs)))])

                # equalizer
                eq = chd.get('equalizer')
                if isinstance(eq, dict):
                    eq = cast(Dict[str, Any], eq)
                    b_list = eq.get('bands')
                else:
                    b_list = None
                if isinstance(b_list, list):
                    for bd in b_list:
                        if not isinstance(bd, dict):
                            continue
                        bd = cast(Dict[str, Any], bd)
                        b_type_raw = bd.get('type', EqBandType.PEQ.value)
                        try:
                            b_type = EqBandType(b_type_raw)
                        except Exception:
                            b_type = EqBandType.PEQ
                        try:
                            b_freq = float(bd.get('frequency', 1000.0))
                        except Exception:
                            b_freq = 1000.0
                        try:
                            b_gain = float(bd.get('gain', 0.0))
                        except Exception:
                            b_gain = 0.0
                        try:
                            b_width = float(bd.get('width', 2.0))
                        except Exception:
                            b_width = 2.0
                        bands_objs.append(EqualizerBand(type=b_type, frequency=b_freq, gain=b_gain, width=b_width))
                # ensure 4 bands
                while len(bands_objs) < 4:
                    bands_objs.append(EqualizerBand.new())
                # construct a 4-tuple explicitly so typing is satisfied
                bands_tuple: Tuple[EqualizerBand, EqualizerBand, EqualizerBand, EqualizerBand] = (
                    bands_objs[0], bands_objs[1], bands_objs[2], bands_objs[3]
                )
                equalizer = FourBandEqualizer(bands=bands_tuple)

                ch = InputChannel(
                    name=ch_name,
                    gain=gain,
                    low_cut_filter=low_cut_filter,
                    low_cut_filter_frequency=low_cut_filter_frequency,
                    is_muted=is_muted,
                    equalizer=equalizer,
                    equalizer_enabled=equalizer_enabled,
                    pan=pan,
                    bus_sends=sends,
                    fader=fader,
                )
                channels.append(ch)

        # pad to 32 channels
        while len(channels) < 32:
            channels.append(InputChannel())

        input_channels = InputChannels(channels=channels[:32])
        return cls(name=name, input_channels=input_channels)

    @classmethod
    def load_json(cls, file_path: str) -> 'MixerScene':
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)

    def save_m32(self, file_path: str) -> None:
        """Save a minimal M32 .scn file representing this MixerScene.

        This writes a simple textual representation compatible with the decoder in this
        repository. It intentionally writes only a small subset (header + per-channel
        config, preamp, eq and mix/send lines) to keep the encoder compact and safe.
        """
        lines: list[str] = []
        # header: version and scene name
        lines.append('#4.0# "{}" "" %000000000 1'.format(self.name or 'Scene'))

        for idx, ch in enumerate(self.input_channels.channels, start=1):
            prefix = f'/ch/{idx:02d}'
            # config line with name
            lines.append(f'{prefix}/config "{ch.name}" 1 WH {idx}')
            # preamp: gain, low_cut presence and frequency
            low_cut_flag = 'ON' if ch.low_cut_filter else 'OFF'
            lines.append(f'{prefix}/preamp {ch.gain:+.1f} OFF {low_cut_flag} 24  {int(ch.low_cut_filter_frequency)}')
            # eq on/off
            eq_on = 'ON' if ch.equalizer_enabled else 'OFF'
            lines.append(f'{prefix}/eq {eq_on}')
            # eq bands
            def fmt_freq_human(hz: float) -> str:
                """Format frequency for M32 .scn files.

                Preserve the compact k-notation the original files use:
                - <1000 Hz: integer if whole, else one decimal (e.g. 124.7)
                - >=1000 and <100000: show as '1k97' for 1970, '10k02' for 10020
                  (two significant digits from the remainder, preserving leading zeroes)
                - Fallback: one decimal when not integer.
                """
                try:
                    hz_f = float(hz)
                except Exception:
                    return str(hz)
                # below 1000 Hz
                if hz_f < 1000.0:
                    if hz_f.is_integer():
                        return str(int(hz_f))
                    return f'{hz_f:.1f}'
                # k-notation: keep two digits from remainder but trim a trailing zero
                if 1000.0 <= hz_f < 100000.0:
                    k = int(hz_f // 1000)
                    rem = int(round(hz_f - k * 1000))
                    # clamp rem to [0,999]
                    rem = max(0, min(999, rem))
                    # Format remainder as 3 digits then strip a trailing zero if present
                    # so 1970 -> '1k97' (rem=970 -> '970' -> strip trailing '0' -> '97')
                    rem_str_3 = f'{rem:03d}'
                    if rem_str_3.endswith('0'):
                        rem_str = rem_str_3[:-1]
                    else:
                        rem_str = rem_str_3
                    return f'{k}k{rem_str}'
                # fallback
                if hz_f.is_integer():
                    return str(int(hz_f))
                return f'{hz_f:.1f}'

            for b_idx, band in enumerate(ch.equalizer.bands, start=1):
                # map type to the short tokens used by M32 .scn files
                def eq_type_token(bt: EqBandType) -> str:
                    if bt == EqBandType.PEQ:
                        return 'PEQ'
                    if bt == EqBandType.HIGH_SHELF:
                        return 'HShv'
                    if bt == EqBandType.LOW_SHELF:
                        return 'LShv'
                    if bt == EqBandType.LOW_CUT:
                        return 'LCut'
                    if bt == EqBandType.HIGH_CUT:
                        return 'HCut'
                    return 'PEQ'

                t = eq_type_token(band.type)
                freq = fmt_freq_human(band.frequency)
                # preserve single-decimal for gain when integer-like but keep +/-, and width one decimal
                gain_str = f'{band.gain:+.2f}' if (abs(band.gain) < 100 and (band.gain != int(band.gain))) else f'{band.gain:+.1f}'
                lines.append(f'{prefix}/eq/{b_idx} {t} {freq} {gain_str} {band.width:.1f}')

            # mix summary (write fader and ON). Preserve '-oo' when fader indicates -90.0 sentinel.
            fader_str = '-oo' if ch.fader <= -90.0 else f'{ch.fader:+.1f}'
            lines.append(f'{prefix}/mix ON {fader_str} ON +0 OFF   -oo')
            # sends
            for s_idx, send in enumerate(ch.bus_sends.sends, start=1):
                is_on = 'ON' if not send.is_muted else 'OFF'
                try:
                    level = float(send.level)
                except Exception:
                    level = -90.0
                # preserve -oo marker for very low levels
                level_str = '-oo' if level <= -90.0 else f'{level:+.1f}'
                insert = 'PRE' if send.type == InsertType.PRE_FADER else 'POST'
                lines.append(f'{prefix}/mix/{s_idx} {is_on} {level_str} {"+0"} {insert} 0')

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')

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

    @staticmethod
    def encode(scene: MixerScene, file_path: str) -> None:
        """Encode a MixerScene to a minimal .scn file by delegating to MixerScene.save_m32.

        Kept as a convenience to mirror the decode API.
        """
        scene.save_m32(file_path)


if __name__ == '__main__':
    # Launch the GUI if possible, otherwise do nothing.
    try:
        # local import to avoid requiring tkinter for library use
        from gui import run_gui
        run_gui()
    except Exception:
        # If GUI cannot be started (no tkinter, headless, etc.), do nothing.
        pass