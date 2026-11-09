from mahjong_engine.domain.rule_profile import RuleProfile, BlueTileConfig, ChipSettlement
from mahjong_engine.domain.tile import PhysicalTile, Suit, TileType, TileVariant
from mahjong_engine.rules.chip_calculator import ChipCalculator


def make_tile(suit: str, rank: int, variant: str = "normal") -> PhysicalTile:
    return PhysicalTile(
        tile_type=TileType(suit=Suit(suit), rank=rank),
        variant=TileVariant(variant),
    )


def test_no_blue_tiles():
    rule = RuleProfile(rule_name="test")
    calc = ChipCalculator(rule)
    hand = [make_tile("m", 1), make_tile("m", 2)]
    assert calc.count_chips(hand, [], is_win=True) == 0


def test_one_blue_tile_win():
    rule = RuleProfile(rule_name="test", blue_tile=BlueTileConfig(chips_per_blue_tile=2))
    calc = ChipCalculator(rule)
    hand = [make_tile("s", 5, "blue"), make_tile("m", 1)]
    assert calc.count_chips(hand, [], is_win=True) == 2


def test_two_blue_tiles_win():
    rule = RuleProfile(rule_name="test", blue_tile=BlueTileConfig(chips_per_blue_tile=2))
    calc = ChipCalculator(rule)
    hand = [make_tile("m", 5, "blue"), make_tile("s", 5, "blue")]
    assert calc.count_chips(hand, [], is_win=True) == 4


def test_no_chip_when_not_win():
    rule = RuleProfile(rule_name="test")
    calc = ChipCalculator(rule)
    hand = [make_tile("s", 5, "blue")]
    assert calc.count_chips(hand, [], is_win=False) == 0


def test_ron_payment():
    rule = RuleProfile(rule_name="test")
    calc = ChipCalculator(rule)
    result = calc.chip_payments(chip_count=2, is_tsumo=False)
    assert result["total"] == 2
    assert result["payers"] == "DEAL_IN_PLAYER"


def test_tsumo_payment():
    rule = RuleProfile(rule_name="test")
    calc = ChipCalculator(rule)
    result = calc.chip_payments(chip_count=2, is_tsumo=True)
    assert result["total"] == 6  # 2 × 3人
    assert result["per_player"] == 2
    assert result["payers"] == "ALL_OPPONENTS"


def test_chip_settlement_value():
    rule = RuleProfile(
        rule_name="test",
        chip_settlement=ChipSettlement(mode="SEPARATE", chip_value=1000),
    )
    calc = ChipCalculator(rule)
    assert calc.chip_settlement_value(4) == 4000


def test_chip_settlement_value_none():
    rule = RuleProfile(rule_name="test")
    calc = ChipCalculator(rule)
    assert calc.chip_settlement_value(4) is None
