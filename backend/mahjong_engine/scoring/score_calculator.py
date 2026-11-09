from mahjong_engine.adapters.base import MahjongEngineAdapter
from mahjong_engine.domain.meld import Meld
from mahjong_engine.domain.rule_profile import RuleProfile
from mahjong_engine.domain.tile import PhysicalTile, TileVariant


class ScoreCalculator:
    def __init__(self, adapter: MahjongEngineAdapter) -> None:
        self._adapter = adapter

    def calculate(
        self,
        hand: list[PhysicalTile],
        win_tile: PhysicalTile,
        melds: list[Meld],
        context: dict,
        rule: RuleProfile,
    ) -> dict:
        aka_dora_count = sum(
            1 for t in hand + [win_tile] if t.is_red()
        )
        context = {**context, "aka_dora_count": aka_dora_count}

        result = self._adapter.calculate_score(hand, win_tile, melds, context)
        if "error" in result:
            return result

        blue_tiles = [t for t in hand + [win_tile] if t.is_blue()]
        blue_han = len(blue_tiles) * rule.blue_tile.han
        result["han"] = result.get("han", 0) + blue_han
        result["blue_tile_count"] = len(blue_tiles)

        if rule.blue_tile.chip_enabled and blue_tiles:
            result["chip_count"] = len(blue_tiles) * rule.blue_tile.chips_per_blue_tile
        else:
            result["chip_count"] = 0

        return result
