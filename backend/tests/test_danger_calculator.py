"""DangerCalculator のテスト"""

import pytest
from uuid import uuid4

from mahjong_engine.analysis.danger_calculator import DangerCalculator
from mahjong_engine.domain.game_state import GameState
from mahjong_engine.domain.tile import PhysicalTile, Suit, TileType, TileVariant


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------

def _make_tile(rank: int, suit: str = "m") -> PhysicalTile:
    return PhysicalTile(TileType(Suit(suit), rank), TileVariant.NORMAL, f"{rank}{suit}")


def _minimal_game_state(
    discards=None,
    player_seat: int = 0,
) -> GameState:
    """最小限のゲーム状態を返す（13枚: 1〜9m + 1〜4p）。"""
    if discards is None:
        discards = [[], [], [], []]
    hand = (
        [_make_tile(i) for i in range(1, 10)]  # 1m〜9m (9枚)
        + [_make_tile(i, "p") for i in range(1, 5)]  # 1p〜4p (4枚)
    )
    return GameState(
        hand=hand,
        scores=[25000] * 4,
        chips=[0] * 4,
        round_wind="east",
        hand_number=1,
        honba=0,
        riichi_sticks=0,
        dealer=0,
        player_seat=player_seat,
        rule_version_id=uuid4(),
        discards=discards,
    )


@pytest.fixture
def calc() -> DangerCalculator:
    return DangerCalculator()


# ---------------------------------------------------------------------------
# calculate_vs_opponent のテスト
# ---------------------------------------------------------------------------

def test_genbutsu_returns_zero(calc):
    """現物（相手の捨て牌に存在する）は 0.0 を返す。"""
    target = _make_tile(5, "m")
    # 対局者 1 の捨て牌に 5m がある
    discards = [[], [target], [], []]
    game_state = _minimal_game_state(discards=discards)

    result = calc.calculate_vs_opponent(target, game_state, opponent_index=1)
    assert result == 0.0


def test_all_four_seen_returns_low_value(calc):
    """4枚全部見えている（ノーチャンス）場合は 0.01 以下を返す。"""
    target_type = TileType(Suit.MAN, 3)
    # 手牌に 3m を 4 枚持たせる（count_tile_type が 4 になるよう）
    extra_tiles = [PhysicalTile(target_type, TileVariant.NORMAL, f"3m_{i}") for i in range(4)]
    game_state = _minimal_game_state()
    # 手牌に 4 枚追加（テスト用に直接 all_known_tiles が 4 返すよう discards に入れる）
    discards = [
        [extra_tiles[0], extra_tiles[1], extra_tiles[2], extra_tiles[3]],
        [], [], []
    ]
    game_state_with_seen = _minimal_game_state(discards=discards)

    target = PhysicalTile(target_type, TileVariant.NORMAL, "3m_new")
    result = calc.calculate_vs_opponent(target, game_state_with_seen, opponent_index=1)
    assert result <= 0.03


def test_honor_tile_in_discards_returns_zero(calc):
    """字牌が相手の捨て牌にある場合（現物）は 0.0 を返す。"""
    honor_tile = _make_tile(1, "z")  # 東
    discards = [[], [honor_tile], [], []]
    game_state = _minimal_game_state(discards=discards)

    result = calc.calculate_vs_opponent(honor_tile, game_state, opponent_index=1)
    assert result == 0.0


def test_honor_tile_not_seen_returns_moderate_danger(calc):
    """字牌が誰の捨て牌にもない場合は 0.04 を返す。"""
    honor_tile = _make_tile(1, "z")  # 東
    game_state = _minimal_game_state()

    result = calc.calculate_vs_opponent(honor_tile, game_state, opponent_index=1)
    assert result == pytest.approx(0.04)


def test_inner_tile_no_info_returns_010(calc):
    """情報のない内側牌（3〜7）は 0.10 を返す。"""
    inner_tile = _make_tile(5, "m")
    game_state = _minimal_game_state()

    result = calc.calculate_vs_opponent(inner_tile, game_state, opponent_index=1)
    assert result == pytest.approx(0.10)


def test_outer_tile_1_returns_006(calc):
    """情報のない 1m は 0.06 を返す。"""
    outer_tile = _make_tile(1, "m")
    game_state = _minimal_game_state()

    result = calc.calculate_vs_opponent(outer_tile, game_state, opponent_index=1)
    assert result == pytest.approx(0.06)


def test_outer_tile_9_returns_006(calc):
    """情報のない 9m は 0.06 を返す。"""
    outer_tile = _make_tile(9, "m")
    game_state = _minimal_game_state()

    result = calc.calculate_vs_opponent(outer_tile, game_state, opponent_index=1)
    assert result == pytest.approx(0.06)


def test_tile_2_returns_007(calc):
    """情報のない 2m は 0.07 を返す。"""
    tile = _make_tile(2, "m")
    game_state = _minimal_game_state()

    result = calc.calculate_vs_opponent(tile, game_state, opponent_index=1)
    assert result == pytest.approx(0.07)


def test_suji_tile_returns_004(calc):
    """筋牌は 0.04 を返す。"""
    # 相手が 1m を捨てている → 4m は筋
    tile_1m = _make_tile(1, "m")
    discards = [[], [tile_1m], [], []]
    game_state = _minimal_game_state(discards=discards)

    target = _make_tile(4, "m")
    result = calc.calculate_vs_opponent(target, game_state, opponent_index=1)
    assert result == pytest.approx(0.04)


def test_opponent_same_as_player_seat_returns_zero(calc):
    """自分自身のシートに対しては 0.0 を返す。"""
    tile = _make_tile(5, "m")
    game_state = _minimal_game_state(player_seat=0)

    result = calc.calculate_vs_opponent(tile, game_state, opponent_index=0)
    assert result == 0.0


# ---------------------------------------------------------------------------
# calculate_total のテスト
# ---------------------------------------------------------------------------

def test_calculate_total_genbutsu_all_opponents(calc):
    """全相手の捨て牌に現物がある場合は合成 0.0 を返す。"""
    target = _make_tile(5, "m")
    discards = [[], [target], [target], [target]]
    game_state = _minimal_game_state(discards=discards, player_seat=0)

    result = calc.calculate_total(target, game_state)
    assert result["deal_in_probability"] == pytest.approx(0.0)
    assert result["max_vs_opponent"] == pytest.approx(0.0)


def test_calculate_total_inner_tile_raises_probability(calc):
    """内側牌（情報なし）では合成放銃確率が各個別確率より高い。"""
    inner_tile = _make_tile(5, "m")
    game_state = _minimal_game_state(player_seat=0)

    result = calc.calculate_total(inner_tile, game_state)
    # 3 人の相手それぞれ 0.10 → 合成: 1-(1-0.1)^3 ≈ 0.271
    assert result["deal_in_probability"] > 0.1
    assert result["max_vs_opponent"] == pytest.approx(0.10)


def test_calculate_total_returns_dict_keys(calc):
    """返値に必要なキーが含まれる。"""
    tile = _make_tile(5, "m")
    game_state = _minimal_game_state()

    result = calc.calculate_total(tile, game_state)
    assert "deal_in_probability" in result
    assert "max_vs_opponent" in result


def test_calculate_total_probability_clamped(calc):
    """合成確率は 0〜1 の範囲に収まる。"""
    tile = _make_tile(5, "m")
    game_state = _minimal_game_state()

    result = calc.calculate_total(tile, game_state)
    assert 0.0 <= result["deal_in_probability"] <= 1.0
    assert 0.0 <= result["max_vs_opponent"] <= 1.0
