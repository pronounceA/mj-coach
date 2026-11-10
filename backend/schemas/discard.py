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
    win_probability: float = 0.0
    expected_han: float = 0.0
    expected_cost: int = 0
    deal_in_probability: float = 0.0
    round_ev: int = 0


class DiscardsRequest(BaseModel):
    game_state: GameStateSchema


class DiscardsResponse(BaseModel):
    candidates: list[DiscardCandidateResult]
