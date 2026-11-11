from __future__ import annotations

from mahjong_engine.domain.game_state import GameState


class WinProbabilityCalculator:
    """シャンテン数・受け入れ枚数・ゲーム状態から和了確率を推定する。"""

    TOTAL_TILES = 136

    def calculate(
        self,
        shanten: int,
        ukeire_count: int,
        game_state: GameState,
    ) -> float:
        """和了確率を 0.0〜1.0 の float で返す。

        Args:
            shanten: シャンテン数（-1 = 和了済）
            ukeire_count: 受け入れ枚数の合計
            game_state: 現在のゲーム状態

        Returns:
            推定和了確率（0.0〜1.0）
        """
        if game_state.junme is not None:
            remaining_draws = max(0, 70 - game_state.junme * 4)
        else:
            remaining_draws = max(
                0, 70 - sum(len(d) for d in game_state.discards)
            )
        unseen = max(0, self.TOTAL_TILES - len(game_state.all_known_tiles()))

        return self._win_prob(shanten, ukeire_count, remaining_draws, unseen, depth=0)

    def _win_prob(
        self,
        shanten: int,
        ukeire_count: int,
        remaining_draws: int,
        unseen: int,
        depth: int,
    ) -> float:
        """再帰的にシャンテン進行確率を計算する。最大深さ 3。"""
        # 和了済み
        if shanten < 0:
            return 1.0

        # ドローが残っていない
        if remaining_draws <= 0:
            return 0.0

        # 受け入れ牌がない
        if ukeire_count <= 0:
            return 0.0

        # unseen が 0 以下（論理的にはありえないが安全のため）
        if unseen <= 0:
            return 0.0

        # テンパイ（shanten == 0）: 二項分布で近似
        if shanten == 0:
            p_not_win_per_draw = max(0.0, 1.0 - ukeire_count / unseen)
            p_not_win_all = p_not_win_per_draw ** remaining_draws
            return max(0.0, min(1.0, 1.0 - p_not_win_all))

        # 再帰深さの上限を超えた場合は小さい値を返す
        if depth >= 3:
            return 0.02

        # シャンテン > 0: 1手でテンパイに近づく確率を計算してから再帰
        p_advance_per_draw = min(1.0, ukeire_count / unseen)

        # 期待進行手数（平均して何手でシャンテンが進むか）
        expected_draws_to_advance = max(1.0, unseen / max(1, ukeire_count))

        # 次のシャンテンの受け入れ枚数は現在の 60% と仮定
        next_ukeire = max(1, int(ukeire_count * 0.6))

        # 進行後の残り手数・未見牌数
        draws_after = max(0, remaining_draws - int(expected_draws_to_advance))
        unseen_after = max(0, unseen - int(expected_draws_to_advance))

        # 1手以上引く間に進行できる確率
        p_advance = 1.0 - (1.0 - p_advance_per_draw) ** remaining_draws

        p_win_if_advance = self._win_prob(
            shanten - 1,
            next_ukeire,
            draws_after,
            unseen_after,
            depth + 1,
        )

        return max(0.0, min(1.0, p_advance * p_win_if_advance))
