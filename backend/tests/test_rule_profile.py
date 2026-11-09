from mahjong_engine.domain.rule_profile import RuleProfile, RedTileConfig, BlueTileConfig


def test_normal_count_default():
    rule = RuleProfile(rule_name="test")
    assert rule.normal_count_per_suit() == 2  # 4 - 1(red) - 1(blue)


def test_no_special_tiles():
    rule = RuleProfile(
        rule_name="test",
        red_tile=RedTileConfig(count_per_suit=0),
        blue_tile=BlueTileConfig(count_per_suit=0),
    )
    assert rule.normal_count_per_suit() == 4
    assert rule.validate() == []


def test_validation_overflow():
    rule = RuleProfile(
        rule_name="test",
        red_tile=RedTileConfig(count_per_suit=4),
        blue_tile=BlueTileConfig(count_per_suit=1),
    )
    errors = rule.validate()
    assert len(errors) > 0


def test_validation_blue_count_invalid():
    rule = RuleProfile(
        rule_name="test",
        blue_tile=BlueTileConfig(count_per_suit=2),
    )
    errors = rule.validate()
    assert any("青牌" in e for e in errors)
