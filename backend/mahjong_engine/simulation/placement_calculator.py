from __future__ import annotations

from mahjong_engine.domain.rule_profile import RuleProfile

_KAESHI = 30_000


class PlacementCalculator:
    """順位・ウマ・精算点を計算する。"""

    def calculate_placements(
        self, scores: list[int], initial_dealer: int = 0
    ) -> list[int]:
        """各座席の1始まり順位を返す。

        同点の場合は起家(initial_dealer)に近い座席を上位とする。
        """
        n = len(scores)

        def _tiebreak(seat: int) -> int:
            return (seat - initial_dealer) % n

        indexed = sorted(range(n), key=lambda s: (-scores[s], _tiebreak(s)))
        placements = [0] * n
        for rank, seat in enumerate(indexed):
            placements[seat] = rank + 1
        return placements

    def calculate_uma(
        self, placements: list[int], rule: RuleProfile
    ) -> list[int]:
        """ウマポイント（点棒単位）を返す。"""
        uma_map = {
            1: rule.scoring.uma.first,
            2: rule.scoring.uma.second,
            3: rule.scoring.uma.third,
            4: rule.scoring.uma.fourth,
        }
        return [uma_map[p] for p in placements]

    def calculate_final_points(
        self,
        scores: list[int],
        placements: list[int],
        rule: RuleProfile,
    ) -> list[int]:
        """精算点（点棒）= (素点 − 返し点) + ウマ [+ オカ(1位のみ)]。"""
        uma = self.calculate_uma(placements, rule)
        oka = rule.scoring.oka or 0
        result = []
        for score, placement, u in zip(scores, placements, uma):
            pts = (score - _KAESHI) + u
            if placement == 1:
                pts += oka
            result.append(pts)
        return result
