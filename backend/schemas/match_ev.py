from pydantic import BaseModel, Field

from schemas.analysis import GameStateSchema, PhysicalTileSchema


class MatchEvRequest(BaseModel):
    game_state: GameStateSchema
    discard: PhysicalTileSchema
    opponent_models: list[str] = Field(default=["basic", "basic", "basic"])
    n_simulations: int = Field(default=2000, ge=50, le=5000)


class PlacementDistribution(BaseModel):
    first: float
    second: float
    third: float
    fourth: float


class MatchEvResponse(BaseModel):
    placement_distribution: PlacementDistribution
    mean_placement: float
    mean_final_score: float
    ci_low_95: float
    ci_high_95: float
    simulation_count: int
