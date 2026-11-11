from pydantic import BaseModel, field_validator
from uuid import UUID


class PhysicalTileSchema(BaseModel):
    suit: str
    rank: int
    variant: str = "normal"
    physical_id: str = ""


class MeldSchema(BaseModel):
    meld_type: str
    tiles: list[PhysicalTileSchema]
    stolen_from: int


class GameStateSchema(BaseModel):
    hand: list[PhysicalTileSchema]
    drawn_tile: PhysicalTileSchema | None = None
    melds: list[MeldSchema] = []
    discards: list[list[PhysicalTileSchema]] = [[], [], [], []]
    dora_indicators: list[PhysicalTileSchema] = []
    scores: list[int]
    chips: list[int]
    round_wind: str
    hand_number: int
    honba: int
    riichi_sticks: int
    dealer: int
    player_seat: int
    junme: int | None = None
    remaining_hands: int | None = None
    rule_version_id: UUID

    @field_validator("scores", "chips")
    @classmethod
    def must_be_four(cls, v: list) -> list:
        if len(v) != 4:
            raise ValueError("4要素必要")
        return v


class ShantenRequest(BaseModel):
    game_state: GameStateSchema


class ShantenResponse(BaseModel):
    shanten: int


class UkeireEntry(BaseModel):
    tile_type: str
    remaining_count: int


class UkeireRequest(BaseModel):
    game_state: GameStateSchema


class UkeireResponse(BaseModel):
    ukeire: list[UkeireEntry]
    total_ukeire: int


class ScoringRequest(BaseModel):
    game_state: GameStateSchema
    win_tile: PhysicalTileSchema
    is_tsumo: bool = False
    is_riichi: bool = False


class ScoringResponse(BaseModel):
    han: int
    fu: int
    cost: dict
    yaku: list[dict]
    blue_tile_count: int
    chip_count: int
    error: str | None = None
