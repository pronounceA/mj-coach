"""WinProbabilityCalculator のテスト"""

import pytest
from uuid import uuid4

from mahjong_engine.analysis.win_probability import WinProbabilityCalculator
from mahjong_engine.domain.game_state import GameState
from mahjong_engine.domain.tile import PhysicalTile, Suit, TileType, TileVariant


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------

def _make_tile(rank: int, suit: str = "m") -> PhysicalTile:
    return PhysicalTile(TileType(Suit(suit), rank), TileVariant.NORMAL, f"{rank}{suit}")


def _minimal_game_state(discards=None) -> GameState:
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
        player_seat=0,
        rule_version_id=uuid4(),
        discards=discards,
    )


# ---------------------------------------------------------------------------
# テスト
# ---------------------------------------------------------------------------

@pytest.fixture
def calc() -> WinProbabilityCalculator:
    return WinProbabilityCalculator()


def test_shanten_minus_one_returns_1(calc):
    """和了済み（shanten=-1）の場合は 1.0 を返す。"""
    game_state = _minimal_game_state()
    result = calc.calculate(shanten=-1, ukeire_count=0, game_state=game_state)
    assert result == 1.0


def test_tenpai_high_ukeire_returns_high_prob(calc):
    """テンパイで受け入れ枚数が多い場合は高確率になる。"""
    game_state = _minimal_game_state()
    # 残り手番が多く受け入れが多ければ高確率
    result = calc.calculate(shanten=0, ukeire_count=16, game_state=game_state)
    assert result > 0.5


def test_tenpai_zero_ukeire_returns_zero(calc):
    """テンパイでも受け入れ枚数が 0 の場合は 0.0 を返す。"""
    game_state = _minimal_game_state()
    result = calc.calculate(shanten=0, ukeire_count=0, game_state=game_state)
    assert result == 0.0


def test_tenpai_no_draws_remaining_returns_zero(calc):
    """残り手番が 0 の場合は 0.0 を返す。"""
    # 各プレイヤーが 18 枚ずつ捨てていれば残り手番はほぼ 0
    # 70 - (18*4) = 70 - 72 = -2 → max(0, -2) = 0
    discards = [[_make_tile((i % 9) + 1) for i in range(18)] for _ in range(4)]
    game_state = _minimal_game_state(discards=discards)
    # drawn_tile を None のまま渡してバリデーションを回避（手牌13枚で固定）
    result = calc.calculate(shanten=0, ukeire_count=8, game_state=game_state)
    assert result == 0.0


def test_shanten_one_returns_between_zero_and_one(calc):
    """1シャンテンの場合は 0〜1 の範囲の確率を返す。"""
    game_state = _minimal_game_state()
    result = calc.calculate(shanten=1, ukeire_count=8, game_state=game_state)
    assert 0.0 <= result <= 1.0


def test_higher_shanten_lower_prob_than_lower_shanten(calc):
    """単調性: シャンテン数が大きいほど和了確率は低い。"""
    game_state = _minimal_game_state()
    p0 = calc.calculate(shanten=0, ukeire_count=8, game_state=game_state)
    p1 = calc.calculate(shanten=1, ukeire_count=8, game_state=game_state)
    p2 = calc.calculate(shanten=2, ukeire_count=8, game_state=game_state)
    assert p0 > p1
    assert p1 > p2


def test_result_is_clamped_between_zero_and_one(calc):
    """返値は常に 0.0〜1.0 の範囲に収まる。"""
    game_state = _minimal_game_state()
    for shanten in range(-1, 4):
        for ukeire in [0, 4, 16, 100]:
            result = calc.calculate(shanten=shanten, ukeire_count=ukeire, game_state=game_state)
            assert 0.0 <= result <= 1.0, (
                f"shanten={shanten}, ukeire={ukeire} → {result}"
            )


def test_deep_shanten_returns_small_value(calc):
    """3 より大きいシャンテン数では小さい値（デフォルト 0.02）が返る。"""
    game_state = _minimal_game_state()
    result = calc.calculate(shanten=4, ukeire_count=8, game_state=game_state)
    assert result < 0.1
