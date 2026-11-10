from __future__ import annotations

from mahjong_engine.adapters.base import MahjongEngineAdapter
from mahjong_engine.domain.game_state import GameState
from mahjong_engine.domain.meld import Meld
from mahjong_engine.domain.rule_profile import RuleProfile
from mahjong_engine.domain.tile import PhysicalTile, Suit, TileType, TileVariant
from mahjong_engine.scoring.score_calculator import ScoreCalculator


def _tile_type_from_str(s: str) -> TileType | None:
    """受け入れ牌文字列 "1m" などを TileType に変換する。"""
    if len(s) < 2:
        return None
    try:
        rank = int(s[:-1])
        suit = Suit(s[-1])
        return TileType(suit=suit, rank=rank)
    except (ValueError, KeyError):
        return None


class HandEvCalculator:
    """受け入れ牌の加重平均から打点期待値を計算する。"""

    def __init__(self, adapter: MahjongEngineAdapter) -> None:
        self._score_calc = ScoreCalculator(adapter)

    def calculate(
        self,
        hand: list[PhysicalTile],
        melds: list[Meld],
        game_state: GameState,
        ukeire_entries: list[dict],
        rule: RuleProfile,
    ) -> dict:
        """打点期待値を計算する。

        Args:
            hand: プレイヤーの手牌（捨て牌後の 13 枚）
            melds: 副露のリスト
            game_state: 現在のゲーム状態
            ukeire_entries: 受け入れ牌リスト（UkeireCalculator の返値形式）
                            [{"tile_type": "1m", "remaining_count": N}, ...]
            rule: ルールプロファイル

        Returns:
            {"expected_han": float, "expected_fu": float, "expected_cost": int}
        """
        if not ukeire_entries:
            return {"expected_han": 0.0, "expected_fu": 0.0, "expected_cost": 0}

        total_weight = sum(e["remaining_count"] for e in ukeire_entries)
        if total_weight <= 0:
            return {"expected_han": 0.0, "expected_fu": 0.0, "expected_cost": 0}

        context = {
            "is_tsumo": False,
            "is_riichi": False,
            "dora_indicators": [
                {"suit": t.tile_type.suit.value, "rank": t.tile_type.rank}
                for t in game_state.dora_indicators
            ],
        }

        weighted_han = 0.0
        weighted_fu = 0.0
        weighted_cost = 0.0

        for entry in ukeire_entries:
            tile_type = _tile_type_from_str(entry["tile_type"])
            if tile_type is None:
                continue

            win_tile = PhysicalTile(
                tile_type=tile_type,
                variant=TileVariant.NORMAL,
                physical_id="",
            )

            result = self._score_calc.calculate(hand, win_tile, melds, context, rule)

            if result.get("error"):
                continue

            weight = entry["remaining_count"]
            han = result.get("han", 0)
            fu = result.get("fu", 0)
            cost = result.get("cost", {}).get("main", 0)

            weighted_han += han * weight
            weighted_fu += fu * weight
            weighted_cost += cost * weight

        expected_han = weighted_han / total_weight
        expected_fu = weighted_fu / total_weight
        expected_cost = int(weighted_cost / total_weight)

        return {
            "expected_han": expected_han,
            "expected_fu": expected_fu,
            "expected_cost": expected_cost,
        }
