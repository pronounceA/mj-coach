from mahjong_engine.domain.rule_profile import RuleProfile
from mahjong_engine.domain.tile import PhysicalTile, Suit, TileType, TileVariant

_HONOR_NEXT = {1: 2, 2: 3, 3: 4, 4: 1, 5: 6, 6: 7, 7: 5}


def _next_tile_type(tile_type: TileType) -> TileType:
    """ドラ表示牌から実際のドラ牌を返す。"""
    if tile_type.suit == Suit.HONOR:
        return TileType(suit=Suit.HONOR, rank=_HONOR_NEXT[tile_type.rank])
    next_rank = tile_type.rank % 9 + 1
    return TileType(suit=tile_type.suit, rank=next_rank)


class DoraCalculator:
    def __init__(self, rule: RuleProfile) -> None:
        self._rule = rule

    def count_dora(
        self,
        hand: list[PhysicalTile],
        melds_tiles: list[PhysicalTile],
        dora_indicators: list[PhysicalTile],
    ) -> dict:
        all_tiles = hand + melds_tiles
        dora_types = {_next_tile_type(d.tile_type) for d in dora_indicators}

        normal_dora = sum(1 for t in all_tiles if t.tile_type in dora_types)

        red_dora = sum(
            self._rule.red_tile.han
            for t in all_tiles
            if t.variant == TileVariant.RED
        )

        blue_dora = sum(
            self._rule.blue_tile.han
            for t in all_tiles
            if t.variant == TileVariant.BLUE
        )

        return {
            "normal_dora": normal_dora,
            "red_dora": red_dora,
            "blue_dora": blue_dora,
            "total_dora_han": normal_dora + red_dora + blue_dora,
        }
