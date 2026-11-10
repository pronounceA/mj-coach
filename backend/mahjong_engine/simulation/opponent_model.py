from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class OpponentType(str, Enum):
    RANDOM = "random"
    BASIC = "basic"
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"


@dataclass(frozen=True)
class OpponentStats:
    win_rate: float
    avg_win_score: int
    deal_in_rate: float


_STATS: dict[OpponentType, OpponentStats] = {
    OpponentType.RANDOM: OpponentStats(
        win_rate=0.12, avg_win_score=4000, deal_in_rate=0.20
    ),
    OpponentType.BASIC: OpponentStats(
        win_rate=0.20, avg_win_score=5000, deal_in_rate=0.14
    ),
    OpponentType.AGGRESSIVE: OpponentStats(
        win_rate=0.24, avg_win_score=7000, deal_in_rate=0.18
    ),
    OpponentType.DEFENSIVE: OpponentStats(
        win_rate=0.17, avg_win_score=4500, deal_in_rate=0.08
    ),
}


def get_opponent_stats(opp_type: str) -> OpponentStats:
    try:
        t = OpponentType(opp_type)
    except ValueError:
        t = OpponentType.BASIC
    return _STATS[t]
