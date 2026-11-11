from fastapi import APIRouter, HTTPException

from mahjong_engine.adapters.mahjong_repository_adapter import MahjongRepositoryAdapter
from mahjong_engine.analysis.danger_calculator import DangerCalculator
from mahjong_engine.analysis.hand_ev import HandEvCalculator
from mahjong_engine.analysis.round_ev import PushFoldAnalyzer, RoundEvCalculator
from mahjong_engine.analysis.win_probability import WinProbabilityCalculator
from mahjong_engine.domain.game_state import GameState
from mahjong_engine.domain.meld import Meld, MeldType
from mahjong_engine.domain.rule_profile import RuleProfile
from mahjong_engine.domain.tile import PhysicalTile, Suit, TileType, TileVariant
from mahjong_engine.efficiency.shanten_calculator import ShantenCalculator
from mahjong_engine.efficiency.ukeire_calculator import UkeireCalculator
from mahjong_engine.rules.chip_calculator import ChipCalculator
from mahjong_engine.rules.dora_calculator import DoraCalculator
from mahjong_engine.scoring.score_calculator import ScoreCalculator
from mahjong_engine.simulation.match_simulator import MatchSimulator
from mahjong_engine.simulation.placement_calculator import PlacementCalculator
from schemas.analysis import (
    ShantenRequest, ShantenResponse,
    UkeireRequest, UkeireResponse,
    ScoringRequest, ScoringResponse,
    PhysicalTileSchema, MeldSchema,
)
from schemas.discard import DiscardsRequest, DiscardsResponse, DiscardCandidateResult
from schemas.match_ev import MatchEvRequest, MatchEvResponse, PlacementDistribution
from schemas.push_fold import PushFoldRequest, PushFoldResponse

router = APIRouter()
_adapter = MahjongRepositoryAdapter()
_shanten_calc = ShantenCalculator(_adapter)
_ukeire_calc = UkeireCalculator(_adapter)
_score_calc = ScoreCalculator(_adapter)
_win_prob_calc = WinProbabilityCalculator()
_hand_ev_calc = HandEvCalculator(_adapter)
_danger_calc = DangerCalculator()
_round_ev_calc = RoundEvCalculator(_win_prob_calc, _hand_ev_calc, _danger_calc)
_push_fold = PushFoldAnalyzer(_round_ev_calc, _danger_calc)
_placement_calc = PlacementCalculator()
_match_sim = MatchSimulator(_placement_calc)


def _to_physical_tile(s: PhysicalTileSchema) -> PhysicalTile:
    tile_type = TileType(suit=Suit(s.suit), rank=s.rank)
    variant = TileVariant(s.variant)
    return PhysicalTile(tile_type=tile_type, variant=variant, physical_id=s.physical_id)


def _to_meld(s: MeldSchema) -> Meld:
    return Meld(
        meld_type=MeldType(s.meld_type),
        tiles=tuple(_to_physical_tile(t) for t in s.tiles),
        stolen_from=s.stolen_from,
    )


def _to_game_state(s) -> GameState:
    return GameState(
        hand=[_to_physical_tile(t) for t in s.hand],
        drawn_tile=_to_physical_tile(s.drawn_tile) if s.drawn_tile else None,
        melds=[_to_meld(m) for m in s.melds],
        discards=[[_to_physical_tile(t) for t in row] for row in s.discards],
        dora_indicators=[_to_physical_tile(t) for t in s.dora_indicators],
        scores=s.scores,
        chips=s.chips,
        round_wind=s.round_wind,
        hand_number=s.hand_number,
        honba=s.honba,
        riichi_sticks=s.riichi_sticks,
        dealer=s.dealer,
        player_seat=s.player_seat,
        junme=s.junme,
        remaining_hands=s.remaining_hands,
        rule_version_id=s.rule_version_id,
    )


def _default_rule() -> RuleProfile:
    return RuleProfile(rule_name="default")


@router.post("/shanten", response_model=ShantenResponse)
async def shanten(req: ShantenRequest) -> ShantenResponse:
    game_state = _to_game_state(req.game_state)
    errors = game_state.validate()
    if errors:
        raise HTTPException(status_code=422, detail=errors)

    hand = game_state.hand + ([game_state.drawn_tile] if game_state.drawn_tile else [])
    shanten_num = _shanten_calc.calculate(hand, game_state.melds)
    return ShantenResponse(shanten=shanten_num)


@router.post("/ukeire", response_model=UkeireResponse)
async def ukeire(req: UkeireRequest) -> UkeireResponse:
    game_state = _to_game_state(req.game_state)
    errors = game_state.validate()
    if errors:
        raise HTTPException(status_code=422, detail=errors)

    rule = _default_rule()
    hand = game_state.hand + ([game_state.drawn_tile] if game_state.drawn_tile else [])
    entries = _ukeire_calc.calculate(hand, game_state.melds, game_state, rule)
    return UkeireResponse(ukeire=entries, total_ukeire=sum(e["remaining_count"] for e in entries))


@router.post("/scoring", response_model=ScoringResponse)
async def scoring(req: ScoringRequest) -> ScoringResponse:
    game_state = _to_game_state(req.game_state)
    win_tile = _to_physical_tile(req.win_tile)
    rule = _default_rule()

    context = {
        "is_tsumo": req.is_tsumo,
        "is_riichi": req.is_riichi,
        "dora_indicators": [
            {"suit": t.tile_type.suit.value, "rank": t.tile_type.rank}
            for t in game_state.dora_indicators
        ],
    }

    result = _score_calc.calculate(
        game_state.hand, win_tile, game_state.melds, context, rule
    )

    if "error" in result and result["error"]:
        return ScoringResponse(
            han=0, fu=0, cost={}, yaku=[], blue_tile_count=0, chip_count=0,
            error=result["error"],
        )

    return ScoringResponse(
        han=result.get("han", 0),
        fu=result.get("fu", 0),
        cost=result.get("cost", {}),
        yaku=result.get("yaku", []),
        blue_tile_count=result.get("blue_tile_count", 0),
        chip_count=result.get("chip_count", 0),
    )


@router.post("/discards", response_model=DiscardsResponse)
async def discards(req: DiscardsRequest) -> DiscardsResponse:
    game_state = _to_game_state(req.game_state)
    errors = game_state.validate()
    if errors:
        raise HTTPException(status_code=422, detail=errors)

    rule = _default_rule()
    dora_calc = DoraCalculator(rule)
    chip_calc = ChipCalculator(rule)

    full_hand = game_state.hand + ([game_state.drawn_tile] if game_state.drawn_tile else [])
    total_tiles = len(full_hand) + sum(len(m.tiles) for m in game_state.melds)
    if total_tiles != 14:
        raise HTTPException(
            status_code=422,
            detail=f"打牌分析には14枚（手牌+ツモ牌）が必要です（現在: {total_tiles}枚）。ツモ牌を入力してください。",
        )

    melds_tiles = [t for m in game_state.melds for t in m.tiles]
    candidates = []

    for discard in full_hand:
        hand_after = [t for t in full_hand if t is not discard]

        shanten = _shanten_calc.calculate(hand_after, game_state.melds)
        ukeire = _ukeire_calc.calculate_after_discard(
            full_hand, discard, game_state.melds, game_state, rule
        )
        dora = dora_calc.count_dora(hand_after, melds_tiles, game_state.dora_indicators)
        chip_count = chip_calc.count_chips(hand_after, melds_tiles, is_win=True)

        ukeire_count = sum(e["remaining_count"] for e in ukeire)
        ev_data = _round_ev_calc.calculate(
            shanten,
            ukeire_count,
            ukeire,
            hand_after,
            game_state.melds,
            discard,
            game_state,
            rule,
        )

        candidates.append(DiscardCandidateResult(
            discard=str(discard),
            shanten=shanten,
            ukeire=ukeire,
            total_ukeire=ukeire_count,
            normal_dora=dora["normal_dora"],
            red_dora=dora["red_dora"],
            blue_dora=dora["blue_dora"],
            total_dora_han=dora["total_dora_han"],
            chip_count_on_win=chip_count,
            win_probability=ev_data["win_probability"],
            expected_han=ev_data["expected_han"],
            expected_cost=ev_data["expected_cost"],
            deal_in_probability=ev_data["deal_in_probability"],
            round_ev=ev_data["round_ev"],
        ))

    candidates.sort(key=lambda c: (c.shanten, -c.total_ukeire))
    return DiscardsResponse(candidates=candidates)


@router.post("/push-fold", response_model=PushFoldResponse)
async def push_fold(req: PushFoldRequest) -> PushFoldResponse:
    game_state = _to_game_state(req.game_state)
    errors = game_state.validate()
    if errors:
        raise HTTPException(status_code=422, detail=errors)

    rule = _default_rule()

    push_tile = _to_physical_tile(req.push_discard)
    fold_tile = _to_physical_tile(req.fold_discard)

    full_hand = game_state.hand + ([game_state.drawn_tile] if game_state.drawn_tile else [])

    # push_tile はスキーマ経由の新規オブジェクトなので is not は使えない。
    # tile_type が一致する最初の1枚だけを取り除く。
    idx = next((i for i, t in enumerate(full_hand) if t.tile_type == push_tile.tile_type), -1)
    if idx < 0:
        raise HTTPException(status_code=422, detail="push_discard が手牌に存在しません")
    hand_after_push = full_hand[:idx] + full_hand[idx + 1:]

    shanten = _shanten_calc.calculate(hand_after_push, game_state.melds)
    ukeire_entries = _ukeire_calc.calculate(hand_after_push, game_state.melds, game_state, rule)
    ukeire_count = sum(e["remaining_count"] for e in ukeire_entries)

    result = _push_fold.analyze(
        hand=hand_after_push,
        melds=game_state.melds,
        shanten=shanten,
        ukeire_count=ukeire_count,
        ukeire_entries=ukeire_entries,
        push_discard=push_tile,
        fold_discard=fold_tile,
        game_state=game_state,
        rule=rule,
    )

    return PushFoldResponse(
        recommendation=result["recommendation"],
        push_ev=result["push_ev"],
        fold_ev=result["fold_ev"],
        ev_diff=result["ev_diff"],
        push_win_probability=result["push_win_probability"],
        push_deal_in_probability=result["push_deal_in_probability"],
        fold_deal_in_probability=result["fold_deal_in_probability"],
    )


@router.post("/match-ev", response_model=MatchEvResponse)
async def match_ev(req: MatchEvRequest) -> MatchEvResponse:
    game_state = _to_game_state(req.game_state)
    errors = game_state.validate()
    if errors:
        raise HTTPException(status_code=422, detail=errors)

    rule = _default_rule()
    discard = _to_physical_tile(req.discard)

    full_hand = game_state.hand + ([game_state.drawn_tile] if game_state.drawn_tile else [])
    idx = next((i for i, t in enumerate(full_hand) if t.tile_type == discard.tile_type), -1)
    if idx < 0:
        raise HTTPException(status_code=422, detail="discard が手牌に存在しません")
    hand_after = full_hand[:idx] + full_hand[idx + 1:]

    shanten = _shanten_calc.calculate(hand_after, game_state.melds)
    ukeire = _ukeire_calc.calculate(hand_after, game_state.melds, game_state, rule)
    ukeire_count = sum(e["remaining_count"] for e in ukeire)

    ev_data = _round_ev_calc.calculate(
        shanten, ukeire_count, ukeire,
        hand_after, game_state.melds, discard, game_state, rule,
    )

    result = _match_sim.simulate(
        game_state=game_state,
        win_probability=ev_data["win_probability"],
        expected_cost=ev_data["expected_cost"],
        deal_in_probability=ev_data["deal_in_probability"],
        opponent_types=req.opponent_models,
        rule=rule,
        n_simulations=req.n_simulations,
    )

    dist = result["placement_distribution"]
    return MatchEvResponse(
        placement_distribution=PlacementDistribution(
            first=dist.get(1, 0.0),
            second=dist.get(2, 0.0),
            third=dist.get(3, 0.0),
            fourth=dist.get(4, 0.0),
        ),
        mean_placement=result["mean_placement"],
        mean_final_score=result["mean_final_score"],
        ci_low_95=result["confidence_interval_95"][0],
        ci_high_95=result["confidence_interval_95"][1],
        simulation_count=result["simulation_count"],
    )
