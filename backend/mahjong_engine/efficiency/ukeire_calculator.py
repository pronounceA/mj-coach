from mahjong_engine.adapters.base import MahjongEngineAdapter
from mahjong_engine.domain.game_state import GameState
from mahjong_engine.domain.meld import Meld
from mahjong_engine.domain.rule_profile import RuleProfile
from mahjong_engine.domain.tile import PhysicalTile, Suit, TileType, TileVariant


def build_remaining(game_state: GameState, rule: RuleProfile) -> dict[str, int]:
    """ルールと既知牌から、各牌種の残り枚数を計算する。"""
    known = game_state.all_known_tiles()

    total: dict[str, int] = {}
    for suit in [Suit.MAN, Suit.PIN, Suit.SOU]:
        for rank in range(1, 10):
            tt = TileType(suit=suit, rank=rank)
            key = str(tt)
            if rank == 5:
                total[key] = rule.normal_count_per_suit()
            else:
                total[key] = 4

    for tile in known:
        key = str(tile.tile_type)
        if key in total:
            total[key] = max(0, total[key] - 1)

    return total


class UkeireCalculator:
    def __init__(self, adapter: MahjongEngineAdapter) -> None:
        self._adapter = adapter

    def calculate(
        self,
        hand: list[PhysicalTile],
        melds: list[Meld],
        game_state: GameState,
        rule: RuleProfile,
    ) -> list[dict]:
        remaining = build_remaining(game_state, rule)
        return self._adapter.calculate_ukeire(hand, melds, remaining)

    def calculate_after_discard(
        self,
        hand: list[PhysicalTile],
        discard: PhysicalTile,
        melds: list[Meld],
        game_state: GameState,
        rule: RuleProfile,
    ) -> list[dict]:
        next_hand = [t for t in hand if t is not discard]
        remaining = build_remaining(game_state, rule)
        return self._adapter.calculate_ukeire(next_hand, melds, remaining)
