from dataclasses import dataclass
from enum import Enum


class Suit(str, Enum):
    MAN = "m"
    PIN = "p"
    SOU = "s"
    HONOR = "z"


class TileVariant(str, Enum):
    NORMAL = "normal"
    RED = "red"
    BLUE = "blue"


class Wind(str, Enum):
    EAST = "east"
    SOUTH = "south"
    WEST = "west"
    NORTH = "north"


@dataclass(frozen=True)
class TileType:
    suit: Suit
    rank: int

    def __post_init__(self) -> None:
        if self.suit == Suit.HONOR:
            if not (1 <= self.rank <= 7):
                raise ValueError(f"字牌のrankは1〜7: {self.rank}")
        else:
            if not (1 <= self.rank <= 9):
                raise ValueError(f"数牌のrankは1〜9: {self.rank}")

    def __str__(self) -> str:
        return f"{self.rank}{self.suit.value}"


@dataclass(frozen=True)
class PhysicalTile:
    tile_type: TileType
    variant: TileVariant = TileVariant.NORMAL
    physical_id: str = ""

    def is_red(self) -> bool:
        return self.variant == TileVariant.RED

    def is_blue(self) -> bool:
        return self.variant == TileVariant.BLUE

    def __str__(self) -> str:
        prefix = {"normal": "", "red": "r", "blue": "b"}[self.variant.value]
        return f"{prefix}{self.tile_type}"
