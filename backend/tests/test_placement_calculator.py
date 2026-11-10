import pytest
from mahjong_engine.simulation.placement_calculator import PlacementCalculator
from mahjong_engine.domain.rule_profile import RuleProfile, ScoringConfig, UmaConfig


def _rule(uma=(30000, 10000, -10000, -30000), oka=0):
    return RuleProfile(
        rule_name="test",
        scoring=ScoringConfig(
            uma=UmaConfig(first=uma[0], second=uma[1], third=uma[2], fourth=uma[3]),
            oka=oka,
        ),
    )


@pytest.fixture
def calc():
    return PlacementCalculator()


class TestCalculatePlacements:
    def test_distinct_scores(self, calc):
        # 40000 > 30000 > 20000 > 10000 → 1,2,3,4
        result = calc.calculate_placements([40000, 30000, 20000, 10000])
        assert result == [1, 2, 3, 4]

    def test_descending_order(self, calc):
        result = calc.calculate_placements([10000, 20000, 40000, 30000])
        assert result == [4, 3, 1, 2]

    def test_tie_initial_dealer_seat0(self, calc):
        # seat 0 と seat 2 が同点 → seat 0 が上位
        result = calc.calculate_placements([30000, 25000, 30000, 15000], initial_dealer=0)
        assert result[0] < result[2]

    def test_tie_initial_dealer_seat1(self, calc):
        # 起家が seat 1 → seat 1 が同点では有利
        result = calc.calculate_placements([30000, 30000, 25000, 15000], initial_dealer=1)
        assert result[1] < result[0]

    def test_all_equal(self, calc):
        # 全員同点 → 起家(seat0)が1位
        result = calc.calculate_placements([25000, 25000, 25000, 25000], initial_dealer=0)
        assert result[0] == 1
        assert sorted(result) == [1, 2, 3, 4]


class TestCalculateUma:
    def test_basic_uma(self, calc):
        rule = _rule(uma=(30000, 10000, -10000, -30000))
        # placements = [1, 2, 3, 4]
        uma = calc.calculate_uma([1, 2, 3, 4], rule)
        assert uma == [30000, 10000, -10000, -30000]

    def test_zero_uma(self, calc):
        rule = _rule(uma=(0, 0, 0, 0))
        uma = calc.calculate_uma([3, 1, 4, 2], rule)
        assert uma == [0, 0, 0, 0]

    def test_uma_sum_zero(self, calc):
        rule = _rule(uma=(30000, 10000, -10000, -30000))
        uma = calc.calculate_uma([1, 2, 3, 4], rule)
        assert sum(uma) == 0


class TestCalculateFinalPoints:
    def test_kaeshi_applied(self, calc):
        # 全員30000点 → 返し後0点
        rule = _rule(uma=(0, 0, 0, 0))
        scores = [30000, 30000, 30000, 30000]
        placements = [1, 2, 3, 4]
        final = calc.calculate_final_points(scores, placements, rule)
        assert all(p == 0 for p in final)

    def test_uma_added(self, calc):
        rule = _rule(uma=(30000, 10000, -10000, -30000))
        scores = [30000, 30000, 30000, 30000]
        placements = [1, 2, 3, 4]
        final = calc.calculate_final_points(scores, placements, rule)
        assert final == [30000, 10000, -10000, -30000]

    def test_oka_to_first(self, calc):
        rule = _rule(uma=(0, 0, 0, 0), oka=20000)
        scores = [40000, 30000, 25000, 25000]
        placements = calc.calculate_placements(scores)
        final = calc.calculate_final_points(scores, placements, rule)
        # 1位(seat0)だけ oka を受け取る
        assert final[0] == (40000 - 30000) + 20000

    def test_zero_sum_no_oka(self, calc):
        rule = _rule(uma=(30000, 10000, -10000, -30000))
        scores = [45000, 32000, 15000, 8000]
        placements = calc.calculate_placements(scores)
        final = calc.calculate_final_points(scores, placements, rule)
        # uma の和がゼロなので精算点の合計も概ねゼロ
        # (素点の和が30000*4=120000から外れている分だけずれる)
        total_base = sum(s - 30000 for s in scores)
        assert sum(final) == total_base
