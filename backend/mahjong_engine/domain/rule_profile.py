from dataclasses import dataclass, field


@dataclass(frozen=True)
class RedTileConfig:
    count_per_suit: int = 1
    han: int = 1


@dataclass(frozen=True)
class ChipPayer:
    ron: str = "DEAL_IN_PLAYER"
    tsumo: str = "ALL_OPPONENTS"


@dataclass(frozen=True)
class BlueTileConfig:
    count_per_suit: int = 1
    han: int = 1
    chip_enabled: bool = True
    chips_per_blue_tile: int = 2
    chip_trigger: str = "AGARI_WITH_BLUE"
    chip_payer: ChipPayer = field(default_factory=ChipPayer)


@dataclass(frozen=True)
class ChipSettlement:
    mode: str = "SEPARATE"
    chip_value: int | None = None


@dataclass(frozen=True)
class UmaConfig:
    first: int = 0
    second: int = 0
    third: int = 0
    fourth: int = 0


@dataclass(frozen=True)
class ScoringConfig:
    oka: int | None = None
    uma: UmaConfig = field(default_factory=UmaConfig)
    tie_break: str = "DEALER_ORDER"
    last_round_win_stop: bool = False


@dataclass(frozen=True)
class RuleProfile:
    rule_name: str
    player_count: int = 4
    red_tile: RedTileConfig = field(default_factory=RedTileConfig)
    blue_tile: BlueTileConfig = field(default_factory=BlueTileConfig)
    chip_settlement: ChipSettlement = field(default_factory=ChipSettlement)
    scoring: ScoringConfig = field(default_factory=ScoringConfig)

    def normal_count_per_suit(self) -> int:
        return 4 - self.red_tile.count_per_suit - self.blue_tile.count_per_suit

    def validate(self) -> list[str]:
        errors = []
        if self.normal_count_per_suit() < 0:
            errors.append(
                f"赤牌({self.red_tile.count_per_suit}枚) + 青牌({self.blue_tile.count_per_suit}枚) > 4枚"
            )
        if self.blue_tile.count_per_suit not in (0, 1):
            errors.append("青牌の枚数は0または1のみ有効")
        if not (0 <= self.red_tile.count_per_suit <= 4):
            errors.append("赤牌の枚数は0〜4の範囲で指定")
        return errors
