from collections import defaultdict
from datetime import datetime, time
from enum import Enum
from pprint import pprint
from typing import Iterable

import pydantic
from dateutil import parser

DIGITAL_MODES = ("JS8",)
PHONE_MODES = (
    "SSB",
    "FM",
)
CW_MODES = ("CW",)


class Band(Enum):
    ONE_SIXTY = "160M"
    EIGHTY = "80M"
    # Sixty = "60M"
    FORTY = "40M"
    # Thirty = "30M"
    TWENTY = "20M"
    # Seventeen = "17M"
    FIFTEEN = "15M"
    # Twelve = "12M"
    TEN = "10M"
    SIX = "6M"
    TWO = "2M"
    SEVENTY_CM = "70CM"


BAND_LOOKUP = {band.value: band for band in Band}


class Mode(Enum):
    CW = "CW"
    Phone = "PHONE"
    Digital = "DIGITAL"


class PowerOutput(Enum):
    QRP_CW = 5
    QRP_DIGITAL = 5
    QRP_PHONE = 10


class Category(Enum):
    HOME = "HOME"
    INDOOR = "INDOOR"
    OUTDOOR = "OUTDOOR"
    MOBILE = "MOBILE"


class StationExchange(pydantic.BaseModel):
    class_: int = pydantic.Field(ge=1)
    category: Category
    location: str


class LogLine(pydantic.BaseModel):
    band: Band
    callsign: str
    exchange: StationExchange
    timestamp: datetime | time
    mode: Mode
    # power: int = pydantic.Field(ge=1, le=100)


def _freq_to_band(freq: str) -> Band:
    if freq.startswith("1."):
        return Band.ONE_SIXTY
    elif freq.startswith("3."):
        return Band.EIGHTY
    elif freq.startswith("7."):
        return Band.FORTY
    elif freq.startswith("14."):
        return Band.TWENTY
    elif freq.startswith("21."):
        return Band.FIFTEEN
    elif freq.startswith("28.") or freq.startswith("29."):
        return Band.TEN
    elif (
        freq.startswith("50.")
        or freq.startswith("51.")
        or freq.startswith("52.")
        or freq.startswith("53.")
        or freq.startswith("54")
    ):
        return Band.SIX
    elif (
        freq.startswith("144.")
        or freq.startswith("145.")
        or freq.startswith("146.")
        or freq.startswith("147.")
        or freq.startswith("148.")
    ):
        return Band.TWO
    elif freq.startswith("42"):
        return Band.SEVENTY_CM

    raise ValueError(f"Invalid frequency: {freq}")


def _raw_category_to_category(cat: str) -> Category:
    lookup = {
        "H": Category.HOME,
        "I": Category.INDOOR,
        "O": Category.OUTDOOR,
        "M": Category.MOBILE,
    }

    return lookup[cat]


def _raw_mode_to_mode(mode: str) -> Mode:
    if mode in CW_MODES:
        return Mode.CW
    elif mode in DIGITAL_MODES:
        return Mode.Digital
    elif mode in PHONE_MODES:
        return Mode.Phone

    raise ValueError(f"Invalid mode: {mode}")


def score_lines(lines: Iterable[LogLine], power: int) -> float:
    # Total Score = (# of QSOs x POM x B/MM)
    worked_bands: set[tuple[Band, Mode]] = set()
    unique_qsos: set[tuple[Band, Mode, str]] = set()

    # TODO: fix this
    if power <= max(
        [
            PowerOutput.QRP_CW.value,
            PowerOutput.QRP_DIGITAL.value,
            PowerOutput.QRP_PHONE.value,
        ]
    ):
        power_multiplier = 2.0
    else:
        power_multiplier = 1.0

    for line in lines:
        worked_bands.add((line.band, line.mode))
        unique_qsos.add((line.band, line.mode, line.callsign))

    cw_digital_qsos = [
        (band.value, mode.value, callsign)
        for band, mode, callsign in unique_qsos
        if mode == Mode.CW or mode == Mode.Digital
    ]

    phone_qsos = [
        (band.value, mode.value, callsign)
        for band, mode, callsign in unique_qsos
        if mode == Mode.Phone
    ]

    num_bands = len(worked_bands)
    num_cw_digital_qsos = len(cw_digital_qsos)
    num_phone_qsos = len(phone_qsos)
    score = (num_cw_digital_qsos * 2 + num_phone_qsos) * power_multiplier * num_bands

    print(f"worked_bans={len(worked_bands)}")
    pprint(worked_bands)
    print()
    print(f"cw_digital_qsos={len(cw_digital_qsos)}")
    pprint(cw_digital_qsos)
    print()
    print(f"phone_qsos={len(phone_qsos)}")
    pprint(phone_qsos)

    print(f"{num_cw_digital_qsos=} {num_phone_qsos=}")
    print(
        f"# QSOs ({num_cw_digital_qsos} * 2 + {num_phone_qsos}) * power multiplier {power_multiplier} * # band multiplier {num_bands} = {score}"
    )
    return score


def parse_line(line: str, delimiter: str | None = None) -> LogLine:
    chunks = line.split(delimiter)

    if len(chunks) == 5:
        raw_band, callsign, raw_exchange, raw_time, raw_mode = chunks
    else:
        raise ValueError(f"Invalid format: {line}")

    raw_class, raw_category, *raw_location = list(raw_exchange)

    exchange = StationExchange(
        class_=int(raw_class),
        category=_raw_category_to_category(cat=raw_category),
        location="".join(raw_location),
    )

    try:
        band = _freq_to_band(raw_band)
    except ValueError:
        band = BAND_LOOKUP[raw_band]

    mode = _raw_mode_to_mode(raw_mode)

    timestamp = parser.parse(raw_time)

    return LogLine(
        band=band,
        callsign=callsign,
        exchange=exchange,
        timestamp=timestamp,
        mode=mode,
    )
