from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from mahjong_engine.domain.rule_profile import (
    BlueTileConfig, ChipPayer, ChipSettlement, RedTileConfig,
    RuleProfile, ScoringConfig, UmaConfig,
)
from models.rule_profile import RuleProfileModel, RuleProfileVersionModel
from schemas.rule_profile import (
    RuleDefinitionSchema, RuleProfileCreateRequest, RuleProfileResponse,
    RuleProfileUpdateRequest, RuleProfileVersionResponse, ValidateResponse,
)

router = APIRouter()

_SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def _definition_to_domain(d: RuleDefinitionSchema) -> RuleProfile:
    return RuleProfile(
        rule_name="",
        player_count=d.player_count,
        red_tile=RedTileConfig(
            count_per_suit=d.red_tile.count_per_suit,
            han=d.red_tile.han,
        ),
        blue_tile=BlueTileConfig(
            count_per_suit=d.blue_tile.count_per_suit,
            han=d.blue_tile.han,
            chip_enabled=d.blue_tile.chip_enabled,
            chips_per_blue_tile=d.blue_tile.chips_per_blue_tile,
            chip_trigger=d.blue_tile.chip_trigger,
            chip_payer=ChipPayer(
                ron=d.blue_tile.chip_payer.ron,
                tsumo=d.blue_tile.chip_payer.tsumo,
            ),
        ),
        chip_settlement=ChipSettlement(
            mode=d.chip_settlement.mode,
            chip_value=d.chip_settlement.chip_value,
        ),
        scoring=ScoringConfig(
            oka=d.scoring.oka,
            uma=UmaConfig(
                first=d.scoring.uma.first,
                second=d.scoring.uma.second,
                third=d.scoring.uma.third,
                fourth=d.scoring.uma.fourth,
            ),
            tie_break=d.scoring.tie_break,
            last_round_win_stop=d.scoring.last_round_win_stop,
        ),
    )


def _to_response(
    profile: RuleProfileModel, version: RuleProfileVersionModel | None
) -> RuleProfileResponse:
    latest = None
    if version:
        latest = RuleProfileVersionResponse(
            id=version.id,
            version=version.version,
            definition=version.definition,
            is_active=version.is_active,
            created_at=version.created_at,
        )
    return RuleProfileResponse(
        id=profile.id,
        name=profile.name,
        description=profile.description,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        latest_version=latest,
    )


@router.get("", response_model=list[RuleProfileResponse])
async def list_rules(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RuleProfileModel).options(selectinload(RuleProfileModel.versions))
    )
    profiles = result.scalars().all()
    return [
        _to_response(p, max(p.versions, key=lambda v: v.version, default=None))
        for p in profiles
    ]


@router.post("", response_model=RuleProfileResponse, status_code=201)
async def create_rule(
    req: RuleProfileCreateRequest, db: AsyncSession = Depends(get_db)
):
    errors = _definition_to_domain(req.definition).validate()
    if errors:
        raise HTTPException(status_code=422, detail=errors)

    profile = RuleProfileModel(
        name=req.name,
        description=req.description,
        created_by=_SYSTEM_USER_ID,
    )
    db.add(profile)
    await db.flush()

    version = RuleProfileVersionModel(
        rule_profile_id=profile.id,
        version=1,
        definition=req.definition.model_dump(),
        is_active=True,
    )
    db.add(version)
    await db.commit()
    await db.refresh(profile)
    return _to_response(profile, version)


@router.get("/{rule_id}", response_model=RuleProfileResponse)
async def get_rule(rule_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RuleProfileModel)
        .where(RuleProfileModel.id == rule_id)
        .options(selectinload(RuleProfileModel.versions))
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="ルールプロファイルが見つかりません")
    latest = max(profile.versions, key=lambda v: v.version, default=None)
    return _to_response(profile, latest)


@router.put("/{rule_id}", response_model=RuleProfileResponse)
async def update_rule(
    rule_id: UUID, req: RuleProfileUpdateRequest, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(RuleProfileModel)
        .where(RuleProfileModel.id == rule_id)
        .options(selectinload(RuleProfileModel.versions))
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="ルールプロファイルが見つかりません")

    if req.definition:
        errors = _definition_to_domain(req.definition).validate()
        if errors:
            raise HTTPException(status_code=422, detail=errors)

    if req.name is not None:
        profile.name = req.name
    if req.description is not None:
        profile.description = req.description

    new_version = None
    if req.definition:
        latest_ver = max((v.version for v in profile.versions), default=0)
        new_version = RuleProfileVersionModel(
            rule_profile_id=profile.id,
            version=latest_ver + 1,
            definition=req.definition.model_dump(),
            is_active=True,
        )
        db.add(new_version)

    await db.commit()
    await db.refresh(profile)

    latest = new_version or max(profile.versions, key=lambda v: v.version, default=None)
    return _to_response(profile, latest)


@router.delete("/{rule_id}", status_code=204)
async def delete_rule(rule_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RuleProfileModel).where(RuleProfileModel.id == rule_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="ルールプロファイルが見つかりません")
    await db.delete(profile)
    await db.commit()


@router.post("/{rule_id}/validate", response_model=ValidateResponse)
async def validate_rule(rule_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RuleProfileVersionModel)
        .where(RuleProfileVersionModel.rule_profile_id == rule_id)
        .order_by(RuleProfileVersionModel.version.desc())
    )
    version = result.scalars().first()
    if not version:
        raise HTTPException(status_code=404, detail="ルールプロファイルが見つかりません")

    definition = RuleDefinitionSchema(**version.definition)
    errors = _definition_to_domain(definition).validate()
    return ValidateResponse(valid=len(errors) == 0, errors=errors)
