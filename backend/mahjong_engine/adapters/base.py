from abc import ABC, abstractmethod

from mahjong_engine.domain.meld import Meld
from mahjong_engine.domain.tile import PhysicalTile


class MahjongEngineAdapter(ABC):
    @abstractmethod
    def calculate_shanten(
        self, hand: list[PhysicalTile], melds: list[Meld]
    ) -> int: ...

    @abstractmethod
    def calculate_ukeire(
        self, hand: list[PhysicalTile], melds: list[Meld], remaining: dict
    ) -> list[dict]: ...

    @abstractmethod
    def calculate_score(
        self, hand: list[PhysicalTile], win_tile: PhysicalTile, melds: list[Meld], context: dict
    ) -> dict: ...
