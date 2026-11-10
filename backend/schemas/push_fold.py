from pydantic import BaseModel

from schemas.analysis import GameStateSchema, PhysicalTileSchema


class PushFoldRequest(BaseModel):
    game_state: GameStateSchema
    push_discard: PhysicalTileSchema
    fold_discard: PhysicalTileSchema


class PushFoldResponse(BaseModel):
    recommendation: str  # "push" | "fold"
    push_ev: int
    fold_ev: int
    ev_diff: int
    push_win_probability: float
    push_deal_in_probability: float
    fold_deal_in_probability: float
