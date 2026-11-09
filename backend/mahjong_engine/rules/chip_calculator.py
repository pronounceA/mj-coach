from mahjong_engine.domain.rule_profile import RuleProfile
from mahjong_engine.domain.tile import PhysicalTile, TileVariant


class ChipCalculator:
    def __init__(self, rule: RuleProfile) -> None:
        self._rule = rule

    def count_chips(
        self,
        hand: list[PhysicalTile],
        melds_tiles: list[PhysicalTile],
        is_win: bool,
    ) -> int:
        """和了時のチップ獲得枚数を計算する。"""
        if not self._rule.blue_tile.chip_enabled or not is_win:
            return 0

        all_tiles = hand + melds_tiles
        blue_count = sum(1 for t in all_tiles if t.variant == TileVariant.BLUE)
        return blue_count * self._rule.blue_tile.chips_per_blue_tile

    def chip_payments(self, chip_count: int, is_tsumo: bool) -> dict:
        """チップの支払い内訳を返す。
        ロン: 放銃者が全額支払う
        ツモ: 他3人がそれぞれ全額支払う
        """
        if chip_count == 0:
            return {"total": 0, "per_player": 0, "payers": "none"}

        if is_tsumo:
            return {
                "total": chip_count * 3,
                "per_player": chip_count,
                "payers": self._rule.blue_tile.chip_payer.tsumo,
            }
        else:
            return {
                "total": chip_count,
                "per_player": chip_count,
                "payers": self._rule.blue_tile.chip_payer.ron,
            }

    def chip_settlement_value(self, chip_count: int) -> int | None:
        """チップの点棒換算額を返す。chip_value が未設定なら None。"""
        if self._rule.chip_settlement.chip_value is None:
            return None
        return chip_count * self._rule.chip_settlement.chip_value
