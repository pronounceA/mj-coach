from dataclasses import dataclass, field
from uuid import UUID

from mahjong_engine.domain.meld import Meld
from mahjong_engine.domain.tile import PhysicalTile, TileType, TileVariant, Suit


@dataclass
class GameState:
    hand: list[PhysicalTile]
    scores: list[int]
    chips: list[int]
    round_wind: str
    hand_number: int
    honba: int
    riichi_sticks: int
    dealer: int
    player_seat: int
    rule_version_id: UUID
    drawn_tile: PhysicalTile | None = None
    melds: list[Meld] = field(default_factory=list)
    discards: list[list[PhysicalTile]] = field(default_factory=lambda: [[], [], [], []])
    dora_indicators: list[PhysicalTile] = field(default_factory=list)
    remaining_hands: int | None = None

    def validate(self) -> list[str]:
        errors = []

        total_tiles = len(self.hand) + sum(len(m.tiles) for m in self.melds)
        if drawn_tile := self.drawn_tile:
            total_tiles += 1
        if total_tiles not in (13, 14):
            errors.append(f"手牌 + 副露の合計枚数が不正: {total_tiles}枚")

        all_tiles = list(self.hand) + (
            [self.drawn_tile] if self.drawn_tile else []
        )
        seen: dict[str, int] = {}
        for tile in all_tiles:
            key = tile.physical_id
            if key:
                seen[key] = seen.get(key, 0) + 1
                if seen[key] > 1:
                    errors.append(f"同一物理牌の重複: {tile}")

        if len(self.scores) != 4:
            errors.append("scoresは4要素必要")
        if len(self.chips) != 4:
            errors.append("chipsは4要素必要")
        if not (0 <= self.dealer <= 3):
            errors.append(f"dealerは0〜3: {self.dealer}")
        if not (0 <= self.player_seat <= 3):
            errors.append(f"player_seatは0〜3: {self.player_seat}")

        return errors

    def all_known_tiles(self) -> list[PhysicalTile]:
        tiles = list(self.hand)
        if self.drawn_tile:
            tiles.append(self.drawn_tile)
        for meld in self.melds:
            tiles.extend(meld.tiles)
        for player_discards in self.discards:
            tiles.extend(player_discards)
        tiles.extend(self.dora_indicators)
        return tiles

    def count_tile_type(self, tile_type: TileType) -> int:
        return sum(1 for t in self.all_known_tiles() if t.tile_type == tile_type)
