import pytest
from uuid import UUID

from mahjong_engine.domain.game_state import GameState
from mahjong_engine.domain.rule_profile import RuleProfile, ScoringConfig, UmaConfig
from mahjong_engine.domain.tile import PhysicalTile, TileType, Suit, TileVariant
from mahjong_engine.simulation.match_simulator import MatchSimulator
from mahjong_engine.simulation.placement_calculator import PlacementCalculator
from mahjong_engine.simulation.opponent_model import get_opponent_stats, OpponentType
from mahjong_engine.simulation.round_simulator import simulate_round
import random


_UUID = UUID("00000000-0000-0000-0000-000000000000")


def _make_tile(suit: str, rank: int) -> PhysicalTile:
    s = {"m": Suit.MAN, "p": Suit.PIN, "s": Suit.SOU, "z": Suit.HONOR}[suit]
    tt = TileType(suit=s, rank=rank)
    return PhysicalTile(tile_type=tt, variant=TileVariant.NORMAL, physical_id=f"{suit}{rank}")


def _make_hand():
    return [_make_tile("m", i) for i in range(1, 10)] + [
        _make_tile("p", 1), _make_tile("p", 2), _make_tile("p", 3), _make_tile("s", 1)
    ]


def _game_state(scores=None, remaining_hands=4):
    return GameState(
        hand=_make_hand(),
        scores=scores or [30000, 30000, 30000, 30000],
        chips=[0, 0, 0, 0],
        round_wind="E",
        hand_number=1,
        honba=0,
        riichi_sticks=0,
        dealer=0,
        player_seat=0,
        remaining_hands=remaining_hands,
        rule_version_id=_UUID,
    )


def _rule(uma=(30000, 10000, -10000, -30000)):
    return RuleProfile(
        rule_name="test",
        scoring=ScoringConfig(
            uma=UmaConfig(first=uma[0], second=uma[1], third=uma[2], fourth=uma[3]),
        ),
    )


@pytest.fixture
def simulator():
    return MatchSimulator(PlacementCalculator())


class TestOpponentModel:
    def test_get_basic(self):
        stats = get_opponent_stats("basic")
        assert 0 < stats.win_rate < 1

    def test_get_unknown_falls_back_to_basic(self):
        stats = get_opponent_stats("unknown_model")
        basic = get_opponent_stats(OpponentType.BASIC)
        assert stats == basic

    def test_aggressive_higher_win_rate_than_defensive(self):
        agg = get_opponent_stats("aggressive")
        defn = get_opponent_stats("defensive")
        assert agg.win_rate > defn.win_rate

    def test_defensive_lower_deal_in_rate(self):
        agg = get_opponent_stats("aggressive")
        defn = get_opponent_stats("defensive")
        assert defn.deal_in_rate < agg.deal_in_rate


class TestRoundSimulator:
    def test_zero_sum(self):
        rng = random.Random(42)
        opp_stats = [get_opponent_stats("basic")] * 3
        for _ in range(100):
            outcome = simulate_round(
                player_seat=0,
                p_win=0.20,
                expected_win_score=5000,
                p_deal_in=0.12,
                opp_stats=opp_stats,
                dealer=0,
                honba=0,
                riichi_sticks=0,
                rng=rng,
            )
            # スコア変化の合計は概ねゼロ（流局時は0、ロン時は0、ツモ時は端数で1-2点のずれあり）
            assert abs(sum(outcome.score_changes)) <= 10

    def test_honba_included_in_win(self):
        rng = random.Random(0)
        opp_stats = [get_opponent_stats("basic")] * 3
        # p_win=1.0 で必ず自家和了
        outcome = simulate_round(
            player_seat=0,
            p_win=1.0,
            expected_win_score=5000,
            p_deal_in=0.0,
            opp_stats=opp_stats,
            dealer=1,
            honba=2,
            riichi_sticks=1,
            rng=rng,
        )
        # 本場ボーナス300*2=600, 供託1000
        expected_min = 5000 + 600 + 1000
        assert outcome.score_changes[0] >= expected_min

    def test_dealer_win_keeps_dealer(self):
        rng = random.Random(0)
        opp_stats = [get_opponent_stats("basic")] * 3
        outcome = simulate_round(
            player_seat=0,
            p_win=1.0,
            expected_win_score=5000,
            p_deal_in=0.0,
            opp_stats=opp_stats,
            dealer=0,
            honba=0,
            riichi_sticks=0,
            rng=rng,
        )
        assert outcome.next_dealer == 0
        assert outcome.next_honba == 1

    def test_non_dealer_win_advances_dealer(self):
        rng = random.Random(0)
        opp_stats = [get_opponent_stats("basic")] * 3
        outcome = simulate_round(
            player_seat=0,
            p_win=1.0,
            expected_win_score=5000,
            p_deal_in=0.0,
            opp_stats=opp_stats,
            dealer=1,
            honba=0,
            riichi_sticks=0,
            rng=rng,
        )
        assert outcome.next_dealer == 2
        assert outcome.next_honba == 0


class TestMatchSimulator:
    def test_simulation_completes(self, simulator):
        gs = _game_state()
        rule = _rule()
        result = simulator.simulate(
            game_state=gs,
            win_probability=0.25,
            expected_cost=5000,
            deal_in_probability=0.10,
            opponent_types=["basic", "basic", "basic"],
            rule=rule,
            n_simulations=100,
            seed=42,
        )
        assert result["simulation_count"] == 100

    def test_placement_distribution_sums_to_one(self, simulator):
        gs = _game_state()
        rule = _rule()
        result = simulator.simulate(
            game_state=gs,
            win_probability=0.25,
            expected_cost=5000,
            deal_in_probability=0.10,
            opponent_types=["basic", "basic", "basic"],
            rule=rule,
            n_simulations=200,
            seed=0,
        )
        total = sum(result["placement_distribution"].values())
        assert abs(total - 1.0) < 1e-9

    def test_mean_placement_range(self, simulator):
        gs = _game_state()
        rule = _rule()
        result = simulator.simulate(
            game_state=gs,
            win_probability=0.25,
            expected_cost=5000,
            deal_in_probability=0.10,
            opponent_types=["basic", "basic", "basic"],
            rule=rule,
            n_simulations=500,
            seed=1,
        )
        # 均等条件なら平均順位は概ね 2.0〜3.0 の範囲
        assert 1.0 <= result["mean_placement"] <= 4.0

    def test_ci_lo_le_hi(self, simulator):
        gs = _game_state()
        rule = _rule()
        result = simulator.simulate(
            game_state=gs,
            win_probability=0.25,
            expected_cost=5000,
            deal_in_probability=0.10,
            opponent_types=["basic", "basic", "basic"],
            rule=rule,
            n_simulations=200,
            seed=99,
        )
        assert result["confidence_interval_95"][0] <= result["confidence_interval_95"][1]

    def test_high_win_prob_improves_placement(self, simulator):
        gs = _game_state()
        rule = _rule()
        low = simulator.simulate(
            game_state=gs,
            win_probability=0.05,
            expected_cost=3000,
            deal_in_probability=0.25,
            opponent_types=["basic", "basic", "basic"],
            rule=rule,
            n_simulations=500,
            seed=7,
        )
        high = simulator.simulate(
            game_state=gs,
            win_probability=0.50,
            expected_cost=8000,
            deal_in_probability=0.03,
            opponent_types=["basic", "basic", "basic"],
            rule=rule,
            n_simulations=500,
            seed=7,
        )
        # 和了確率が高い方が平均順位が良い（数値が小さい）
        assert high["mean_placement"] < low["mean_placement"]

    def test_seed_reproducibility(self, simulator):
        gs = _game_state()
        rule = _rule()
        kwargs = dict(
            game_state=gs,
            win_probability=0.20,
            expected_cost=5000,
            deal_in_probability=0.12,
            opponent_types=["basic", "basic", "basic"],
            rule=rule,
            n_simulations=100,
            seed=42,
        )
        r1 = simulator.simulate(**kwargs)
        r2 = simulator.simulate(**kwargs)
        assert r1["mean_final_score"] == r2["mean_final_score"]
