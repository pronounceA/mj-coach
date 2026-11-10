"""HandEvCalculator のテスト"""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from mahjong_engine.analysis.hand_ev import HandEvCalculator, _tile_type_from_str
from mahjong_engine.domain.game_state import GameState
from mahjong_engine.domain.rule_profile import RuleProfile
from mahjong_engine.domain.tile import PhysicalTile, Suit, TileType, TileVariant


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------

def _make_tile(rank: int, suit: str = "m") -> PhysicalTile:
    return PhysicalTile(TileType(Suit(suit), rank), TileVariant.NORMAL, f"{rank}{suit}")


def _minimal_game_state() -> GameState:
    """最小限のゲーム状態を返す（13枚: 1〜9m + 1〜4p）。"""
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
        player_seat=0,
        rule_version_id=uuid4(),
        discards=[[], [], [], []],
    )


def _default_rule() -> RuleProfile:
    return RuleProfile(rule_name="default")


# ---------------------------------------------------------------------------
# _tile_type_from_str のユニットテスト
# ---------------------------------------------------------------------------

def test_tile_type_from_str_valid_man():
    tt = _tile_type_from_str("1m")
    assert tt is not None
    assert tt.suit == Suit.MAN
    assert tt.rank == 1


def test_tile_type_from_str_valid_honor():
    tt = _tile_type_from_str("7z")
    assert tt is not None
    assert tt.suit == Suit.HONOR
    assert tt.rank == 7


def test_tile_type_from_str_too_short():
    assert _tile_type_from_str("m") is None


def test_tile_type_from_str_invalid_suit():
    assert _tile_type_from_str("1x") is None


def test_tile_type_from_str_invalid_rank():
    assert _tile_type_from_str("am") is None


# ---------------------------------------------------------------------------
# HandEvCalculator のテスト
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_adapter():
    adapter = MagicMock()
    return adapter


def test_empty_ukeire_returns_zeros(mock_adapter):
    """受け入れ牌が空の場合はすべて 0 を返す。"""
    calc = HandEvCalculator(mock_adapter)
    game_state = _minimal_game_state()
    rule = _default_rule()
    hand = (
        [_make_tile(i) for i in range(1, 10)]
        + [_make_tile(i, "p") for i in range(1, 5)]
    )

    result = calc.calculate(hand, [], game_state, [], rule)

    assert result == {"expected_han": 0.0, "expected_fu": 0.0, "expected_cost": 0}
    mock_adapter.calculate_score.assert_not_called()


def test_zero_total_weight_returns_zeros(mock_adapter):
    """全受け入れ牌の remaining_count が 0 の場合はすべて 0 を返す。"""
    calc = HandEvCalculator(mock_adapter)
    game_state = _minimal_game_state()
    rule = _default_rule()
    hand = (
        [_make_tile(i) for i in range(1, 10)]
        + [_make_tile(i, "p") for i in range(1, 5)]
    )
    ukeire = [{"tile_type": "1m", "remaining_count": 0}]

    result = calc.calculate(hand, [], game_state, ukeire, rule)

    assert result == {"expected_han": 0.0, "expected_fu": 0.0, "expected_cost": 0}


def test_single_ukeire_entry_weighted_result(mock_adapter):
    """単一受け入れ牌エントリの場合、スコア計算結果がそのまま返る。"""
    # ScoreCalculator.calculate が特定の値を返すようにモック
    mock_adapter.calculate_score.return_value = {
        "han": 3,
        "fu": 40,
        "cost": {"main": 7700, "dealer": 11600},
        "yaku": [],
    }

    calc = HandEvCalculator(mock_adapter)
    game_state = _minimal_game_state()
    rule = _default_rule()

    # 13 枚の手牌（テスト用: 1〜9m + 1〜4p）
    hand = (
        [_make_tile(i) for i in range(1, 10)]
        + [_make_tile(i, "p") for i in range(1, 5)]
    )
    ukeire = [{"tile_type": "1m", "remaining_count": 4}]

    result = calc.calculate(hand, [], game_state, ukeire, rule)

    # 1 エントリのみなので期待値 = スコア計算値そのまま
    assert result["expected_han"] == pytest.approx(3.0)
    assert result["expected_fu"] == pytest.approx(40.0)
    assert result["expected_cost"] == 7700


def test_multiple_ukeire_entries_weighted_average(mock_adapter):
    """複数受け入れ牌エントリの場合、枚数で加重平均を取る。"""
    # 1枚目の呼び出しで 2000 点、2枚目の呼び出しで 4000 点を返す
    mock_adapter.calculate_score.side_effect = [
        {"han": 1, "fu": 30, "cost": {"main": 2000}, "yaku": []},
        {"han": 2, "fu": 40, "cost": {"main": 4000}, "yaku": []},
    ]

    calc = HandEvCalculator(mock_adapter)
    game_state = _minimal_game_state()
    rule = _default_rule()

    hand = (
        [_make_tile(i) for i in range(1, 10)]
        + [_make_tile(i, "p") for i in range(1, 5)]
    )
    ukeire = [
        {"tile_type": "1m", "remaining_count": 2},  # weight=2, cost=2000
        {"tile_type": "2m", "remaining_count": 2},  # weight=2, cost=4000
    ]

    result = calc.calculate(hand, [], game_state, ukeire, rule)

    # 加重平均: (2000*2 + 4000*2) / (2+2) = 12000/4 = 3000
    assert result["expected_cost"] == 3000
    # han: (1*2 + 2*2) / 4 = 6/4 = 1.5
    assert result["expected_han"] == pytest.approx(1.5)


def test_score_error_entry_is_skipped(mock_adapter):
    """スコア計算がエラーを返したエントリはスキップする。"""
    mock_adapter.calculate_score.side_effect = [
        {"error": "和了できません"},
        {"han": 2, "fu": 40, "cost": {"main": 3900}, "yaku": []},
    ]

    calc = HandEvCalculator(mock_adapter)
    game_state = _minimal_game_state()
    rule = _default_rule()

    hand = (
        [_make_tile(i) for i in range(1, 10)]
        + [_make_tile(i, "p") for i in range(1, 5)]
    )
    ukeire = [
        {"tile_type": "1m", "remaining_count": 2},  # エラー → スキップ
        {"tile_type": "2m", "remaining_count": 2},  # 有効
    ]

    result = calc.calculate(hand, [], game_state, ukeire, rule)

    # エラーエントリはスキップ → weight=2 のみ有効
    # expected_cost = 3900 * 2 / (2+2) = 1950
    assert result["expected_cost"] == 1950


def test_invalid_tile_type_string_is_skipped(mock_adapter):
    """無効な tile_type 文字列はスキップされる。"""
    calc = HandEvCalculator(mock_adapter)
    game_state = _minimal_game_state()
    rule = _default_rule()

    hand = (
        [_make_tile(i) for i in range(1, 10)]
        + [_make_tile(i, "p") for i in range(1, 5)]
    )
    ukeire = [{"tile_type": "invalid", "remaining_count": 4}]

    result = calc.calculate(hand, [], game_state, ukeire, rule)

    # 有効な受け入れ牌がないのでスコア計算は呼ばれない
    mock_adapter.calculate_score.assert_not_called()
    # 重みが 0 なので 0 を返す
    assert result["expected_cost"] == 0
