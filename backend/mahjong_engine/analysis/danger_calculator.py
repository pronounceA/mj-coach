from __future__ import annotations

from mahjong_engine.domain.game_state import GameState
from mahjong_engine.domain.tile import PhysicalTile, Suit, TileType

# 筋マップ: あるランクを捨てていた場合、安全になるランクのリスト
_SUJI_MAP: dict[int, list[int]] = {
    1: [4],
    2: [5],
    3: [6],
    4: [1, 7],
    5: [2, 8],
    6: [3, 9],
    7: [4],
    8: [5],
    9: [6],
}


class DangerCalculator:
    """特定の牌を特定の対局者に対して切る危険度を推定する。"""

    def calculate_vs_opponent(
        self,
        tile: PhysicalTile,
        game_state: GameState,
        opponent_index: int,
    ) -> float:
        """指定した対局者に対する放銃確率推定値（0.0〜1.0）を返す。

        Rules (優先順位順):
        1. 対局者が自分と同じシート: 0.0
        2. 現物（相手の捨て牌に存在する）: 0.0
        3. 4枚全部見えている（no-chance）: 0.01
        4. 字牌で既に捨てられている: 0.0（上記現物で処理済みだが念のため）
        5. 字牌: 1枚以下見えている → 0.04、2枚以上 → 0.02
        6. 筋牌: 0.04
        7. 壁牌（隣接3枚以上見えている）: 0.03
        8. 外側牌（1,9）: 0.06、（2,8）: 0.07、内側牌（3〜7）: 0.10
        """
        # 自分自身のシートは評価しない
        if opponent_index == game_state.player_seat:
            return 0.0

        # 有効なインデックス確認
        if not (0 <= opponent_index <= 3):
            return 0.0

        opponent_discards = game_state.discards[opponent_index]
        opponent_discard_tile_types = {d.tile_type for d in opponent_discards}

        tile_type = tile.tile_type

        # 現物チェック
        if tile_type in opponent_discard_tile_types:
            return 0.0

        # 全体で見えている枚数
        total_seen = game_state.count_tile_type(tile_type)

        # 4枚全部見えている（ノーチャンス）
        if total_seen >= 4:
            return 0.01

        # 字牌の場合
        if tile_type.suit == Suit.HONOR:
            if total_seen <= 1:
                return 0.04
            else:
                return 0.02

        # 数牌：筋チェック
        rank = tile_type.rank
        suit = tile_type.suit

        suji_ranks = _SUJI_MAP.get(rank, [])
        for suji_rank in suji_ranks:
            suji_tile_type = TileType(suit=suit, rank=suji_rank)
            if suji_tile_type in opponent_discard_tile_types:
                return 0.04

        # 壁チェック（隣接する3枚以上の同一スートの牌が見えているか）
        if _is_kabe(tile_type, game_state):
            return 0.03

        # 外側・内側による基本危険度
        if rank in (1, 9):
            return 0.06
        elif rank in (2, 8):
            return 0.07
        else:
            return 0.10

    def calculate_total(
        self,
        tile: PhysicalTile,
        game_state: GameState,
    ) -> dict:
        """全対局者に対する合成放銃確率を返す。

        Returns:
            {
                "deal_in_probability": float,  # 合成放銃確率（1 - Π(1 - p_i)）
                "max_vs_opponent": float,       # 最大個別危険度
            }
        """
        probabilities = []
        for i in range(4):
            if i == game_state.player_seat:
                continue
            p = self.calculate_vs_opponent(tile, game_state, i)
            probabilities.append(p)

        if not probabilities:
            return {"deal_in_probability": 0.0, "max_vs_opponent": 0.0}

        combined = 1.0
        for p in probabilities:
            combined *= 1.0 - p
        deal_in_probability = max(0.0, min(1.0, 1.0 - combined))

        max_vs_opponent = max(probabilities)

        return {
            "deal_in_probability": deal_in_probability,
            "max_vs_opponent": max_vs_opponent,
        }


def _is_kabe(tile_type: TileType, game_state: GameState) -> bool:
    """壁（カベ）チェック: 隣接スートで 3 枚以上見えている牌が存在するか。

    同一スートの隣接 ±1 のランクの牌が合計 3 枚以上見えていれば壁と判断する。
    """
    suit = tile_type.suit
    rank = tile_type.rank

    for neighbor_rank in [rank - 1, rank + 1]:
        if not (1 <= neighbor_rank <= 9):
            continue
        neighbor_type = TileType(suit=suit, rank=neighbor_rank)
        seen_count = game_state.count_tile_type(neighbor_type)
        if seen_count >= 3:
            return True

    return False
