from mahjong_engine.adapters.base import MahjongEngineAdapter
from mahjong_engine.domain.meld import Meld
from mahjong_engine.domain.tile import PhysicalTile


class ShantenCalculator:
    def __init__(self, adapter: MahjongEngineAdapter) -> None:
        self._adapter = adapter

    def calculate(self, hand: list[PhysicalTile], melds: list[Meld]) -> int:
        return self._adapter.calculate_shanten(hand, melds)

    def calculate_after_discard(
        self, hand: list[PhysicalTile], discard: PhysicalTile, melds: list[Meld]
    ) -> int:
        next_hand = [t for t in hand if t is not discard]
        return self._adapter.calculate_shanten(next_hand, melds)
