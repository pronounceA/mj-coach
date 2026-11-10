from __future__ import annotations

import random
import statistics

from mahjong_engine.domain.game_state import GameState
from mahjong_engine.domain.rule_profile import RuleProfile
from mahjong_engine.simulation.opponent_model import OpponentStats, get_opponent_stats
from mahjong_engine.simulation.placement_calculator import PlacementCalculator
from mahjong_engine.simulation.round_simulator import simulate_round

_FUTURE_WIN_PROB = 0.20
_FUTURE_DEAL_IN_PROB = 0.12
_FUTURE_WIN_SCORE = 5000


class MatchSimulator:
    """Monte Carlo 法による半荘シミュレーター。"""

    def __init__(self, placement_calc: PlacementCalculator) -> None:
        self._placement_calc = placement_calc

    def simulate(
        self,
        game_state: GameState,
        win_probability: float,
        expected_cost: int,
        deal_in_probability: float,
        opponent_types: list[str],
        rule: RuleProfile,
        n_simulations: int = 500,
        seed: int | None = None,
    ) -> dict:
        """半荘シミュレーションを実行し、自家の精算点分布を返す。

        Returns:
            {
                "placement_distribution": {1: float, 2: float, 3: float, 4: float},
                "mean_placement": float,
                "mean_final_score": float,
                "confidence_interval_95": (float, float),
                "simulation_count": int,
            }
        """
        rng = random.Random(seed)

        types = (opponent_types + ["basic"] * 3)[:3]
        opp_stats: list[OpponentStats] = [get_opponent_stats(t) for t in types]
        remaining = game_state.remaining_hands or 8

        final_scores: list[int] = []
        placement_counts = {1: 0, 2: 0, 3: 0, 4: 0}

        for _ in range(n_simulations):
            score, placement = self._run_one(
                game_state=game_state,
                win_probability=win_probability,
                expected_cost=expected_cost,
                deal_in_probability=deal_in_probability,
                opp_stats=opp_stats,
                remaining=remaining,
                rule=rule,
                rng=rng,
            )
            final_scores.append(score)
            placement_counts[placement] += 1

        mean_final = statistics.mean(final_scores)
        mean_placement = statistics.mean(
            p for p, cnt in placement_counts.items() for _ in range(cnt)
        )

        sorted_scores = sorted(final_scores)
        lo = sorted_scores[max(0, int(0.025 * n_simulations))]
        hi = sorted_scores[min(n_simulations - 1, int(0.975 * n_simulations))]

        distribution = {p: placement_counts[p] / n_simulations for p in range(1, 5)}

        return {
            "placement_distribution": distribution,
            "mean_placement": mean_placement,
            "mean_final_score": mean_final,
            "confidence_interval_95": (lo, hi),
            "simulation_count": n_simulations,
        }

    def _run_one(
        self,
        game_state: GameState,
        win_probability: float,
        expected_cost: int,
        deal_in_probability: float,
        opp_stats: list[OpponentStats],
        remaining: int,
        rule: RuleProfile,
        rng: random.Random,
    ) -> tuple[int, int]:
        """1回の半荘をシミュレートし (精算点, 順位) を返す。"""
        scores = list(game_state.scores)
        player_seat = game_state.player_seat
        dealer = game_state.dealer
        honba = game_state.honba
        riichi_sticks = game_state.riichi_sticks

        for round_idx in range(remaining):
            is_current = round_idx == 0
            p_win = win_probability if is_current else _FUTURE_WIN_PROB
            p_din = deal_in_probability if is_current else _FUTURE_DEAL_IN_PROB
            win_score = expected_cost if is_current else _FUTURE_WIN_SCORE

            outcome = simulate_round(
                player_seat=player_seat,
                p_win=p_win,
                expected_win_score=win_score,
                p_deal_in=p_din,
                opp_stats=opp_stats,
                dealer=dealer,
                honba=honba,
                riichi_sticks=riichi_sticks,
                rng=rng,
            )

            for i, delta in enumerate(outcome.score_changes):
                scores[i] += delta

            dealer = outcome.next_dealer
            honba = outcome.next_honba
            riichi_sticks = outcome.next_riichi_sticks

        placements = self._placement_calc.calculate_placements(scores)
        final_points = self._placement_calc.calculate_final_points(
            scores, placements, rule
        )
        return final_points[player_seat], placements[player_seat]
