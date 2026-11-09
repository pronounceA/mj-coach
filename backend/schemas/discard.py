from pydantic import BaseModel
from schemas.analysis import GameStateSchema


class DiscardCandidateResult(BaseModel):
    discard: str
    shanten: int
    ukeire: list[dict]
    total_ukeire: int
    normal_dora: int
    red_dora: int
    blue_dora: int
    total_dora_han: int
    chip_count_on_win: int


class DiscardsRequest(BaseModel):
    game_state: GameStateSchema


class DiscardsResponse(BaseModel):
    candidates: list[DiscardCandidateResult]
