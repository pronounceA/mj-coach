from mahjong_engine.domain.rule_profile import RuleProfile, RedTileConfig, BlueTileConfig
from mahjong_engine.domain.tile import PhysicalTile, Suit, TileType, TileVariant
from mahjong_engine.rules.dora_calculator import DoraCalculator


def make_tile(suit: str, rank: int, variant: str = "normal") -> PhysicalTile:
    return PhysicalTile(
        tile_type=TileType(suit=Suit(suit), rank=rank),
        variant=TileVariant(variant),
    )


def test_normal_dora():
    rule = RuleProfile(rule_name="test")
    calc = DoraCalculator(rule)
    # ドラ表示牌が1m → ドラは2m
    hand = [make_tile("m", 2), make_tile("m", 2)]
    dora_indicators = [make_tile("m", 1)]
    result = calc.count_dora(hand, [], dora_indicators)
    assert result["normal_dora"] == 2
    assert result["red_dora"] == 0
    assert result["blue_dora"] == 0


def test_red_dora():
    rule = RuleProfile(rule_name="test", red_tile=RedTileConfig(han=1))
    calc = DoraCalculator(rule)
    hand = [make_tile("p", 5, "red"), make_tile("p", 5)]
    result = calc.count_dora(hand, [], [])
    assert result["red_dora"] == 1
    assert result["total_dora_han"] == 1


def test_blue_dora():
    rule = RuleProfile(rule_name="test", blue_tile=BlueTileConfig(han=1))
    calc = DoraCalculator(rule)
    hand = [make_tile("s", 5, "blue"), make_tile("s", 5, "blue")]
    result = calc.count_dora(hand, [], [])
    assert result["blue_dora"] == 2
    assert result["total_dora_han"] == 2


def test_dora_wrap_around():
    rule = RuleProfile(rule_name="test")
    calc = DoraCalculator(rule)
    # ドラ表示牌が9m → ドラは1m
    hand = [make_tile("m", 1)]
    dora_indicators = [make_tile("m", 9)]
    result = calc.count_dora(hand, [], dora_indicators)
    assert result["normal_dora"] == 1
