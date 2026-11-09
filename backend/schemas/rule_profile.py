from pydantic import BaseModel, field_validator
from uuid import UUID
from datetime import datetime


class RedTileConfigSchema(BaseModel):
    count_per_suit: int = 1
    han: int = 1


class ChipPayerSchema(BaseModel):
    ron: str = "DEAL_IN_PLAYER"
    tsumo: str = "ALL_OPPONENTS"


class BlueTileConfigSchema(BaseModel):
    count_per_suit: int = 1
    han: int = 1
    chip_enabled: bool = True
    chips_per_blue_tile: int = 2
    chip_trigger: str = "AGARI_WITH_BLUE"
    chip_payer: ChipPayerSchema = ChipPayerSchema()


class ChipSettlementSchema(BaseModel):
    mode: str = "SEPARATE"
    chip_value: int | None = None


class UmaConfigSchema(BaseModel):
    first: int = 0
    second: int = 0
    third: int = 0
    fourth: int = 0


class ScoringConfigSchema(BaseModel):
    oka: int | None = None
    uma: UmaConfigSchema = UmaConfigSchema()
    tie_break: str = "DEALER_ORDER"
    last_round_win_stop: bool = False


class RuleDefinitionSchema(BaseModel):
    player_count: int = 4
    red_tile: RedTileConfigSchema = RedTileConfigSchema()
    blue_tile: BlueTileConfigSchema = BlueTileConfigSchema()
    chip_settlement: ChipSettlementSchema = ChipSettlementSchema()
    scoring: ScoringConfigSchema = ScoringConfigSchema()


class RuleProfileCreateRequest(BaseModel):
    name: str
    description: str | None = None
    definition: RuleDefinitionSchema


class RuleProfileUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    definition: RuleDefinitionSchema


class RuleProfileVersionResponse(BaseModel):
    id: UUID
    version: int
    definition: dict
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class RuleProfileResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    latest_version: RuleProfileVersionResponse | None = None

    model_config = {"from_attributes": True}


class ValidateResponse(BaseModel):
    valid: bool
    errors: list[str]
