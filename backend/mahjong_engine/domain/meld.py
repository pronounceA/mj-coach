from dataclasses import dataclass
from enum import Enum

from mahjong_engine.domain.tile import PhysicalTile


class MeldType(str, Enum):
    CHI = "chi"
    PON = "pon"
    KAN_OPEN = "kan_open"
    KAN_CLOSED = "kan_closed"
    KAN_ADDED = "kan_added"


@dataclass(frozen=True)
class Meld:
    meld_type: MeldType
    tiles: tuple[PhysicalTile, ...]
    stolen_from: int  # 0〜3: どの座席から鳴いたか（カンクローズは自分の座席）
