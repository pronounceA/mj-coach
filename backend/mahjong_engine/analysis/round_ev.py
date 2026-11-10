from __future__ import annotations

from mahjong_engine.analysis.danger_calculator import DangerCalculator
from mahjong_engine.analysis.hand_ev import HandEvCalculator
from mahjong_engine.analysis.win_probability import WinProbabilityCalculator
from mahjong_engine.domain.game_state import GameState
from mahjong_engine.domain.meld import Meld
from mahjong_engine.domain.rule_profile import RuleProfile
from mahjong_engine.domain.tile import PhysicalTile


class RoundEvCalculator:
    """局単位の期待値（EV）を計算する。"""

    AVG_DEAL_IN_LOSS = 6000.0
    TENPAI_BONUS = 500.0

    def __init__(
        self,
        win_prob_calc: WinProbabilityCalculator,
        hand_ev_calc: HandEvCalculator,
        danger_calc: DangerCalculator,
    ) -> None:
        self._win_prob_calc = win_prob_calc
        self._hand_ev_calc = hand_ev_calc
        self._danger_calc = danger_calc

    def calculate(
        self,
        shanten: int,
        ukeire_count: int,
        ukeire_entries: list[dict],
        hand: list[PhysicalTile],
        melds: list[Meld],
        discard_tile: PhysicalTile,
        game_state: GameState,
        rule: RuleProfile,
    ) -> dict:
        """局単位 EV を計算する。

        Args:
            shanten: 捨て牌後のシャンテン数
            ukeire_count: 受け入れ枚数合計
            ukeire_entries: 受け入れ牌リスト
            hand: 捨て牌後の手牌
            melds: 副露のリスト
            discard_tile: 切る予定の牌（放銃危険度算出に使用）
            game_state: 現在のゲーム状態
            rule: ルールプロファイル

        Returns:
            {
                "win_probability": float,
                "expected_cost": int,
                "expected_han": float,
                "deal_in_probability": float,
                "round_ev": int,
            }
        """
        p_win = self._win_prob_calc.calculate(shanten, ukeire_count, game_state)

        hand_ev_data = self._hand_ev_calc.calculate(
            hand, melds, game_state, ukeire_entries, rule
        )
        expected_cost = hand_ev_data["expected_cost"]
        expected_han = hand_ev_data["expected_han"]

        danger_data = self._danger_calc.calculate_total(discard_tile, game_state)
        p_deal_in = danger_data["deal_in_probability"]

        # テンパイ時のノーテン罰符期待値（テンパイ確率 * ボーナス）
        tenpai_ev = p_win * self.TENPAI_BONUS if shanten <= 0 else 0.0

        round_ev = (
            p_win * expected_cost
            - p_deal_in * self.AVG_DEAL_IN_LOSS
            + tenpai_ev
        )

        return {
            "win_probability": p_win,
            "expected_cost": expected_cost,
            "expected_han": expected_han,
            "deal_in_probability": p_deal_in,
            "round_ev": int(round_ev),
        }


class PushFoldAnalyzer:
    """押し引き（push/fold）評価を行う。"""

    def __init__(
        self,
        round_ev_calc: RoundEvCalculator,
        danger_calc: DangerCalculator,
    ) -> None:
        self._round_ev_calc = round_ev_calc
        self._danger_calc = danger_calc

    def analyze(
        self,
        hand: list[PhysicalTile],
        melds: list[Meld],
        shanten: int,
        ukeire_count: int,
        ukeire_entries: list[dict],
        push_discard: PhysicalTile,
        fold_discard: PhysicalTile,
        game_state: GameState,
        rule: RuleProfile,
    ) -> dict:
        """押し引き評価を行い、推奨行動を返す。

        Args:
            hand: 現在の手牌
            melds: 副露のリスト
            shanten: 現在のシャンテン数
            ukeire_count: 受け入れ枚数合計
            ukeire_entries: 受け入れ牌リスト
            push_discard: 押し牌（危険牌を切って攻める場合）
            fold_discard: 折り牌（安全牌を切って守る場合）
            game_state: 現在のゲーム状態
            rule: ルールプロファイル

        Returns:
            {
                "recommendation": str,              # "push" | "fold"
                "push_ev": int,
                "fold_ev": int,
                "ev_diff": int,
                "push_win_probability": float,
                "push_deal_in_probability": float,
                "fold_deal_in_probability": float,
            }
        """
        # 押し時の EV
        push_data = self._round_ev_calc.calculate(
            shanten,
            ukeire_count,
            ukeire_entries,
            hand,
            melds,
            push_discard,
            game_state,
            rule,
        )
        push_ev = push_data["round_ev"]
        push_win_prob = push_data["win_probability"]
        push_deal_in = push_data["deal_in_probability"]

        # 折り時の勝率: テンパイの場合は押し時の 50%、非テンパイは 5%
        is_tenpai = shanten <= 0
        fold_win_prob = push_win_prob * (0.5 if is_tenpai else 0.05)

        # 折り牌の放銃危険度
        fold_danger_data = self._danger_calc.calculate_total(fold_discard, game_state)
        fold_deal_in = fold_danger_data["deal_in_probability"]

        # 折り時の手牌 EV: 平均打点は大幅に下がるが同一モデルで近似
        fold_hand_ev = self._round_ev_calc._hand_ev_calc.calculate(
            hand, melds, game_state, ukeire_entries, rule
        )
        fold_expected_cost = fold_hand_ev["expected_cost"]

        fold_tenpai_ev = fold_win_prob * RoundEvCalculator.TENPAI_BONUS if is_tenpai else 0.0

        fold_ev = int(
            fold_win_prob * fold_expected_cost
            - fold_deal_in * RoundEvCalculator.AVG_DEAL_IN_LOSS
            + fold_tenpai_ev
        )

        ev_diff = push_ev - fold_ev
        recommendation = "push" if push_ev >= fold_ev else "fold"

        return {
            "recommendation": recommendation,
            "push_ev": push_ev,
            "fold_ev": fold_ev,
            "ev_diff": ev_diff,
            "push_win_probability": push_win_prob,
            "push_deal_in_probability": push_deal_in,
            "fold_deal_in_probability": fold_deal_in,
        }
